import json
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from utils.logger import setup_logger

logger = setup_logger("GoogleSheetsService")

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class EmptySheetError(Exception):
    pass


class GoogleSheetsService:
    def __init__(self):
        self.client = None
        self.sheet = None
        self._load_config()

    def _load_config(self):
        self.sa_json_path = ""
        self.spreadsheet_id = ""
        self.sheet_name = "Trades"
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                config = json.load(f)
            gs = config.get("google_sheets", {})
            self.sa_json_path = gs.get("service_account_json", "")
            self.spreadsheet_id = gs.get("spreadsheet_id", "")
            self.sheet_name = gs.get("sheet_name", "Trades")

    def is_configured(self) -> bool:
        return bool(
            self.sa_json_path
            and self.spreadsheet_id
            and Path(self.sa_json_path).exists()
        )

    def connect(self):
        if not self.is_configured():
            logger.error("Google Sheets credentials not configured or JSON missing.")
            raise ValueError("Google Sheets credentials not configured.")
        try:
            creds = Credentials.from_service_account_file(
                self.sa_json_path, scopes=SCOPES
            )
            self.client = gspread.authorize(creds)
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            try:
                self.sheet = spreadsheet.worksheet(self.sheet_name)
            except gspread.WorksheetNotFound:
                logger.info(
                    f"Worksheet {self.sheet_name} not found. Creating a new one."
                )
                self.sheet = spreadsheet.add_worksheet(
                    self.sheet_name, rows=1000, cols=26
                )
                # Do NOT auto-write header here per user request for GUI pop-up
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}", exc_info=True)
            raise

    def _write_header(self):
        from utils.column_mapper import DEFAULT_HEADERS

        self.sheet.update("A1", [DEFAULT_HEADERS()])

    def append_trade(self, trade: dict, skip_header_check: bool = False):
        try:
            if not self.sheet:
                self.connect()

            # Fetch the actual headers from the sheet first
            headers = self.sheet.row_values(1)
            if not headers:
                if not skip_header_check:
                    raise EmptySheetError(
                        "Google Sheet is empty and requires initialization."
                    )
                else:
                    from utils.column_mapper import DEFAULT_HEADERS

                    headers = DEFAULT_HEADERS()

            # What is the row number this trade will be appended to?
            # It's row count + 1 (for formulas)
            row_num = len(self.sheet.col_values(1)) + 1

            from utils.column_mapper import map_trade_to_columns

            row = map_trade_to_columns(
                trade, headers, is_google_sheets=True, row_num=row_num
            )

            self.sheet.append_row(row, value_input_option="USER_ENTERED")
            logger.info(f"Appended trade {trade.get('trade_code')} to Google Sheets.")
        except Exception as e:
            logger.error(f"Error appending trade to Google Sheets: {e}", exc_info=True)
            raise

    def update_trade_row(
        self, trade_id: int, update_data: dict, trade_updates: dict = None
    ):
        try:
            if not self.sheet:
                self.connect()

            # Dynamic header finding
            headers = self.sheet.row_values(1)
            try:
                db_id_col = headers.index("DB ID") + 1
            except ValueError:
                db_id_col = 2

            # Try to find ID in the new location
            try:
                cell = self.sheet.find(str(trade_id), in_column=db_id_col)
            except gspread.CellNotFound:
                cell = None

            # Fallback to column 1 for old rows before Trade Code was added
            if not cell:
                try:
                    cell = self.sheet.find(str(trade_id), in_column=1)
                except gspread.CellNotFound:
                    pass

            if not cell:
                logger.warning(
                    f"Trade ID {trade_id} not found in Google Sheets for update."
                )
                return False

            row_num = cell.row

            # Map update keys directly to header names
            mapping = {
                "target": "Target",
                "stop_loss": "Stop Loss",
                "status": "Status",
                "remarks": "Remarks",
                "updated_at": "Updated At",
                "risk_reward": "Risk:Reward",
                "reward": "Reward",
                "risk": "Risk",
                "reward_pct": "Reward %",
                "risk_pct": "Risk %",
            }

            for key, header_name in mapping.items():
                if key in update_data or (trade_updates and key in trade_updates):
                    try:
                        col_idx = headers.index(header_name) + 1
                        val = update_data.get(key) or (trade_updates or {}).get(key, "")
                        self.sheet.update_cell(row_num, col_idx, val)
                    except ValueError:
                        pass  # Ignore if that column header isn't in Google Sheets

            logger.info(f"Updated trade {trade_id} row in Google Sheets.")
            return True
        except Exception as e:
            logger.error(
                f"Error updating trade row in Google Sheets: {e}", exc_info=True
            )
            return False
