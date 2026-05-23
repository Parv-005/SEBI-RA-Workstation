"""
Centralized display formatters for trade data.

Every currency, date, percentage, zone, and risk-reward formatting passes
through a single module so that symbol changes, locale preferences, and
display tweaks happen in one place.
"""

from datetime import datetime

from utils.constants import (
    CURRENCY_SYMBOL,
    DATE_FMT_DB,
    DATE_FMT_DISPLAY,
    DATE_FMT_SHORT,
    EMPTY_PLACEHOLDER,
)
from utils.logger import setup_logger

logger = setup_logger("Formatters")


# ══════════════════════════════════════════════════════════════════════════════
#  Currency
# ══════════════════════════════════════════════════════════════════════════════

def format_currency(value, symbol: str | None = None) -> str:
    """Return ``"{symbol}{value:,.2f}"`` or ``"—"`` when *value* is not numeric."""
    if isinstance(value, (int, float)):
        return f"{symbol or CURRENCY_SYMBOL}{value:,.2f}"
    return EMPTY_PLACEHOLDER


# ══════════════════════════════════════════════════════════════════════════════
#  Percentage
# ══════════════════════════════════════════════════════════════════════════════

def format_percentage(value) -> str:
    """Return ``"{value:.2f}%"`` or ``"—"`` when *value* is not numeric."""
    if isinstance(value, (int, float)):
        return f"{value:.2f}%"
    return EMPTY_PLACEHOLDER


def format_decimal(value) -> str:
    """Return ``"{value:.2f}"`` (no suffix) or ``"—"`` when *value* is not numeric."""
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return EMPTY_PLACEHOLDER


# ══════════════════════════════════════════════════════════════════════════════
#  Risk–Reward Ratio
# ══════════════════════════════════════════════════════════════════════════════

def format_risk_reward(ratio) -> str:
    """Return ``"1 : 1.50"`` or ``"—"`` when *ratio* is not valid."""
    if isinstance(ratio, (int, float)):
        if ratio <= 0:
            return EMPTY_PLACEHOLDER
        return f"1 : {ratio:.2f}"
    if isinstance(ratio, str) and ratio.strip():
        return ratio
    return EMPTY_PLACEHOLDER


# ══════════════════════════════════════════════════════════════════════════════
#  Zone Range
# ══════════════════════════════════════════════════════════════════════════════

def format_zone(zone_start, zone_end, symbol: str | None = None) -> str:
    """Return ``"{symbol}start – {symbol}end"`` or ``"—"``."""
    cur = symbol or CURRENCY_SYMBOL
    parts: list[str] = []
    for val in (zone_start, zone_end):
        if val in (None, "", "None"):
            continue
        try:
            parts.append(f"{cur}{float(val):,.2f}")
        except (ValueError, TypeError):
            parts.append(str(val))
    if not parts:
        return EMPTY_PLACEHOLDER
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} \u2013 {parts[1]}"


# ══════════════════════════════════════════════════════════════════════════════
#  Dates
# ══════════════════════════════════════════════════════════════════════════════

def parse_db_date(ts_str) -> datetime | None:
    """Parse a database-format timestamp string into a datetime object."""
    if not ts_str:
        return None
    try:
        return datetime.strptime(str(ts_str), DATE_FMT_DB)
    except (ValueError, Overflowerror):
        logger.debug(f"Could not parse timestamp: {ts_str!r}")
        return None


def format_date_display(ts_str=None) -> str:
    """DB timestamp → ``"dd-Mon-YYYY HH:MM AM/PM"``. Uses current time when *ts_str* is None."""
    if ts_str is None:
        return datetime.now().strftime(DATE_FMT_DISPLAY)
    dt = parse_db_date(ts_str)
    if dt:
        return dt.strftime(DATE_FMT_DISPLAY)
    return str(ts_str) if ts_str else EMPTY_PLACEHOLDER


def format_date_short(ts_str) -> str:
    """DB timestamp → ``"YYYY-MM-DD"`` (date portion only)."""
    if not ts_str:
        return EMPTY_PLACEHOLDER
    ts = str(ts_str).split(" ")[0]
    if ts == "None":
        return EMPTY_PLACEHOLDER
    return ts


def format_date_full(ts_str) -> str:
    """DB timestamp formatted as ``"YYYY-MM-DD HH:MM:SS"`` (strips sub-seconds)."""
    if not ts_str:
        return EMPTY_PLACEHOLDER
    ts = str(ts_str)
    if ts == "None":
        return EMPTY_PLACEHOLDER
    return ts.split(".")[0]


def format_date_db_now() -> str:
    """Return the current time formatted with ``DATE_FMT_DB``."""
    return datetime.now().strftime(DATE_FMT_DB)


# ══════════════════════════════════════════════════════════════════════════════
#  Price (simple numeric, no currency sign)
# ══════════════════════════════════════════════════════════════════════════════

def format_price(value) -> str:
    """Return ``"1234.56"`` or ``"—"``."""
    if isinstance(value, (int, float)):
        return f"{value:,.2f}"
    return EMPTY_PLACEHOLDER
