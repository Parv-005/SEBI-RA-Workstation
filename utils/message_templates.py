"""Template engine for Telegram message formatting.

Config-driven: reads field_formats, computed_vars, and default_templates
from app_constants.json.  No business rules are hardcoded here -- this
module is a generic engine that processes data-driven configuration.

Template syntax
~~~~~~~~~~~~~~~
``{variable}`` is substituted with the formatted value from the context.
Empty / None values render as empty strings.  No conditionals, no special
strings -- the user designs their template to suit their needs.

Context building
~~~~~~~~~~~~~~~~
- Every key in ``headers_schema`` becomes a ``{key}`` variable.
- ``field_formats`` (app_constants.json) declares how each key is
  formatted (currency, percentage, datetime, ...).  Keys not listed
  default to plain ``str()``.
- ``computed_vars`` (app_constants.json) declares additional variables
  that cannot be derived from a single schema-key lookup.

Template loading
~~~~~~~~~~~~~~~~
Three-tier cascade (highest priority first):

1. ``settings.json``   -- user customisation saved via the Settings UI
2. ``app_constants.json```` -- system defaults shipped with the app
3. Python fallback   -- ``FALLBACK_TEMPLATES`` below
"""

import json
import logging
import re
from datetime import datetime

from utils.constants import DATE_FMT_DISPLAY
from utils.constants_loader import get_constant
from utils.formatters import (
    format_currency,
    format_date_display,
    format_percentage,
    format_risk_reward,
    format_zone,
)

_logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
#  Formatter registry -- maps format type names to callables
# ══════════════════════════════════════════════════════════════════════════════

FORMATTERS = {
    "text": str,
    "currency": format_currency,
    "percentage": format_percentage,
    "risk_reward": format_risk_reward,
    "datetime": format_date_display,
}

# ══════════════════════════════════════════════════════════════════════════════
#  Computed-variable resolvers
# ══════════════════════════════════════════════════════════════════════════════

def _resolve_zone(trade, _update=None):
    zs = trade.get("zone_start")
    ze = trade.get("zone_end")
    if zs in (None, "") and ze in (None, ""):
        return ""
    return format_zone(zs, ze)


def _resolve_current_time(_trade=None, _update=None):
    return datetime.now().strftime(DATE_FMT_DISPLAY)


COMPUTED_RESOLVERS = {
    "zone": _resolve_zone,
    "current_time": _resolve_current_time,
}

# ══════════════════════════════════════════════════════════════════════════════
#  Python fallback templates (lowest priority)
# ══════════════════════════════════════════════════════════════════════════════

FALLBACK_TEMPLATES = {
    "new_trade": (
        "**{action}** — {stock_name}\n"
        "Segment     : {segment}\n"
        "Entry Price : {entry_price}\n"
        "Target      : {target}\n"
        "Stop Loss   : {stop_loss}\n"
        "Risk:Reward : {risk_reward}\n"
        "{created_at} | {trade_code}"
    ),
    "update": (
        "**TRADE UPDATE** — {update_type}\n"
        "\n"
        "{stock_name} ({segment})\n"
        "Action      : {action}\n"
        "Entry Price : {entry_price}\n"
        "{field_changes}\n"
        "{details}\n"
        "\n"
        "{current_time} | {trade_code}"
    ),
    "field_change_with_old": "{field_name}: {old_value} → {new_value}",
    "field_change_new_only": "{field_name}: {new_value}",
}

# ══════════════════════════════════════════════════════════════════════════════
#  Template loading
# ══════════════════════════════════════════════════════════════════════════════

def load_template(key: str) -> str:
    """Return a template string, respecting the three-tier priority."""

    # 1.  User customisation (settings DB)
    try:
        from database.settings_db import get_setting
        custom = get_setting(f"template_{key}")
        if custom:
            return custom
    except Exception:
        pass

    # 2.  System config (app_constants.json)
    defaults = get_constant("default_templates", {})
    if key in defaults:
        return defaults[key]

    # 3.  Python fallback
    fallback = FALLBACK_TEMPLATES.get(key)
    if fallback is not None:
        return fallback
    return ""


# ══════════════════════════════════════════════════════════════════════════════
#  Context builders
# ══════════════════════════════════════════════════════════════════════════════

def _build_schema_context(data: dict) -> dict:
    """Build a context dict from schema fields present in *data*."""
    context: dict = {}
    schema = get_constant("headers_schema", [])
    field_formats = get_constant("field_formats", {})

    for field in schema:
        key = field["key"]
        raw = data.get(key)
        if raw is not None and raw != "":
            fmt = field_formats.get(key, "text")
            if isinstance(raw, str) and fmt in ("currency", "percentage"):
                try:
                    raw = float(raw)
                except (ValueError, TypeError):
                    pass
            formatter = FORMATTERS.get(fmt, str)
            context[key] = formatter(raw)
        else:
            context[key] = ""

    return context


