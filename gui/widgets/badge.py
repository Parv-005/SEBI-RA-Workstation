from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from gui.theme import get_color


_BADGE_COLORS = {
    "ACTIVE": ("badge_teal", "#ffffff"),
    "CLOSED": ("badge_gray", "#ffffff"),
    "LONG": ("badge_green", "#ffffff"),
    "SHORT": ("badge_red", "#ffffff"),
    "TARGET_HIT": ("badge_green", "#ffffff"),
    "SL_HIT": ("badge_red", "#ffffff"),
    "PARTIAL_PROFIT": ("badge_teal", "#ffffff"),
    "TRAIL_SL": ("badge_blue", "#ffffff"),
    "COST_TO_COST": ("badge_yellow", "#1a1a2e"),
    "EXIT": ("badge_yellow", "#1a1a2e"),
    "MODIFY_TARGET": ("badge_blue", "#ffffff"),
    "MODIFY_SL": ("badge_blue", "#ffffff"),
}


class Badge(QFrame):
    def __init__(self, text, badge_type=None, font_size=11, parent=None):
        super().__init__(parent)
        self.setObjectName("badge")

        if badge_type is None:
            badge_type = text.upper()

        color_key, text_color = _BADGE_COLORS.get(
            badge_type, ("badge_blue", "#ffffff")
        )
        bg = get_color(color_key)

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
        color_key, text_color = _BADGE_COLORS.get(
            badge_type, ("badge_blue", "#ffffff")
        )
        bg = get_color(color_key)
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
