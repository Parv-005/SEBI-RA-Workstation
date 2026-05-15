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


def _load_settings() -> dict:
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_settings(data: dict):
    _ensure_data_dir()
    with open(SETTINGS_PATH, "w") as f:
        json.dump(data, f, indent=2)