import json
import shutil
from functools import lru_cache
from typing import Any

from core.paths import CONFIG_PATH
from utils.logger import setup_logger

logger = setup_logger("Config")


def _auto_create_config():
    example_path = CONFIG_PATH.parent / "config_example.json"
    if not CONFIG_PATH.exists() and example_path.exists():
        try:
            shutil.copy2(example_path, CONFIG_PATH)
            logger.info(f"First launch: copied config_example.json → config.json")
        except OSError as e:
            logger.warning(f"Could not create config.json from example: {e}")


class Config:
    _cache: dict | None = None

    @classmethod
    @lru_cache(maxsize=1)
    def get(cls) -> dict[str, Any]:
        if cls._cache is not None:
            logger.debug("Config cache hit")
            return cls._cache
        logger.debug("Config cache miss, loading from file")
        return cls._load()

    @classmethod
    def _load(cls) -> dict[str, Any]:
        if not CONFIG_PATH.exists():
            _auto_create_config()
        if not CONFIG_PATH.exists():
            logger.warning(f"Config file not found at {CONFIG_PATH}, using empty defaults")
            return {}
        try:
            with open(CONFIG_PATH) as f:
                cls._cache = json.load(f)
                logger.info(f"Config loaded from {CONFIG_PATH}")
                return cls._cache
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to parse config.json: {e}", exc_info=True)
            return {}

    @classmethod
    def reload(cls):
        logger.debug("Config reload requested")
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