import json

from services.results import BroadcastResult
from services.google_sheets_service import GoogleSheetsService
from utils.async_helper import run_async
from utils.logger import setup_logger

logger = setup_logger("TradeController")


def _sync_telegram_to_sheets(gs, trade_code: str, telegram_fields: dict, result: BroadcastResult):
    try:
        if gs and gs.is_configured():
            if not gs.sheet:
                gs.connect()
            gs.update_trade_row(trade_code, telegram_fields)
            logger.info(f"Synced telegram data to Google Sheets for {trade_code}")
    except Exception as e:
        logger.warning(f"Failed to sync telegram data to Google Sheets: {e}")
        result.errors.append(f"Sheets telegram sync: {e}")


def _parse_telegram_msg_ids(raw):
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


def _load_config_groups():
    try:
        from core.paths import CONFIG_PATH
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
            return cfg.get("telegram", {}).get("groups", {})
    except Exception:
        pass
    return {}


def _build_update_targets(trade_code, config_groups):
    from database.trades_db import get_trade
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


class TradeController:
    def broadcast_new_trade(self, trade: dict, selected_groups: dict | None = None) -> BroadcastResult:
        from services.image_generator import ImageGenerator
        from services.telegram_service import TelegramService
        from services.google_sheets_service import GoogleSheetsService
        from database.trades_db import update_trade

        result = BroadcastResult()
        img_path = None
        gs = None

        try:
            img_gen = ImageGenerator()
            img_path = img_gen.generate_trade_image(trade)
            result.image_success = img_path is not None
            result.image_path = img_path
        except Exception as e:
            logger.error(f"Image generation error: {e}", exc_info=True)
            result.image_success = False

        try:
            gs = GoogleSheetsService()
            if gs.is_configured():
                try:
                    append_result = gs.append_trade(trade)
                    result.sheets_success = append_result.success
                    result.sheets_unmapped = append_result.unmapped_columns
                except Exception as e:
                    logger.error(f"Sheets Error: {e}", exc_info=True)
                    result.sheets_success = False
                    result.errors.append(f"Google Sheets: {e}")
            else:
                result.sheets_success = "not_configured"
        except Exception as e:
            logger.error(f"Sheets Error: {e}", exc_info=True)
            result.sheets_success = False
            result.errors.append(f"Google Sheets: {e}")

        try:
            tg = TelegramService()
            if tg.is_configured():
                from utils.message_formatter import format_new_trade

                if selected_groups:
                    async def send_tg():
                        try:
                            authorized = await tg.connect()
                            if not authorized:
                                logger.warning("Telegram: user not authorized (OTP required). Skipping send.")
                                return "not_authorized"
                            msg = format_new_trade(trade)
                            msg_ids, failures = await tg.send_to_groups(msg, selected_groups, img_path)
                            return ("multi", msg_ids, failures)
                        except Exception as e:
                            logger.error(f"Telegram send error: {e}", exc_info=True)
                            raise
                        finally:
                            await tg.disconnect()

                    success = run_async(send_tg())
                    if isinstance(success, tuple) and success[0] == "multi":
                        msg_ids = success[1]
                        failures = success[2]
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
                    elif success == "not_authorized":
                        result.telegram_success = "not_authorized"
                    else:
                        result.telegram_success = bool(success)
                else:
                    async def send_tg():
                        try:
                            authorized = await tg.connect()
                            if not authorized:
                                logger.warning("Telegram: user not authorized (OTP required). Skipping send.")
                                return "not_authorized"
                            msg = format_new_trade(trade)
                            msg_id = await tg.send_trade_message(msg, img_path)
                            return msg_id
                        except Exception as e:
                            logger.error(f"Telegram send error: {e}", exc_info=True)
                            raise
                        finally:
                            await tg.disconnect()

                    success = run_async(send_tg())
                    if isinstance(success, int):
                        result.telegram_success = True
                        result.telegram_msg_ids = {"Default": success}
                        telegram_fields = {
                            "telegram_msg_id": str(success),
                            "telegram_groups": "Default"
                        }
                        try:
                            update_trade(trade["trade_code"], telegram_fields)
                        except Exception as e:
                            logger.warning(f"Failed to persist telegram data: {e}")
                        _sync_telegram_to_sheets(gs, trade["trade_code"], telegram_fields, result)
                    elif success == "not_authorized":
                        result.telegram_success = "not_authorized"
                    else:
                        result.telegram_success = bool(success)
            else:
                result.telegram_success = "not_configured"
        except Exception as e:
            logger.error(f"Telegram Error: {e}", exc_info=True)
            result.telegram_success = False
            result.errors.append(f"Telegram: {e}")

        return result

    def broadcast_update(self, trade: dict, update_data: dict) -> BroadcastResult:
        from services.image_generator import ImageGenerator
        from services.telegram_service import TelegramService
        from services.google_sheets_service import GoogleSheetsService
        from database.trades_db import update_trade

        if not trade.get("trade_code") or trade["trade_code"] == "?":
            raise ValueError("Strict Check Failed: trade_code is required to broadcast an update.")

        result = BroadcastResult()
        img_path = None
        gs = None

        try:
            img_gen = ImageGenerator()
            img_path = img_gen.generate_update_image(trade, update_data)
            result.image_success = img_path is not None
            result.image_path = img_path
        except Exception as e:
            logger.error(f"Image generation error: {e}", exc_info=True)
            result.image_success = False

        try:
            gs = GoogleSheetsService()
            if gs.is_configured():
                trade_updates = update_data.get("_trade_updates", {})
                gs_result = gs.update_trade_row(
                    trade["trade_code"], update_data, trade_updates
                )
                if gs_result.get("success"):
                    result.sheets_success = True
                else:
                    err_msg = gs_result.get("error", "Failed")
                    result.sheets_success = False
                    result.errors.append(f"Google Sheets: {err_msg}")

                try:
                    gs.append_update_row(update_data)
                except Exception as ue:
                    logger.warning(f"Failed to append update row to Updates sheet: {ue}")
            else:
                result.sheets_success = "not_configured"
        except Exception as e:
            logger.error(f"Sheets Update Error: {e}", exc_info=True)
            result.sheets_success = False
            result.errors.append(f"Google Sheets: {e}")

        try:
            tg = TelegramService()
            if tg.is_configured():
                from utils.message_formatter import format_trade_update

                config_groups = _load_config_groups()
                groups, reply_to_map = _build_update_targets(trade["trade_code"], config_groups)

                if groups:
                    async def send_tg():
                        try:
                            authorized = await tg.connect()
                            if not authorized:
                                logger.warning("Telegram: user not authorized (OTP required). Skipping send.")
                                return "not_authorized"
                            msg = format_trade_update(trade, update_data)
                            msg_ids, failures = await tg.send_to_groups(msg, groups, img_path, reply_to_map)
                            return ("multi", msg_ids, failures)
                        except Exception as e:
                            logger.error(f"Telegram send error: {e}", exc_info=True)
                            raise
                        finally:
                            await tg.disconnect()

                    success = run_async(send_tg())
                    if isinstance(success, tuple) and success[0] == "multi":
                        msg_ids = success[1]
                        failures = success[2]
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
                    elif success == "not_authorized":
                        result.telegram_success = "not_authorized"
                    else:
                        result.telegram_success = bool(success)
                else:
                    from database.trades_db import get_trade
                    reply_to_id = None
                    fresh_trade = get_trade(trade["trade_code"])
                    raw = fresh_trade.get("telegram_msg_id") if fresh_trade else None
                    if raw:
                        parsed = _parse_telegram_msg_ids(raw)
                        if parsed:
                            reply_to_id = next(iter(parsed.values()))

                    async def send_tg():
                        try:
                            authorized = await tg.connect()
                            if not authorized:
                                logger.warning("Telegram: user not authorized (OTP required). Skipping send.")
                                return "not_authorized"
                            msg = format_trade_update(trade, update_data)
                            msg_id = await tg.send_update_message(msg, img_path, reply_to=reply_to_id)
                            return msg_id
                        except Exception as e:
                            logger.error(f"Telegram send error: {e}", exc_info=True)
                            raise
                        finally:
                            await tg.disconnect()

                    success = run_async(send_tg())
                    if isinstance(success, int):
                        result.telegram_success = True
                        result.telegram_msg_ids = {"Default": success}
                        telegram_fields = {
                            "telegram_msg_id": str(success),
                            "telegram_groups": "Default"
                        }
                        try:
                            update_trade(trade["trade_code"], telegram_fields)
                        except Exception as e:
                            logger.warning(f"Failed to persist telegram data: {e}")
                        _sync_telegram_to_sheets(gs, trade["trade_code"], telegram_fields, result)
                    elif success == "not_authorized":
                        result.telegram_success = "not_authorized"
                    else:
                        result.telegram_success = bool(success)
            else:
                result.telegram_success = "not_configured"
        except Exception as e:
            logger.error(f"Telegram Update Error: {e}", exc_info=True)
            result.telegram_success = False
            result.errors.append(f"Telegram: {e}")

        return result