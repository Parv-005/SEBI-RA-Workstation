from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel,
    QComboBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from gui.theme import get_color, current_theme, apply_theme
from gui.signals import get_signals


class Sidebar(QFrame):
    _PAGES = [
        ("new_trade", "New Trade", "Ctrl+N"),
        ("active_trades", "Active Trades", "Ctrl+R"),
        ("settings", "Settings", "Ctrl+S"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)

        self._active_page = None
        self._buttons = {}

        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(self._sidebar_qss())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        title = QLabel("RA\nAutomation")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(f"color: {get_color('text_primary')}; padding: 0 0 20 0;")
        title.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(title)

        nav_container = QWidget()
        nav_container.setObjectName("nav_container")
        nav_container.setStyleSheet("background-color: transparent;")
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)

        for page_id, label, shortcut in self._PAGES:
            btn = QPushButton(f"  {label}")
            btn.setObjectName("nav_button")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(40)
            btn.setToolTip(f"{shortcut}")
            btn.clicked.connect(lambda checked=False, p=page_id: self._on_nav_click(p))
            nav_layout.addWidget(btn)
            self._buttons[page_id] = btn

        nav_layout.addStretch()
        layout.addWidget(nav_container, 1)

        theme_container = QWidget()
        theme_container.setObjectName("theme_container")
        theme_container.setStyleSheet("background-color: transparent;")
        theme_layout = QVBoxLayout(theme_container)
        theme_layout.setContentsMargins(0, 10, 0, 0)
        theme_layout.setSpacing(4)

        theme_label = QLabel("Appearance")
        theme_label.setStyleSheet(
            f"color: {get_color('text_secondary')}; font-size: 11px; "
            f"font-weight: 600; text-transform: uppercase; padding: 4px 0;"
        )
        theme_layout.addWidget(theme_label)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark", "Light"])
        self._theme_combo.setCurrentText("Dark" if current_theme() == "dark" else "Light")
        self._theme_combo.currentTextChanged.connect(self._on_theme_change)
        theme_layout.addWidget(self._theme_combo)

        layout.addWidget(theme_container)

        self._update_active_button()

    def _sidebar_qss(self):
        bg = get_color("surface")
        hover = get_color("surface_hover")
        accent = get_color("accent")
        text = get_color("text_primary")
        muted = get_color("text_secondary")
        border = get_color("border")

        return f"""
        #sidebar {{
            background-color: {bg};
            border-right: 1px solid {border};
            border-radius: 0px;
        }}
        QPushButton#nav_button {{
            background-color: transparent;
            color: {muted};
            border: none;
            border-radius: 8px;
            padding: 10px 14px;
            text-align: left;
            font-size: 13px;
            font-weight: 500;
        }}
        QPushButton#nav_button:hover {{
            background-color: {hover};
            color: {text};
        }}
        QPushButton#nav_button:checked,
        QPushButton#nav_button[active="true"] {{
            background-color: {accent};
            color: {text};
        }}
        QComboBox {{
            font-size: 12px;
            padding: 6px 10px;
            min-height: 16px;
        }}
        """

    def _on_nav_click(self, page_id):
        self._active_page = page_id
        self._update_active_button()
        get_signals().navigate.emit(page_id, None)

    def _update_active_button(self):
        for page_id, btn in self._buttons.items():
            is_active = page_id == self._active_page
            btn.setProperty("active", "true" if is_active else "false")
            btn.setChecked(is_active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_theme_change(self, mode):
        theme = mode.lower()
        apply_theme(theme)
        self.setStyleSheet(self._sidebar_qss())
        get_signals().theme_changed.emit(theme)

    def set_active(self, page_id):
        self._active_page = page_id
        self._update_active_button()
