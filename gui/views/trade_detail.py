from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from gui.signals import get_signals
from gui.theme import get_color
from gui.widgets.badge import Badge
from gui.widgets.field_row import FieldRow
from gui.widgets.section_card import SectionCard
from gui.widgets.toast import ToastWidget
from services.trade_service import to_display_action
from utils.constants import STATUS_COLORS, STATUSES, ACTION_COLORS


UPDATE_TYPE_COLORS = {
    "TARGET_HIT": "#28a745",
    "SL_HIT": "#dc3545",
    "PARTIAL_PROFIT": "#17a2b8",
    "TRAIL_SL": "#0f3460",
    "COST_TO_COST": "#0f3460",
    "EXIT": "#f0ad4e",
    "MODIFY_TARGET": "#6c757d",
    "MODIFY_SL": "#6c757d",
}

REWARD_COLOR = "#28a745"
RISK_COLOR = "#dc3545"


class TradeDetailView(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._signals = get_signals()
        self._trade = None
        self._updates = []

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        header_bar = QWidget()
        header_bar.setStyleSheet(f"background-color: {get_color('surface')};")
        header_bar.setFixedHeight(60)
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(24, 0, 24, 0)
        header_layout.setSpacing(16)

        self._back_btn = QPushButton("\u2190  Back to Active Trades")
        self._back_btn.setObjectName("ghost")
        self._back_btn.setCursor(Qt.PointingHandCursor)
        self._back_btn.clicked.connect(self._go_back)
        header_layout.addWidget(self._back_btn)

        self._title_label = QLabel("Trade Detail")
        self._title_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self._title_label.setStyleSheet(
            f"color: {get_color('text_primary')}; background: transparent;"
        )
        header_layout.addWidget(self._title_label, 1)

        self._update_btn = QPushButton("Update Trade")
        self._update_btn.setObjectName("success")
        self._update_btn.setCursor(Qt.PointingHandCursor)
        self._update_btn.clicked.connect(self._open_update_modal)
        header_layout.addWidget(self._update_btn)

        outer_layout.addWidget(header_bar)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet("background-color: transparent; border: none;")

        self._body = QWidget()
        self._body.setStyleSheet("background-color: transparent;")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(32, 24, 32, 24)
        self._body_layout.setSpacing(20)

        self._scroll.setWidget(self._body)
        outer_layout.addWidget(self._scroll, 1)

    def _connect_signals(self):
        self._signals.trade_detail_loaded.connect(self._on_detail_loaded)

    def on_show(self, trade=None):
        if trade:
            self._trade = trade
        if self._trade:
            self._load_detail(self._trade)

    def _load_detail(self, trade):
        self._controller.get_trade_by_code(trade.get("trade_code"))

    def _on_detail_loaded(self, trade, updates):
        if not trade:
            self._signals.notification.emit(
                "Trade not found", ToastWidget.ERROR, 4000
            )
            self._go_back()
            return
        self._trade = trade
        self._updates = updates
        self._populate_body()

    def _populate_body(self):
        trade = self._trade
        updates = self._updates

        self._title_label.setText(f"#{trade.get('trade_code', '?')}")

        for i in reversed(range(self._body_layout.count())):
            item = self._body_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        c = get_color("border")

        summary = QWidget()
        summary.setStyleSheet("background-color: transparent;")
        summary_layout = QHBoxLayout(summary)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setSpacing(12)

        stock = QLabel(trade.get("stock_name") or "\u2014")
        stock.setFont(QFont("Segoe UI", 18, QFont.Bold))
        stock.setStyleSheet(f"color: {get_color('text_primary')}; background: transparent;")
        summary_layout.addWidget(stock)

        segment_val = (trade.get("segment") or "\u2014").strip() or "\u2014"
        segment_badge = Badge(segment_val, segment_val.upper(), 10)
        summary_layout.addWidget(segment_badge)

        action_display = to_display_action(trade.get("action") or "LONG")
        action_badge = Badge(action_display, action_display, 10)
        summary_layout.addWidget(action_badge)

        status_text = trade.get("status") or "\u2014"
        status_badge = Badge(status_text, status_text, 10)
        summary_layout.addWidget(status_badge)

        summary_layout.addStretch()
        self._body_layout.addWidget(summary)

        card1 = SectionCard("Trade Identity")
        left_right1 = QHBoxLayout()
        left_right1.setSpacing(24)

        left1 = QWidget()
        left1.setStyleSheet("background-color: transparent;")
        left1_layout = QVBoxLayout(left1)
        left1_layout.setContentsMargins(0, 0, 0, 0)
        left1_layout.setSpacing(2)

        right1 = QWidget()
        right1.setStyleSheet("background-color: transparent;")
        right1_layout = QVBoxLayout(right1)
        right1_layout.setContentsMargins(0, 0, 0, 0)
        right1_layout.setSpacing(2)

        left1_layout.addWidget(FieldRow("Trade Code", trade.get("trade_code") or "\u2014"))
        left1_layout.addWidget(FieldRow("Stock Name", trade.get("stock_name") or "\u2014"))
        left1_layout.addWidget(FieldRow("Segment", trade.get("segment") or "\u2014"))
        left1_layout.addWidget(FieldRow("Action", action_display))
        left1_layout.addWidget(FieldRow("Trade Type", trade.get("trade_type") or "\u2014"))
        left1_layout.addWidget(FieldRow("Approx Time", trade.get("approx_time") or "\u2014"))

        status_color = STATUS_COLORS.get(status_text, "#6c757d")
        right1_layout.addWidget(FieldRow("Status", status_text, status_color))
        created_at = str(trade.get("created_at") or "\u2014").split(".")[0]
        right1_layout.addWidget(FieldRow("Created At", created_at))
        updated_at = str(trade.get("updated_at") or "\u2014").split(".")[0]
        right1_layout.addWidget(FieldRow("Updated At", updated_at))
        cmp_at_entry = trade.get("cmp_at_entry")
        cmp_str = f"\u20b9{cmp_at_entry:,.2f}" if isinstance(cmp_at_entry, (int, float)) else "\u2014"
        right1_layout.addWidget(FieldRow("CMP at Entry", cmp_str))

        left_right1.addWidget(left1, 1)
        left_right1.addWidget(right1, 1)
        card1.add_layout(left_right1)
        self._body_layout.addWidget(card1)

        card2 = SectionCard("Price Levels")
        left_right2 = QHBoxLayout()
        left_right2.setSpacing(24)

        left2 = QWidget()
        left2.setStyleSheet("background-color: transparent;")
        left2_layout = QVBoxLayout(left2)
        left2_layout.setContentsMargins(0, 0, 0, 0)
        left2_layout.setSpacing(2)

        right2 = QWidget()
        right2.setStyleSheet("background-color: transparent;")
        right2_layout = QVBoxLayout(right2)
        right2_layout.setContentsMargins(0, 0, 0, 0)
        right2_layout.setSpacing(2)

        entry_price = trade.get("entry_price")
        target = trade.get("target")
        stop_loss = trade.get("stop_loss")
        exit_price = trade.get("exit_price")
        latest_sl = trade.get("latest_sl_price")
        latest_target = trade.get("latest_target")

        entry_str = f"\u20b9{entry_price:,.2f}" if isinstance(entry_price, (int, float)) else "\u2014"
        target_str = f"\u20b9{target:,.2f}" if isinstance(target, (int, float)) else "\u2014"
        sl_str = f"\u20b9{stop_loss:,.2f}" if isinstance(stop_loss, (int, float)) else "\u2014"
        exit_str = f"\u20b9{exit_price:,.2f}" if isinstance(exit_price, (int, float)) else "\u2014"
        latest_sl_str = f"\u20b9{latest_sl:,.2f}" if isinstance(latest_sl, (int, float)) else "\u2014"
        latest_target_str = f"\u20b9{latest_target:,.2f}" if isinstance(latest_target, (int, float)) else "\u2014"

        left2_layout.addWidget(FieldRow("Entry Price", entry_str))
        left2_layout.addWidget(FieldRow("Target", target_str))
        left2_layout.addWidget(FieldRow("Stop Loss", sl_str))
        zone_start = trade.get("zone_start") or ""
        zone_end = trade.get("zone_end") or ""
        zone_str = f"{zone_start} \u2013 {zone_end}" if zone_start and zone_end else "\u2014"
        left2_layout.addWidget(FieldRow("Zone", zone_str))

        right2_layout.addWidget(FieldRow("Latest SL", latest_sl_str))
        right2_layout.addWidget(FieldRow("Latest Target", latest_target_str))
        right2_layout.addWidget(FieldRow("Exit Price", exit_str))
        exit_date = trade.get("exit_datetime") or ""
        exit_date_str = str(exit_date).split(".")[0] if exit_date else "\u2014"
        right2_layout.addWidget(FieldRow("Exit Date", exit_date_str))

        left_right2.addWidget(left2, 1)
        left_right2.addWidget(right2, 1)
        card2.add_layout(left_right2)
        self._body_layout.addWidget(card2)

        card3 = SectionCard("Risk & Reward")
        left_right3 = QHBoxLayout()
        left_right3.setSpacing(24)

        left3 = QWidget()
        left3.setStyleSheet("background-color: transparent;")
        left3_layout = QVBoxLayout(left3)
        left3_layout.setContentsMargins(0, 0, 0, 0)
        left3_layout.setSpacing(2)

        right3 = QWidget()
        right3.setStyleSheet("background-color: transparent;")
        right3_layout = QVBoxLayout(right3)
        right3_layout.setContentsMargins(0, 0, 0, 0)
        right3_layout.setSpacing(2)

        reward = trade.get("reward")
        risk = trade.get("risk")
        reward_pct = trade.get("reward_pct")
        risk_pct = trade.get("risk_pct")
        rr = trade.get("risk_reward") or ""

        reward_str = f"\u20b9{reward:,.2f}" if isinstance(reward, (int, float)) else "\u2014"
        risk_str = f"\u20b9{risk:,.2f}" if isinstance(risk, (int, float)) else "\u2014"
        reward_pct_str = f"{reward_pct:.2f}%" if isinstance(reward_pct, (int, float)) else "\u2014"
        risk_pct_str = f"{risk_pct:.2f}%" if isinstance(risk_pct, (int, float)) else "\u2014"

        left3_layout.addWidget(FieldRow("Reward", reward_str, REWARD_COLOR))
        left3_layout.addWidget(FieldRow("Risk", risk_str, RISK_COLOR))
        right3_layout.addWidget(FieldRow("Reward %", reward_pct_str, REWARD_COLOR))
        right3_layout.addWidget(FieldRow("Risk %", risk_pct_str, RISK_COLOR))

        left_right3.addWidget(left3, 1)
        left_right3.addWidget(right3, 1)
        card3.add_layout(left_right3)

        rr_widget = FieldRow("Risk : Reward", rr if rr else "\u2014")
        rr_container = QWidget()
        rr_container.setStyleSheet("background-color: transparent;")
        rr_container_layout = QHBoxLayout(rr_container)
        rr_container_layout.setContentsMargins(0, 4, 0, 0)
        rr_container_layout.addWidget(rr_widget, 1)
        card3.add_widget(rr_container)

        self._body_layout.addWidget(card3)

        close_narration = trade.get("close_narration") or ""
        remarks = trade.get("remarks") or ""

        if close_narration or remarks:
            notes_card = SectionCard("Notes")
            if close_narration and (not remarks or close_narration == remarks):
                notes_card.add_widget(FieldRow("Remarks", close_narration))
            else:
                if close_narration:
                    notes_card.add_widget(FieldRow("Close Narration", close_narration))
                if remarks:
                    notes_card.add_widget(FieldRow("Remarks", remarks))
            self._body_layout.addWidget(notes_card)

        if updates:
            sep = QFrame()
            sep.setObjectName("separator")
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background-color: {get_color('border')}; border: none;")
            self._body_layout.addWidget(sep)

            updates_title = QLabel("Updates Timeline")
            updates_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
            updates_title.setStyleSheet(
                f"color: {get_color('text_primary')}; background: transparent;"
            )
            self._body_layout.addWidget(updates_title)

            for i, update in enumerate(updates):
                update_card = self._render_update_card(update, i)
                self._body_layout.addWidget(update_card)

        is_closed = (trade.get("status") or "").upper() == "CLOSED"
        self._update_btn.setVisible(not is_closed)

        self._body_layout.addStretch()

    def _render_update_card(self, update, index):
        update_type = update.get("update_type", "\u2014")
        created_at = str(update.get("created_at", "")).split(".")[0]
        message = update.get("message", "") or update.get("details", "")
        changes = update.get("changes", "")

        accent_color = UPDATE_TYPE_COLORS.get(update_type, get_color("text_muted"))
        bg_color = get_color("surface_hover") if index % 2 == 0 else get_color("surface")

        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(f"""
        #card {{
            background-color: {bg_color};
            border-radius: 8px;
            border-left: 4px solid {accent_color};
        }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(8)

        ut_label = QLabel(update_type.replace("_", " ").title())
        ut_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        ut_label.setStyleSheet(f"color: {accent_color}; background: transparent; border: none;")
        header.addWidget(ut_label)

        header.addStretch()

        time_label = QLabel(created_at)
        time_label.setStyleSheet(
            f"color: {get_color('text_muted')}; font-size: 11px; "
            f"background: transparent; border: none;"
        )
        header.addWidget(time_label)

        layout.addLayout(header)

        if message:
            msg_label = QLabel(message)
            msg_label.setWordWrap(True)
            msg_label.setStyleSheet(
                f"color: {get_color('text_primary')}; font-size: 12px; "
                f"background: transparent; border: none;"
            )
            layout.addWidget(msg_label)

        if changes:
            changes_label = QLabel(changes)
            changes_label.setWordWrap(True)
            changes_label.setStyleSheet(
                f"color: {get_color('text_secondary')}; font-size: 11px; "
                f"background: transparent; border: none;"
            )
            layout.addWidget(changes_label)

        return card

    def _open_update_modal(self):
        if not self._trade:
            return

        from gui.views.update_dialog import UpdateDialog
        dialog = UpdateDialog(self._trade, self._controller, self)
        dialog.finished.connect(self._on_update_dialog_finished)
        dialog.open()

    def _on_update_dialog_finished(self, result):
        if result == 1:
            if self._trade:
                self._load_detail(self._trade)

    def _go_back(self):
        self._signals.navigate.emit("active_trades", None)
