import json
from functools import lru_cache
from typing import Any

from core.paths import CONFIG_PATH


class Config:
    _cache: dict | None = None

    @classmethod
    @lru_cache(maxsize=1)
    def get(cls) -> dict[str, Any]:
        if cls._cache is not None:
            return cls._cache
        return cls._load()

    @classmethod
    def _load(cls) -> dict[str, Any]:
        if not CONFIG_PATH.exists():
            return {}
        try:
            with open(CONFIG_PATH) as f:
                cls._cache = json.load(f)
                return cls._cache
        except (json.JSONDecodeError, OSError):
            return {}

    @classmethod
    def reload(cls):
        cls.get.cache_clear()
        cls._cache = None
        cls.get()

    @classmethod
    def get_section(cls, section: str) -> dict[str, Any]:
        config = cls.get()
        return config.get(section, {})

    @classmethod
    def get_value(cls, section: str, key: str, default: Any = None) -> Any:
        section_data = cls.get_section(section)
        return section_data.get(key, default)