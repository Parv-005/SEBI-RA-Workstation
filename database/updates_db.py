import json
from datetime import datetime
from core.paths import DATA_DIR, UPDATES_PATH
from database.db_helpers import (
    _ensure_data_dir, _load_wb, _save_workbook, _wb_to_dicts,
    _get_cached_rows, invalidate_cache,
)
from utils.constants import DATE_FMT_DB
from utils.logger import setup_logger

logger = setup_logger("UpdatesDB")

# Columns stored in trade_updates.xlsx (and mirrored in the Google Sheets Updates sheet).
# Designed to be update-type-agnostic: changes are stored as a formatted string.
UPDATES_HEADERS = [
    "trade_code",
    "update_type",
    "message",      # filled message / remarks text
    "changes",      # human-readable "field: old → new" pairs
    "created_at",
]


# ── Formatting helpers ────────────────────────────────────────────────────────

def format_changes(old_value: dict | None, new_value: dict | None) -> str:
    """Build a compact 'field: old → new' string from old/new dicts."""
    if not new_value:
        return ""
    parts = []
    for field, new_val in new_value.items():
        old_val = (old_value or {}).get(field)
        old_str = str(old_val) if old_val is not None else "—"
        parts.append(f"{field}: {old_str} → {new_val}")
    return " | ".join(parts)


def format_update_line(update: dict) -> str:
    """Format a single update record into a one/two-line display string."""
    line = f"[{update.get('update_type', '?')}] {update.get('message', '')}"
    changes = update.get("changes", "")
    if changes:
        line += f"\n  {changes}"
    return line


def build_updates_column_text(updates: list[dict]) -> str:
    """
    Given a list of update dicts (already sorted latest-first), produce the
    multi-line text that goes into the 'Updates' column of the Trades sheet.
    """
    lines = [format_update_line(u) for u in updates]
    return "\n---\n".join(lines)


# ── DB operations ─────────────────────────────────────────────────────────────

def insert_trade_update(update_data: dict) -> None:
    """
    Persist a trade update row.

    Expected keys in update_data:
        trade_code, update_type, message (or details), old_value, new_value
    """
    if not update_data.get("trade_code") or update_data["trade_code"] == "?":
        raise ValueError("Strict Check Failed: trade_code is required to insert an update.")

    try:
        _ensure_data_dir()
        wb = _load_wb(UPDATES_PATH, UPDATES_HEADERS)
        ws = wb.active

        now = datetime.now().strftime(DATE_FMT_DB)

        old_val = update_data.get("old_value")
        new_val = update_data.get("new_value")
        message = update_data.get("message", update_data.get("details", ""))
        changes = format_changes(old_val, new_val)

        row = [
            update_data["trade_code"],
            update_data["update_type"],
            message,
            changes,
            now,
        ]
        ws.append(row)
        _save_workbook(wb, UPDATES_PATH)
        invalidate_cache("updates")

        logger.info(
            f"Inserted trade update for trade code {update_data['trade_code']} "
            f"(Type: {update_data['update_type']})"
        )
    except Exception as e:
        logger.error(f"Error inserting trade update: {e}", exc_info=True)
        raise


def get_trade_updates(trade_code: str) -> list[dict]:
    try:
        logger.debug(f"Fetching updates for trade: {trade_code}")
        rows = _get_cached_rows(UPDATES_PATH, UPDATES_HEADERS, is_trades=False)
        filtered = [r for r in rows if r.get("trade_code") == trade_code]
        filtered.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        return filtered
    except Exception as e:
        logger.error(f"Error fetching trade updates for trade code {trade_code}: {e}", exc_info=True)
        return []


def get_formatted_updates_text(trade_code: str) -> str:
    """Fetch all updates for a trade and return the formatted column text (latest first)."""
    updates = get_trade_updates(trade_code)
    return build_updates_column_text(updates)