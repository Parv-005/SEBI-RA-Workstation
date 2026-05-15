from core.paths import DATA_DIR, TRADES_PATH, UPDATES_PATH
from utils.column_mapper import DEFAULT_HEADERS, map_row_to_trade
from utils.logger import setup_logger
from openpyxl import load_workbook, Workbook
from datetime import datetime

logger = setup_logger("DBHelpers")


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_wb(path, headers: list):
    if path.exists():
        return load_workbook(path)
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    wb.save(path)
    return wb


def _save_workbook(wb, path):
    wb.save(path)


def _next_id(ws) -> int:
    max_id = 0
    for row in ws.iter_rows(min_row=2, max_col=1, values_only=True):
        val = row[0]
        if isinstance(val, int) and val > max_id:
            max_id = val
    return max_id + 1


def _wb_to_dicts(ws, headers=None, is_trades=True):
    rows = []
    sheet_headers = [c.value for c in ws[1]]
    if not any(sheet_headers):
        sheet_headers = headers if headers else DEFAULT_HEADERS()

    for row in ws.iter_rows(min_row=2, values_only=True):
        if all(v is None for v in row):
            continue
        processed = []
        for v in row:
            if isinstance(v, datetime):
                processed.append(v.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                processed.append(v)
        row_dict = dict(zip(sheet_headers, processed))
        if is_trades:
            rows.append(map_row_to_trade(row_dict))
        else:
            rows.append(row_dict)
    return rows