def build_trade_context(trade: dict) -> dict:
    """Build template context for a new-trade message."""

    context = _build_schema_context(trade)

    for var in get_constant("computed_vars", {}).get("trade", []):
        key = var["key"]
        resolver = COMPUTED_RESOLVERS.get(key)
        if resolver:
            val = resolver(trade)
            context[key] = "" if val is None else str(val)

    return context


def build_update_context(trade: dict, update: dict) -> dict:
    """Build template context for a trade-update message."""

    context = _build_schema_context(trade)
    field_formats = get_constant("field_formats", {})
    schema = get_constant("headers_schema", [])

    # Only overlay update fields that carry real values (no blanks)
    for field in schema:
        key = field["key"]
        raw = update.get(key)
        if raw is not None and raw != "":
            fmt = field_formats.get(key, "text")
            formatter = FORMATTERS.get(fmt, str)
            context[key] = formatter(raw)

    # Resolve trade-specific computed vars (zone)
    for var in get_constant("computed_vars", {}).get("trade", []):
        key = var["key"]
        resolver = COMPUTED_RESOLVERS.get(key)
        if resolver:
            val = resolver(trade, update)
            context[key] = "" if val is None else str(val)

    # Update-specific direct fields
    context["update_type"] = str(update.get("update_type", ""))
    context["details"] = str(update.get("details", ""))

    # Computed vars for update
    for var in get_constant("computed_vars", {}).get("update", []):
        key = var["key"]
        if key == "field_changes":
            context[key] = _build_field_changes(update)
        else:
            resolver = COMPUTED_RESOLVERS.get(key)
            if resolver:
                val = resolver(trade, update)
                context[key] = "" if val is None else str(val)

    return context


# ══════════════════════════════════════════════════════════════════════════════
#  Field-changes sub-renderer
# ══════════════════════════════════════════════════════════════════════════════

def _parse_value(raw):
    """Parse a JSON-encoded value string back to a dict, or return as-is."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    return {}


def _build_field_changes(update: dict) -> str:
    """Render the ``{field_changes}`` block using the sub-templates."""
    new_val = _parse_value(update.get("new_value"))
    old_val = _parse_value(update.get("old_value"))

    if not new_val:
        return ""

    field_formats = get_constant("field_formats", {})
    schema = get_constant("headers_schema", [])
    schema_by_key = {f["key"]: f for f in schema}

    with_old_tpl = load_template("field_change_with_old")
    new_only_tpl = load_template("field_change_new_only")

    lines = []
    for field_key, n_val in new_val.items():
        if n_val is None:
            continue
        schema_info = schema_by_key.get(field_key, {})
        label = schema_info.get("label", field_key.replace("_", " ").title())
        fmt = field_formats.get(field_key, "text")
        formatter = FORMATTERS.get(fmt, str)

        n_formatted = formatter(n_val) if n_val is not None else ""
        o_val = old_val.get(field_key)

        if o_val is not None and str(o_val) != str(n_val):
            o_formatted = formatter(o_val) if o_val is not None else ""
            line = (
                with_old_tpl.replace("{field_name}", label)
                .replace("{old_value}", str(o_formatted))
                .replace("{new_value}", str(n_formatted))
            )
        else:
            line = (
                new_only_tpl.replace("{field_name}", label)
                .replace("{new_value}", str(n_formatted))
            )
        lines.append(line)

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
#  Generic template renderer
# ══════════════════════════════════════════════════════════════════════════════

_VAR_RE = re.compile(r"\{(\w+)\}")


def render_template(template: str, context: dict) -> str:
    """Replace every ``{variable}`` placeholder with its context value.

    Unknown variables and ``None`` values render as empty strings.
    """

    def _replace(match):
        key = match.group(1)
        value = context.get(key, "")
        return "" if value is None else str(value)

    return _VAR_RE.sub(_replace, template)


# ══════════════════════════════════════════════════════════════════════════════
#  Variable discovery (for the Settings UI)
# ══════════════════════════════════════════════════════════════════════════════

def get_available_variables(template_type: str = "trade") -> list[dict]:
    """Return a list of variable metadata dicts suitable for the variable
    picker in the Settings UI.

    Derived entirely from ``headers_schema``, ``field_formats``, and
    ``computed_vars`` -- zero hard-coded variable lists.
    """
    schema = get_constant("headers_schema", [])
    field_formats = get_constant("field_formats", {})
    computed = get_constant("computed_vars", {}).get(template_type, [])

    variables: list[dict] = []

    for field in schema:
        key = field["key"]
        fmt = field_formats.get(key, "text")
        variables.append({
            "key": key,
            "label": field.get("label", key),
            "format": fmt,
            "computed": False,
            "description": field.get("label", key),
        })

    for var in computed:
        variables.append({
            "key": var["key"],
            "label": var.get("label", var["key"]),
            "format": var.get("format", "text"),
            "computed": True,
            "description": var.get("description", ""),
            "sample": var.get("sample", ""),
            "template_type": template_type,
        })

    return variables
