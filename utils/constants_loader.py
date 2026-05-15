import json
import threading
from core.paths import CONSTANTS_PATH
from utils.logger import setup_logger

logger = setup_logger("ConstantsLoader")

_cache: dict | None = None
_lock = threading.Lock()


def get_constant(key: str, default=None):
    global _cache
    with _lock:
        if _cache is None:
            if not CONSTANTS_PATH.exists():
                raise FileNotFoundError(f"Configuration file {CONSTANTS_PATH} is missing!")
            try:
                with open(CONSTANTS_PATH, "r") as f:
                    _cache = json.load(f)
                logger.debug(f"Constants loaded from {CONSTANTS_PATH}")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in {CONSTANTS_PATH}: {e}")
    return _cache.get(key, default)


def clear_cache():
    global _cache
    with _lock:
        _cache = None
        logger.debug("Constants cache cleared")