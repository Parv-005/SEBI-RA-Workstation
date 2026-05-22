from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QWidget, QScrollArea, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from gui.theme import get_color
from utils.logger import setup_logger

logger = setup_logger("GroupSelectDialog")


class GroupSelectDialog(QDialog):
    def __init__(self, groups: dict[str, str], parent=None):
        super().__init__(parent)
        self._groups = groups
        self._checkboxes: dict[str, QCheckBox] = {}
        self._result: dict[str, str] | None = None

        self.setWindowTitle("Select Telegram Groups")
        self.setMinimumWidth(440)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("Send trade to which groups?")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {get_color('text_primary')}; background: transparent;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        check_layout = QVBoxLayout(container)
        check_layout.setContentsMargins(0, 4, 0, 4)
        check_layout.setSpacing(8)

        for name in self._groups:
            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.setFont(QFont("Segoe UI", 12))
            cb.setStyleSheet(f"""
            QCheckBox {{
                color: {get_color('text_primary')};
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {get_color('input_border')};
                border-radius: 4px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {get_color('accent')};
                border-color: {get_color('accent')};
            }}
            """)
            self._checkboxes[name] = cb
            check_layout.addWidget(cb)

        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        select_all_btn = QPushButton("Select All")
        select_all_btn.setObjectName("ghost")
        select_all_btn.setCursor(Qt.PointingHandCursor)
        select_all_btn.clicked.connect(self._select_all)
        btn_row.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.setObjectName("ghost")
        deselect_all_btn.setCursor(Qt.PointingHandCursor)
        deselect_all_btn.clicked.connect(self._deselect_all)
        btn_row.addWidget(deselect_all_btn)

        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghost")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        send_btn = QPushButton("Send Trade")
        send_btn.setObjectName("success")
        send_btn.setMinimumWidth(140)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.clicked.connect(self._on_send)
        btn_row.addWidget(send_btn)

        layout.addLayout(btn_row)

    def _select_all(self):
        for cb in self._checkboxes.values():
            cb.setChecked(True)

    def _deselect_all(self):
        for cb in self._checkboxes.values():
            cb.setChecked(False)

    def _on_send(self):
        selected = {}
        for name, cb in self._checkboxes.items():
            if cb.isChecked():
                selected[name] = self._groups[name]
        if not selected:
            logger.debug("No groups selected in GroupSelectDialog")
            QMessageBox.warning(self, "No Groups Selected", "Please select at least one Telegram group.")
            return
        logger.debug(f"Groups selected: {list(selected.keys())}")
        self._result = selected
        self.accept()

    def get_selected_groups(self) -> dict[str, str] | None:
        return self._result
