import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QWidget, QLineEdit, QMessageBox,
    QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from gui.signals import get_signals
from gui.theme import get_color
from gui.widgets.toast import ToastWidget
from utils.constants import UPDATE_TYPES_DICT, UPDATE_TYPES, ACTION_COLORS, TRADE_TYPES
from services.trade_service import (
    compute_update_fields, to_display_action,
    BLOCK_ON_MISSING_EXIT_PRICE
)
from database.db_manager import get_trade, get_trade_updates, insert_trade_update
from database.updates_db import get_formatted_updates_text
from database.trades_db import update_trade


class UpdateDialog(QDialog):
    def __init__(self, trade, controller, parent=None):
        super().__init__(parent)
        self.trade = trade
        self._controller = controller
        self._signals = get_signals()
        self._dynamic_inputs = {}
        self._extra_exit_entry = None
        self._close_trade_var = False

        self.setWindowTitle(f"Update Trade - #{trade.get('trade_code', '?')}")
        self.setMinimumWidth(580)
        self.setModal(True)

        self._setup_ui()

        if UPDATE_TYPES:
            self._on_update_type_change(UPDATE_TYPES[0])
            self._update_type_menu.setCurrentText(UPDATE_TYPES[0])

        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        trade = self.trade
        action_display = to_display_action(trade.get("action") or "LONG")
        entry = trade.get("entry_price")
        target = trade.get("target")
        sl = trade.get("stop_loss")
        entry_str = f"\u20b9{entry:,.2f}" if isinstance(entry, (int, float)) else "\u2014"
        target_str = f"\u20b9{target:,.2f}" if isinstance(target, (int, float)) else "\u2014"
        sl_str = f"\u20b9{sl:,.2f}" if isinstance(sl, (int, float)) else "\u2014"

        info = QLabel(
            f"{trade.get('stock_name') or '?'} | {trade.get('segment') or '?'} | "
            f"{action_display} | Entry: {entry_str} | Target: {target_str} | SL: {sl_str}"
        )
        info.setWordWrap(True)
        info.setFont(QFont("Segoe UI", 12))
        info.setStyleSheet(
            f"color: {get_color('text_primary')}; font-weight: 600; "
            f"background: transparent; padding: 8px 0;"
        )
        layout.addWidget(info)

        type_row = QHBoxLayout()
        type_row.setSpacing(8)
        type_label = QLabel("Update Type:")
        type_label.setStyleSheet(
            f"color: {get_color('text_secondary')}; background: transparent;"
        )
        type_row.addWidget(type_label)
        self._update_type_menu = QComboBox()
        self._update_type_menu.addItems(UPDATE_TYPES)
        self._update_type_menu.currentTextChanged.connect(self._on_update_type_change)
        type_row.addWidget(self._update_type_menu, 1)
        layout.addLayout(type_row)

        self._close_trade_cb = QCheckBox("Closes Trade")
        self._close_trade_cb.setEnabled(False)
        self._close_trade_cb.setStyleSheet(f"""
        QCheckBox {{
            color: {get_color('danger')};
            font-weight: 600;
        }}
        QCheckBox::indicator:checked {{
            background-color: {get_color('danger')};
            border-color: {get_color('danger')};
        }}
        """)
        layout.addWidget(self._close_trade_cb)

        self._dynamic_fields_widget = QWidget()
        self._dynamic_fields_widget.setObjectName("dynamic_fields")
        self._dynamic_fields_widget.setStyleSheet("#dynamic_fields { background-color: transparent; }")
        self._dynamic_fields_layout = QVBoxLayout(self._dynamic_fields_widget)
        self._dynamic_fields_layout.setContentsMargins(0, 8, 0, 8)
        self._dynamic_fields_layout.setSpacing(8)
        layout.addWidget(self._dynamic_fields_widget)

        msg_label = QLabel("Message:")
        msg_label.setStyleSheet(
            f"color: {get_color('text_secondary')}; background: transparent;"
        )
        layout.addWidget(msg_label)

        self._remarks_entry = QTextEdit()
        self._remarks_entry.setMinimumHeight(80)
        self._remarks_entry.setPlaceholderText("Update message will appear here...")
        layout.addWidget(self._remarks_entry)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghost")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        btn_row.addStretch()

        self._submit_btn = QPushButton("Broadcast Update")
        self._submit_btn.setObjectName("success")
        self._submit_btn.setMinimumWidth(180)
        self._submit_btn.setCursor(Qt.PointingHandCursor)
        self._submit_btn.clicked.connect(self._on_submit)
        btn_row.addWidget(self._submit_btn)

        layout.addLayout(btn_row)

    def _connect_signals(self):
        self._signals.trade_updated.connect(self._on_trade_updated)
        self._signals.trade_update_error.connect(self._on_update_error)
        self._signals.update_broadcast_complete.connect(self._on_broadcast_complete)

    def _on_update_type_change(self, update_type):
        for i in reversed(range(self._dynamic_fields_layout.count())):
            item = self._dynamic_fields_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self._dynamic_inputs = {}
        self._extra_exit_entry = None

        utype = UPDATE_TYPES_DICT.get(update_type, {})
        is_close = utype.get("close_trade", False)
        message_template = utype.get("message", "")
        fields_to_set = utype.get("set", {})

        self._close_trade_var = is_close
        self._close_trade_cb.setChecked(is_close)

        placeholders = re.findall(r"<([^>]+)>", message_template)
        unique_placeholders = list(dict.fromkeys(placeholders))

        for ph in unique_placeholders:
            row = QHBoxLayout()
            row.setSpacing(8)

            label = QLabel(f"{ph}:")
            label.setFixedWidth(120)
            label.setStyleSheet(
                f"color: {get_color('text_secondary')}; background: transparent;"
            )
            row.addWidget(label)

            entry = QLineEdit()
            entry.setPlaceholderText(f"Enter {ph.lower()}...")
            entry.textChanged.connect(self._make_message_updater(message_template))
            row.addWidget(entry, 1)

            self._dynamic_inputs[ph] = entry

            container = QWidget()
            container.setObjectName("dyn_field_row")
            container.setStyleSheet("#dyn_field_row { background-color: transparent; }")
            container.setLayout(row)
            self._dynamic_fields_layout.addWidget(container)

        if is_close and "Exit Price" not in self._dynamic_inputs:
            row = QHBoxLayout()
            row.setSpacing(8)

            label = QLabel("Exit Price:")
            label.setFixedWidth(120)
            label.setStyleSheet(
                f"color: {get_color('warning')}; font-weight: 600; "
                f"background: transparent;"
            )
            row.addWidget(label)

            self._extra_exit_entry = QLineEdit()
            self._extra_exit_entry.setPlaceholderText("Enter exit price...")
            self._extra_exit_entry.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {get_color('warning')};
            }}
            """)
            row.addWidget(self._extra_exit_entry, 1)

            self._dynamic_inputs["Exit Price"] = self._extra_exit_entry

            container = QWidget()
            container.setObjectName("dyn_field_row_exit")
            container.setStyleSheet("#dyn_field_row_exit { background-color: transparent; }")
            container.setLayout(row)
            self._dynamic_fields_layout.addWidget(container)

        self._remarks_entry.setText(message_template)
        self._update_message_from_fields()

    def _make_message_updater(self, template):
        def updater(text):
            QTimer.singleShot(50, lambda: self._update_message_from_fields())
        return updater

    def _update_message_from_fields(self):
        template = self._remarks_entry.toPlainText()
        for ph, entry in self._dynamic_inputs.items():
            value = entry.text().strip()
            if value:
                template = template.replace(f"<{ph}>", value)
        self._remarks_entry.blockSignals(True)
        self._remarks_entry.setText(template)
        self._remarks_entry.blockSignals(False)

    def _on_submit(self):
        update_type = self._update_type_menu.currentText()
        remarks = self._remarks_entry.toPlainText().strip()

        dynamic_values = {}
        for ph, entry in self._dynamic_inputs.items():
            val = entry.text().strip()
            if val:
                dynamic_values[ph] = val

        try:
            trade_updates, old_value, new_value, update_data_dict = (
                compute_update_fields(
                    self.trade, update_type, dynamic_values, remarks
                )
            )
        except ValueError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
            return

        if self._close_trade_var and "Exit Price" not in dynamic_values and self._extra_exit_entry:
            exit_val = self._extra_exit_entry.text().strip()
            if not exit_val:
                if BLOCK_ON_MISSING_EXIT_PRICE:
                    QMessageBox.warning(
                        self, "Validation Error",
                        "Exit Price is required for this update type."
                    )
                    return
                else:
                    confirm = QMessageBox.question(
                        self, "Exit Price Missing",
                        "Exit Price is empty. Continue anyway?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if confirm != QMessageBox.Yes:
                        return

        self._submit_btn.setEnabled(False)
        self._submit_btn.setText("Processing...")

        self._controller.update_trade_and_broadcast(
            self.trade, update_type, dynamic_values, remarks
        )

    def _on_trade_updated(self, trade):
        self.trade = trade

    def _on_update_error(self, err):
        self._submit_btn.setEnabled(True)
        self._submit_btn.setText("Broadcast Update")
        QMessageBox.critical(self, "Error", str(err))

    def _on_broadcast_complete(self, result):
        self._submit_btn.setEnabled(True)
        self._submit_btn.setText("Broadcast Update")

        parts = []
        if result.image_success:
            parts.append("Image generated")
        if result.sheets_success is True:
            parts.append("Google Sheets updated")
        elif result.sheets_success == "not_configured":
            parts.append("Sheets not configured")
        if result.telegram_success is True:
            parts.append("Telegram sent")
        elif result.telegram_success == "not_configured":
            parts.append("Telegram not configured")
        elif result.telegram_success == "not_authorized":
            parts.append("Telegram not authorized")

        summary = " | ".join(parts)

        if result.errors:
            self._signals.notification.emit(
                f"Update submitted with issues: {summary}",
                ToastWidget.WARNING,
                5000,
            )
        else:
            self._signals.notification.emit(
                f"Trade updated successfully! {summary}",
                ToastWidget.SUCCESS,
                4000,
            )

        self.accept()
