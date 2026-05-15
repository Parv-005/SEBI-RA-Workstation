import sys
import json
import tkinter.messagebox as messagebox
# pyrefly: ignore [missing-import]
import customtkinter as ctk
from core.paths import DATA_DIR, CONSTANTS_PATH

_DEFAULT_CONSTANTS = {
    "headers_schema": [
        {"key": "trade_code", "label": "Trade Code", "type": "string"},
        {"key": "action", "label": "LONG/SHORT", "type": "string"},
        {"key": "trade_type", "label": "Trade Type", "type": "string"},
        {"key": "created_at", "label": "Trade Given DateTime", "type": "string"},
        {"key": "stock_name", "label": "Security Name", "type": "string"},
        {"key": "cmp_at_entry", "label": "Security CMP when Trade Given", "type": "string"},
        {"key": "entry_price", "label": "Entry Price", "type": "string"},
        {"key": "zone", "label": "Entry Price Zone", "type": "custom"},
        {"key": "stop_loss", "label": "Stop Loss", "type": "string"},
        {"key": "latest_sl_price", "label": "Latest Stop Loss", "type": "string"},
        {"key": "remarks", "label": "Trade Instructions", "type": "string"},
        {"key": "risk_reward", "label": "Risk Reward Ratio", "type": "string"},
        {"key": "risk", "label": "Risk", "type": "string"},
        {"key": "reward", "label": "Reward", "type": "string"},
        {"key": "approx_time", "label": "Approx Time", "type": "string"},
        {"key": "target", "label": "Target", "type": "string"},
        {"key": "latest_target", "label": "Latest Target", "type": "string"},
        {
            "key": "cmp",
            "label": "CMP",
            "type": "formula",
            "template": '=IF(ISBLANK({stock_name_col}{row}), "", GOOGLEFINANCE("NSE:"&{stock_name_col}{row}, "price"))',
            "dependencies": ["stock_name"],
        },
        {
            "key": "live_pnl",
            "label": "Live PNL",
            "type": "formula",
            "template": "=IF(ISBLANK({cmp_col}{row}), \"\", IF({action_col}{row}=\"LONG\", {cmp_col}{row}-{entry_col}{row}, {entry_col}{row}-{cmp_col}{row}))",
            "dependencies": ["cmp", "action", "entry_price"],
        },
        {"key": "status", "label": "Status", "type": "string"},
        {"key": "close_narration", "label": "Close Narration", "type": "string"},
        {"key": "exit_price", "label": "Trade Exit Price", "type": "string"},
        {"key": "exit_datetime", "label": "Trade Exit DateTime", "type": "string"},
        {"key": "holding_period", "label": "Holding Period", "type": "string"},
        {"key": "updates", "label": "Updates", "type": "string"},
    ],
    "trade_types": [
        "INTRADAY",
        "POSITIONAL",
        "BTST",
        "STBT",
        "SCALPING",
        "LONG TERM",
    ],
    "segments": ["Cash", "F&O", "MCX", "Currency", "Index"],
    "actions": {
        "display": ["LONG", "SHORT"],
        "db": ["BUY", "SELL"],
        "display_to_db": {"LONG": "BUY", "SHORT": "SELL"},
        "db_to_display": {"BUY": "LONG", "SELL": "SHORT"},
    },
    "statuses": ["ACTIVE", "CLOSED"],
    "update_types": {
        "TARGET_HIT": {
            "close_trade": True,
            "message": "Target Achieved! Book Profits at <Exit Price>.",
            "set": {
                "exit_price": "<Exit Price>"
            }
        },
        "SL_HIT": {
            "close_trade": True,
            "message": "Stop Loss Hit at <Exit Price>. Exit trade.",
            "set": {
                "exit_price": "<Exit Price>"
            }
        },
        "PARTIAL_PROFIT": {
            "close_trade": False,
            "message": "Book partial profits at <Booking Price>. Trail SL for rest to <New SL>.",
            "set": {
                "latest_sl_price": "<New SL>",
                "booked_price": "<Booking Price>"
            }
        },
        "TRAIL_SL": {
            "close_trade": False,
            "message": "Update Stop Loss to <New Stop Loss> to protect profits.",
            "set": {
                "latest_sl_price": "<New Stop Loss>"
            }
        },
        "COST_TO_COST": {
            "close_trade": False,
            "message": "Trail SL to Cost at <Cost Price>. Hold rest.",
            "set": {
                "latest_sl_price": "<Cost Price>"
            }
        },
        "EXIT": {
            "close_trade": True,
            "message": "Exit position at <Exit Price>.",
            "set": {
                "exit_price": "<Exit Price>"
            }
        },
        "MODIFY_TARGET": {
            "close_trade": False,
            "message": "Modify Target to <New Target>.",
            "set": {
                "latest_target": "<New Target>"
            }
        },
        "MODIFY_SL": {
            "close_trade": False,
            "message": "Modify Stop Loss to <New Stop Loss>.",
            "set": {
                "latest_sl_price": "<New Stop Loss>"
            }
        }
    },
    "exchange_map": {
        "Cash": "NSE",
        "F&O": "NFO",
        "MCX": "MCX",
        "Currency": "CDS",
        "Index": "NSE",
    },
    "status_colors": {
        "ACTIVE": "#17a2b8",
        "CLOSED": "#6c757d",
    },
}


def check_constants_file():
    if not CONSTANTS_PATH.exists():
        root = ctk.CTk()
        root.withdraw()
        ans = messagebox.askyesno(
            "Missing Configuration",
            "The essential configuration file 'app_constants.json' is missing.\n\n"
            "Should the software automatically create it with default values to continue?",
        )
        if ans:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONSTANTS_PATH, "w") as f:
                json.dump(_DEFAULT_CONSTANTS, f, indent=4)
            messagebox.showinfo("Success", "app_constants.json recreated successfully.")
        else:
            messagebox.showerror("Error", "The application cannot start without 'app_constants.json'. Exiting.")
            sys.exit(1)
        root.destroy()