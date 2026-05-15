import json
# pyrefly: ignore [missing-import]
import pyotp
# pyrefly: ignore [missing-import]
from SmartApi import SmartConnect
from core.paths import CONFIG_PATH
from utils.constants import EXCHANGE_MAP
from utils.logger import setup_logger

logger = setup_logger("AngelOneService")


class AngelOneService:
    def __init__(self):
        self.smart_api = None
        self.connected = False
        self._load_config()

    def _load_config(self):
        self.api_key = ""
        self.client_id = ""
        self.password = ""
        self.totp_secret = ""
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                config = json.load(f)
            ao = config.get("angelone", {})
            self.api_key = ao.get("api_key", "")
            self.client_id = ao.get("client_id", "")
            self.password = ao.get("password", "")
            self.totp_secret = ao.get("totp_secret", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.client_id and self.password and self.totp_secret)

    def connect(self) -> bool:
        if not self.is_configured():
            logger.error("AngelOne credentials not configured.")
            raise ValueError("AngelOne credentials not configured.")
        try:
            self.smart_api = SmartConnect(api_key=self.api_key)
            totp = pyotp.TOTP(self.totp_secret).now()
            data = self.smart_api.generateSession(self.client_id, self.password, totp)
            if data.get("status"):
                self.connected = True
                logger.info("AngelOne connected successfully.")
                return True
            logger.error(f"AngelOne login failed: {data.get('message', 'Unknown error')}")
            raise ConnectionError(f"AngelOne login failed: {data.get('message', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error during AngelOne connection: {e}", exc_info=True)
            raise

    def get_ltp(self, symbol: str, exchange: str, token: str) -> float | None:
        if not self.connected:
            self.connect()
        try:
            data = self.smart_api.ltpData(exchange, symbol, token)
            if data.get("status") and data.get("data"):
                return data["data"].get("ltp")
            logger.warning(f"Failed to get LTP for {symbol}: {data}")
        except Exception as e:
            logger.error(f"Error getting LTP for {symbol}: {e}", exc_info=True)
        return None

    def search_symbol(self, query: str, segment: str = "Cash") -> list[dict]:
        if not self.connected:
            self.connect()
        exchange = EXCHANGE_MAP.get(segment, "NSE")
        try:
            results = self.smart_api.searchScrip(exchange, query)
            if results and results.get("data"):
                return results["data"]
        except Exception as e:
            logger.error(f"Error searching symbol {query}: {e}", exc_info=True)
        return []

    def disconnect(self):
        if self.smart_api and self.connected:
            try:
                self.smart_api.terminateSession(self.client_id)
                self.connected = False
                logger.info("AngelOne disconnected successfully.")
            except Exception as e:
                logger.error(f"Error disconnecting AngelOne: {e}", exc_info=True)
