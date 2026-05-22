import json
import os


# pyrefly: ignore [missing-import]
from telethon import TelegramClient

# pyrefly: ignore [missing-import]
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
        self.groups = {}
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                config = json.load(f)
            tg = config.get("telegram", {})
            self.api_id = tg.get("api_id", "")
            self.api_hash = tg.get("api_hash", "")
            self.phone = tg.get("phone", "")
            self.group_id = tg.get("group_id", "")
            self.groups = tg.get("groups", {})

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

    async def _send_to_single_group(self, group_id: str | int, message: str,
                                    image_path: str | None = None,
                                    reply_to: int | None = None) -> int:
        target = int(group_id) if str(group_id).lstrip("-").isdigit() else group_id
        kwargs = {}
        if reply_to is not None:
            kwargs["reply_to"] = reply_to
        if image_path and os.path.exists(image_path):
            msg = await self.client.send_file(target, image_path, caption=message, **kwargs)
        else:
            msg = await self.client.send_message(target, message, **kwargs)
        return msg.id

    async def send_trade_message(self, message: str, image_path: str | None = None) -> int:
        if not self.connected or not self.client:
            logger.error("Attempted to send message while Telegram is not connected.")
            raise ConnectionError("Telegram not connected.")
        try:
            return await self._send_to_single_group(self.group_id, message, image_path)
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}", exc_info=True)
            raise

    async def send_update_message(self, message: str, image_path: str | None = None,
                                  reply_to: int | None = None) -> int:
        if not self.connected or not self.client:
            logger.error("Attempted to send message while Telegram is not connected.")
            raise ConnectionError("Telegram not connected.")
        try:
            return await self._send_to_single_group(self.group_id, message, image_path, reply_to)
        except Exception as e:
            logger.error(f"Failed to send Telegram update message: {e}", exc_info=True)
            raise

    async def send_to_groups(self, message: str, groups: dict[str, str],
                             image_path: str | None = None,
                             reply_to_map: dict[str, int] | None = None) -> tuple[dict[str, int], dict[str, str]]:
        if not self.connected or not self.client:
            logger.error("Attempted to send message while Telegram is not connected.")
            raise ConnectionError("Telegram not connected.")
        msg_ids: dict[str, int] = {}
        failures: dict[str, str] = {}
        reply_to_map = reply_to_map or {}
        for name, group_id in groups.items():
            try:
                reply_to = reply_to_map.get(name)
                msg_id = await self._send_to_single_group(group_id, message, image_path, reply_to)
                msg_ids[name] = msg_id
                logger.info(f"Sent message to group '{name}' ({group_id}), msg_id={msg_id}")
            except Exception as e:
                error_text = str(e)
                failures[name] = error_text
                logger.error(f"Failed to send to group '{name}' ({group_id}): {e}", exc_info=True)
        return msg_ids, failures

    async def disconnect(self):
        if self.client:
            try:
                await self.client.disconnect()
                self.connected = False
                logger.info("Telegram client disconnected.")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}", exc_info=True)
