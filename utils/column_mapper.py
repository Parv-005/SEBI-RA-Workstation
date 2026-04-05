"""
Centralized utility to map internal `trade_data` dictionaries to user-configured 
Spreadsheet/XLSX header columns. Supports dynamic formulas.
"""
from utils.constants_loader import get_constant
from string import ascii_uppercase

DEFAULT_HEADERS = get_constant("default_headers", [])

def col_idx_to_letter(col_idx: int) -> str:
    """Convert 1-based column index to letter (1 -> A, 2 -> B, 27 -> AA)."""
    result = ""
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        result = ascii_uppercase[remainder] + result
    return result

def get_column_letter(headers: list, target_header: str) -> str:
    """Find a header's column index and return its Excel/Sheets letter. Returns 'A' if not found."""
    try:
        idx = headers.index(target_header) + 1
        return col_idx_to_letter(idx)
    except ValueError:
        return "A"  # fallback

def map_trade_to_columns(trade: dict, headers: list, is_google_sheets: bool = False, row_num: int = None) -> list:
    """
    Given an internal trade dict and a list of headers, build an ordered row list.
    If `is_google_sheets` is True and `row_num` is provided, live formulas are injected.
    """
    row = []
    
    # Pre-calculate column letters for formulas
    sec_name_col = get_column_letter(headers, "Security Name")
    entry_col = get_column_letter(headers, "Entry Price")
    action_col = get_column_letter(headers, "LONG/SHORT")
    cmp_col = get_column_letter(headers, "CMP")
    
    for header in headers:
        val = ""
        
        # Simple Maps
        if header == "Trade Code":
            val = trade.get("trade_code", "")
        elif header == "LONG/SHORT":
            val = trade.get("action", "")
        elif header == "Trade Type":
            val = trade.get("trade_type", "")
        elif header == "Trade Given DateTime":
            val = trade.get("created_at", "")
        elif header == "Security Name":
            val = trade.get("stock_name", "")
        elif header == "Security CMP when Trade Given":
            val = trade.get("cmp_at_entry", "")
        elif header == "Entry Price":
            val = trade.get("entry_price", "")
        elif header == "Stop Loss":
            val = trade.get("stop_loss", "")
        elif header == "Trade Instructions":
            val = trade.get("remarks", "")
            # If trade has closed and there's no exit narration, use remarks
            if trade.get("status") in ["EXITED", "CLOSED", "TARGET_HIT", "SL_HIT"]:
                if trade.get("close_narration"):
                    val = trade.get("close_narration", "")
        elif header == "Risk Reward Ratio":
            val = trade.get("risk_reward", "")
        elif header == "Risk":
            val = trade.get("risk", "")
        elif header == "Reward":
            val = trade.get("reward", "")
        elif header == "Approx Time":
            val = trade.get("approx_time", "")
        elif header == "Target":
            val = trade.get("target", "")
        elif header == "Trade Status (ACTIVE/CLOSE)":
            val = trade.get("status", "ACTIVE")
            
        # Complex/Derived Maps
        elif header == "Entry Price Zone":
            zs = trade.get("zone_start")
            ze = trade.get("zone_end")
            if zs and ze:
                val = f"{zs} - {ze}"
            elif zs:
                val = str(zs)
            else:
                val = str(trade.get("entry_price", ""))

        elif header == "Trade Close Narration":
            val = trade.get("close_narration", "")
        elif header == "Trade Exit Price":
            val = trade.get("exit_price", "")
        elif header == "Trade Exit DateTime":
            val = trade.get("exit_datetime", "")
            
        elif header == "Holding Period":
            # For local XLSX we might do a text calculation if we wanted, but let's keep it simple
            if trade.get("exit_datetime") and trade.get("created_at"):
                val = "Calculated externally" # Will enhance later if needed
            else:
                val = ""
                
        # Formula Injection
        elif header == "CMP":
            if is_google_sheets and row_num:
                # =IF(ISBLANK(E2), "", GOOGLEFINANCE("NSE:"&E2, "price"))
                val = f'=IF(ISBLANK({sec_name_col}{row_num}), "", GOOGLEFINANCE("NSE:"&{sec_name_col}{row_num}, "price"))'
            else:
                val = ""
                
        elif header == "Live PNL":
            if is_google_sheets and row_num:
                # PNL formula depending on action being LONG or SHORT
                # =IF(ISBLANK(CMP_COL), "", IF(ACTION_COL="LONG", CMP_COL - ENTRY_COL, ENTRY_COL - CMP_COL))
                val = f'=IF(ISBLANK({cmp_col}{row_num}), "", IF({action_col}{row_num}="LONG", {cmp_col}{row_num}-{entry_col}{row_num}, {entry_col}{row_num}-{cmp_col}{row_num}))'
            else:
                val = ""

        else:
            # Fallback for old/unmapped columns
            # Try to see if it matches an internal key
            internal_key = header.lower().replace(" ", "_").replace(":", "_")
            if internal_key in trade:
                val = trade[internal_key]
            else:
                val = ""
                
        row.append(val)
        
    return row

def map_row_to_trade(row_dict: dict) -> dict:
    """Map a dictionary keyed by human-readable Headers back to an internal trade dict."""
    trade = {}
    
    mapping = {
         "Trade Code": "trade_code",
         "LONG/SHORT": "action",
         "Trade Type": "trade_type",
         "Trade Given DateTime": "created_at",
         "Security Name": "stock_name",
         "Security CMP when Trade Given": "cmp_at_entry",
         "Entry Price": "entry_price",
         "Stop Loss": "stop_loss",
         "Trade Instructions": "remarks",
         "Risk Reward Ratio": "risk_reward",
         "Risk": "risk",
         "Reward": "reward",
         "Approx Time": "approx_time",
         "Target": "target",
         "Trade Status (ACTIVE/CLOSE)": "status",
         "Trade Close Narration": "close_narration",
         "Trade Exit Price": "exit_price",
         "Trade Exit DateTime": "exit_datetime",
    }
    
    if "id" in row_dict:
        trade["id"] = row_dict["id"]
        
    for header, value in row_dict.items():
        if header in mapping:
            trade[mapping[header]] = value
        elif header == "Entry Price Zone":
            if value:
                parts = str(value).split("-")
                if len(parts) == 2:
                    trade["zone_start"] = parts[0].strip()
                    trade["zone_end"] = parts[1].strip()
                else:
                    trade["zone_start"] = str(value).strip()
        elif header and header.lower() == "id":
            trade["id"] = value
        elif header:
            # Fallback
            internal_key = header.lower().replace(" ", "_").replace(":", "_")
            trade[internal_key] = value
            
    return trade
