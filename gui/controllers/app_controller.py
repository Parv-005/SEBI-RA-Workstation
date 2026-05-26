import traceback
import json
from datetime import datetime
from PySide6.QtCore import QObject, QThreadPool
from PySide6.QtWidgets import QApplication

from gui.signals import get_signals
from gui.workers import Worker
from database.db_manager import (
    get_all_trades, get_trade, insert_trade,
    update_trade, get_trade_updates, insert_trade_update
)
from database.updates_db import get_formatted_updates_text
from services.trade_service import (
    calculate_risk_reward, compute_update_fields,
    to_display_action, to_db_action
)
from services.results import BroadcastResult
from services.telegram_service import TelegramService
from services.google_sheets_service import GoogleSheetsService
from services.image_generator import ImageGenerator
from utils.message_formatter import format_new_trade, format_trade_update
from utils.async_helper import run_async, run_async_in_thread
from core.config import Config
from utils.config_manager import save_config
from utils.constants import DATE_FMT_DB, THREAD_POOL_SIZE, AUTH_TIMEOUT_SEC, BROADCAST_NOT_CONFIGURED, BROADCAST_NOT_AUTHORIZED
from utils.logger import setup_logger
import threading
import asyncio

logger = setup_logger("AppController")


def _parse_telegram_msg_ids(raw: str | None) -> dict[str, int] | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        pass
    try:
        return {"Default": int(raw)}
    except (ValueError, TypeError):
        return None


def _load_config_groups() -> dict[str, str]:
    try:
        from core.paths import CONFIG_PATH
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
            return cfg.get("telegram", {}).get("groups", {})
    except Exception:
        pass
    return {}


def _build_update_targets(trade_code: str, config_groups: dict[str, str]):
    fresh = get_trade(trade_code)
    if not fresh:
        return None, None

    groups_raw = fresh.get("telegram_groups", "") or ""
    msg_id_raw = fresh.get("telegram_msg_id", "") or ""

    msg_ids = _parse_telegram_msg_ids(msg_id_raw)
    if not msg_ids:
        return None, None

    names = [n.strip() for n in groups_raw.split(",") if n.strip()]
    if not names:
        names = list(msg_ids.keys())

    groups = {}
    reply_to_map = {}
    for name in names:
        gid = config_groups.get(name)
        if gid is not None and name in msg_ids:
            groups[name] = gid
            reply_to_map[name] = msg_ids[name]

    if not groups:
        return None, None
    return groups, reply_to_map


def _sync_telegram_to_sheets(gs: GoogleSheetsService, trade_code: str, telegram_fields: dict, result: BroadcastResult):
    try:
        if gs and gs.is_configured():
            if not gs.sheet:
                gs.connect()
            gs.update_trade_row(trade_code, telegram_fields)
            logger.info(f"Synced telegram data to Google Sheets for {trade_code}")
    except Exception as e:
        logger.warning(f"Failed to sync telegram data to Google Sheets: {e}")
        result.errors.append(f"Sheets telegram sync: {e}")


