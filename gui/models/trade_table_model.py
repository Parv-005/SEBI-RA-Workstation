from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QColor

from services.trade_service import to_display_action
from utils.constants import EMPTY_PLACEHOLDER, CURRENCY_SYMBOL, DEFAULT_ACTION, FILTER_ALL
from utils.formatters import format_currency, format_date_short


COLUMNS = [
    "Trade Code", "Date", "Stock", "Segment",
    "Action", "Entry", "Target", "SL", "Status",
]

COL_WIDTHS = [120, 95, 150, 85, 70, 100, 100, 100, 90]


class TradeTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._trades = []
        self._rows = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows) if not parent.isValid() else 0

    def columnCount(self, parent=QModelIndex()):
        return len(COLUMNS) if not parent.isValid() else 0

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if row >= len(self._rows):
            return None

        if role == Qt.DisplayRole:
            return self._rows[row][col]
        elif role == Qt.UserRole:
            return self._trades[row] if row < len(self._trades) else None
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(COLUMNS):
                return COLUMNS[section]
        return None

    def _format_price(self, value):
        return format_currency(value)

    def _build_row(self, trade):
        date_str = format_date_short(trade.get("created_at"))
        trade_code = trade.get("trade_code") or "?"
        action_display = to_display_action(trade.get("action") or DEFAULT_ACTION)
        entry_str = self._format_price(trade.get("entry_price"))
        target_str = self._format_price(trade.get("target"))
        sl_str = self._format_price(trade.get("stop_loss"))
        status_text = trade.get("status") or EMPTY_PLACEHOLDER

        return (
            trade_code,
            date_str,
            trade.get("stock_name") or EMPTY_PLACEHOLDER,
            trade.get("segment") or EMPTY_PLACEHOLDER,
            action_display,
            entry_str,
            target_str,
            sl_str,
            status_text,
        )

    def set_trades(self, trades):
        self.beginResetModel()
        self._trades = list(trades) if trades else []
        self._rows = [self._build_row(t) for t in self._trades]
        self.endResetModel()

    def trade_at(self, row):
        if 0 <= row < len(self._trades):
            return self._trades[row]
        return None

    def refresh(self):
        if hasattr(self, "_last_fetch_fn"):
            trades = self._last_fetch_fn() if callable(self._last_fetch_fn) else []
            self.set_trades(trades)


class TradeFilterModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._status_filter = None
        self._search_query = None
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setSortRole(Qt.DisplayRole)

    def set_status_filter(self, status):
        self._status_filter = status if status and status != FILTER_ALL else None
        self.invalidateFilter()

    def set_search_query(self, query):
        self._search_query = query.strip().lower() if query else None
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        if not model:
            return True
        trade = model.trade_at(source_row)
        if not trade:
            return True

        if self._status_filter:
            trade_status = (trade.get("status") or "")
            if trade_status != self._status_filter:
                return False

        if self._search_query:
            stock = (trade.get("stock_name") or "").lower()
            code = (trade.get("trade_code") or "").lower()
            if (
                self._search_query not in stock
                and self._search_query not in code
            ):
                return False

        return True

    def lessThan(self, left, right):
        source = self.sourceModel()
        if not source:
            return super().lessThan(left, right)
        l_trade = source.trade_at(left.row())
        r_trade = source.trade_at(right.row())
        if l_trade and r_trade:
            l_date = l_trade.get("created_at") or ""
            r_date = r_trade.get("created_at") or ""
            if l_date != r_date:
                return l_date < r_date
        return super().lessThan(left, right)
