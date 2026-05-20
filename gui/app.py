import traceback
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget,
    QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QAction

from gui.signals import get_signals
from gui.widgets.sidebar import Sidebar
from gui.widgets.toast import ToastManager, ToastWidget
from gui.theme import apply_theme


class MainWindow(QMainWindow):
    PAGE_NEW_TRADE = "new_trade"
    PAGE_ACTIVE_TRADES = "active_trades"
    PAGE_TRADE_DETAIL = "trade_detail"
    PAGE_SETTINGS = "settings"

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._signals = get_signals()

        self._current_trade = None
        self._views = {}

        self._setup_ui()
        self._connect_signals()
        self._setup_shortcuts()

        QTimer.singleShot(0, lambda: self._navigate_to(self.PAGE_ACTIVE_TRADES, None))

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("central")
        central.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)

        content_container = QWidget()
        content_container.setObjectName("content_container")
        content_container.setStyleSheet("background-color: transparent;")
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: transparent;")
        content_layout.addWidget(self.stack, 1)

        self.toast_overlay = ToastManager(content_container)
        self.toast_overlay.setGeometry(0, 0, 0, 0)
        self.toast_overlay.raise_()

        main_layout.addWidget(content_container, 1)

        self._update_toast_bounds = True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self._reposition_toasts)

    def _reposition_toasts(self):
        if self.toast_overlay:
            w = self.stack.width() if self.stack else self.width()
            h = self.stack.height() if self.stack else self.height()
            self.toast_overlay.setGeometry(
                w - 380, 20, 380, h - 40
            )

    def _connect_signals(self):
        self._signals.navigate.connect(self._navigate_to)
        self._signals.notification.connect(self._show_notification)

    def _setup_shortcuts(self):
        sc_new = QShortcut(QKeySequence("Ctrl+N"), self)
        sc_new.activated.connect(lambda: self._navigate_to(self.PAGE_NEW_TRADE, None))

        sc_list = QShortcut(QKeySequence("Ctrl+R"), self)
        sc_list.activated.connect(
            lambda: self._navigate_to(self.PAGE_ACTIVE_TRADES, None)
        )

        sc_settings = QShortcut(QKeySequence("Ctrl+S"), self)
        sc_settings.activated.connect(lambda: self._navigate_to(self.PAGE_SETTINGS, None))

        sc_back = QShortcut(QKeySequence("Escape"), self)
        sc_back.activated.connect(self._on_escape)

    def _get_or_create_view(self, page_name):
        if page_name not in self._views:
            view = self._create_view(page_name)
            if view:
                self._views[page_name] = view
                self.stack.addWidget(view)
        return self._views.get(page_name)

    def _create_view(self, page_name):
        try:
            if page_name == self.PAGE_NEW_TRADE:
                from gui.views.trade_form import NewTradeView
                return NewTradeView(self._controller)
            elif page_name == self.PAGE_ACTIVE_TRADES:
                from gui.views.trade_list import TradeListView
                return TradeListView(self._controller)
            elif page_name == self.PAGE_SETTINGS:
                from gui.views.settings_page import SettingsView
                return SettingsView(self._controller)
            elif page_name == self.PAGE_TRADE_DETAIL:
                from gui.views.trade_detail import TradeDetailView
                return TradeDetailView(self._controller)
        except Exception as e:
            self._show_critical(f"Failed to create view '{page_name}'", str(e))
            return None

    def _navigate_to(self, page_name, data):
        try:
            if page_name == self.PAGE_TRADE_DETAIL:
                if page_name in self._views:
                    old = self._views.pop(page_name)
                    self.stack.removeWidget(old)
                    old.deleteLater()
            elif page_name == self.PAGE_NEW_TRADE:
                if page_name in self._views:
                    old = self._views.pop(page_name)
                    self.stack.removeWidget(old)
                    old.deleteLater()

            view = self._get_or_create_view(page_name)
            if not view:
                return

            self.sidebar.set_active(page_name)
            self.stack.setCurrentWidget(view)

            if hasattr(view, 'on_show') and data is not None:
                view.on_show(data)
            elif hasattr(view, 'on_show'):
                view.on_show()

            self._reposition_toasts()
        except Exception as e:
            self._show_critical("Navigation error", str(e))

    def _show_notification(self, message, level, duration_ms):
        ToastManager.show(message, level, duration_ms)

    def _show_critical(self, title, message):
        QMessageBox.critical(self, title, message)

    def _on_escape(self):
        if self.sidebar:
            self._navigate_to(self.PAGE_ACTIVE_TRADES, None)

    def show_trade_detail(self, trade):
        self._navigate_to(self.PAGE_TRADE_DETAIL, trade)

    def closeEvent(self, event):
        self._views.clear()
        super().closeEvent(event)
