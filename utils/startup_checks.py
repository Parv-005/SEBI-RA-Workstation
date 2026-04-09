import sys
import json
from pathlib import Path
import tkinter.messagebox as messagebox
import customtkinter as ctk

def check_constants_file():
    """Verify that the essential app_constants.json file exists before starting the app."""
    data_dir = Path(__file__).resolve().parent.parent / "data"
    constants_path = data_dir / "app_constants.json"
    
    if not constants_path.exists():
        root = ctk.CTk()
        root.withdraw()
        ans = messagebox.askyesno(
            "Missing Configuration", 
            "The essential configuration file 'app_constants.json' is missing.\n\nShould the software automatically create it with default values to continue?"
        )
        if ans:
            data_dir.mkdir(parents=True, exist_ok=True)
            with open(constants_path, "w") as f:
                json.dump({
                    "headers_schema": [
                        { "key": "trade_code", "label": "Trade Code", "type": "string" },
                        { "key": "action", "label": "LONG/SHORT", "type": "string" },
                        { "key": "trade_type", "label": "Trade Type", "type": "string" },
                        { "key": "created_at", "label": "Trade Given DateTime", "type": "string" },
                        { "key": "stock_name", "label": "Security Name", "type": "string" },
                        { "key": "cmp_at_entry", "label": "Security CMP when Trade Given", "type": "string" },
                        { "key": "entry_price", "label": "Entry Price", "type": "string" },
                        { "key": "zone", "label": "Entry Price Zone", "type": "custom" },
                        { "key": "stop_loss", "label": "Stop Loss", "type": "string" },
                        { "key": "remarks", "label": "Trade Instructions", "type": "string" },
                        { "key": "risk_reward", "label": "Risk Reward Ratio", "type": "string" },
                        { "key": "risk", "label": "Risk", "type": "string" },
                        { "key": "reward", "label": "Reward", "type": "string" },
                        { "key": "approx_time", "label": "Approx Time", "type": "string" },
                        { "key": "target", "label": "Target", "type": "string" },
                        { 
                            "key": "cmp", 
                            "label": "CMP", 
                            "type": "formula", 
                            "template": "=IF(ISBLANK({stock_name_col}{row}), \"\", GOOGLEFINANCE(\"NSE:\"&{stock_name_col}{row}, \"price\"))",
                            "dependencies": ["stock_name"] 
                        },
                        { 
                            "key": "live_pnl", 
                            "label": "Live PNL", 
                            "type": "formula", 
                            "template": "=IF(ISBLANK({cmp_col}{row}), \"\", IF({action_col}{row}=\"LONG\", {cmp_col}{row}-{entry_col}{row}, {entry_col}{row}-{cmp_col}{row}))",
                            "dependencies": ["cmp", "action", "entry_price"] 
                        },
                        { "key": "status", "label": "Trade Status (ACTIVE/CLOSE)", "type": "string" },
                        { "key": "close_narration", "label": "Trade Close Narration", "type": "string" },
                        { "key": "exit_price", "label": "Trade Exit Price", "type": "string" },
                        { "key": "exit_datetime", "label": "Trade Exit DateTime", "type": "string" },
                        { "key": "holding_period", "label": "Holding Period", "type": "string" }
                    ],
                    "trade_types": [
                        "INTRADAY", "POSITIONAL", "BTST", "STBT", "SCALPING", "LONG TERM"
                    ]
                }, f, indent=4)
            messagebox.showinfo("Success", "app_constants.json recreated successfully.")
        else:
            messagebox.showerror("Error", "The application cannot start without 'app_constants.json'. Exiting.")
            sys.exit(1)
        root.destroy()
