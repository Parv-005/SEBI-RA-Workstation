from datetime import datetime


def format_new_trade(trade: dict) -> str:
    action_emoji = "🟢" if trade["action"] == "BUY" else "🔴"
    segment = trade["segment"]

    lines = [
        f"{action_emoji} **{trade['action']}** — {trade['stock_name']}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"📊 Segment     : {segment}",
        f"💰 Entry Price : ₹{trade['entry_price']:.2f}",
    ]

    # Zone (optional)
    if trade.get("zone_start") and trade.get("zone_end"):
        lines.append(
            f"📍 Entry Zone  : ₹{trade['zone_start']:.2f} – ₹{trade['zone_end']:.2f}"
        )

    lines += [
        f"🎯 Target      : ₹{trade['target']:.2f}",
        f"🛑 Stop Loss   : ₹{trade['stop_loss']:.2f}",
    ]

    if trade.get("trade_type"):
        lines.append(f"🏷️  Trade Type  : {trade['trade_type']}")

    if trade.get("approx_time"):
        lines.append(f"🕰️  Approx Time : {trade['approx_time']}")

    lines.append(f"━━━━━━━━━━━━━━━━━━━━")

    if trade.get("reward") or trade.get("risk"):
        lines += [
            f"🟢 Reward      : ₹{trade.get('reward', 0):.2f} ({trade.get('reward_pct', 0):.2f}%)",
            f"🔴 Risk        : ₹{trade.get('risk', 0):.2f} ({trade.get('risk_pct', 0):.2f}%)",
        ]

    if trade.get("risk_reward"):
        lines.append(f"⚖️  Risk:Reward : {trade['risk_reward']}")

    if trade.get("cmp_at_entry"):
        lines.append(f"📈 CMP         : ₹{trade['cmp_at_entry']:.2f}")

    if trade.get("remarks"):
        lines.append(f"📝 Remarks     : {trade['remarks']}")

    lines.append(f"━━━━━━━━━━━━━━━━━━━━")

    # Use DB timestamp if available, else current time
    ts = trade.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        dt = datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S")
        ts_fmt = dt.strftime("%d-%b-%Y %I:%M %p")
    except Exception:
        ts_fmt = str(ts)
    lines.append(f"🕐 {ts_fmt}")

    if trade.get("trade_code"):
        lines.append(f"🆔 {trade['trade_code']}")

    return "\n".join(lines)


def format_trade_update(trade: dict, update: dict) -> str:
    type_labels = {
        "TARGET_HIT":    "🎯 TARGET HIT",
        "SL_HIT":        "🛑 STOP LOSS HIT",
        "PARTIAL_PROFIT": "💰 PARTIAL PROFIT BOOKED",
        "TRAIL_SL":      "🔄 STOP LOSS TRAILED",
        "COST_TO_COST":  "⚖️ MOVED TO COST TO COST",
        "EXIT":          "🚪 EXIT / CLOSE TRADE",
        "MODIFY_TARGET": "🎯 TARGET MODIFIED",
        "MODIFY_SL":     "🛑 STOP LOSS MODIFIED",
    }

    update_type = update.get("update_type", "")
    label = type_labels.get(update_type, update_type)

    lines = [
        f"📢 **TRADE UPDATE**",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"{label}",
        f"",
        f"📊 {trade['stock_name']} ({trade['segment']})",
        f"📌 Action      : {trade['action']}",
        f"💰 Entry Price : ₹{trade['entry_price']:.2f}",
    ]

    if update_type in ("TRAIL_SL", "MODIFY_SL") and update.get("new_value"):
        import json
        new_val = update["new_value"]
        if isinstance(new_val, str):
            new_val = json.loads(new_val)
        old_val = update.get("old_value")
        if isinstance(old_val, str):
            old_val = json.loads(old_val)
        lines.append(f"🛑 Old SL      : ₹{old_val.get('stop_loss', 'N/A')}")
        lines.append(f"🛑 New SL      : ₹{new_val.get('stop_loss', 'N/A')}")

    elif update_type == "MODIFY_TARGET" and update.get("new_value"):
        import json
        new_val = update["new_value"]
        if isinstance(new_val, str):
            new_val = json.loads(new_val)
        old_val = update.get("old_value")
        if isinstance(old_val, str):
            old_val = json.loads(old_val)
        lines.append(f"🎯 Old Target  : ₹{old_val.get('target', 'N/A')}")
        lines.append(f"🎯 New Target  : ₹{new_val.get('target', 'N/A')}")

    if update.get("details"):
        lines.append(f"📝 {update['details']}")

    lines.append(f"━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🕐 {datetime.now().strftime('%d-%b-%Y %I:%M %p')}")

    if trade.get("trade_code"):
        lines.append(f"🆔 {trade['trade_code']}")

    return "\n".join(lines)
