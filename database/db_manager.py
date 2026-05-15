"""
Backward-compatible facade — all public symbols are re-exported
from the focused sub-modules. Existing imports continue to work:

    from database.db_manager import insert_trade, get_all_trades, ...
"""

from database.trades_db import (
    insert_trade,
    get_trade,
    get_all_trades,
    update_trade,
    generate_trade_code,
    get_trades_headers,
    TRADES_HEADERS,
)
from database.updates_db import (
    insert_trade_update,
    get_trade_updates,
    UPDATES_HEADERS,
)
from database.settings_db import (
    get_setting,
    set_setting,
)
from database.db_helpers import _ensure_data_dir, _load_wb

from core.paths import TRADES_PATH, UPDATES_PATH


def init_db():
    try:
        _ensure_data_dir()
        _load_wb(TRADES_PATH, TRADES_HEADERS)
        _load_wb(UPDATES_PATH, UPDATES_HEADERS)
        from utils.logger import setup_logger
        logger = setup_logger("DBManager")
        logger.info("Data store initialised (xlsx).")
    except Exception as e:
        from utils.logger import setup_logger
        logger = setup_logger("DBManager")
        logger.error(f"Error initialising data store: {e}", exc_info=True)
        raise