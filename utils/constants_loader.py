import json
from core.paths import CONSTANTS_PATH

_cache: dict | None = None


def get_constant(key: str, default=None):
    global _cache
    if _cache is None:
        if not CONSTANTS_PATH.exists():
            raise FileNotFoundError(f"Configuration file {CONSTANTS_PATH} is missing!")
        try:
            with open(CONSTANTS_PATH, "r") as f:
                _cache = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {CONSTANTS_PATH}: {e}")
    return _cache.get(key, default)


def clear_cache():
    global _cache
    _cache = None