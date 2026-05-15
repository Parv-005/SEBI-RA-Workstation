from utils.constants import SEGMENTS, ACTION_DB, STATUSES, UPDATE_TYPES, EXCHANGE_MAP


def calculate_risk_reward(entry: float, target: float, stop_loss: float) -> str:
    risk = abs(entry - stop_loss)
    reward = abs(target - entry)
    if risk == 0:
        return "N/A"
    ratio = reward / risk
    return f"1:{ratio:.2f}"