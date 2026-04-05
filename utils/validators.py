SEGMENTS = ["Cash", "F&O", "MCX", "Currency", "Index"]
ACTIONS = ["BUY", "SELL"]
STATUSES = ["ACTIVE", "TARGET_HIT", "SL_HIT", "CLOSED", "EXITED"]
UPDATE_TYPES = [
    "TARGET_HIT", "SL_HIT", "PARTIAL_PROFIT", "TRAIL_SL",
    "COST_TO_COST", "EXIT", "MODIFY_TARGET", "MODIFY_SL",
]


def validate_trade(data: dict) -> list[str]:
    errors = []

    if not data.get("stock_name", "").strip():
        errors.append("Stock name is required.")

    if data.get("segment") not in SEGMENTS:
        errors.append(f"Segment must be one of: {', '.join(SEGMENTS)}")

    if data.get("action") not in ACTIONS:
        errors.append("Action must be BUY or SELL.")

    for field in ("entry_price", "target", "stop_loss"):
        val = data.get(field)
        if val is None:
            errors.append(f"{field.replace('_', ' ').title()} is required.")
        else:
            try:
                v = float(val)
                if v <= 0:
                    errors.append(f"{field.replace('_', ' ').title()} must be positive.")
            except (ValueError, TypeError):
                errors.append(f"{field.replace('_', ' ').title()} must be a valid number.")

    # Trade Type logic (replaces deprecated timeframe terminology)
    from utils.constants_loader import get_constant
    trade_types = get_constant("trade_types", [])

    t_type = data.get("trade_type")
    if t_type and trade_types and t_type not in trade_types:
        errors.append(f"Trade Type must be one of: {', '.join(trade_types)}")

    if not errors:
        entry = float(data["entry_price"])
        target = float(data["target"])
        sl = float(data["stop_loss"])
        action = data["action"]

        if action == "BUY":
            if target <= entry:
                errors.append("Target should be above entry price for BUY.")
            if sl >= entry:
                errors.append("Stop loss should be below entry price for BUY.")
        elif action == "SELL":
            if target >= entry:
                errors.append("Target should be below entry price for SELL.")
            if sl <= entry:
                errors.append("Stop loss should be above entry price for SELL.")

    return errors


def validate_update(data: dict) -> list[str]:
    errors = []

    if not data.get("trade_id"):
        errors.append("Trade ID is required.")

    if data.get("update_type") not in UPDATE_TYPES:
        errors.append(f"Update type must be one of: {', '.join(UPDATE_TYPES)}")

    update_type = data.get("update_type")
    if update_type in ("TRAIL_SL", "MODIFY_SL"):
        new_sl = data.get("new_value", {}).get("stop_loss") if isinstance(data.get("new_value"), dict) else None
        if new_sl is not None:
            try:
                float(new_sl)
            except (ValueError, TypeError):
                errors.append("New stop loss must be a valid number.")

    if update_type == "MODIFY_TARGET":
        new_target = data.get("new_value", {}).get("target") if isinstance(data.get("new_value"), dict) else None
        if new_target is not None:
            try:
                float(new_target)
            except (ValueError, TypeError):
                errors.append("New target must be a valid number.")

    return errors


def calculate_risk_reward(entry: float, target: float, stop_loss: float) -> str:
    risk = abs(entry - stop_loss)
    reward = abs(target - entry)
    if risk == 0:
        return "N/A"
    ratio = reward / risk
    return f"1:{ratio:.2f}"
