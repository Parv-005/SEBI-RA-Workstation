import json
from core.paths import DATA_DIR, UPDATES_PATH
from database.db_helpers import _ensure_data_dir, _load_wb, _save_workbook, _wb_to_dicts
from utils.logger import setup_logger

logger = setup_logger("UpdatesDB")

UPDATES_HEADERS = [
    "trade_code",
    "update_type",
    "details",
    "old_value",
    "new_value",
    "created_at",
]


def insert_trade_update(update_data: dict) -> None:
    try:
        _ensure_data_dir()
        wb = _load_wb(UPDATES_PATH, UPDATES_HEADERS)
        ws = wb.active

        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        old_val = update_data.get("old_value")
        new_val = update_data.get("new_value")
        row = [
            update_data["trade_code"],
            update_data["update_type"],
            update_data.get("details", ""),
            json.dumps(old_val) if old_val is not None else "",
            json.dumps(new_val) if new_val is not None else "",
            now,
        ]
        ws.append(row)
        _save_workbook(wb, UPDATES_PATH)

        logger.info(
            f"Inserted trade update for trade code {update_data['trade_code']} "
            f"(Type: {update_data['update_type']})"
        )
    except Exception as e:
        logger.error(f"Error inserting trade update: {e}", exc_info=True)
        raise


def get_trade_updates(trade_code: str) -> list[dict]:
    try:
        wb = _load_wb(UPDATES_PATH, UPDATES_HEADERS)
        ws = wb.active
        rows = _wb_to_dicts(ws, UPDATES_HEADERS, is_trades=False)
        filtered = [r for r in rows if r.get("trade_code") == trade_code]
        filtered.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        return filtered
    except Exception as e:
        logger.error(f"Error fetching trade updates for trade code {trade_code}: {e}", exc_info=True)
        return []