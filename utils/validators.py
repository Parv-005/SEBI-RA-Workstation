from utils.constants_loader import get_constant

SEGMENTS = get_constant("segments", ["Cash", "F&O", "MCX", "Currency", "Index"])
ACTIONS = get_constant("actions", {}).get("db", ["BUY", "SELL"])
STATUSES = get_constant("statuses", ["ACTIVE", "TARGET_HIT", "SL_HIT", "EXITED"])
UPDATE_TYPES = get_constant("update_types", [
    "TARGET_HIT", "SL_HIT", "PARTIAL_PROFIT", "TRAIL_SL",
    "COST_TO_COST", "EXIT", "MODIFY_TARGET", "MODIFY_SL",
])
EXCHANGE_MAP = get_constant("exchange_map", {
    "Cash": "NSE",
    "F&O": "NFO",
    "MCX": "MCX",
    "Currency": "CDS",
    "Index": "NSE",
})


def calculate_risk_reward(entry: float, target: float, stop_loss: float) -> str:
    risk = abs(entry - stop_loss)
    reward = abs(target - entry)
    if risk == 0:
        return "N/A"
    ratio = reward / risk
    return f"1:{ratio:.2f}"