import customtkinter as ctk
import tkinter.ttk as ttk
from database.db_manager import get_all_trades
from utils.constants import STATUS_COLORS, STATUSES, ACTION_COLORS
from services.trade_service import to_display_action
from utils.logger import setup_logger

logger = setup_logger("TradeList")

_DARK_THEME = {
    "bg": "#2b2b2b",
    "fg": "#e6e6e6",
    "header_bg": "#3b3b3b",
    "header_fg": "#cccccc",
    "row_even": "#2b2b2b",
    "row_odd": "#363636",
    "hover_bg": "#45476a",
    "selected_bg": "#3a3a5c",
}

_LIGHT_THEME = {
    "bg": "#f2f2f2",
    "fg": "#1a1a1a",
    "header_bg": "#e0e0e0",
    "header_fg": "#333333",
    "row_even": "#f2f2f2",
    "row_odd": "#e8e8e8",
    "hover_bg": "#d4d4f0",
    "selected_bg": "#c0c0e0",
}


class TradeList(ctk.CTkFrame):
    COLUMNS = ["Trade Code", "Date", "Stock", "Segment", "Action",
               "Entry", "Target", "SL", "Status"]
    COL_WIDTHS = [120, 90, 140, 85, 70, 95, 95, 95, 85]

    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=0, fg_color="transparent", **kwargs)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._trade_map = {}
        self._idle_refresh_id = None
        self._hover_row_id = None
        self._theme = _DARK_THEME

        self._build_header_area()
        self._build_treeview()

    def _build_header_area(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            frame, text="Active Trades",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        self.status_filter = ctk.CTkOptionMenu(
            frame,
            values=["ALL"] + list(STATUSES),
            command=self._on_filter_change
        )
        self.status_filter.grid(row=0, column=1, padx=15)

        self.count_label = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60")
        )
        self.count_label.grid(row=0, column=2, padx=(0, 10), sticky="e")

        self.refresh_btn = ctk.CTkButton(
            frame, text="\u21bb Refresh", width=80, command=self.refresh_data
        )
        self.refresh_btn.grid(row=0, column=3)

    def _build_treeview(self):
        self._container = ctk.CTkFrame(self, fg_color="transparent")
        self._container.grid(row=1, column=0, sticky="nsew")
        self._container.grid_rowconfigure(0, weight=1)
        self._container.grid_columnconfigure(0, weight=1)

        self._apply_theme()

        vsb = ctk.CTkScrollbar(self._container, orientation="vertical")
        hsb = ctk.CTkScrollbar(self._container, orientation="horizontal")

        self.tree = ttk.Treeview(
            self._container,
            columns=self.COLUMNS,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode="browse",
            style="TradeList.Treeview",
        )
        vsb.configure(command=self.tree.yview)
        hsb.configure(command=self.tree.xview)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._no_data_label = ctk.CTkLabel(
            self, text="No trades found matching filters.",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60"),
        )

        self._configure_columns()
        self._bind_tree_events()
        self._configure_tags()

    def _apply_theme(self):
        mode = ctk.get_appearance_mode()
        self._theme = _LIGHT_THEME if mode == "Light" else _DARK_THEME
        t = self._theme

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TradeList.Treeview",
                        background=t["bg"],
                        foreground=t["fg"],
                        fieldbackground=t["bg"],
                        borderwidth=0,
                        relief="flat",
                        bordercolor=t["bg"],
                        lightcolor=t["bg"],
                        darkcolor=t["bg"],
                        rowheight=34,
                        font=("Segoe UI", 10))
        style.configure("TradeList.Treeview.Heading",
                        background=t["header_bg"],
                        foreground=t["header_fg"],
                        borderwidth=0,
                        relief="flat",
                        bordercolor=t["header_bg"],
                        lightcolor=t["header_bg"],
                        darkcolor=t["header_bg"],
                        font=("Segoe UI", 9, "bold"),
                        padding=(0, 8))
        style.map("TradeList.Treeview.Heading",
                  background=[("active", t["header_bg"])],
                  foreground=[("active", t["header_fg"])])

        if hasattr(self, 'tree') and self.tree is not None:
            self.tree.configure(style="TradeList.Treeview")
            self._configure_tags()
            for item in self.tree.get_children():
                tags = list(self.tree.item(item, "tags") or [])
                base = "even" if "even" in tags else "odd"
                self.tree.item(item, tags=(base,))

    def _configure_tags(self):
        t = self._theme
        self.tree.tag_configure("even", background=t["row_even"], foreground=t["fg"])
        self.tree.tag_configure("odd", background=t["row_odd"], foreground=t["fg"])
        self.tree.tag_configure("hover", background=t["hover_bg"], foreground=t["fg"])

    def _configure_columns(self):
        for col, w in zip(self.COLUMNS, self.COL_WIDTHS):
            self.tree.column(col, width=w, minwidth=50, anchor="w")
            self.tree.heading(col, text=col, anchor="w")

    def _bind_tree_events(self):
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Motion>", self._on_motion)
        self.tree.bind("<Leave>", self._on_leave)

    def _on_filter_change(self, *args):
        self.refresh_data()

    def _on_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        trade = self._trade_map.get(row_id)
        if trade:
            self.open_trade_detail(trade)

    def _on_motion(self, event):
        row_id = self.tree.identify_row(event.y)
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell" and row_id and row_id != self._hover_row_id:
            self._clear_hover()
            self._hover_row_id = row_id
            self.tree.item(row_id, tags=("hover",))
            self.tree.configure(cursor="hand2")
        elif not row_id or region != "cell":
            self._clear_hover()
            self.tree.configure(cursor="")

    def _on_leave(self, event):
        self._clear_hover()
        self.tree.configure(cursor="")

    def _clear_hover(self):
        if self._hover_row_id:
            try:
                self.tree.item(self._hover_row_id, tags=("odd",))
                try:
                    idx = self.tree.index(self._hover_row_id)
                    tag = "even" if idx % 2 == 0 else "odd"
                    self.tree.item(self._hover_row_id, tags=(tag,))
                except Exception:
                    pass
            except Exception:
                pass
            self._hover_row_id = None

    def refresh_data(self, *args):
        if self._idle_refresh_id is not None:
            self.after_cancel(self._idle_refresh_id)
            self._idle_refresh_id = None
        self._idle_refresh_id = self.after(0, self._do_refresh)

    def _do_refresh(self):
        self._idle_refresh_id = None
        self._trade_map.clear()
        self._clear_hover()

        for item in self.tree.get_children():
            self.tree.delete(item)

        status = self.status_filter.get()
        filter_dict = {} if status == "ALL" else {"status": status}
        trades = get_all_trades(filter_dict)

        self.count_label.configure(
            text=f"{len(trades)} trade{'s' if len(trades) != 1 else ''}"
        )

        if not trades:
            self._no_data_label.place(relx=0.5, rely=0.65, anchor="center")
            return

        self._no_data_label.place_forget()

        for i, trade in enumerate(trades):
            row = self._trade_to_row(trade)
            tag = "even" if i % 2 == 0 else "odd"
            row_id = self.tree.insert("", "end", values=row, tags=(tag,))
            self._trade_map[row_id] = trade

    def _trade_to_row(self, trade: dict) -> tuple:
        date_str = str(trade.get('created_at', '—')).split(' ')[0] if trade.get('created_at') else "—"
        trade_code = trade.get('trade_code', '?')
        action_display = to_display_action(trade.get('action', 'LONG'))
        entry_price = trade.get('entry_price')
        target = trade.get('target')
        stop_loss = trade.get('stop_loss')
        status_text = trade.get('status', '—')

        entry_str = f"\u20b9{entry_price:.2f}" if isinstance(entry_price, (int, float)) else "\u20b9—"
        target_str = f"\u20b9{target:.2f}" if isinstance(target, (int, float)) else "\u20b9—"
        sl_str = f"\u20b9{stop_loss:.2f}" if isinstance(stop_loss, (int, float)) else "\u20b9—"

        return (
            trade_code,
            date_str,
            trade.get('stock_name', '—'),
            trade.get('segment') or '—',
            action_display,
            entry_str,
            target_str,
            sl_str,
            status_text,
        )

    def update_theme(self):
        self._apply_theme()

    def open_trade_detail(self, trade):
        logger.debug(f"Opening trade detail for {trade.get('trade_code')}")
        self.master.show_trade_detail(trade)