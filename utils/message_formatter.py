import json
from datetime import datetime

from utils.constants import DATE_FMT_DISPLAY, EMPTY_PLACEHOLDER, EMOJI
from utils.formatters import format_currency, format_date_display, format_percentage, format_zone
from utils.logger import setup_logger

logger = setup_logger("MessageFormatter")


def _is_long(action) -> bool:
    return str(action).upper() in ("BUY", "LONG")


def format_new_trade(trade: dict) -> str:
    action = trade.get("action") or EMPTY_PLACEHOLDER
    action_emoji = EMOJI["LONG"] if _is_long(action) else EMOJI["SHORT"]
    segment = trade.get("segment") or EMPTY_PLACEHOLDER
    stock_name = trade.get("stock_name") or EMPTY_PLACEHOLDER

    lines = [
        f"{action_emoji} **{action}** \u2014 {stock_name}",
        EMOJI["SEPARATOR"],
        f"{EMOJI['SEGMENT']} Segment     : {segment}",
        f"{EMOJI['ENTRY_PRICE']} Entry Price : {format_currency(trade.get('entry_price'))}",
    ]

    zone_str = format_zone(trade.get("zone_start"), trade.get("zone_end"))
    if zone_str != EMPTY_PLACEHOLDER:
        lines.append(f"{EMOJI['ENTRY_ZONE']} Entry Zone  : {zone_str}")

    lines += [
        f"{EMOJI['TARGET']} Target      : {format_currency(trade.get('target'))}",
        f"{EMOJI['STOP_LOSS']} Stop Loss   : {format_currency(trade.get('stop_loss'))}",
    ]

    if trade.get("trade_type"):
        lines.append(f"{EMOJI['TRADE_TYPE']} Trade Type  : {trade['trade_type']}")

    if trade.get("approx_time"):
        lines.append(f"{EMOJI['APPROX_TIME']} Approx Time : {trade['approx_time']}")

    lines.append(EMOJI["SEPARATOR"])

    if trade.get("reward") is not None or trade.get("risk") is not None:
        lines += [
            f"{EMOJI['REWARD']} Reward      : {format_currency(trade.get('reward'))} ({format_percentage(trade.get('reward_pct'))})",
            f"{EMOJI['RISK']} Risk        : {format_currency(trade.get('risk'))} ({format_percentage(trade.get('risk_pct'))})",
        ]

    if trade.get("risk_reward"):
        lines.append(f"{EMOJI['RISK_REWARD']} Risk:Reward : {trade['risk_reward']}")

    if trade.get("cmp_at_entry"):
        lines.append(f"{EMOJI['CMP']} CMP         : {format_currency(trade.get('cmp_at_entry'))}")

    if trade.get("remarks"):
        lines.append(f"{EMOJI['REMARKS']} Remarks     : {trade['remarks']}")

    lines.append(EMOJI["SEPARATOR"])
    lines.append(f"{EMOJI['TIMESTAMP']} {format_date_display(trade.get('created_at'))}")

    if trade.get("trade_code"):
        lines.append(f"{EMOJI['TRADE_ID']} {trade['trade_code']}")

    return "\n".join(lines)


def format_trade_update(trade: dict, update: dict) -> str:
    update_type = update.get("update_type", "")
    label = f"{EMOJI['UPDATE']} {update_type.replace('_', ' ')}"

    stock = trade.get("stock_name") or EMPTY_PLACEHOLDER
    segment = trade.get("segment") or EMPTY_PLACEHOLDER
    action = trade.get("action") or EMPTY_PLACEHOLDER

    lines = [
        f"{EMOJI['TRADE_UPDATE']} **TRADE UPDATE**",
        EMOJI["SEPARATOR"],
        label,
        "",
        f"{EMOJI['SEGMENT']} {stock} ({segment})",
        f"{EMOJI['ACTION']} Action      : {action}",
        f"{EMOJI['ENTRY_PRICE']} Entry Price : {format_currency(trade.get('entry_price'))}",
    ]

    new_val = update.get("new_value")
    old_val = update.get("old_value")

    if isinstance(new_val, str):
        try:
            new_val = json.loads(new_val) if new_val else {}
        except Exception:
            logger.debug(f"Could not parse new_value JSON: {new_val}")
            new_val = {}
    if isinstance(old_val, str):
        try:
            old_val = json.loads(old_val) if old_val else {}
        except Exception:
            logger.debug(f"Could not parse old_value JSON: {old_val}")
            old_val = {}

    if new_val:
        for field, n_val in new_val.items():
            o_val = (old_val or {}).get(field)
            f_name = field.replace("_", " ").title()
            if o_val is not None and str(o_val) != str(n_val):
                lines.append(f"{EMOJI['FIELD_CHANGE']} {f_name}: {o_val} \u2192 {n_val}")
            else:
                lines.append(f"{EMOJI['FIELD_CHANGE']} {f_name}: {n_val}")

    msg = update.get("message") or update.get("details")
    if msg:
        lines.append(f"{EMOJI['REMARKS']} {msg}")

    lines.append(EMOJI["SEPARATOR"])
    lines.append(f"{EMOJI['TIMESTAMP']} {format_date_display()}")

    if trade.get("trade_code"):
        lines.append(f"{EMOJI['TRADE_ID']} {trade['trade_code']}")

    return "\n".join(lines)
