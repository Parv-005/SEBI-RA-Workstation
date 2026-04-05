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
                    "default_headers": [
                        "Trade Code", "LONG/SHORT", "Trade Type", "Trade Given DateTime", 
                        "Security Name", "Security CMP when Trade Given", "Entry Price", 
                        "Entry Price Zone", "Stop Loss", "Trade Instructions", 
                        "Risk Reward Ratio", "Risk", "Reward", "Approx Time", "Target", 
                        "CMP", "Live PNL", "Trade Status (ACTIVE/CLOSE)", 
                        "Trade Close Narration", "Trade Exit Price", "Trade Exit DateTime", 
                        "Holding Period"
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
