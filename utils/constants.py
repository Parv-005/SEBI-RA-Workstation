"""
Centralized constants facade.

All constants are resolved once at import time from app_constants.json
via get_constant(). Consumers import from this module instead of calling
get_constant() directly, eliminating duplicated fallback defaults across files.
"""

from utils.constants_loader import get_constant

# ══════════════════════════════════════════════════════════════════════════════
#  Date / Time Formats
# ══════════════════════════════════════════════════════════════════════════════

DATE_FMT_DB = "%Y-%m-%d %H:%M:%S"
DATE_FMT_COMPACT = "%Y%m%d"
DATE_FMT_FILENAME = "%Y%m%d_%H%M%S"
DATE_FMT_DISPLAY = "%d-%b-%Y %I:%M %p"
DATE_FMT_SHORT = "%d %b %Y"

# ══════════════════════════════════════════════════════════════════════════════
#  Display Symbols
# ══════════════════════════════════════════════════════════════════════════════

CURRENCY_SYMBOL = get_constant("currency_symbol", "\u20b9")
EMPTY_PLACEHOLDER = "\u2014"

# ══════════════════════════════════════════════════════════════════════════════
#  Shared Defaults
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_ACTION = "LONG"
STATUS_ACTIVE = "ACTIVE"
STATUS_CLOSED = "CLOSED"

FILTER_ALL = "ALL"

BROADCAST_NOT_CONFIGURED = "not_configured"
BROADCAST_NOT_AUTHORIZED = "not_authorized"

# ══════════════════════════════════════════════════════════════════════════════
#  Magic Numbers (runtime-tunable via app_constants.json)
# ══════════════════════════════════════════════════════════════════════════════

THREAD_POOL_SIZE: int = int(get_constant("thread_pool_size", 4))
MAX_TRADE_CODE_ATTEMPTS: int = int(get_constant("max_trade_code_attempts", 10))
AUTH_TIMEOUT_SEC: int = int(get_constant("auth_timeout_sec", 120))

# ══════════════════════════════════════════════════════════════════════════════
#  Color Definitions (imported from theme or used standalone)
# ══════════════════════════════════════════════════════════════════════════════

COLOR_REWARD = "#28a745"
COLOR_RISK = "#dc3545"
COLOR_GOLD = "#D4AF37"
COLOR_GOLD_HOVER = "#E6C24F"

# ══════════════════════════════════════════════════════════════════════════════
#  Business Domain (loaded from app_constants.json)
# ══════════════════════════════════════════════════════════════════════════════

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
    "statuses", ["ACTIVE", "CLOSED"],
)

# ── Update Types ──────────────────────────────────────────
_UPDATE_TYPES_FALLBACK = {
    "TARGET_HIT": {"close_trade": True, "message": "Target Achieved! Book Profits at <Exit Price>.", "set": {"exit_price": "<Exit Price>"}},
    "SL_HIT": {"close_trade": True, "message": "Stop Loss Hit at <Exit Price>. Exit trade.", "set": {"exit_price": "<Exit Price>"}},
    "PARTIAL_PROFIT": {"close_trade": False, "message": "Book partial profits at <Booking Price>. Trail SL for rest to <New SL>.", "set": {"latest_sl_price": "<New SL>", "booked_price": "<Booking Price>"}},
    "TRAIL_SL": {"close_trade": False, "message": "Update Stop Loss to <New Stop Loss> to protect profits.", "set": {"latest_sl_price": "<New Stop Loss>"}},
    "COST_TO_COST": {"close_trade": False, "message": "Trail SL to Cost at <Cost Price>. Hold rest.", "set": {"latest_sl_price": "<Cost Price>"}},
    "EXIT": {"close_trade": True, "message": "Exit position at <Exit Price>.", "set": {"exit_price": "<Exit Price>"}},
    "MODIFY_TARGET": {"close_trade": False, "message": "Modify Target to <New Target>.", "set": {"latest_target": "<New Target>"}},
    "MODIFY_SL": {"close_trade": False, "message": "Modify Stop Loss to <New Stop Loss>.", "set": {"latest_sl_price": "<New Stop Loss>"}},
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
    "CLOSED": "#6c757d",
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

UPDATE_TYPE_COLORS: dict[str, str] = {
    "TARGET_HIT": "#28a745",
    "SL_HIT": "#dc3545",
    "PARTIAL_PROFIT": "#17a2b8",
    "TRAIL_SL": "#0f3460",
    "COST_TO_COST": "#0f3460",
    "EXIT": "#f0ad4e",
    "MODIFY_TARGET": "#6c757d",
    "MODIFY_SL": "#6c757d",
}
