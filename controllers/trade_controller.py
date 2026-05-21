from services.results import BroadcastResult
from utils.async_helper import run_async
from utils.logger import setup_logger

logger = setup_logger("TradeController")


class TradeController:
    def broadcast_new_trade(self, trade: dict) -> BroadcastResult:
        from services.image_generator import ImageGenerator
        from services.telegram_service import TelegramService
        from services.google_sheets_service import GoogleSheetsService
        from database.trades_db import update_trade

        result = BroadcastResult()
        img_path = None

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
                    result.sheets_success = True
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

                async def send_tg():
                    try:
                        authorized = await tg.connect()
                        if not authorized:
                            logger.warning("Telegram: user not authorized (OTP required). Skipping send.")
                            await tg.disconnect()
                            return "not_authorized"
                        msg = format_new_trade(trade)
                        msg_id = await tg.send_trade_message(msg, img_path)
                        await tg.disconnect()
                        return msg_id
                    except Exception as e:
                        logger.error(f"Telegram send error: {e}", exc_info=True)
                        raise

                success = run_async(send_tg())
                if isinstance(success, int):
                    result.telegram_success = True
                    result.telegram_msg_id = success
                    try:
                        update_trade(trade["trade_code"], {"telegram_msg_id": str(success)})
                    except Exception as e:
                        logger.warning(f"Failed to persist telegram_msg_id: {e}")
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
        from database.trades_db import update_trade, get_trade

        if not trade.get("trade_code") or trade["trade_code"] == "?":
            raise ValueError("Strict Check Failed: trade_code is required to broadcast an update.")

        result = BroadcastResult()
        img_path = None

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
                    result.sheets_success = err_msg
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

                reply_to_id = None
                fresh_trade = get_trade(trade["trade_code"])
                raw = fresh_trade.get("telegram_msg_id") if fresh_trade else None
                if raw:
                    try:
                        reply_to_id = int(raw)
                    except (ValueError, TypeError):
                        reply_to_id = None

                async def send_tg():
                    try:
                        authorized = await tg.connect()
                        if not authorized:
                            logger.warning("Telegram: user not authorized (OTP required). Skipping send.")
                            await tg.disconnect()
                            return "not_authorized"
                        msg = format_trade_update(trade, update_data)
                        msg_id = await tg.send_update_message(msg, img_path, reply_to=reply_to_id)
                        await tg.disconnect()
                        return msg_id
                    except Exception as e:
                        logger.error(f"Telegram send error: {e}", exc_info=True)
                        raise

                success = run_async(send_tg())
                if isinstance(success, int):
                    result.telegram_success = True
                    result.telegram_msg_id = success
                    try:
                        update_trade(trade["trade_code"], {"telegram_msg_id": str(success)})
                    except Exception as e:
                        logger.warning(f"Failed to persist telegram_msg_id: {e}")
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