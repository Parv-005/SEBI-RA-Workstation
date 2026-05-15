from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"
IMAGES_DIR = DATA_DIR / "images"
TEMPLATES_DIR = ROOT_DIR / "templates"
CONFIG_PATH = ROOT_DIR / "config.json"
CONSTANTS_PATH = DATA_DIR / "app_constants.json"
SETTINGS_PATH = DATA_DIR / "settings.json"
TRADES_PATH = DATA_DIR / "trades.xlsx"
UPDATES_PATH = DATA_DIR / "trade_updates.xlsx"
TELEGRAM_SESSION_DIR = ROOT_DIR