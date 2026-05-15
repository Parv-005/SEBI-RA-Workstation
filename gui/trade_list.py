# pyrefly: ignore [missing-import]
import customtkinter as ctk
from database.db_manager import get_all_trades
from utils.constants import STATUS_COLORS, STATUSES, ACTION_COLORS
from services.trade_service import to_display_action
from utils.logger import setup_logger

logger = setup_logger("TradeList")


class TradeList(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=0, fg_color="transparent", **kwargs)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.header_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            self.header_frame, text="Active Trades",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        self.status_filter = ctk.CTkOptionMenu(
            self.header_frame,
            values=STATUSES,
            command=self.refresh_data
        )
        self.status_filter.grid(row=0, column=1, padx=20)

        self.refresh_btn = ctk.CTkButton(
            self.header_frame, text="↻ Refresh", width=80, command=self.refresh_data
        )
        self.refresh_btn.grid(row=0, column=2)

        self.table_header = ctk.CTkFrame(self)
        self.table_header.grid(row=1, column=0, sticky="ew", pady=(0, 2))

        columns = ["Trade Code", "Date", "Stock", "Segment", "Action",
                   "Entry", "Target", "SL", "Status", "Action"]
        weights = [3, 2, 3, 2, 1, 2, 2, 2, 2, 2]

        for i, (col, weight) in enumerate(zip(columns, weights)):
            self.table_header.grid_columnconfigure(i, weight=weight)
            lbl = ctk.CTkLabel(self.table_header, text=col, font=ctk.CTkFont(weight="bold"))
            lbl.grid(row=0, column=i, pady=5, padx=5, sticky="ew")

        self.data_frame = ctk.CTkScrollableFrame(self)
        self.data_frame.grid(row=2, column=0, sticky="nsew")

        for i, weight in enumerate(weights):
            self.data_frame.grid_columnconfigure(i, weight=weight)

    def refresh_data(self, *args):
        for widget in self.data_frame.winfo_children():
            widget.destroy()

        status = self.status_filter.get()
        filter_dict = {} if status == "ALL" else {"status": status}

        trades = get_all_trades(filter_dict)
        logger.debug(f"Refreshed trade list with {len(trades)} trades (filter: {filter_dict})")

        if not trades:
            ctk.CTkLabel(
                self.data_frame,
                text="No trades found matching filters."
            ).grid(row=0, column=0, columnspan=10, pady=20)
            return

        for i, trade in enumerate(trades):
            date_str = str(trade.get('created_at', '—')).split(' ')[0] if trade.get('created_at') else "—"
            trade_code = trade.get('trade_code', '?')
            action_display = to_display_action(trade.get('action', 'LONG'))
            action_color = ACTION_COLORS["LONG"] if trade.get('action') == "BUY" else ACTION_COLORS["SHORT"]

            row_bg = ("gray95", "gray17") if i % 2 == 0 else ("gray90", "gray20")

            ctk.CTkLabel(
                self.data_frame, text=trade_code,
                font=ctk.CTkFont(size=11), fg_color=row_bg, corner_radius=0
            ).grid(row=i, column=0, pady=2, padx=2, sticky="ew")

            ctk.CTkLabel(self.data_frame, text=date_str).grid(
                row=i, column=1, pady=2, padx=5
            )
            ctk.CTkLabel(
                self.data_frame, text=trade.get('stock_name', '—'),
                font=ctk.CTkFont(weight="bold")
            ).grid(row=i, column=2, pady=2, padx=5)

            ctk.CTkLabel(self.data_frame, text=trade.get('segment', '—')).grid(
                row=i, column=3, pady=2, padx=5
            )
            ctk.CTkLabel(
                self.data_frame, text=action_display,
                text_color=action_color, font=ctk.CTkFont(weight="bold")
            ).grid(row=i, column=4, pady=2, padx=5)

            ctk.CTkLabel(self.data_frame, text=f"₹{trade.get('entry_price', '—')}").grid(
                row=i, column=5, pady=2, padx=5
            )
            ctk.CTkLabel(self.data_frame, text=f"₹{trade.get('target', '—')}").grid(
                row=i, column=6, pady=2, padx=5
            )
            ctk.CTkLabel(self.data_frame, text=f"₹{trade.get('stop_loss', '—')}").grid(
                row=i, column=7, pady=2, padx=5
            )

            status_colors = STATUS_COLORS if isinstance(STATUS_COLORS, dict) else {}
            status_lbl = ctk.CTkLabel(
                self.data_frame, text=trade.get('status', '—'),
                text_color=status_colors.get(trade.get('status'), "white")
            )
            status_lbl.grid(row=i, column=8, pady=2, padx=5)

            update_btn = ctk.CTkButton(
                self.data_frame, text="Update", width=60, height=24,
                command=lambda t=trade: self.open_update_modal(t)
            )
            update_btn.grid(row=i, column=9, pady=2, padx=5)

    def open_update_modal(self, trade):
        from .update_form import UpdateForm
        UpdateForm(self, trade, on_success_callback=self.refresh_data)