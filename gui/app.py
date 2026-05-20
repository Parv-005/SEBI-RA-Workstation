import customtkinter as ctk
from utils.logger import setup_logger

logger = setup_logger("App")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SEBI RA Automation Software")
        self.geometry("1100x700")
        self.minsize(900, 600)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, text="RA Automation",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.new_trade_btn = ctk.CTkButton(
            self.sidebar_frame, text="New Trade", command=self.show_new_trade
        )
        self.new_trade_btn.grid(row=1, column=0, padx=20, pady=10)

        self.active_trades_btn = ctk.CTkButton(
            self.sidebar_frame, text="Active Trades", command=self.show_active_trades
        )
        self.active_trades_btn.grid(row=2, column=0, padx=20, pady=10)

        self.settings_btn = ctk.CTkButton(
            self.sidebar_frame, text="Settings", command=self.show_settings
        )
        self.settings_btn.grid(row=3, column=0, padx=20, pady=10)

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(
            self.sidebar_frame, values=["Dark", "Light", "System"],
            command=self.change_appearance_mode_event
        )
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 20))

        self.frames = {}
        self._trade_detail_frame = None
        self._trade_list_dirty = True
        self._trade_list_after_id = None

        self.after(0, self._startup_show_new_trade)

    def _ensure_frame(self, key, cls):
        if key not in self.frames or self.frames[key] is None:
            self.frames[key] = cls(self)
        return self.frames[key]

    def _startup_show_new_trade(self):
        self.show_new_trade()

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        for frame in self.frames.values():
            if frame is not None and hasattr(frame, 'update_theme'):
                frame.update_theme()

    def hide_all_frames(self):
        for frame in self.frames.values():
            if frame is not None:
                frame.grid_forget()
        if self._trade_detail_frame is not None:
            self._trade_detail_frame.grid_forget()
            self._trade_detail_frame.destroy()
            self._trade_detail_frame = None

    def show_new_trade(self):
        self.hide_all_frames()
        frame = self._ensure_frame("new_trade", self._import_trade_form)
        frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def _import_trade_form(self, master):
        from gui.trade_form import TradeForm
        return TradeForm(master)

    def show_active_trades(self):
        self.hide_all_frames()
        frame = self._ensure_frame("active_trades", self._import_trade_list)
        frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        if self._trade_list_dirty:
            if self._trade_list_after_id is not None:
                self.after_cancel(self._trade_list_after_id)
            self._trade_list_after_id = self.after(50, self._refresh_trade_list)

    def _import_trade_list(self, master):
        from gui.trade_list import TradeList
        return TradeList(master)

    def _refresh_trade_list(self):
        self._trade_list_after_id = None
        frame = self.frames.get("active_trades")
        if frame is not None:
            frame.refresh_data()
        self._trade_list_dirty = False

    def show_trade_detail(self, trade: dict):
        self.hide_all_frames()
        from gui.trade_detail import TradeDetail
        self._trade_detail_frame = TradeDetail(self, trade)
        self._trade_detail_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_settings(self):
        self.hide_all_frames()
        frame = self._ensure_frame("settings", self._import_settings_page)
        frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def _import_settings_page(self, master):
        from gui.settings_page import SettingsPage
        return SettingsPage(master)
