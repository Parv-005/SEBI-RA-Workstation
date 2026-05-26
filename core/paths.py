import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    _EXEC_DIR = Path(sys.executable).resolve().parent
    _INTERNAL_DIR = _EXEC_DIR / "_internal"
    ROOT_DIR = _EXEC_DIR
    _BUNDLED_DATA_DIR = _INTERNAL_DIR / "data"
else:
    ROOT_DIR = Path(__file__).resolve().parent.parent
    _BUNDLED_DATA_DIR = ROOT_DIR / "data"

DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"
IMAGES_DIR = DATA_DIR / "images"
TEMPLATES_DIR = ROOT_DIR / "templates"
CONFIG_PATH = ROOT_DIR / "config.json"
CONSTANTS_PATH = _BUNDLED_DATA_DIR / "app_constants.json"
SETTINGS_PATH = DATA_DIR / "settings.json"
TRADES_PATH = DATA_DIR / "trades.xlsx"
UPDATES_PATH = DATA_DIR / "trade_updates.xlsx"
TELEGRAM_SESSION_DIR = ROOT_DIR