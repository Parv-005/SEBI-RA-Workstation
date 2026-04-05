import json
from pathlib import Path

CONSTANTS_PATH = Path(__file__).resolve().parent.parent / "data" / "app_constants.json"

def get_constant(key: str, default=None):
    """Retrieve a configuration array or string from app_constants.json safely."""
    if not CONSTANTS_PATH.exists():
        raise FileNotFoundError(f"Configuration file {CONSTANTS_PATH} is missing!")
    
    with open(CONSTANTS_PATH, "r") as f:
        return json.load(f).get(key, default)
