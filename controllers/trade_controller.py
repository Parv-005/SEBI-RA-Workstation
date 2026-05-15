import threading
from services.image_generator import ImageGenerator
from services.telegram_service import TelegramService
from services.google_sheets_service import GoogleSheetsService
from services.results import BroadcastResult
from utils.async_helper import run_async
from utils.logger import setup_logger

logger = setup_logger("TradeController")


class TradeController:
    def broadcast_new_trade(self, trade: dict) -> BroadcastResult:
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
                        await tg.connect()
                        msg = format_new_trade(trade)
                        await tg.send_trade_message(msg, img_path)
                        await tg.disconnect()
                        return True
                    except Exception as e:
                        logger.error(f"Telegram send error: {e}", exc_info=True)
                        raise

                success = run_async(send_tg())
                result.telegram_success = bool(success)
            else:
                result.telegram_success = "not_configured"
        except Exception as e:
            logger.error(f"Telegram Error: {e}", exc_info=True)
            result.telegram_success = False
            result.errors.append(f"Telegram: {e}")

        return result

    def broadcast_update(self, trade: dict, update_data: dict) -> BroadcastResult:
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

                async def send_tg():
                    try:
                        await tg.connect()
                        msg = format_trade_update(trade, update_data)
                        await tg.send_update_message(msg, img_path)
                        await tg.disconnect()
                        return True
                    except Exception as e:
                        logger.error(f"Telegram send error: {e}", exc_info=True)
                        raise

                success = run_async(send_tg())
                result.telegram_success = bool(success)
            else:
                result.telegram_success = "not_configured"
        except Exception as e:
            logger.error(f"Telegram Update Error: {e}", exc_info=True)
            result.telegram_success = False
            result.errors.append(f"Telegram: {e}")

        return result