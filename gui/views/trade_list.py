from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableView, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QSortFilterProxyModel
from PySide6.QtGui import QFont, QColor, QPalette

from gui.models.trade_table_model import TradeTableModel, TradeFilterModel, COL_WIDTHS
from gui.signals import get_signals
from gui.theme import get_color
from gui.widgets.toast import ToastWidget
from utils.constants import STATUSES, STATUS_COLORS, ACTION_COLORS
from utils.logger import setup_logger

logger = setup_logger("TradeList")


class TradeListView(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._signals = get_signals()
        self._trade_map = {}

        self._model = TradeTableModel()
        self._proxy = TradeFilterModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setSortRole(Qt.DisplayRole)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(12)

        title = QLabel("Active Trades")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet(f"color: {get_color('text_primary')}; background: transparent;")
        header.addWidget(title)

        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["ALL"] + list(STATUSES))
        self._filter_combo.setMinimumWidth(120)
        self._filter_combo.currentTextChanged.connect(self._on_filter_change)
        header.addWidget(self._filter_combo)

        self._count_label = QLabel("")
        self._count_label.setStyleSheet(
            f"color: {get_color('text_secondary')}; font-size: 12px; background: transparent;"
        )
        header.addWidget(self._count_label)

        header.addStretch()

        self._refresh_btn = QPushButton("\u21bb  Refresh")
        self._refresh_btn.setObjectName("ghost")
        self._refresh_btn.setCursor(Qt.PointingHandCursor)
        self._refresh_btn.clicked.connect(self._do_refresh)
        header.addWidget(self._refresh_btn)

        layout.addLayout(header)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableView.SelectRows)
        self._table.setSelectionMode(QTableView.SingleSelection)
        self._table.setShowGrid(False)
        self._table.setSortingEnabled(True)
        self._table.verticalHeader().hide()
        self._table.setMouseTracking(True)
        self._table.setCursor(Qt.PointingHandCursor)

        header_view = self._table.horizontalHeader()
        header_view.setStretchLastSection(True)
        header_view.setSectionsClickable(True)
        header_view.setHighlightSections(False)
        header_view.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        for i, w in enumerate(COL_WIDTHS):
            self._table.setColumnWidth(i, w)

        self._table.clicked.connect(self._on_row_click)

        layout.addWidget(self._table, 1)

        self._no_data_label = QLabel("No trades found matching filters.")
        self._no_data_label.setAlignment(Qt.AlignCenter)
        self._no_data_label.setStyleSheet(
            f"color: {get_color('text_muted')}; font-size: 14px; "
            f"background: transparent; padding: 40px;"
        )
        self._no_data_label.setFont(QFont("Segoe UI", 14))
        self._no_data_label.hide()
        layout.addWidget(self._no_data_label)

    def _connect_signals(self):
        self._signals.trades_loaded.connect(self._on_trades_loaded)
        self._signals.trades_error.connect(self._on_trades_error)

    def _on_filter_change(self, status):
        self._proxy.set_status_filter(status)
        self._update_count()

    def on_show(self):
        self._do_refresh()

    def _do_refresh(self):
        try:
            trades = self._controller.get_trades()
        except Exception as e:
            logger.error(f"Controller get_trades failed: {e}", exc_info=True)
            trades = []
            from database.db_manager import get_all_trades
            try:
                trades = get_all_trades()
            except Exception as e2:
                logger.error(f"Direct DB fallback also failed: {e2}", exc_info=True)
                self._signals.notification.emit(
                    f"Failed to load trades: {e2}", ToastWidget.ERROR, 5000
                )
        self._on_trades_loaded(trades)

    def _on_trades_loaded(self, trades):
        self._model.set_trades(trades)
        self._proxy.sort(1, Qt.DescendingOrder)
        self._update_count()

        has_data = len(trades) > 0
        self._table.setVisible(has_data)
        self._no_data_label.setVisible(not has_data)

    def _on_trades_error(self, err):
        self._signals.notification.emit(
            f"Failed to load trades: {err}",
            ToastWidget.ERROR,
            5000,
        )

    def _update_count(self):
        count = self._proxy.rowCount()
        self._count_label.setText(
            f"{count} trade{'s' if count != 1 else ''}"
        )

    def _on_row_click(self, index):
        proxy_index = self._table.currentIndex()
        source_index = self._proxy.mapToSource(proxy_index)
        trade = self._model.trade_at(source_index.row())
        if trade:
            logger.debug(f"Trade selected: {trade.get('trade_code')}")
            self._signals.navigate.emit("trade_detail", trade)
