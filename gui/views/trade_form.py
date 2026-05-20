import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTextEdit, QScrollArea, QFrame,
    QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QDoubleValidator, QIntValidator

from gui.signals import get_signals
from gui.theme import get_color
from gui.widgets.toast import ToastWidget
from gui.widgets.section_card import SectionCard
from services.trade_service import calculate_risk_reward, to_db_action, to_display_action
from utils.constants import SEGMENTS, ACTION_DISPLAY, ACTION_COLORS, TRADE_TYPES


class NewTradeView(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._signals = get_signals()
        self._dynamic_inputs = {}
        self._is_submitting = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        form_layout = QVBoxLayout(scroll_content)
        form_layout.setContentsMargins(32, 24, 32, 24)
        form_layout.setSpacing(20)

        title = QLabel("New Trade Entry")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet(f"color: {get_color('text_primary')}; background: transparent;")
        form_layout.addWidget(title)

        self._identity_card = SectionCard("Trade Identity")
        self._build_identity_section()
        form_layout.addWidget(self._identity_card)

        self._prices_card = SectionCard("Price Levels")
        self._build_prices_section()
        form_layout.addWidget(self._prices_card)

        self._risk_card = SectionCard("Risk & Reward")
        self._build_risk_section()
        form_layout.addWidget(self._risk_card)

        self._notes_card = SectionCard("Notes")
        self._build_notes_section()
        form_layout.addWidget(self._notes_card)

        submit_layout = QHBoxLayout()
        submit_layout.setContentsMargins(0, 8, 0, 0)
        submit_layout.addStretch()

        self._submit_btn = QPushButton("Submit Trade & Broadcast")
        self._submit_btn.setObjectName("success")
        self._submit_btn.setMinimumHeight(48)
        self._submit_btn.setMinimumWidth(280)
        self._submit_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self._submit_btn.setCursor(Qt.PointingHandCursor)
        self._submit_btn.clicked.connect(self._on_submit)
        submit_layout.addWidget(self._submit_btn)

        form_layout.addLayout(submit_layout)
        form_layout.addStretch()

        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll, 1)

    def _add_field_row(self, card, label_text, widget, label_width=130):
        row = QHBoxLayout()
        row.setSpacing(12)
        label = QLabel(label_text)
        label.setFixedWidth(label_width)
        label.setStyleSheet(
            f"color: {get_color('text_secondary')}; font-size: 13px; "
            f"font-weight: 500; background: transparent;"
        )
        row.addWidget(label)
        row.addWidget(widget, 1)
        card.add_layout(row)

    def _build_identity_section(self):
        self._segment_combo = QComboBox()
        self._segment_combo.addItems(SEGMENTS)
        self._add_field_row(self._identity_card, "Segment:", self._segment_combo)

        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        action_label = QLabel("Action:")
        action_label.setFixedWidth(130)
        action_label.setStyleSheet(
            f"color: {get_color('text_secondary')}; font-size: 13px; "
            f"font-weight: 500; background: transparent;"
        )
        action_row.addWidget(action_label)

        self._action_combo = QComboBox()
        self._action_combo.addItems(ACTION_DISPLAY)
        self._action_combo.currentTextChanged.connect(self._on_action_change)
        action_row.addWidget(self._action_combo, 1)

        stock_label = QLabel("Stock / Symbol:")
        stock_label.setStyleSheet(
            f"color: {get_color('text_secondary')}; font-size: 13px; "
            f"font-weight: 500; background: transparent;"
        )
        stock_label.setFixedWidth(100)
        action_row.addWidget(stock_label)

        self._stock_entry = QLineEdit()
        self._stock_entry.setPlaceholderText("e.g. RELIANCE, BANKNIFTY")
        action_row.addWidget(self._stock_entry, 1)

        self._fetch_cmp_btn = QPushButton("Fetch CMP")
        self._fetch_cmp_btn.setObjectName("ghost")
        self._fetch_cmp_btn.setCursor(Qt.PointingHandCursor)
        self._fetch_cmp_btn.clicked.connect(self._on_fetch_cmp)
        action_row.addWidget(self._fetch_cmp_btn)

        self._identity_card.add_layout(action_row)

        self._on_action_change(ACTION_DISPLAY[0])

        type_row = QHBoxLayout()
        type_row.setSpacing(12)

        type_label = QLabel("Trade Type:")
        type_label.setFixedWidth(130)
        type_label.setStyleSheet(
            f"color: {get_color('text_secondary')}; font-size: 13px; "
            f"font-weight: 500; background: transparent;"
        )
        type_row.addWidget(type_label)

        self._trade_type_combo = QComboBox()
        self._trade_type_combo.addItems(TRADE_TYPES)
        type_row.addWidget(self._trade_type_combo, 1)

        time_label = QLabel("Approx Time:")
        time_label.setFixedWidth(100)
        time_label.setStyleSheet(
            f"color: {get_color('text_secondary')}; font-size: 13px; "
            f"font-weight: 500; background: transparent;"
        )
        type_row.addWidget(time_label)

        self._approx_time_entry = QLineEdit()
        self._approx_time_entry.setPlaceholderText("e.g. 2-3 days, 1 week")
        type_row.addWidget(self._approx_time_entry, 1)

        self._identity_card.add_layout(type_row)

    def _on_action_change(self, action):
        action_color = ACTION_COLORS.get(action, "#28a745")
        self._action_combo.setStyleSheet(f"""
        QComboBox {{
            color: {action_color};
            font-weight: 700;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 6px 12px;
        }}
        """)

    def _build_prices_section(self):
        grid_card = QWidget()
        grid_card.setStyleSheet("background-color: transparent;")
        grid_layout = QHBoxLayout(grid_card)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(24)

        left = QWidget()
        left.setStyleSheet("background-color: transparent;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        right = QWidget()
        right.setStyleSheet("background-color: transparent;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self._entry_price = QLineEdit()
        self._entry_price.setPlaceholderText("0.00")
        self._entry_price.textChanged.connect(self._on_rr_input_change)
        self._add_price_row(left_layout, "Entry Price:", self._entry_price)

        self._target_price = QLineEdit()
        self._target_price.setPlaceholderText("0.00")
        self._target_price.textChanged.connect(self._on_rr_input_change)
        self._add_price_row(right_layout, "Target Price:", self._target_price)

        self._zone_start = QLineEdit()
        self._zone_start.setPlaceholderText("Lower bound")
        self._zone_start.editingFinished.connect(self._apply_zone_offsets)
        self._add_price_row(left_layout, "Zone Start:", self._zone_start)

        self._zone_end = QLineEdit()
        self._zone_end.setPlaceholderText("Upper bound")
        self._zone_end.editingFinished.connect(self._apply_zone_offsets)
        self._add_price_row(right_layout, "Zone End:", self._zone_end)

        self._stop_loss = QLineEdit()
        self._stop_loss.setPlaceholderText("0.00")
        self._stop_loss.textChanged.connect(self._on_rr_input_change)
        self._add_price_row(left_layout, "Stop Loss:", self._stop_loss)

        grid_layout.addWidget(left, 1)
        grid_layout.addWidget(right, 1)
        self._prices_card.add_widget(grid_card)

    def _add_price_row(self, parent, label_text, edit):
        row = QHBoxLayout()
        row.setSpacing(8)
        label = QLabel(label_text)
        label.setFixedWidth(100)
        label.setStyleSheet(
            f"color: {get_color('text_secondary')}; font-size: 13px; "
            f"font-weight: 500; background: transparent;"
        )
        row.addWidget(label)
        row.addWidget(edit, 1)

        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        container.setLayout(row)
        parent.addWidget(container)

    def _build_risk_section(self):
        grid_card = QWidget()
        grid_card.setStyleSheet("background-color: transparent;")
        grid_layout = QHBoxLayout(grid_card)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(24)

        left = QWidget()
        left.setStyleSheet("background-color: transparent;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        right = QWidget()
        right.setStyleSheet("background-color: transparent;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self._reward_display = self._make_readonly_field()
        self._add_price_row(left_layout, "Reward:", self._reward_display)

        self._risk_display = self._make_readonly_field()
        self._add_price_row(right_layout, "Risk:", self._risk_display)

        self._reward_pct_display = self._make_readonly_field()
        self._add_price_row(left_layout, "Reward %:", self._reward_pct_display)

        self._risk_pct_display = self._make_readonly_field()
        self._add_price_row(right_layout, "Risk %:", self._risk_pct_display)

        self._rr_display = self._make_readonly_field()
        row = QHBoxLayout()
        row.setSpacing(8)
        rr_label = QLabel("Risk : Reward:")
        rr_label.setFixedWidth(100)
        rr_label.setStyleSheet(
            f"color: {get_color('text_secondary')}; font-size: 13px; "
            f"font-weight: 500; background: transparent;"
        )
        row.addWidget(rr_label)
        row.addWidget(self._rr_display, 1)
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        container.setLayout(row)

        left_layout.addWidget(container)

        grid_layout.addWidget(left, 1)
        grid_layout.addWidget(right, 1)
        self._risk_card.add_widget(grid_card)

    def _make_readonly_field(self):
        edit = QLineEdit()
        edit.setReadOnly(True)
        edit.setStyleSheet(f"""
        QLineEdit {{
            background-color: {get_color('disabled_bg')};
            color: {get_color('text_secondary')};
            font-weight: 600;
        }}
        """)
        return edit

    def _build_notes_section(self):
        self._remarks_entry = QTextEdit()
        self._remarks_entry.setPlaceholderText(
            "Enter trade instructions, remarks, or any additional notes..."
        )
        self._remarks_entry.setMinimumHeight(100)
        self._notes_card.add_widget(self._remarks_entry)

    def _connect_signals(self):
        self._signals.trade_created.connect(self._on_trade_created)
        self._signals.trade_create_error.connect(self._on_trade_create_error)
        self._signals.broadcast_complete.connect(self._on_broadcast_complete)
        self._signals.cmp_fetched.connect(self._on_cmp_fetched)
        self._signals.cmp_fetch_error.connect(self._on_cmp_fetch_error)

    def on_show(self):
        self._do_rr_calc()

    def _on_rr_input_change(self):
        QTimer.singleShot(100, self._do_rr_calc)

    def _do_rr_calc(self):
        try:
            action = self._action_combo.currentText()
            entry = float(self._entry_price.text()) if self._entry_price.text() else 0
            target = float(self._target_price.text()) if self._target_price.text() else 0
            sl = float(self._stop_loss.text()) if self._stop_loss.text() else 0
        except (ValueError, TypeError):
            return

        if entry <= 0 or target <= 0 or sl <= 0:
            return

        result = self._controller.calculate_rr(action, entry, target, sl)
        if result is None:
            return

        green = get_color("success")
        red = get_color("danger")

        self._reward_display.setText(f"\u20b9{result.reward:,.2f}")
        self._reward_display.setStyleSheet(f"""
        QLineEdit {{
            background-color: {get_color('disabled_bg')};
            color: {green};
            font-weight: 600;
        }}
        """)

        self._risk_display.setText(f"\u20b9{result.risk:,.2f}")
        self._risk_display.setStyleSheet(f"""
        QLineEdit {{
            background-color: {get_color('disabled_bg')};
            color: {red};
            font-weight: 600;
        }}
        """)

        self._reward_pct_display.setText(f"{result.reward_pct:.2f}%")
        self._reward_pct_display.setStyleSheet(f"""
        QLineEdit {{
            background-color: {get_color('disabled_bg')};
            color: {green};
            font-weight: 600;
        }}
        """)

        self._risk_pct_display.setText(f"{result.risk_pct:.2f}%")
        self._risk_pct_display.setStyleSheet(f"""
        QLineEdit {{
            background-color: {get_color('disabled_bg')};
            color: {red};
            font-weight: 600;
        }}
        """)

        self._rr_display.setText(result.risk_reward)
        self._rr_display.setStyleSheet(f"""
        QLineEdit {{
            background-color: {get_color('disabled_bg')};
            color: {get_color('text_primary')};
            font-weight: 600;
        }}
        """)

    def _apply_zone_offsets(self):
        sender = self.sender()
        if not sender:
            return

        try:
            entry = float(self._entry_price.text()) if self._entry_price.text() else 0
        except (ValueError, TypeError):
            entry = 0

        text = sender.text().strip()
        if not text or entry <= 0:
            return

        match_abs = re.match(r'^[+\-]\d+(\.\d+)?$', text)
        match_pct = re.match(r'^[+\-]\d+(\.\d+)?%$', text)
        match_range = re.match(r'^[+\-]\d+(\.\d+)?$', text)

        if match_pct:
            pct = float(text[:-1])
            offset = entry * pct / 100
            value = entry + offset if '+' in text else entry - abs(offset)
            sender.setText(f"{value:.2f}")
        elif match_abs:
            delta = float(text)
            value = entry + delta
            sender.setText(f"{value:.2f}")

        self._sync_zone_fields()

    def _sync_zone_fields(self):
        try:
            zs = float(self._zone_start.text()) if self._zone_start.text() else None
            ze = float(self._zone_end.text()) if self._zone_end.text() else None
        except (ValueError, TypeError):
            return

        if zs is not None and ze is not None and zs > ze:
            self._zone_start.setText(f"{ze:.2f}")
            self._zone_end.setText(f"{zs:.2f}")

    def _on_fetch_cmp(self):
        stock = self._stock_entry.text().strip()
        if not stock:
            QMessageBox.warning(self, "Warning", "Enter a stock symbol first.")
            return

        self._fetch_cmp_btn.setEnabled(False)
        self._fetch_cmp_btn.setText("Fetching...")
        self._controller.fetch_cmp(stock, self._segment_combo.currentText())

    def _on_cmp_fetched(self, ltp):
        self._entry_price.setText(f"{ltp:.2f}")
        self._fetch_cmp_btn.setEnabled(True)
        self._fetch_cmp_btn.setText("Fetch CMP")
        self._signals.notification.emit(
            f"CMP: \u20b9{ltp:,.2f}", ToastWidget.SUCCESS, 3000
        )

    def _on_cmp_fetch_error(self, err):
        self._fetch_cmp_btn.setEnabled(True)
        self._fetch_cmp_btn.setText("Fetch CMP")
        QMessageBox.warning(self, "CMP Fetch Error", err)

    def _on_submit(self):
        if self._is_submitting:
            return

        trade_data = self._validate_and_build()
        if not trade_data:
            return

        self._is_submitting = True
        self._submit_btn.setEnabled(False)
        self._submit_btn.setText("Submitting...")

        self._controller.create_trade_and_broadcast(trade_data)

    def _validate_and_build(self):
        stock = self._stock_entry.text().strip()
        if not stock:
            QMessageBox.warning(self, "Validation Error",
                                "Stock / Symbol is required.")
            self._stock_entry.setFocus()
            return None

        try:
            entry = float(self._entry_price.text()) if self._entry_price.text() else 0
            target = float(self._target_price.text()) if self._target_price.text() else 0
            sl = float(self._stop_loss.text()) if self._stop_loss.text() else 0
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Validation Error",
                                "Entry Price, Target, and Stop Loss must be valid numbers.")
            return None

        if entry <= 0:
            QMessageBox.warning(self, "Validation Error",
                                "Entry Price must be greater than 0.")
            self._entry_price.setFocus()
            return None

        if target <= 0:
            QMessageBox.warning(self, "Validation Error",
                                "Target must be greater than 0.")
            self._target_price.setFocus()
            return None

        if sl <= 0:
            QMessageBox.warning(self, "Validation Error",
                                "Stop Loss must be greater than 0.")
            self._stop_loss.setFocus()
            return None

        action_db = to_db_action(self._action_combo.currentText())
        segment = self._segment_combo.currentText()

        trade_data = {
            "stock_name": stock,
            "segment": segment,
            "action": action_db,
            "trade_type": self._trade_type_combo.currentText(),
            "approx_time": self._approx_time_entry.text().strip(),
            "entry_price": entry,
            "target": target,
            "stop_loss": sl,
            "zone_start": self._zone_start.text().strip(),
            "zone_end": self._zone_end.text().strip(),
            "remarks": self._remarks_entry.toPlainText().strip(),
            "status": "ACTIVE",
        }

        return trade_data

    def _on_trade_created(self, trade_code):
        pass

    def _on_trade_create_error(self, err):
        self._is_submitting = False
        self._submit_btn.setEnabled(True)
        self._submit_btn.setText("Submit Trade & Broadcast")
        QMessageBox.critical(self, "Error", f"Failed to save trade:\n{err}")

    def _on_broadcast_complete(self, result):
        self._is_submitting = False
        self._submit_btn.setEnabled(True)
        self._submit_btn.setText("Submit Trade & Broadcast")

        parts = []
        if result.image_success:
            parts.append("Image generated")
        if result.sheets_success is True:
            parts.append("Google Sheets updated")
        elif result.sheets_success == "not_configured":
            parts.append("Sheets not configured")
        elif not result.sheets_success:
            parts.append("Sheets failed")
        if result.telegram_success is True:
            parts.append("Telegram sent")
        elif result.telegram_success == "not_configured":
            parts.append("Telegram not configured")
        elif result.telegram_success == "not_authorized":
            parts.append("Telegram not authorized")
        elif not result.telegram_success:
            parts.append("Telegram failed")

        summary = " | ".join(parts)

        self._clear_form()
        if result.errors:
            self._signals.notification.emit(
                f"Trade submitted with issues: {summary}",
                ToastWidget.WARNING,
                5000,
            )
        else:
            self._signals.notification.emit(
                f"Trade submitted successfully! {summary}",
                ToastWidget.SUCCESS,
                4000,
            )
        self._signals.navigate.emit("active_trades", None)

    def _clear_form(self):
        self._stock_entry.clear()
        self._entry_price.clear()
        self._target_price.clear()
        self._stop_loss.clear()
        self._zone_start.clear()
        self._zone_end.clear()
        self._approx_time_entry.clear()
        self._remarks_entry.clear()
        self._segment_combo.setCurrentIndex(0)
        self._action_combo.setCurrentIndex(0)
        self._trade_type_combo.setCurrentIndex(0)
        self._reward_display.clear()
        self._risk_display.clear()
        self._reward_pct_display.clear()
        self._risk_pct_display.clear()
        self._rr_display.clear()
