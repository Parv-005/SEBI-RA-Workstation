SEGMENTS = ["Cash", "F&O", "MCX", "Currency", "Index"]
ACTIONS = ["BUY", "SELL"]
STATUSES = ["ACTIVE", "TARGET_HIT", "SL_HIT", "EXITED"]
UPDATE_TYPES = [
    "TARGET_HIT", "SL_HIT", "PARTIAL_PROFIT", "TRAIL_SL",
    "COST_TO_COST", "EXIT", "MODIFY_TARGET", "MODIFY_SL",
]


def calculate_risk_reward(entry: float, target: float, stop_loss: float) -> str:
    risk = abs(entry - stop_loss)
    reward = abs(target - entry)
    if risk == 0:
        return "N/A"
    ratio = reward / risk
    return f"1:{ratio:.2f}"