import json
from core.paths import DATA_DIR, SETTINGS_PATH
from database.db_helpers import _ensure_data_dir
from utils.logger import setup_logger

logger = setup_logger("SettingsDB")


def get_setting(key: str) -> str | None:
    try:
        data = _load_settings()
        return data.get(key)
    except Exception as e:
        logger.error(f"Error fetching setting {key}: {e}", exc_info=True)
        return None


def set_setting(key: str, value: str):
    try:
        data = _load_settings()
        data[key] = value
        _save_settings(data)
    except Exception as e:
        logger.error(f"Error setting {key} to {value}: {e}", exc_info=True)


def get_template(key: str, default: str | None = None) -> str | None:
    """Load a message template from settings."""
    return get_setting(f"template_{key}") if get_setting(f"template_{key}") else default


def set_template(key: str, value: str):
    """Save a message template to settings."""
    set_setting(f"template_{key}", value)


def delete_template(key: str):
    """Remove a message template from settings (reverts to defaults)."""
    try:
        data = _load_settings()
        full_key = f"template_{key}"
        if full_key in data:
            del data[full_key]
            _save_settings(data)
            logger.info(f"Deleted template: {full_key}")
    except Exception as e:
        logger.error(f"Error deleting template {key}: {e}", exc_info=True)


def _load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH) as f:
                data = json.load(f)
                logger.debug(f"Settings loaded from {SETTINGS_PATH}")
                return data
        except Exception as e:
            logger.error(f"Failed to load settings from {SETTINGS_PATH}: {e}", exc_info=True)
    return {}


def _save_settings(data: dict):
    _ensure_data_dir()
    with open(SETTINGS_PATH, "w") as f:
        json.dump(data, f, indent=2)