from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from gui.theme import get_color


class SectionCard(QFrame):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setObjectName("card")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 16, 20, 16)
        self._layout.setSpacing(8)

        if title:
            header = QLabel(title)
            header.setObjectName("card_header")
            header.setFont(QFont("Segoe UI", 12, QFont.Bold))
            header.setStyleSheet(
                f"color: {get_color('text_primary')}; background: transparent; "
                f"border: none; font-size: 14px; padding-bottom: 4px;"
            )
            self._layout.addWidget(header)

            separator = QFrame()
            separator.setObjectName("separator")
            separator.setFixedHeight(1)
            separator.setStyleSheet(
                f"background-color: {get_color('border')}; border: none;"
            )
            self._layout.addWidget(separator)

            self._separator = separator

        self._content = QWidget()
        self._content.setStyleSheet("background-color: transparent;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 8, 0, 0)
        self._content_layout.setSpacing(2)
        self._layout.addWidget(self._content, 1)

    def content_layout(self):
        return self._content_layout

    def add_widget(self, widget):
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        self._content_layout.addLayout(layout)
