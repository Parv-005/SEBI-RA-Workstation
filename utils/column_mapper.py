"""
Centralized utility to map internal `trade_data` dictionaries to user-configured
Spreadsheet/XLSX header columns. Supports dynamic formulas.
"""

from utils.constants_loader import get_constant
from utils.logger import setup_logger
from string import ascii_uppercase

logger = setup_logger("ColumnMapper")

_headers_schema = None


def get_headers_schema():
    global _headers_schema
    if _headers_schema is None:
        try:
            _headers_schema = get_constant("headers_schema", [])
        except FileNotFoundError:
            _headers_schema = []
    return _headers_schema


def DEFAULT_HEADERS():
    """Lazy-loaded default headers dynamically generated from the schema."""
    return [h.get("label") for h in get_headers_schema()]


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


def map_trade_to_columns(
    trade: dict, headers: list, is_google_sheets: bool = False, row_num: int = None
) -> list:
    """
    Given an internal trade dict and a list of headers, build an ordered row list dynamically from schema.
    If `is_google_sheets` is True and `row_num` is provided, live formulas are injected dynamically.
    """
    row = []
    schema = get_headers_schema()

    # Pre-calculate column letters for formulas
    column_letters = {}
    for h in schema:
        # e.g., creates "stock_name_col", "cmp_col" mappings for template injection
        column_letters[f"{h.get('key')}_col"] = get_column_letter(headers, h.get("label"))

    for header in headers:
        val = ""
        # Find corresponding schema map
        schema_entry = next((item for item in schema if item.get("label") == header), None)

        if schema_entry:
            key = schema_entry.get("key")
            field_type = schema_entry.get("type", "string")

            if field_type == "formula":
                if is_google_sheets and row_num:
                    template = schema_entry.get("template", "")
                    format_kwargs = {"row": row_num}
                    format_kwargs.update(column_letters)
                    try:
                        val = template.format(**format_kwargs)
                    except KeyError:
                        val = ""
                else:
                    val = ""

            elif field_type == "custom" and key == "zone":
                zs = trade.get("zone_start")
                ze = trade.get("zone_end")
                if zs and ze:
                    val = f"{zs} - {ze}"
                elif zs:
                    val = str(zs)
                else:
                    val = str(trade.get("entry_price", ""))

            else:
                # normal field mapping
                val = trade.get(key, "")

                # special fallback override purely for missing close_narration logic
                if key == "remarks" and trade.get("status") in ["EXITED", "TARGET_HIT", "SL_HIT"]:
                    if trade.get("close_narration"):
                        val = trade.get("close_narration", "")
                        
                elif key == "holding_period":
                    if trade.get("exit_datetime") and trade.get("created_at"):
                        val = "Calculated externally"
        else:
            # Fallback for old/unmapped columns
            internal_key = header.lower().replace(" ", "_").replace(":", "_")
            val = trade.get(internal_key, "")

        row.append(val)

    return row


def map_row_to_trade(row_dict: dict) -> dict:
    """Map a dictionary keyed by human-readable Headers back to an internal trade dict dynamically from schema."""
    trade = {}
    schema = get_headers_schema()

    if "id" in row_dict:
        trade["id"] = row_dict["id"]

    for header, value in row_dict.items():
        schema_entry = next((item for item in schema if item.get("label") == header), None)

        if schema_entry:
            key = schema_entry.get("key")
            field_type = schema_entry.get("type", "string")

            if field_type == "custom" and key == "zone":
                if value:
                    parts = str(value).split("-")
                    if len(parts) == 2:
                        trade["zone_start"] = parts[0].strip()
                        trade["zone_end"] = parts[1].strip()
                    else:
                        trade["zone_start"] = str(value).strip()
            elif field_type != "formula":
                # Only map back normal values, skipped dynamically structured ones like formulas
                trade[key] = value
                
            # If the user renamed the Status column but it corresponds to `status`, it will be dynamically mapped.
        elif header and header.lower() == "id":
            trade["id"] = value
        elif header:
            # Fallback
            internal_key = header.lower().replace(" ", "_").replace(":", "_")
            trade[internal_key] = value

    return trade

