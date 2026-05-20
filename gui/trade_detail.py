import customtkinter as ctk
from database.db_manager import get_trade, get_trade_updates
from utils.constants import ACTION_COLORS, STATUS_COLORS
from services.trade_service import to_display_action
from utils.logger import setup_logger

logger = setup_logger("TradeDetail")

UPDATE_TYPE_COLORS = {
    "TARGET_HIT": "#28a745",
    "SL_HIT": "#dc3545",
    "PARTIAL_PROFIT": "#17a2b8",
    "TRAIL_SL": "#2196F3",
    "COST_TO_COST": "#2196F3",
    "EXIT": "#f0ad4e",
    "MODIFY_TARGET": "#6c757d",
    "MODIFY_SL": "#6c757d",
}

# Semantic colors for financial data
REWARD_COLOR = "#28a745"
RISK_COLOR = "#dc3545"


class _FieldRow:
    """A label:value pair in a tight 2-column grid (fixed label width)."""

    def __init__(self, parent, label, value, row, value_color=None):
        self.label_widget = ctk.CTkLabel(
            parent, text=label,
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
        )
        self.label_widget.grid(row=row, column=0, sticky="w", padx=(8, 4), pady=2)

        self.value_widget = ctk.CTkLabel(
            parent, text=str(value) if value is not None else "\u2014",
            font=ctk.CTkFont(size=12), anchor="w", text_color=value_color
        )
        self.value_widget.grid(row=row, column=1, sticky="w", padx=(0, 8), pady=2)


