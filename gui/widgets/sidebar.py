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
        layout.setContentsMargins(16, 24, 16, 16)
        layout.setSpacing(0)

        title = QLabel("RA\nAutomation")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet(
            f"color: {get_color('accent')}; padding: 0 0 28 0; background: transparent; border: none;"
        )
        title.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(title)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(
            f"background-color: {get_color('border')}; border: none; margin: 0 0 16 0;"
        )
        layout.addWidget(sep)

        nav_container = QWidget()
        nav_container.setObjectName("nav_container")
        nav_container.setStyleSheet("#nav_container { background-color: transparent; }")
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(2)

        for page_id, label, shortcut in self._PAGES:
            btn = QPushButton(label)
            btn.setObjectName("nav_button")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(40)
            btn.setToolTip(shortcut)
            btn.clicked.connect(lambda checked=False, p=page_id: self._on_nav_click(p))
            nav_layout.addWidget(btn)
            self._buttons[page_id] = btn

        nav_layout.addStretch()
        layout.addWidget(nav_container, 1)

        theme_container = QWidget()
        theme_container.setObjectName("theme_container")
        theme_container.setStyleSheet("#theme_container { background-color: transparent; }")
        theme_layout = QVBoxLayout(theme_container)
        theme_layout.setContentsMargins(0, 10, 0, 0)
        theme_layout.setSpacing(6)

        theme_label = QLabel("Appearance")
        theme_label.setStyleSheet(
            f"color: {get_color('text_muted')}; font-size: 10px; "
            f"font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; "
            f"padding: 0; background: transparent; border: none;"
        )
        theme_layout.addWidget(theme_label)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark", "Light"])
        self._theme_combo.setCurrentText("Dark" if current_theme() == "dark" else "Light")
        self._theme_combo.currentTextChanged.connect(self._on_theme_change)
        theme_layout.addWidget(self._theme_combo)

        compliance = QLabel("SEBI Reg: INH000021386")
        compliance.setStyleSheet(
            f"color: {get_color('text_muted')}; font-size: 9px; "
            f"padding: 8 0 0 0; background: transparent; border: none;"
        )
        compliance.setAlignment(Qt.AlignLeft)
        theme_layout.addWidget(compliance)

        layout.addWidget(theme_container)

        self._update_active_button()

    def _sidebar_qss(self):
        bg = get_color("surface")
        hover = get_color("surface_hover")
        accent = get_color("accent")
        text = get_color("text_primary")
        muted = get_color("text_secondary")
        border = get_color("border")
        nav_active = get_color("nav_active_bg")
        nav_border = get_color("nav_active_border")
        text_muted = get_color("text_muted")

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
            border-left: 3px solid transparent;
            border-radius: 0 6px 6px 0;
            padding: 10px 14px 10px 11px;
            text-align: left;
            font-size: 13px;
            font-weight: 500;
            margin: 1px 6px 1px 0;
        }}
        QPushButton#nav_button:hover {{
            background-color: {hover};
            color: {text};
            border-left: 3px solid {text_muted};
        }}
        QPushButton#nav_button:checked,
        QPushButton#nav_button[active="true"] {{
            background-color: {nav_active};
            color: {accent};
            border-left: 3px solid {nav_border};
            font-weight: 600;
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
        self._update_active_button()
        for child in self.findChildren(QLabel):
            if "SEBI" in child.text():
                child.setStyleSheet(
                    f"color: {get_color('text_muted')}; font-size: 9px; "
                    f"padding: 8 0 0 0; background: transparent; border: none;"
                )
        get_signals().theme_changed.emit(theme)

    def set_active(self, page_id):
        self._active_page = page_id
        self._update_active_button()

    def refresh_style(self):
        self.setStyleSheet(self._sidebar_qss())
        self._update_active_button()