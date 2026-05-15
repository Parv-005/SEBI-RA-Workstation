from dataclasses import dataclass
from utils.constants import ACTION_DISPLAY_MAP, ACTION_DB_MAP
from utils.logger import setup_logger

logger = setup_logger("TradeService")


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
    return ACTION_DB_MAP.get(db_action, db_action)


# ── Validation behaviour ──────────────────────────────────
# Set to True to BLOCK submission when close_trade=True and no exit price given.
# Set to False to only WARN and allow proceeding.
BLOCK_ON_MISSING_EXIT_PRICE: bool = True


def compute_update_fields(
    trade: dict, update_type: str, dynamic_values: dict[str, str], remarks: str
) -> tuple[dict, dict | None, dict | None, dict]:
    """
    Fully data-driven computation of trade field updates based on the update_types
    config (UPDATE_TYPES_DICT). No hardcoded conditions per update_type value.

    Returns (trade_updates, old_value, new_value, update_data_dict).
    """
    from utils.constants import UPDATE_TYPES_DICT
    from datetime import datetime

    trade_code = trade.get("trade_code", "?")
    logger.debug(f"compute_update_fields: trade_code={trade_code}, update_type={update_type}")

    update_info = UPDATE_TYPES_DICT.get(update_type, {})
    close_trade: bool = update_info.get("close_trade", False)
    set_fields: dict = update_info.get("set", {})

    trade_updates: dict = {}
    old_value: dict = {}
    new_value: dict = {}

    # ── Handle trade closure (driven purely by close_trade flag) ──────────────
    if close_trade:
        trade_updates["status"] = "CLOSED"
        trade_updates["exit_datetime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trade_updates["close_narration"] = f"[{update_type}] {remarks}"

    # ── Process configured set fields ─────────────────────────────────────────
    for field, placeholder in set_fields.items():
        dynamic_key = placeholder.strip("<>")
        val_str = dynamic_values.get(dynamic_key, "")
        if val_str:
            try:
                val = float(val_str)
            except ValueError:
                val = val_str
            trade_updates[field] = val
            new_value[field] = val

            # old_value: prefer the "latest_" variant already stored, fall back
            # to the original field by stripping the "latest_" prefix and resolving
            # the canonical field name via LATEST_FIELD_ORIGINALS.
            old_value[field] = _resolve_old_value(trade, field)

    # ── Extra Exit Price input when close_trade=True but no exit_price in set ─
    # (guards future update types that close a trade without an exit_price set field)
    if close_trade and "exit_price" not in set_fields:
        extra_exit_str = dynamic_values.get("Exit Price", "")
        if extra_exit_str:
            val = float(extra_exit_str)
            trade_updates["exit_price"] = val
            new_value["exit_price"] = val
            old_value["exit_price"] = trade.get("exit_price")

    # ── Recalculate Risk/Reward if SL or target moved ─────────────────────────
    if "latest_sl_price" in trade_updates or "latest_target" in trade_updates:
        entry = float(trade.get("entry_price", 0) or 0)
        current_tgt = float(trade.get("latest_target") or trade.get("target", 0) or 0)
        current_sl = float(trade.get("latest_sl_price") or trade.get("stop_loss", 0) or 0)
        action = trade.get("action", "LONG")

        mod_tgt = trade_updates.get("latest_target", current_tgt)
        mod_sl = trade_updates.get("latest_sl_price", current_sl)

        rr = calculate_risk_reward(action, entry, mod_tgt, mod_sl)
        trade_updates["reward"] = rr.reward
        trade_updates["risk"] = rr.risk
        trade_updates["reward_pct"] = rr.reward_pct
        trade_updates["risk_pct"] = rr.risk_pct
        trade_updates["risk_reward"] = rr.risk_reward

    # ── Normalise empties ─────────────────────────────────────────────────────
    final_old = old_value if old_value else None
    final_new = new_value if new_value else None

    if not trade_code or trade_code == "?":
        raise ValueError("Strict Check Failed: trade_code is missing or invalid.")

    update_data_dict: dict = {
        "trade_code": trade_code,
        "update_type": update_type,
        "details": remarks,
        "old_value": final_old,
        "new_value": final_new,
    }
    for k in ("reward", "risk", "reward_pct", "risk_pct", "risk_reward"):
        if k in trade_updates:
            update_data_dict[k] = trade_updates[k]

    return trade_updates, final_old, final_new, update_data_dict


# ── Helpers ───────────────────────────────────────────────────────────────────

# Maps "latest_X" field names to their original counterpart in the trade dict.
# Extend this dict if new "latest_" fields are added.
_LATEST_FIELD_ORIGINALS: dict[str, str] = {
    "latest_sl_price": "stop_loss",
    "latest_target": "target",
}


def _resolve_old_value(trade: dict, field: str):
    """Return the existing value for a field, using the original field as fallback for latest_ variants."""
    current = trade.get(field)
    if current is not None:
        return current
    original = _LATEST_FIELD_ORIGINALS.get(field)
    if original:
        return trade.get(original)
    return None