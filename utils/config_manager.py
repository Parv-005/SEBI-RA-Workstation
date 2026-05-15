import json
from typing import Dict, Any
from core.paths import CONFIG_PATH
from utils.logger import setup_logger

logger = setup_logger("ConfigManager")


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        logger.warning(f"Config file not found at {CONFIG_PATH}")
        return {}
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config.json: {e}")
        return {}


def save_config(config: Dict[str, Any]) -> bool:
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
        logger.info("Config saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}", exc_info=True)
        return False