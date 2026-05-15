import json
import os

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from core.paths import CONFIG_PATH, TELEGRAM_SESSION_DIR
from utils.logger import setup_logger

logger = setup_logger("TelegramService")


class TelegramService:
    def __init__(self):
        self.client = None
        self.connected = False
        self._load_config()

    def _load_config(self):
        self.api_id = ""
        self.api_hash = ""
        self.phone = ""
        self.group_id = ""
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                config = json.load(f)
            tg = config.get("telegram", {})
            self.api_id = tg.get("api_id", "")
            self.api_hash = tg.get("api_hash", "")
            self.phone = tg.get("phone", "")
            self.group_id = tg.get("group_id", "")

    def is_configured(self) -> bool:
        return bool(self.api_id and self.api_hash and self.phone)

    async def connect(self):
        if not self.is_configured():
            logger.error("Telegram credentials not configured.")
            raise ValueError("Telegram credentials not configured.")
        try:
            self.client = TelegramClient(str(TELEGRAM_SESSION_DIR / "telegram_session"), int(self.api_id), self.api_hash)
            await self.client.connect()
            if not await self.client.is_user_authorized():
                logger.info("User not authorized. Sending code request.")
                await self.client.send_code_request(self.phone)
                return False  # needs OTP
            self.connected = True
            logger.info("Telegram client connected successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect Telegram client: {e}", exc_info=True)
            raise

    async def sign_in(self, code: str, password: str | None = None):
        try:
            await self.client.sign_in(self.phone, code)
            self.connected = True
            logger.info("Signed in successfully with code.")
        except SessionPasswordNeededError:
            if password:
                await self.client.sign_in(password=password)
                self.connected = True
                logger.info("Signed in successfully with password.")
            else:
                logger.warning("Two-step verification enabled, but no password provided.")
                raise ValueError("Two-step verification is enabled. Password required.")
        except Exception as e:
            logger.error(f"Sign in failed: {e}", exc_info=True)
            raise

    async def send_trade_message(self, message: str, image_path: str | None = None):
        if not self.connected or not self.client:
            logger.error("Attempted to send message while Telegram is not connected.")
            raise ConnectionError("Telegram not connected.")
        try:
            group = int(self.group_id) if self.group_id.lstrip("-").isdigit() else self.group_id
            if image_path and os.path.exists(image_path):
                await self.client.send_file(group, image_path, caption=message)
                logger.info("Sent message with image to Telegram.")
            else:
                await self.client.send_message(group, message)
                logger.info("Sent text message to Telegram.")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}", exc_info=True)
            raise

    async def send_update_message(self, message: str, image_path: str | None = None):
        await self.send_trade_message(message, image_path)

    async def disconnect(self):
        if self.client:
            try:
                await self.client.disconnect()
                self.connected = False
                logger.info("Telegram client disconnected.")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}", exc_info=True)
