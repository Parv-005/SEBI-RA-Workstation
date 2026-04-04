import customtkinter as ctk
import os
import sys

from gui.trade_form import TradeForm
from gui.trade_list import TradeList
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

        # Configure grid layout (1x2)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Create sidebar frame
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, text="RA Automation",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Sidebar Buttons
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

        # Create main content frames
        self.frames = {}

        self.frames["new_trade"] = TradeForm(self)
        self.frames["active_trades"] = TradeList(self)

        # Placeholder for settings
        from gui.settings_page import SettingsPage
        self.frames["settings"] = SettingsPage(self)

        # Show default frame
        self.show_new_trade()

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def hide_all_frames(self):
        for frame in self.frames.values():
            frame.grid_forget()

    def show_new_trade(self):
        self.hide_all_frames()
        self.frames["new_trade"].grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_active_trades(self):
        self.hide_all_frames()
        self.frames["active_trades"].refresh_data()
        self.frames["active_trades"].grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_settings(self):
        self.hide_all_frames()
        self.frames["settings"].grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
