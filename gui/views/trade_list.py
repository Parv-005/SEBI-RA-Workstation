from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableView, QHeaderView, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QSortFilterProxyModel, QEvent
from PySide6.QtGui import QFont, QColor, QPalette

from gui.models.trade_table_model import (
    TradeTableModel, TradeFilterModel, COL_WIDTHS, COL_UPDATE,
)
from gui.signals import get_signals
from gui.theme import get_color
from gui.widgets.button_delegate import ButtonDelegate
from gui.widgets.row_hover_delegate import RowHoverDelegate
from gui.widgets.toast import ToastWidget
from utils.constants import STATUSES, STATUS_COLORS, ACTION_COLORS, FILTER_ALL
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
        self._filter_combo.addItems([FILTER_ALL] + list(STATUSES))
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

        self._row_delegate = RowHoverDelegate(self._table)
        self._table.setItemDelegate(self._row_delegate)

        self._btn_delegate = ButtonDelegate(self._table, self._row_delegate)
        self._table.setItemDelegateForColumn(COL_UPDATE, self._btn_delegate)

        self._table.viewport().installEventFilter(self)

        header_view = self._table.horizontalHeader()
        header_view.setStretchLastSection(False)
        header_view.setSectionResizeMode(
            COL_UPDATE - 1, QHeaderView.Stretch
        )
        header_view.setSectionResizeMode(
            COL_UPDATE, QHeaderView.Fixed
        )
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
        if index.column() == COL_UPDATE:
            return
        proxy_index = self._table.currentIndex()
        source_index = self._proxy.mapToSource(proxy_index)
        trade = self._model.trade_at(source_index.row())
        if trade:
            logger.debug(f"Trade selected: {trade.get('trade_code')}")
            self._signals.navigate.emit("trade_detail", trade)

    def _open_update_dialog(self, trade):
        from gui.views.update_dialog import UpdateDialog
        dialog = UpdateDialog(trade, self._controller, self)
        dialog.finished.connect(self._on_update_dialog_finished)
        dialog.open()

    def _on_update_dialog_finished(self, result):
        if result == 1:
            self._do_refresh()

    def eventFilter(self, obj, event):
        if obj is self._table.viewport():
            et = event.type()
            if et == QEvent.MouseMove:
                pos = event.position().toPoint()
                row = self._table.rowAt(pos.y())
                col = self._table.columnAt(pos.x())
                self._row_delegate.hover_row = row
                if col == COL_UPDATE and row >= 0:
                    self._btn_delegate.set_hover(row)
                else:
                    self._btn_delegate.clear_hover()
            elif et == QEvent.Leave:
                self._row_delegate.clear_pressed()
                self._row_delegate.clear_hover()
                self._btn_delegate.clear_hover()
                self._btn_delegate.clear_pressed()
            elif et == QEvent.MouseButtonPress:
                pos = event.position().toPoint()
                row = self._table.rowAt(pos.y())
                col = self._table.columnAt(pos.x())
                self._row_delegate.pressed_row = row
                if col == COL_UPDATE and row >= 0:
                    self._btn_delegate.set_pressed(row)
                else:
                    self._btn_delegate.clear_pressed()
            elif et == QEvent.MouseButtonRelease:
                pos = event.position().toPoint()
                row = self._table.rowAt(pos.y())
                col = self._table.columnAt(pos.x())
                self._row_delegate.clear_pressed()
                if col == COL_UPDATE and row >= 0 and self._btn_delegate._press_row == row:
                    proxy_idx = self._proxy.index(row, col)
                    source_idx = self._proxy.mapToSource(proxy_idx)
                    trade = self._model.trade_at(source_idx.row())
                    if trade:
                        self._open_update_dialog(trade)
                self._btn_delegate.clear_pressed()
        return super().eventFilter(obj, event)

    def refresh_style(self):
        self._table.viewport().update()