class AppController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = get_signals()
        self._pool = QThreadPool.globalInstance()
        self._pool.setMaxThreadCount(THREAD_POOL_SIZE)
        self._auth_event = threading.Event()
        self._auth_input = None
        self._auth_input_lock = threading.Lock()

    def get_trades(self, filters=None):
        try:
            trades = get_all_trades(filters) if filters else get_all_trades()
            logger.debug(f"get_trades: filters={filters}, returned {len(trades)} trades")
            self.signals.trades_loaded.emit(trades)
            return trades
        except Exception as e:
            self.signals.trades_error.emit(str(e))
            return []

    def get_trade_by_code(self, trade_code):
        try:
            trade = get_trade(trade_code)
            updates = get_trade_updates(trade_code)
            self.signals.trade_detail_loaded.emit(trade, updates)
            return trade, updates
        except Exception as e:
            self.signals.trades_error.emit(str(e))
            return None, []

    def create_trade(self, trade_data):
        try:
            trade_code, enriched = insert_trade(trade_data)
            self.signals.trade_created.emit(trade_code)
            return trade_code, enriched
        except Exception as e:
            self.signals.trade_create_error.emit(str(e))
            return None, None

    def create_trade_and_broadcast(self, trade_data, selected_groups=None):
        trade_code, enriched = self.create_trade(trade_data)
        if not trade_code:
            return
        logger.info(f"Broadcasting new trade: {trade_code}, groups={list(selected_groups.keys()) if selected_groups else 'default'}")
        worker = Worker(self._do_broadcast_new_trade, enriched, selected_groups)
        worker.signals.done.connect(self._on_broadcast_done)
        worker.signals.error.connect(self._on_broadcast_error)
        self._pool.start(worker)

    def _do_broadcast_new_trade(self, trade, selected_groups=None):
        result = BroadcastResult()
        gs = None
        config = Config.get()
        image_enabled = config.get("broadcast", {}).get("image_generation_enabled", True)
        if image_enabled:
            try:
                img = ImageGenerator()
                img_path = img.generate_trade_image(trade)
                result.image_success = img_path is not None
                result.image_path = img_path
            except Exception as e:
                result.errors.append(f"Image: {e}")
        else:
            result.image_success = True
            result.image_path = None

        try:
            gs = GoogleSheetsService()
            if gs.is_configured():
                gs.connect()
                append_result = gs.append_trade(trade)
                result.sheets_success = append_result.success
                result.sheets_unmapped = append_result.unmapped_columns
            else:
                result.sheets_success = BROADCAST_NOT_CONFIGURED
        except Exception as e:
            result.errors.append(f"Sheets: {e}")
            logger.error(f"Sheets broadcast failed in new_trade: {e}", exc_info=True)

        try:
            tg = TelegramService()
            if tg.is_configured():
                if selected_groups:
                    async def _send():
                        try:
                            authed = await tg.connect()
                            if not authed:
                                return BROADCAST_NOT_AUTHORIZED
                            msg = format_new_trade(trade)
                            msg_ids, failures = await tg.send_to_groups(msg, selected_groups, result.image_path)
                            return ("multi", msg_ids, failures)
                        finally:
                            await tg.disconnect()

                    tg_result = run_async(_send())
                    if isinstance(tg_result, tuple) and tg_result[0] == "multi":
                        msg_ids = tg_result[1]
                        failures = tg_result[2]
                        if msg_ids:
                            result.telegram_success = True
                            result.telegram_msg_ids = msg_ids
                            telegram_fields = {
                                "telegram_msg_id": json.dumps(msg_ids),
                                "telegram_groups": ", ".join(msg_ids.keys())
                            }
                            try:
                                update_trade(trade["trade_code"], telegram_fields)
                            except Exception as e:
                                logger.warning(f"Failed to persist telegram data: {e}")
                            _sync_telegram_to_sheets(gs, trade["trade_code"], telegram_fields, result)
                        if failures:
                            result.telegram_failures = failures
                            for name, err in failures.items():
                                result.errors.append(f"Telegram ({name}): {err}")
                        if not msg_ids and failures:
                            result.telegram_success = False
                    elif tg_result == BROADCAST_NOT_AUTHORIZED:
                        result.telegram_success = BROADCAST_NOT_AUTHORIZED
                    else:
                        result.telegram_success = bool(tg_result)
                else:
                    async def _send():
                        try:
                            authed = await tg.connect()
                            if not authed:
                                return BROADCAST_NOT_AUTHORIZED
                            msg = format_new_trade(trade)
                            msg_id = await tg.send_trade_message(msg, result.image_path)
                            return msg_id
                        finally:
                            await tg.disconnect()

                    tg_result = run_async(_send())
                    if isinstance(tg_result, int):
                        result.telegram_success = True
                        result.telegram_msg_ids = {"Default": tg_result}
                        telegram_fields = {
                            "telegram_msg_id": str(tg_result),
                            "telegram_groups": "Default"
                        }
                        try:
                            update_trade(trade["trade_code"], telegram_fields)
                        except Exception as e:
                            logger.warning(f"Failed to persist telegram data: {e}")
                        _sync_telegram_to_sheets(gs, trade["trade_code"], telegram_fields, result)
                    elif tg_result == BROADCAST_NOT_AUTHORIZED:
                        result.telegram_success = BROADCAST_NOT_AUTHORIZED
                    else:
                        result.telegram_success = bool(tg_result)
            else:
                result.telegram_success = BROADCAST_NOT_CONFIGURED
        except Exception as e:
            result.errors.append(f"Telegram: {e}")
            logger.error(f"Telegram broadcast failed in new_trade: {e}", exc_info=True)

        return result

    def _on_broadcast_done(self, result):
        self.signals.broadcast_complete.emit(result)

    def _on_broadcast_error(self, err):
        result = BroadcastResult()
        result.errors.append(err)
        self.signals.broadcast_complete.emit(result)

    def update_trade_and_broadcast(
        self, trade, update_type, dynamic_values, remarks
    ):
        try:
            trade_updates, old_value, new_value, update_data_dict = (
                compute_update_fields(
                    trade, update_type, dynamic_values, remarks
                )
            )
        except ValueError as e:
            self.signals.trade_update_error.emit(str(e))
            return

        if not trade_updates:
            self.signals.trade_update_error.emit("No fields to update.")
            return

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trade_updates["updated_at"] = now_str

        try:
            insert_trade_update(update_data_dict)
            update_trade(trade["trade_code"], trade_updates)
            self.signals.trade_updated.emit(trade)
        except Exception as e:
            self.signals.trade_update_error.emit(str(e))
            return

        updates_text = get_formatted_updates_text(trade["trade_code"])
        trade_updates["updates"] = updates_text

        worker = Worker(
            self._do_broadcast_update,
            trade, update_data_dict, trade_updates
        )
        worker.signals.done.connect(self._on_update_broadcast_done)
        worker.signals.error.connect(self._on_update_broadcast_error)
        self._pool.start(worker)

    def _do_broadcast_update(self, trade, update_data_dict, trade_updates):
        result = BroadcastResult()
        gs = None
        config = Config.get()
        image_enabled = config.get("broadcast", {}).get("image_generation_enabled", True)
        if image_enabled:
            try:
                img = ImageGenerator()
                img_path = img.generate_update_image(trade, update_data_dict)
                result.image_success = img_path is not None
                result.image_path = img_path
            except Exception as e:
                result.errors.append(f"Image: {e}")
        else:
            result.image_success = True
            result.image_path = None

        try:
            gs = GoogleSheetsService()
            if gs.is_configured():
                gs.connect()
                gs_result = gs.update_trade_row(
                    trade["trade_code"], update_data_dict, trade_updates
                )
                if gs_result.get("success"):
                    result.sheets_success = True
                else:
                    err_msg = gs_result.get("error", "Failed")
                    result.sheets_success = False
                    result.errors.append(f"Sheets: {err_msg}")

                try:
                    gs.append_update_row(update_data_dict)
                except Exception as ue:
                    logger.warning(f"Failed to append update row to Updates sheet: {ue}")
            else:
                result.sheets_success = BROADCAST_NOT_CONFIGURED
        except Exception as e:
            result.errors.append(f"Sheets: {e}")
            logger.error(f"Sheets broadcast failed in update: {e}", exc_info=True)

        try:
            tg = TelegramService()
            if tg.is_configured():
                config_groups = _load_config_groups()
                groups, reply_to_map = _build_update_targets(trade["trade_code"], config_groups)

                if groups:
                    async def _send_multi():
                        try:
                            authed = await tg.connect()
                            if not authed:
                                return BROADCAST_NOT_AUTHORIZED
                            msg = format_trade_update(trade, update_data_dict)
                            msg_ids, failures = await tg.send_to_groups(msg, groups, result.image_path, reply_to_map)
                            return ("multi", msg_ids, failures)
                        finally:
                            await tg.disconnect()

                    tg_result = run_async(_send_multi())
                    if isinstance(tg_result, tuple) and tg_result[0] == "multi":
                        msg_ids = tg_result[1]
                        failures = tg_result[2]
                        if msg_ids:
                            result.telegram_success = True
                            result.telegram_msg_ids = msg_ids
                            telegram_fields = {
                                "telegram_msg_id": json.dumps(msg_ids),
                                "telegram_groups": ", ".join(msg_ids.keys())
                            }
                            try:
                                update_trade(trade["trade_code"], telegram_fields)
                            except Exception as e:
                                logger.warning(f"Failed to persist telegram data: {e}")
                            _sync_telegram_to_sheets(gs, trade["trade_code"], telegram_fields, result)
                        if failures:
                            result.telegram_failures = failures
                            for name, err in failures.items():
                                result.errors.append(f"Telegram ({name}): {err}")
                        if not msg_ids and failures:
                            result.telegram_success = False
                    elif tg_result == BROADCAST_NOT_AUTHORIZED:
                        result.telegram_success = BROADCAST_NOT_AUTHORIZED
                    else:
                        result.telegram_success = bool(tg_result)
                else:
                    reply_to_id = None
                    fresh_trade = get_trade(trade["trade_code"])
                    raw = fresh_trade.get("telegram_msg_id") if fresh_trade else None
                    if raw:
                        parsed = _parse_telegram_msg_ids(raw)
                        if parsed:
                            reply_to_id = next(iter(parsed.values()))

                    async def _send_single():
                        try:
                            authed = await tg.connect()
                            if not authed:
                                return BROADCAST_NOT_AUTHORIZED
                            msg = format_trade_update(trade, update_data_dict)
                            msg_id = await tg.send_update_message(msg, result.image_path, reply_to=reply_to_id)
                            return msg_id
                        finally:
                            await tg.disconnect()

                    tg_result = run_async(_send_single())
                    if isinstance(tg_result, int):
                        result.telegram_success = True
                        result.telegram_msg_ids = {"Default": tg_result}
                        telegram_fields = {
                            "telegram_msg_id": str(tg_result),
                            "telegram_groups": "Default"
                        }
                        try:
                            update_trade(trade["trade_code"], telegram_fields)
                        except Exception as e:
                            logger.warning(f"Failed to persist telegram data: {e}")
                        _sync_telegram_to_sheets(gs, trade["trade_code"], telegram_fields, result)
                    elif tg_result == BROADCAST_NOT_AUTHORIZED:
                        result.telegram_success = BROADCAST_NOT_AUTHORIZED
                    else:
                        result.telegram_success = bool(tg_result)
            else:
                result.telegram_success = BROADCAST_NOT_CONFIGURED
        except Exception as e:
            result.errors.append(f"Telegram: {e}")
            logger.error(f"Telegram broadcast failed in update: {e}", exc_info=True)

        return result

    def _on_update_broadcast_done(self, result):
        self.signals.update_broadcast_complete.emit(result)

    def _on_update_broadcast_error(self, err):
        result = BroadcastResult()
        result.errors.append(err)
        self.signals.update_broadcast_complete.emit(result)

    def fetch_cmp(self, stock_name, segment="Cash"):
        worker = Worker(self._do_fetch_cmp, stock_name, segment)
        worker.signals.done.connect(self._on_cmp_done)
        worker.signals.error.connect(self._on_cmp_error)
        self._pool.start(worker)

    def _do_fetch_cmp(self, stock_name, segment):
        from services.angelone_service import AngelOneService
        ao = AngelOneService()
        if not ao.is_configured():
            raise ValueError("AngelOne is not configured")
        ao.connect()
        results = ao.search_symbol(stock_name, segment)
        if not results:
            raise ValueError(f"Symbol '{stock_name}' not found")
        tradingsymbol = results[0].get("tradingsymbol")
        exchange = results[0].get("exchange")
        symboltoken = results[0].get("symboltoken")
        ltp = ao.get_ltp(tradingsymbol, exchange, symboltoken)
        ao.disconnect()
        if ltp is None:
            raise ValueError(f"Could not fetch LTP for {tradingsymbol}")
        return ltp

    def _on_cmp_done(self, ltp):
        self.signals.cmp_fetched.emit(ltp)

    def _on_cmp_error(self, err):
        self.signals.cmp_fetch_error.emit(str(err))

    def save_settings(self, config_dict):
        try:
            save_config(config_dict)
            Config.reload()
            self.signals.settings_saved.emit()
        except Exception as e:
            self.signals.settings_error.emit(str(e))

    def auth_telegram(self):
        worker = Worker(self._do_telegram_auth)
        worker.signals.done.connect(self._on_auth_done)
        worker.signals.error.connect(self._on_auth_error)
        self._pool.start(worker)

    def _do_telegram_auth(self):
        tg = TelegramService()
        if not tg.is_configured():
            raise ValueError("Telegram is not configured. Save settings first.")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _auth():
            authed = await tg.connect()
            if authed:
                await tg.disconnect()
                return True
            self.signals.telegram_auth_needs_otp.emit()
            code = self._wait_for_auth_input()
            if code is None:
                await tg.disconnect()
                raise ValueError("Authentication cancelled")
            try:
                await tg.sign_in(code)
            except Exception:
                self.signals.telegram_auth_needs_2fa.emit()
                password = self._wait_for_auth_input()
                if password is None:
                    await tg.disconnect()
                    raise ValueError("Authentication cancelled")
                await tg.sign_in(code, password)
            await tg.disconnect()
            return True

        return loop.run_until_complete(_auth())

    def _wait_for_auth_input(self):
        self._auth_event.clear()
        self._auth_input = None
        self._auth_event.wait(timeout=AUTH_TIMEOUT_SEC)
        with self._auth_input_lock:
            return self._auth_input

    def submit_auth_input(self, value):
        with self._auth_input_lock:
            self._auth_input = value
        self._auth_event.set()

    def cancel_auth(self):
        self.submit_auth_input(None)

    def _on_auth_done(self, result):
        if result is True:
            self.signals.telegram_auth_success.emit()
        else:
            self.signals.telegram_auth_error.emit("Authentication failed")

    def _on_auth_error(self, err):
        self.signals.telegram_auth_error.emit(str(err))

    def calculate_rr(self, action, entry, target, stop_loss):
        try:
            entry_f = float(entry) if entry else 0
            target_f = float(target) if target else 0
            sl_f = float(stop_loss) if stop_loss else 0
            return calculate_risk_reward(action, entry_f, target_f, sl_f)
        except (ValueError, TypeError):
            return None

    def to_display_action(self, db_action):
        return to_display_action(db_action)

    def to_db_action(self, display_action):
        return to_db_action(display_action)
