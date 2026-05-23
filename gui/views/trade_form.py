import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTextEdit, QScrollArea, QFrame,
    QGridLayout, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from gui.signals import get_signals
from gui.theme import get_color
from gui.widgets.toast import ToastWidget
from gui.widgets.section_card import SectionCard
from gui.widgets.group_select_dialog import GroupSelectDialog
from services.trade_service import calculate_risk_reward, to_db_action, to_display_action
from services.results import build_broadcast_summary, build_broadcast_detail
from utils.constants import SEGMENTS, ACTION_DISPLAY, ACTION_COLORS, TRADE_TYPES, COLOR_GOLD, COLOR_GOLD_HOVER
from utils.logger import setup_logger
from core.config import Config

logger = setup_logger("TradeForm")


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
        scroll.setObjectName("form_scroll")
        scroll.setStyleSheet("#form_scroll { background-color: transparent; border: none; }")

        scroll_content = QWidget()
        scroll_content.setObjectName("form_content")
        scroll_content.setStyleSheet("#form_content { background-color: transparent; }")
        form_layout = QVBoxLayout(scroll_content)
        form_layout.setContentsMargins(40, 32, 40, 32)
        form_layout.setSpacing(16)

        title = QLabel("New Trade Entry")
        title.setFont(QFont("Segoe UI", 26, QFont.Bold))
        title.setStyleSheet(
            f"color: {get_color('accent')}; background: transparent; border: none;"
        )
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

        form_layout.addStretch()

        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll, 1)

        # Fixed footer — always visible, outside scroll area
        footer = QFrame()
        footer.setObjectName("form_footer")
        footer.setStyleSheet(
            f"#form_footer {{ background-color: {get_color('surface')}; "
            f"border-top: 1px solid {get_color('border')}; }}"
        )
        footer.setMinimumHeight(72)
        footer.setMaximumHeight(72)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(40, 0, 40, 0)
        footer_layout.setSpacing(0)
        footer_layout.addStretch()

        self._submit_btn = QPushButton("Submit Trade & Broadcast")
        self._submit_btn.setObjectName("gold")
        self._submit_btn.setMinimumHeight(48)
        self._submit_btn.setMinimumWidth(280)
        self._submit_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self._submit_btn.setCursor(Qt.PointingHandCursor)
        self._submit_btn.clicked.connect(self._on_submit)
        footer_layout.addWidget(self._submit_btn)

        outer_layout.addWidget(footer)

    def _make_label(self, text, bold=True, size=11):
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", size, QFont.Bold if bold else QFont.Normal))
        lbl.setStyleSheet(
            f"color: {get_color('text_muted')}; background: transparent; border: none; "
            f"letter-spacing: 0.3px;"
        )
        return lbl

    def _make_input(self, placeholder=""):
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        return edit

    def _make_combo(self, items):
        combo = QComboBox()
        combo.addItems(items)
        return combo

    def _build_identity_section(self):
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        row = 0

        seg_label = self._make_label("Segment")
        grid.addWidget(seg_label, row, 0)
        self._segment_combo = self._make_combo(SEGMENTS)
        grid.addWidget(self._segment_combo, row, 1)

        action_label = self._make_label("Action")
        grid.addWidget(action_label, row, 2)
        self._action_combo = self._make_combo(ACTION_DISPLAY)
        self._action_combo.currentTextChanged.connect(self._on_action_change)
        grid.addWidget(self._action_combo, row, 3)

        row += 1

        stock_label = self._make_label("Stock / Symbol")
        grid.addWidget(stock_label, row, 0)
        self._stock_entry = self._make_input("e.g. RELIANCE, BANKNIFTY")
        grid.addWidget(self._stock_entry, row, 1, 1, 2)

        self._fetch_cmp_btn = QPushButton("Fetch CMP")
        self._fetch_cmp_btn.setObjectName("gold")
        self._fetch_cmp_btn.setMinimumWidth(110)
        self._fetch_cmp_btn.setCursor(Qt.PointingHandCursor)
        self._fetch_cmp_btn.clicked.connect(self._on_fetch_cmp)
        grid.addWidget(self._fetch_cmp_btn, row, 3)

        row += 1

        type_label = self._make_label("Trade Type")
        grid.addWidget(type_label, row, 0)
        self._trade_type_combo = self._make_combo(TRADE_TYPES)
        grid.addWidget(self._trade_type_combo, row, 1)

        time_label = self._make_label("Approx Time")
        grid.addWidget(time_label, row, 2)
        self._approx_time_entry = self._make_input("e.g. 2-3 days, 1 week")
        grid.addWidget(self._approx_time_entry, row, 3)

        self._on_action_change(ACTION_DISPLAY[0])
        self._identity_card.add_layout(grid)

    def _on_action_change(self, action):
        action_color = ACTION_COLORS.get(action, "#4CAF50")
        self._action_combo.setStyleSheet(f"""
        QComboBox {{
            color: {action_color};
            font-weight: 700;
            border: 1px solid {get_color('input_border')};
            border-radius: 6px;
            padding: 8px 12px;
            min-height: 20px;
        }}
        QComboBox:focus {{
            border: 2px solid {get_color('input_border_focus')};
            padding: 7px 11px;
        }}
        QComboBox QAbstractItemView {{
            padding: 6px 12px;
        }}
        """)

    def _build_prices_section(self):
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        row = 0

        entry_label = self._make_label("Entry Price")
        grid.addWidget(entry_label, row, 0)
        self._entry_price = self._make_input("0.00")
        self._entry_price.textChanged.connect(self._on_rr_input_change)
        grid.addWidget(self._entry_price, row, 1)

        target_label = self._make_label("Target Price")
        grid.addWidget(target_label, row, 2)
        self._target_price = self._make_input("0.00")
        self._target_price.textChanged.connect(self._on_rr_input_change)
        grid.addWidget(self._target_price, row, 3)

        row += 1

        zone_start_label = self._make_label("Zone Start")
        grid.addWidget(zone_start_label, row, 0)
        self._zone_start = self._make_input("Lower bound or +50/-5%")
        self._zone_start.editingFinished.connect(self._apply_zone_offsets)
        grid.addWidget(self._zone_start, row, 1)

        zone_end_label = self._make_label("Zone End")
        grid.addWidget(zone_end_label, row, 2)
        self._zone_end = self._make_input("Upper bound or +100")
        self._zone_end.editingFinished.connect(self._apply_zone_offsets)
        grid.addWidget(self._zone_end, row, 3)

        row += 1

        sl_label = self._make_label("Stop Loss")
        grid.addWidget(sl_label, row, 0)
        self._stop_loss = self._make_input("0.00")
        self._stop_loss.textChanged.connect(self._on_rr_input_change)
        grid.addWidget(self._stop_loss, row, 1)

        self._prices_card.add_layout(grid)

    def _build_risk_section(self):
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        row = 0

        reward_label = self._make_label("Reward")
        grid.addWidget(reward_label, row, 0)
        self._reward_display = self._make_readonly_field()
        grid.addWidget(self._reward_display, row, 1)

        risk_label = self._make_label("Risk")
        grid.addWidget(risk_label, row, 2)
        self._risk_display = self._make_readonly_field()
        grid.addWidget(self._risk_display, row, 3)

        row += 1

        reward_pct_label = self._make_label("Reward %")
        grid.addWidget(reward_pct_label, row, 0)
        self._reward_pct_display = self._make_readonly_field()
        grid.addWidget(self._reward_pct_display, row, 1)

        risk_pct_label = self._make_label("Risk %")
        grid.addWidget(risk_pct_label, row, 2)
        self._risk_pct_display = self._make_readonly_field()
        grid.addWidget(self._risk_pct_display, row, 3)

        row += 1

        rr_label = self._make_label("Risk : Reward")
        grid.addWidget(rr_label, row, 0)
        self._rr_display = self._make_readonly_field()
        grid.addWidget(self._rr_display, row, 1, 1, 3)

        self._risk_card.add_layout(grid)

    def _make_readonly_field(self):
        edit = QLineEdit()
        edit.setReadOnly(True)
        edit.setObjectName("readonly")
        edit.setStyleSheet(
            f"background-color: {get_color('readonly_bg')}; "
            f"color: {get_color('text_secondary')}; "
            f"border: 1px solid {get_color('readonly_border')}; "
            f"font-weight: 600;"
        )
        return edit

    def _update_readonly_style(self, edit, text_color):
        edit.setStyleSheet(
            f"background-color: {get_color('readonly_bg')}; "
            f"color: {text_color}; "
            f"border: 1px solid {get_color('readonly_border')}; "
            f"font-weight: 600; font-size: 13px;"
        )

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
            logger.debug("RR calc skipped: non-numeric input")
            return

        if entry <= 0 or target <= 0 or sl <= 0:
            logger.debug(f"RR calc skipped: invalid prices entry={entry} target={target} sl={sl}")
            return

        result = self._controller.calculate_rr(action, entry, target, sl)
        if result is None:
            return

        green = get_color("reward_green")
        red = get_color("risk_red")

        self._reward_display.setText(f"\u20b9{result.reward:,.2f}")
        self._update_readonly_style(self._reward_display, green)

        self._risk_display.setText(f"\u20b9{result.risk:,.2f}")
        self._update_readonly_style(self._risk_display, red)

        self._reward_pct_display.setText(f"{result.reward_pct:.2f}%")
        self._update_readonly_style(self._reward_pct_display, green)

        self._risk_pct_display.setText(f"{result.risk_pct:.2f}%")
        self._update_readonly_style(self._risk_pct_display, red)

        self._rr_display.setText(result.risk_reward)
        self._update_readonly_style(self._rr_display, get_color("text_primary"))

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
            logger.debug(f"Zone offset not applied: text='{text}' entry={entry}")
            return

        match_pct = re.match(r'^[+\-]\d+(\.\d+)?%$', text)
        match_abs = re.match(r'^[+\-]\d+(\.\d+)?$', text)

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
            QMessageBox.warning(self.window(), "Warning", "Enter a stock symbol first.")
            return

        segment = self._segment_combo.currentText()
        logger.debug(f"Fetching CMP for '{stock}' in {segment}")
        self._fetch_cmp_btn.setEnabled(False)
        self._fetch_cmp_btn.setText("Fetching...")
        self._controller.fetch_cmp(stock, segment)

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
        QMessageBox.warning(self.window(), "CMP Fetch Error", err)

    def _on_submit(self):
        if self._is_submitting:
            return

        trade_data = self._validate_and_build()
        if not trade_data:
            return

        telegram_config = Config.get_section("telegram")
        groups = telegram_config.get("groups", {})
        selected_groups = None
        if groups:
            dialog = GroupSelectDialog(groups, self)
            if dialog.exec() == GroupSelectDialog.Accepted:
                selected_groups = dialog.get_selected_groups()
            if not selected_groups:
                logger.info("Trade submit cancelled: no groups selected")
                return

        logger.info(f"Submitting trade: stock={trade_data.get('stock_name')}, groups={list(selected_groups.keys()) if selected_groups else 'default'}")
        self._is_submitting = True
        self._submit_btn.setEnabled(False)
        self._submit_btn.setText("Submitting...")

        self._controller.create_trade_and_broadcast(trade_data, selected_groups)

    def _validate_and_build(self):
        stock = self._stock_entry.text().strip()
        if not stock:
            logger.debug("Validation failed: empty stock symbol")
            QMessageBox.warning(self.window(), "Validation Error",
                                "Stock / Symbol is required.")
            self._stock_entry.setFocus()
            return None

        try:
            entry = float(self._entry_price.text()) if self._entry_price.text() else 0
            target = float(self._target_price.text()) if self._target_price.text() else 0
            sl = float(self._stop_loss.text()) if self._stop_loss.text() else 0
        except (ValueError, TypeError):
            logger.debug("Validation failed: non-numeric price")
            QMessageBox.warning(self.window(), "Validation Error",
                                "Entry Price, Target, and Stop Loss must be valid numbers.")
            return None

        if entry <= 0:
            logger.debug(f"Validation failed: entry={entry}")
            QMessageBox.warning(self.window(), "Validation Error",
                                "Entry Price must be greater than 0.")
            self._entry_price.setFocus()
            return None

        if target <= 0:
            logger.debug(f"Validation failed: target={target}")
            QMessageBox.warning(self.window(), "Validation Error",
                                "Target must be greater than 0.")
            self._target_price.setFocus()
            return None

        if sl <= 0:
            logger.debug(f"Validation failed: sl={sl}")
            QMessageBox.warning(self.window(), "Validation Error",
                                "Stop Loss must be greater than 0.")
            self._stop_loss.setFocus()
            return None

        action_db = to_db_action(self._action_combo.currentText())
        segment = self._segment_combo.currentText()

        rr_result = self._controller.calculate_rr(
            self._action_combo.currentText(), entry, target, sl
        )

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

        if rr_result:
            trade_data["reward"] = round(rr_result.reward, 2)
            trade_data["risk"] = round(rr_result.risk, 2)
            trade_data["reward_pct"] = round(rr_result.reward_pct, 2)
            trade_data["risk_pct"] = round(rr_result.risk_pct, 2)
            trade_data["risk_reward"] = rr_result.risk_reward

        return trade_data

    def _on_trade_created(self, trade_code):
        logger.debug(f"Trade created signal received: {trade_code}")

    def _on_trade_create_error(self, err):
        logger.error(f"Trade creation failed: {err}")
        self._is_submitting = False
        self._submit_btn.setEnabled(True)
        self._submit_btn.setText("Submit Trade & Broadcast")
        QMessageBox.critical(self.window(), "Error", f"Failed to save trade:\n{err}")

    def _on_broadcast_complete(self, result):
        self._is_submitting = False
        self._submit_btn.setEnabled(True)
        self._submit_btn.setText("Submit Trade & Broadcast")

        summary = build_broadcast_summary(result)

        logger.info(f"Broadcast complete: image={result.image_success} sheets={result.sheets_success} telegram={result.telegram_success} errors={result.errors} failures={result.telegram_failures}")
        self._clear_form()

        has_issues = result.errors or result.telegram_failures or not result.sheets_success
        if has_issues:
            self._signals.notification.emit(
                f"Trade submitted with issues: {summary}",
                ToastWidget.WARNING,
                5000,
            )
            detail_lines = build_broadcast_detail(result)
            if detail_lines:
                QMessageBox.warning(
                    self.window(), "Broadcast Issues",
                    "\n".join(detail_lines)
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

    def refresh_style(self):
        pass