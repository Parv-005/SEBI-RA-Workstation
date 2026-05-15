from dataclasses import dataclass
from utils.constants_loader import get_constant
from utils.logger import setup_logger

logger = setup_logger("TradeService")

_actions_config = get_constant("actions", {})
ACTION_DISPLAY_MAP = _actions_config.get("display_to_db", {"LONG": "BUY", "SHORT": "SELL"})
DISPLAY_ACTION_MAP = _actions_config.get("db_to_display", {"BUY": "LONG", "SELL": "SHORT"})

UPDATE_TYPE_DEFAULTS = get_constant("update_type_defaults", {
    "TARGET_HIT": "Target Achieved! Book Profits.",
    "SL_HIT": "Stop Loss Hit. Exit trade.",
    "COST_TO_COST": "Trail SL to Cost. Hold rest.",
    "PARTIAL_PROFIT": "Book partial profits here. Trail SL for rest.",
    "TRAIL_SL": "Update Stop Loss to protect profits.",
    "EXIT": "Exit position at CMP.",
    "MODIFY_TARGET": "",
    "MODIFY_SL": "",
})

UPDATE_TYPES = get_constant("update_types", list(UPDATE_TYPE_DEFAULTS.keys()))


@dataclass
class RiskRewardResult:
    reward: float
    risk: float
    reward_pct: float
    risk_pct: float
    risk_reward: str


def calculate_risk_reward(
    action: str, entry: float, target: float, stop_loss: float
) -> RiskRewardResult:
    if action in ("LONG", "BUY"):
        reward = target - entry
        risk = entry - stop_loss
    else:
        reward = entry - target
        risk = abs(entry - stop_loss)

    reward_pct = (reward / entry * 100) if entry > 0 else 0.0
    risk_pct = (risk / entry * 100) if entry > 0 else 0.0

    if risk == 0 or reward <= 0:
        risk_reward_str = ""
    else:
        ratio = reward / risk
        risk_reward_str = f"1 : {ratio:.2f}"

    return RiskRewardResult(
        reward=reward,
        risk=risk,
        reward_pct=reward_pct,
        risk_pct=risk_pct,
        risk_reward=risk_reward_str,
    )


def to_db_action(display_action: str) -> str:
    return ACTION_DISPLAY_MAP.get(display_action, display_action)


def to_display_action(db_action: str) -> str:
    return DISPLAY_ACTION_MAP.get(db_action, db_action)


def compute_update_fields(
    trade: dict, update_type: str, new_value_str: str, remarks: str
) -> tuple[dict, dict | None, dict | None]:
    trade_id = trade.get("id", "?")
    logger.debug(f"compute_update_fields: trade_id={trade_id}, update_type={update_type}")
    trade_updates = {}
    old_value = None
    new_value = None

    if update_type in ("TRAIL_SL", "MODIFY_SL"):
        new_sl = float(new_value_str) if new_value_str else None
        if new_sl is None:
            raise ValueError("New Stop Loss is required.")
        old_value = {"stop_loss": trade["stop_loss"]}
        new_value = {"stop_loss": new_sl}
        trade_updates["stop_loss"] = new_sl

    elif update_type == "MODIFY_TARGET":
        new_tgt = float(new_value_str) if new_value_str else None
        if new_tgt is None:
            raise ValueError("New Target is required.")
        old_value = {"target": trade["target"]}
        new_value = {"target": new_tgt}
        trade_updates["target"] = new_tgt

    elif update_type == "TARGET_HIT":
        trade_updates["status"] = "TARGET_HIT"

    elif update_type == "SL_HIT":
        trade_updates["status"] = "SL_HIT"

    elif update_type == "EXIT":
        from datetime import datetime

        trade_updates["status"] = "EXITED"
        trade_updates["close_narration"] = remarks
        trade_updates["exit_datetime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if new_value_str:
            exit_price = float(new_value_str)
            new_value = {"exit_price": exit_price}
            trade_updates["exit_price"] = exit_price

    elif update_type == "COST_TO_COST":
        old_value = {"stop_loss": trade["stop_loss"]}
        new_value = {"stop_loss": trade["entry_price"]}
        trade_updates["stop_loss"] = trade["entry_price"]

    elif update_type == "PARTIAL_PROFIT":
        if new_value_str:
            booked_price = float(new_value_str)
            new_value = {"booked_price": booked_price}
            trade_updates["booked_price"] = booked_price

    if update_type in ("TRAIL_SL", "MODIFY_SL", "MODIFY_TARGET", "COST_TO_COST"):
        entry = float(trade.get("entry_price", 0) or 0)
        current_tgt = float(trade.get("target", 0) or 0)
        current_sl = float(trade.get("stop_loss", 0) or 0)
        action = trade.get("action", "LONG")

        mod_tgt = trade_updates.get("target", current_tgt)
        mod_sl = trade_updates.get("stop_loss", current_sl)

        rr = calculate_risk_reward(action, entry, mod_tgt, mod_sl)
        trade_updates["reward"] = rr.reward
        trade_updates["risk"] = rr.risk
        trade_updates["reward_pct"] = rr.reward_pct
        trade_updates["risk_pct"] = rr.risk_pct
        trade_updates["risk_reward"] = rr.risk_reward

    update_data_dict = {
        "update_type": update_type,
        "details": remarks,
        "old_value": old_value,
        "new_value": new_value,
    }
    for k in ("reward", "risk", "reward_pct", "risk_pct", "risk_reward"):
        if k in trade_updates:
            update_data_dict[k] = trade_updates[k]

    return trade_updates, old_value, new_value, update_data_dict