"""
Centralized constants facade.

All constants are resolved once at import time from app_constants.json
via get_constant(). Consumers import from this module instead of calling
get_constant() directly, eliminating duplicated fallback defaults across files.
"""

from utils.constants_loader import get_constant

# ── Segments ──────────────────────────────────────────────
SEGMENTS: list[str] = get_constant(
    "segments", ["Cash", "F&O", "MCX", "Currency", "Index"],
)

# ── Actions ───────────────────────────────────────────────
_actions = get_constant("actions", {})
ACTION_DB: list[str] = _actions.get("db", ["BUY", "SELL"])
ACTION_DISPLAY: list[str] = _actions.get("display", ["LONG", "SHORT"])
ACTION_DISPLAY_MAP: dict[str, str] = _actions.get(
    "display_to_db", {"LONG": "BUY", "SHORT": "SELL"},
)
ACTION_DB_MAP: dict[str, str] = _actions.get(
    "db_to_display", {"BUY": "LONG", "SELL": "SHORT"},
)

# ── Statuses ──────────────────────────────────────────────
STATUSES: list[str] = get_constant(
    "statuses", ["ACTIVE", "TARGET_HIT", "SL_HIT", "EXITED"],
)

# ── Update Types ──────────────────────────────────────────
_UPDATE_TYPES_FALLBACK = {
    "TARGET_HIT": {"close_trade": True, "message": "Target Achieved! Book Profits at <Exit Price>."},
    "SL_HIT": {"close_trade": True, "message": "Stop Loss Hit at <Exit Price>. Exit trade."},
    "PARTIAL_PROFIT": {"close_trade": False, "message": "Book partial profits at <Booked Price>. Trail SL for rest to <New SL>."},
    "TRAIL_SL": {"close_trade": False, "message": "Update Stop Loss to <New Stop Loss> to protect profits."},
    "COST_TO_COST": {"close_trade": False, "message": "Trail SL to Cost at <Cost Price>. Hold rest."},
    "EXIT": {"close_trade": True, "message": "Exit position at <Exit Price>."},
    "MODIFY_TARGET": {"close_trade": False, "message": "Modify Target to <New Target>."},
    "MODIFY_SL": {"close_trade": False, "message": "Modify Stop Loss to <New Stop Loss>."},
}
UPDATE_TYPES_DICT: dict[str, dict] = get_constant(
    "update_types", _UPDATE_TYPES_FALLBACK,
)
UPDATE_TYPES: list[str] = list(UPDATE_TYPES_DICT.keys())

# ── Exchange Map ──────────────────────────────────────────
EXCHANGE_MAP: dict[str, str] = get_constant("exchange_map", {
    "Cash": "NSE",
    "F&O": "NFO",
    "MCX": "MCX",
    "Currency": "CDS",
    "Index": "NSE",
})

# ── Status Colors ─────────────────────────────────────────
STATUS_COLORS: dict[str, str] = get_constant("status_colors", {
    "ACTIVE": "#17a2b8",
    "TARGET_HIT": "#28a745",
    "SL_HIT": "#dc3545",
    "EXITED": "gray",
})

# ── Trade Types ───────────────────────────────────────────
TRADE_TYPES: list[str] = get_constant("trade_types", [
    "INTRADAY", "POSITIONAL", "BTST", "STBT", "SCALPING", "LONG TERM",
])

# ── Action Colors (theming — not in JSON) ─────────────────
ACTION_COLORS: dict[str, str] = {
    "LONG": "#28a745",
    "SHORT": "#dc3545",
    "LONG_HOVER": "#218838",
    "LONG_HOVER2": "#1e7e34",
    "SHORT_HOVER": "#c82333",
    "SHORT_HOVER2": "#bd2130",
}
