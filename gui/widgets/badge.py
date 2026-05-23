from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from gui.theme import get_color
from utils.constants import STATUS_COLORS, UPDATE_TYPE_COLORS


_BADGE_TYPE_TO_THEME = {
    "ACTIVE": "badge_teal",
    "CLOSED": "badge_gray",
    "LONG": "badge_green",
    "SHORT": "badge_red",
    "TARGET_HIT": "badge_green",
    "SL_HIT": "badge_red",
    "PARTIAL_PROFIT": "badge_teal",
    "TRAIL_SL": "badge_blue",
    "COST_TO_COST": "badge_yellow",
    "EXIT": "badge_yellow",
    "MODIFY_TARGET": "badge_blue",
    "MODIFY_SL": "badge_blue",
}

_BADGE_TEXT_DARK = "#1a1a2e"


def _resolve_badge_style(badge_type: str) -> tuple[str, str]:
    theme_key = _BADGE_TYPE_TO_THEME.get(badge_type, "badge_blue")
    bg_color = get_color(theme_key)
    text_color = "#ffffff"
    if theme_key == "badge_yellow":
        text_color = _BADGE_TEXT_DARK
    return bg_color, text_color


class Badge(QFrame):
    def __init__(self, text, badge_type=None, font_size=11, parent=None):
        super().__init__(parent)
        self.setObjectName("badge")

        if badge_type is None:
            badge_type = text.upper()

        bg, text_color = _resolve_badge_style(badge_type)

        self.setStyleSheet(f"""
        #badge {{
            background-color: {bg};
            border-radius: 4px;
            padding: 2px 8px;
        }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)

        self._label = QLabel(text)
        self._label.setStyleSheet(f"color: {text_color}; background: transparent; border: none;")
        self._label.setFont(QFont("Segoe UI", font_size, QFont.Bold))
        self._label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._label)

    def set_text(self, text):
        self._label.setText(text)

    def set_color(self, badge_type):
        bg, text_color = _resolve_badge_style(badge_type)
        self.setStyleSheet(f"""
        #badge {{
            background-color: {bg};
            border-radius: 4px;
            padding: 2px 8px;
        }}
        """)
        self._label.setStyleSheet(
            f"color: {text_color}; background: transparent; border: none;"
        )