class TradeDetail(ctk.CTkFrame):
    def __init__(self, master, trade, **kwargs):
        super().__init__(master, corner_radius=0, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._trade_code = trade.get("trade_code")
        self._build_header()
        self._build_body()

    def _create_badge(self, parent, text, color, font_size=11):
        badge = ctk.CTkFrame(parent, fg_color=color, corner_radius=4)
        ctk.CTkLabel(
            badge, text=text, text_color="white",
            font=ctk.CTkFont(size=font_size, weight="bold")
        ).pack(padx=8, pady=2)
        return badge

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(1, weight=1)

        self.back_btn = ctk.CTkButton(
            header, text="\u2190  Back to Active Trades",
            fg_color=("gray60", "gray35"), hover_color=("gray50", "gray45"),
            command=self._go_back, font=ctk.CTkFont(size=12), width=180
        )
        self.back_btn.grid(row=0, column=0, sticky="w")

        title = f"#{self._trade_code}" if self._trade_code else "Trade Detail"
        ctk.CTkLabel(
            header, text=title,
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=1, padx=10)

        self.update_btn = ctk.CTkButton(
            header, text="Update Trade",
            command=self._open_update_modal
        )
        self.update_btn.grid(row=0, column=2, sticky="e")

    def _build_body(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=2, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self._populate_body()

    def _make_card(self, title_text: str):
        """Create a bordered section card with title + divider line."""
        card = ctk.CTkFrame(
            self.scroll_frame, corner_radius=10,
            fg_color=("gray95", "gray17"),
            border_width=1, border_color=("gray80", "gray30")
        )
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)

        # Section title
        ctk.CTkLabel(
            card, text=f"  {title_text}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray40", "gray70"), anchor="w"
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 2), sticky="ew")

        # Divider line
        divider = ctk.CTkFrame(card, height=1, fg_color=("gray80", "gray35"))
        divider.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))
        divider.grid_propagate(False)

        return card

    def _make_half_frame(self, parent, row, col):
        """Create a sub-frame for left/right side of a card with fixed label width."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, sticky="nsew", padx=(8, 8), pady=(0, 6))
        frame.grid_columnconfigure(0, weight=0, minsize=140)
        frame.grid_columnconfigure(1, weight=1)
        return frame

    def _populate_body(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        trade = get_trade(self._trade_code) or {}
        action_display = to_display_action(trade.get("action", "LONG"))
        action_color = ACTION_COLORS["LONG"] if trade.get("action") == "BUY" else ACTION_COLORS["SHORT"]
        status_colors = STATUS_COLORS if isinstance(STATUS_COLORS, dict) else {}
        status = trade.get("status", "\u2014")
        status_color = status_colors.get(status, "#6c757d")
        stock_name = trade.get('stock_name') or '\u2014'
        segment = trade.get('segment') or '\u2014'
        is_closed = trade.get("status") == "CLOSED"

        # ── Summary bar ─────────────────────────────────────────────────────
        summary = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        summary.grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 16))
        summary.grid_columnconfigure(6, weight=1)

        ctk.CTkLabel(
            summary, text=stock_name,
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            summary, text="  \u00b7  ", font=ctk.CTkFont(size=16),
            text_color=("gray50", "gray60")
        ).grid(row=0, column=1)

        ctk.CTkLabel(
            summary, text=segment, font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray70")
        ).grid(row=0, column=2, padx=(0, 8), sticky="w")

        action_badge = self._create_badge(summary, action_display, action_color, font_size=10)
        action_badge.grid(row=0, column=3, padx=2)

        status_badge = self._create_badge(summary, status, status_color, font_size=10)
        status_badge.grid(row=0, column=4, padx=2)

        row = 1  # next row in scroll_frame

        # ── Card 1: TRADE IDENTITY ──────────────────────────────────────────
        card1 = self._make_card("TRADE IDENTITY")
        card1.grid(row=row, column=0, sticky="ew", padx=10, pady=(0, 8))
        row += 1

        left1 = self._make_half_frame(card1, row=2, col=0)
        right1 = self._make_half_frame(card1, row=2, col=1)

        _FieldRow(left1, "Trade Code:", trade.get("trade_code") or "\u2014", 0)
        _FieldRow(left1, "Stock Name:", stock_name, 1)
        _FieldRow(left1, "Segment:", segment, 2)
        _FieldRow(left1, "Action:", action_display, 3)
        _FieldRow(left1, "Trade Type:", trade.get("trade_type") or "\u2014", 4)
        _FieldRow(left1, "Approx Time:", trade.get("approx_time") or "\u2014", 5)

        _FieldRow(right1, "Status:", status, 0, value_color=status_color)
        _FieldRow(right1, "Created At:", trade.get("created_at") or "\u2014", 1)
        _FieldRow(right1, "Updated At:", trade.get("updated_at") or "\u2014", 2)
        _FieldRow(right1, "CMP at Entry:", trade.get("cmp_at_entry") or "\u2014", 3)

        # ── Card 2: PRICE LEVELS ────────────────────────────────────────────
        card2 = self._make_card("PRICE LEVELS")
        card2.grid(row=row, column=0, sticky="ew", padx=10, pady=(0, 8))
        row += 1

        left2 = self._make_half_frame(card2, row=2, col=0)
        right2 = self._make_half_frame(card2, row=2, col=1)

        _FieldRow(left2, "Entry Price (\u20b9):", trade.get("entry_price") or "\u2014", 0)
        _FieldRow(left2, "Target (\u20b9):", trade.get("target") or "\u2014", 1)
        _FieldRow(left2, "Stop Loss (\u20b9):", trade.get("stop_loss") or "\u2014", 2)
        _FieldRow(left2, "Zone Start (\u20b9):", trade.get("zone_start") or "\u2014", 3)
        _FieldRow(left2, "Zone End (\u20b9):", trade.get("zone_end") or "\u2014", 4)

        _FieldRow(right2, "Latest SL (\u20b9):", trade.get("latest_sl_price") or "\u2014", 0)
        _FieldRow(right2, "Latest Target (\u20b9):", trade.get("latest_target") or "\u2014", 1)
        _FieldRow(right2, "Exit Price (\u20b9):", trade.get("exit_price") or "\u2014", 2)
        _FieldRow(right2, "Exit Date:", trade.get("exit_datetime") or "\u2014", 3)

        # ── Card 3: RISK & REWARD ─────────────────────────────────────────
        card3 = self._make_card("RISK & REWARD")
        card3.grid(row=row, column=0, sticky="ew", padx=10, pady=(0, 8))
        row += 1

        left3 = self._make_half_frame(card3, row=2, col=0)
        right3 = self._make_half_frame(card3, row=2, col=1)

        reward_val = trade.get("reward") or "\u2014"
        risk_val = trade.get("risk") or "\u2014"
        reward_pct = trade.get("reward_pct") or "\u2014"
        risk_pct = trade.get("risk_pct") or "\u2014"
        rr_val = trade.get("risk_reward") or "\u2014"

        _FieldRow(left3, "Reward (\u20b9):", reward_val, 0, value_color=REWARD_COLOR)
        _FieldRow(left3, "Risk (\u20b9):", risk_val, 1, value_color=RISK_COLOR)
        _FieldRow(left3, "Reward %:", reward_pct, 2, value_color=REWARD_COLOR)

        _FieldRow(right3, "Risk %:", risk_pct, 0, value_color=RISK_COLOR)
        _FieldRow(right3, "Risk:Reward:", rr_val, 1)

        # ── Card 4: NOTES (Close Narration / Remarks) ───────────────────────
        close_narration = (trade.get("close_narration") or "").strip()
        remarks = (trade.get("remarks") or "").strip()

        if close_narration and remarks and close_narration == remarks:
            # Identical — show once
            notes_card = self._make_card("NOTES")
            notes_card.grid(row=row, column=0, sticky="ew", padx=10, pady=(0, 8))
            row += 1
            ctk.CTkLabel(
                notes_card, text=close_narration,
                font=ctk.CTkFont(size=12), anchor="w", wraplength=700
            ).grid(row=2, column=0, columnspan=2, sticky="w", padx=(14, 20), pady=(0, 8))
        else:
            if close_narration:
                cn_card = self._make_card("CLOSE NARRATION")
                cn_card.grid(row=row, column=0, sticky="ew", padx=10, pady=(0, 8))
                row += 1
                ctk.CTkLabel(
                    cn_card, text=close_narration,
                    font=ctk.CTkFont(size=12), anchor="w", wraplength=700
                ).grid(row=2, column=0, columnspan=2, sticky="w", padx=(14, 20), pady=(0, 8))

            if remarks:
                rm_card = self._make_card("REMARKS")
                rm_card.grid(row=row, column=0, sticky="ew", padx=10, pady=(0, 8))
                row += 1
                ctk.CTkLabel(
                    rm_card, text=remarks,
                    font=ctk.CTkFont(size=12), anchor="w", wraplength=700
                ).grid(row=2, column=0, columnspan=2, sticky="w", padx=(14, 20), pady=(0, 8))

        # ── Update button state ────────────────────────────────────────────
        self.update_btn.configure(state="disabled" if is_closed else "normal")

        # ── Separator ──────────────────────────────────────────────────────
        sep = ctk.CTkFrame(self.scroll_frame, height=2, fg_color=("gray70", "gray30"))
        sep.grid(row=row, column=0, sticky="ew", padx=10, pady=12)
        sep.grid_propagate(False)
        row += 1

        # ── Updates timeline ──────────────────────────────────────────────
        ctk.CTkLabel(
            self.scroll_frame, text="Updates",
            font=ctk.CTkFont(size=18, weight="bold"), anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=10, pady=(0, 8))
        row += 1

        updates = get_trade_updates(self._trade_code)
        if not updates:
            ctk.CTkLabel(
                self.scroll_frame,
                text="No updates recorded for this trade.",
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray60")
            ).grid(row=row, column=0, sticky="w", padx=20, pady=8)
            row += 1
        else:
            for i, upd in enumerate(updates):
                self._render_update_card(i, upd, row)
                row += 1

    def _get_update_type_color(self, update_type: str) -> str:
        return UPDATE_TYPE_COLORS.get(update_type, "#6c757d")

    def _render_update_card(self, index: int, upd: dict, row: int):
        bg = ("gray95", "gray17") if index % 2 == 0 else ("gray90", "gray20")
        accent_color = self._get_update_type_color(upd.get('update_type', ''))

        card = ctk.CTkFrame(self.scroll_frame, fg_color=bg, corner_radius=6)
        card.grid(row=row, column=0, sticky="ew", padx=12, pady=2)
        card.grid_columnconfigure(1, weight=1)

        accent = ctk.CTkFrame(card, fg_color=accent_color, width=4, corner_radius=0)
        accent.grid(row=0, column=0, rowspan=3, sticky="ns")

        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.grid(row=0, column=1, sticky="ew", padx=(8, 6), pady=(4, 1))
        header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_frame,
            text=f"\u2699  {upd.get('update_type', '?')}",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header_frame,
            text=upd.get("created_at", ""),
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray60"),
            anchor="e"
        ).grid(row=0, column=1, sticky="e")

        if upd.get("message"):
            ctk.CTkLabel(
                card, text=upd.get("message", ""),
                font=ctk.CTkFont(size=11), anchor="w", wraplength=640
            ).grid(row=1, column=1, sticky="ew", padx=(8, 6), pady=(0, 1))

        if upd.get("changes"):
            ctk.CTkLabel(
                card, text=upd.get("changes", ""),
                font=ctk.CTkFont(size=10),
                text_color=("gray40", "gray70"), anchor="w", wraplength=640
            ).grid(row=2, column=1, sticky="ew", padx=(8, 6), pady=(0, 3))

    def _open_update_modal(self):
        trade = get_trade(self._trade_code)
        if not trade:
            return
        from .update_form import UpdateForm
        UpdateForm(self, trade, on_success_callback=self._refresh)

    def _refresh(self):
        self._populate_body()

    def _go_back(self):
        self.master._trade_list_dirty = True
        self.master.show_active_trades()
