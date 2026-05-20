from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from gui.theme import get_color


class FieldRow(QWidget):
    def __init__(self, label, value="", value_color=None, label_width=140, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        self._label = QLabel(label)
        self._label.setFixedWidth(label_width)
        self._label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self._label.setStyleSheet(f"color: {get_color('text_secondary')}; "
                                   f"background: transparent; border: none;")
        layout.addWidget(self._label)

        self._value = QLabel(str(value))
        self._value.setFont(QFont("Segoe UI", 12))
        self._value.setStyleSheet(f"color: {get_color('text_primary')}; "
                                   f"background: transparent; border: none;")
        if value_color:
            self._value.setStyleSheet(
                f"color: {value_color}; background: transparent; border: none;"
            )
        self._value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self._value, 1)

    def set_value(self, text, color=None):
        self._value.setText(str(text))
        if color:
            self._value.setStyleSheet(
                f"color: {color}; background: transparent; border: none;"
            )
        else:
            self._value.setStyleSheet(
                f"color: {get_color('text_primary')}; background: transparent; border: none;"
            )

    def set_value_color(self, color):
        if color:
            self._value.setStyleSheet(
                f"color: {color}; background: transparent; border: none;"
            )
