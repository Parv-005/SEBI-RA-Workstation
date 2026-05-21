import traceback
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
from utils.logger import setup_logger
import threading
import asyncio

logger = setup_logger("AppController")


class AppController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = get_signals()
        self._pool = QThreadPool.globalInstance()
        self._pool.setMaxThreadCount(4)
        self._auth_event = threading.Event()
        self._auth_input = None
        self._auth_input_lock = threading.Lock()

    def get_trades(self, filters=None):
        try:
            trades = get_all_trades(filters) if filters else get_all_trades()
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

    def create_trade_and_broadcast(self, trade_data):
        trade_code, enriched = self.create_trade(trade_data)
        if not trade_code:
            return
        worker = Worker(self._do_broadcast_new_trade, enriched)
        worker.signals.done.connect(self._on_broadcast_done)
        worker.signals.error.connect(self._on_broadcast_error)
        self._pool.start(worker)

    def _do_broadcast_new_trade(self, trade):
        result = BroadcastResult()
        try:
            img = ImageGenerator()
            img_path = img.generate_trade_image(trade)
            result.image_success = img_path is not None
            result.image_path = img_path
        except Exception as e:
            result.errors.append(f"Image: {e}")

        try:
            gs = GoogleSheetsService()
            if gs.is_configured():
                gs.connect()
                append_result = gs.append_trade(trade)
                result.sheets_success = append_result.success
                result.sheets_unmapped = append_result.unmapped_columns
            else:
                result.sheets_success = "not_configured"
        except Exception as e:
            result.errors.append(f"Sheets: {e}")

        try:
            tg = TelegramService()
            if tg.is_configured():

                async def _send():
                    authed = await tg.connect()
                    if not authed:
                        return "not_authorized"
                    msg = format_new_trade(trade)
                    msg_id = await tg.send_trade_message(msg, result.image_path)
                    await tg.disconnect()
                    return msg_id

                tg_result = run_async(_send())
                if isinstance(tg_result, int):
                    result.telegram_success = True
                    result.telegram_msg_id = tg_result
                    try:
                        update_trade(trade["trade_code"], {"telegram_msg_id": str(tg_result)})
                    except Exception as e:
                        logger.warning(f"Failed to persist telegram_msg_id: {e}")
                elif tg_result == "not_authorized":
                    result.telegram_success = "not_authorized"
                else:
                    result.telegram_success = bool(tg_result)
            else:
                result.telegram_success = "not_configured"
        except Exception as e:
            result.errors.append(f"Telegram: {e}")

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

        try:
            insert_trade_update(update_data_dict)
            update_trade(trade["trade_code"], trade_updates)
            self.signals.trade_updated.emit(trade)
        except Exception as e:
            self.signals.trade_update_error.emit(str(e))
            return

        worker = Worker(
            self._do_broadcast_update,
            trade, update_data_dict, trade_updates
        )
        worker.signals.done.connect(self._on_update_broadcast_done)
        worker.signals.error.connect(self._on_update_broadcast_error)
        self._pool.start(worker)

    def _do_broadcast_update(self, trade, update_data_dict, trade_updates):
        result = BroadcastResult()
        try:
            img = ImageGenerator()
            img_path = img.generate_update_image(trade, update_data_dict)
            result.image_success = img_path is not None
            result.image_path = img_path
        except Exception as e:
            result.errors.append(f"Image: {e}")

        try:
            gs = GoogleSheetsService()
            if gs.is_configured():
                gs.connect()
                gs.update_trade_row(
                    trade["trade_code"], update_data_dict, trade_updates
                )
                result.sheets_success = True
            else:
                result.sheets_success = "not_configured"
        except Exception as e:
            result.errors.append(f"Sheets: {e}")

        try:
            tg = TelegramService()
            if tg.is_configured():
                reply_to_id = None
                fresh_trade = get_trade(trade["trade_code"])
                raw = fresh_trade.get("telegram_msg_id") if fresh_trade else None
                if raw:
                    try:
                        reply_to_id = int(raw)
                    except (ValueError, TypeError):
                        reply_to_id = None

                async def _send():
                    authed = await tg.connect()
                    if not authed:
                        return "not_authorized"
                    msg = format_trade_update(trade, update_data_dict)
                    msg_id = await tg.send_update_message(msg, result.image_path, reply_to=reply_to_id)
                    await tg.disconnect()
                    return msg_id

                tg_result = run_async(_send())
                if isinstance(tg_result, int):
                    result.telegram_success = True
                    result.telegram_msg_id = tg_result
                    try:
                        update_trade(trade["trade_code"], {"telegram_msg_id": str(tg_result)})
                    except Exception as e:
                        logger.warning(f"Failed to persist telegram_msg_id: {e}")
                elif tg_result == "not_authorized":
                    result.telegram_success = "not_authorized"
                else:
                    result.telegram_success = bool(tg_result)
            else:
                result.telegram_success = "not_configured"
        except Exception as e:
            result.errors.append(f"Telegram: {e}")

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
        token = results[0].get("symbol")
        exchange = results[0].get("exchange")
        ltp = ao.get_ltp(token, exchange, token)
        ao.disconnect()
        if ltp is None:
            raise ValueError(f"Could not fetch LTP for {stock_name}")
        return ltp

    def _on_cmp_done(self, ltp):
        self.signals.cmp_fetched.emit(ltp)

    def _on_cmp_error(self, err):
        self.signals.cmp_fetch_error.emit(str(err))

    def save_settings(self, config_dict):
        try:
            save_config(config_dict)
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
        self._auth_event.wait(timeout=120)
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
