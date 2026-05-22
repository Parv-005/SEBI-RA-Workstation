import json
from datetime import datetime

from utils.logger import setup_logger

logger = setup_logger("MessageFormatter")


def _safe_float(value, field_name="unknown"):
    try:
        return float(value) if value is not None else 0
    except (ValueError, TypeError):
        logger.debug(f"Non-numeric value for {field_name}: {value}")
        raise


def format_new_trade(trade: dict) -> str:
    action = trade.get("action", "—")
    action_emoji = "🟢" if action in ("BUY", "LONG") else "🔴"
    segment = trade.get("segment", "—")
    stock_name = trade.get("stock_name", "—")

    try:
        entry_price_fmt = f"₹{_safe_float(trade.get('entry_price'), 'entry_price'):.2f}"
    except (ValueError, TypeError):
        entry_price_fmt = str(trade.get("entry_price", "—"))

    lines = [
        f"{action_emoji} **{action}** — {stock_name}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"📊 Segment     : {segment}",
        f"💰 Entry Price : {entry_price_fmt}",
    ]

    if trade.get("zone_start") and trade.get("zone_end"):
        try:
            lines.append(f"📍 Entry Zone  : ₹{_safe_float(trade['zone_start'], 'zone_start'):.2f} – ₹{_safe_float(trade['zone_end'], 'zone_end'):.2f}")
        except (ValueError, TypeError):
            lines.append(f"📍 Entry Zone  : {trade['zone_start']} – {trade['zone_end']}")

    try:
        tgt_fmt = f"₹{_safe_float(trade.get('target'), 'target'):.2f}"
    except (ValueError, TypeError):
        tgt_fmt = str(trade.get('target', '—'))

    try:
        sl_fmt = f"₹{_safe_float(trade.get('stop_loss'), 'stop_loss'):.2f}"
    except (ValueError, TypeError):
        sl_fmt = str(trade.get('stop_loss', '—'))

    lines += [
        f"🎯 Target      : {tgt_fmt}",
        f"🛑 Stop Loss   : {sl_fmt}",
    ]

    if trade.get("trade_type"):
        lines.append(f"🏷️  Trade Type  : {trade['trade_type']}")

    if trade.get("approx_time"):
        lines.append(f"🕰️  Approx Time : {trade['approx_time']}")

    lines.append(f"━━━━━━━━━━━━━━━━━━━━")

    if trade.get("reward") is not None or trade.get("risk") is not None:
        try:
            reward_fmt = f"₹{_safe_float(trade.get('reward'), 'reward'):.2f} ({_safe_float(trade.get('reward_pct'), 'reward_pct'):.2f}%)"
            risk_fmt = f"₹{_safe_float(trade.get('risk'), 'risk'):.2f} ({_safe_float(trade.get('risk_pct'), 'risk_pct'):.2f}%)"
        except (ValueError, TypeError):
            reward_fmt = str(trade.get("reward", "—"))
            risk_fmt = str(trade.get("risk", "—"))

        lines += [
            f"🟢 Reward      : {reward_fmt}",
            f"🔴 Risk        : {risk_fmt}",
        ]

    if trade.get("risk_reward"):
        lines.append(f"⚖️  Risk:Reward : {trade['risk_reward']}")

    if trade.get("cmp_at_entry"):
        try:
            cmp_fmt = f"₹{_safe_float(trade['cmp_at_entry'], 'cmp_at_entry'):.2f}"
        except (ValueError, TypeError):
            cmp_fmt = str(trade['cmp_at_entry'])
        lines.append(f"📈 CMP         : {cmp_fmt}")

    if trade.get("remarks"):
        lines.append(f"📝 Remarks     : {trade['remarks']}")

    lines.append(f"━━━━━━━━━━━━━━━━━━━━")

    ts = trade.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        dt = datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S")
        ts_fmt = dt.strftime("%d-%b-%Y %I:%M %p")
    except Exception:
        logger.debug(f"Could not parse timestamp: {ts}")
        ts_fmt = str(ts)
    lines.append(f"🕐 {ts_fmt}")

    if trade.get("trade_code"):
        lines.append(f"🆔 {trade['trade_code']}")

    return "\n".join(lines)


def format_trade_update(trade: dict, update: dict) -> str:
    update_type = update.get("update_type", "")
    label = f"🔔 {update_type.replace('_', ' ')}"

    stock = trade.get('stock_name', '—')
    segment = trade.get('segment', '—')
    action = trade.get('action', '—')
    try:
        entry_price = f"₹{_safe_float(trade.get('entry_price'), 'entry_price'):.2f}"
    except (ValueError, TypeError):
        entry_price = str(trade.get('entry_price', '—'))

    lines = [
        f"📢 **TRADE UPDATE**",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"{label}",
        f"",
        f"📊 {stock} ({segment})",
        f"📌 Action      : {action}",
        f"💰 Entry Price : {entry_price}",
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
            f_name = field.replace('_', ' ').title()
            if o_val is not None and str(o_val) != str(n_val):
                lines.append(f"🔄 {f_name}: {o_val} → {n_val}")
            else:
                lines.append(f"🔄 {f_name}: {n_val}")

    msg = update.get("message") or update.get("details")
    if msg:
        lines.append(f"📝 {msg}")

    lines.append(f"━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🕐 {datetime.now().strftime('%d-%b-%Y %I:%M %p')}")

    if trade.get("trade_code"):
        lines.append(f"🆔 {trade['trade_code']}")

    return "\n".join(lines)
