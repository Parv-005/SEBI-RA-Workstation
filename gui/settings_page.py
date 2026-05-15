import customtkinter as ctk
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
from utils.config_manager import load_config, save_config


class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=0, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(0, 20), sticky="w")

        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20)
        self.grid_rowconfigure(1, weight=1)
        self.scroll_frame.grid_columnconfigure(1, weight=1)

        self.config = self._load_config()

        # --- Telegram Settings ---
        self._add_section_header("Telegram API (Telethon)", row=0)
        tg = self.config.get("telegram", {})
        self.tg_api_id = self._add_entry("API ID:", tg.get("api_id", ""), row=1)
        self.tg_api_hash = self._add_entry("API Hash:", tg.get("api_hash", ""), row=2)
        self.tg_phone = self._add_entry("Phone Number (+91...):", tg.get("phone", ""), row=3)
        self.tg_group = self._add_entry("Group/Channel ID:", tg.get("group_id", ""), row=4)

        # --- Google Sheets Settings ---
        self._add_section_header("Google Sheets Integration", row=5)
        gs = self.config.get("google_sheets", {})
        self.gs_json = self._add_entry_with_browse("Service Account JSON path:", gs.get("service_account_json", ""), row=6)
        self.gs_sheet_id = self._add_entry("Spreadsheet ID:", gs.get("spreadsheet_id", ""), row=7)

        # --- AngelOne Settings ---
        self._add_section_header("AngelOne SmartAPI", row=8)
        ao = self.config.get("angelone", {})
        self.ao_api_key = self._add_entry("API Key:", ao.get("api_key", ""), row=9)
        self.ao_client_id = self._add_entry("Client ID:", ao.get("client_id", ""), row=10)
        self.ao_password = self._add_entry("Password (PIN):", ao.get("password", ""), row=11)
        self.ao_totp = self._add_entry("TOTP Secret:", ao.get("totp_secret", ""), row=12)

        # Save Button
        self.save_btn = ctk.CTkButton(self, text="Save Settings", font=ctk.CTkFont(weight="bold"), command=self._save_settings)
        self.save_btn.grid(row=2, column=0, pady=20)

    def _load_config(self):
        return load_config()

    def _add_section_header(self, text, row):
        lbl = ctk.CTkLabel(self.scroll_frame, text=text, font=ctk.CTkFont(size=18, weight="bold"))
        lbl.grid(row=row, column=0, columnspan=2, sticky="w", pady=(30, 10))

    def _add_entry(self, label_text, default_val, row):
        ctk.CTkLabel(self.scroll_frame, text=label_text).grid(row=row, column=0, sticky="w", padx=10, pady=5)
        entry = ctk.CTkEntry(self.scroll_frame, width=400)
        entry.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
        if default_val:
            entry.insert(0, str(default_val))
        return entry

    def _add_entry_with_browse(self, label_text, default_val, row):
        ctk.CTkLabel(self.scroll_frame, text=label_text).grid(row=row, column=0, sticky="w", padx=10, pady=5)

        container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        container.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
        container.grid_columnconfigure(0, weight=1)

        entry = ctk.CTkEntry(container, width=340)
        entry.grid(row=0, column=0, sticky="ew")
        if default_val:
            entry.insert(0, str(default_val))

        def browse(_entry=entry):
            path = filedialog.askopenfilename(
                title="Select Service Account JSON",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            )
            if path:
                _entry.delete(0, "end")
                _entry.insert(0, path)

        ctk.CTkButton(container, text="Browse…", width=80, command=browse).grid(
            row=0, column=1, padx=(8, 0)
        )
        return entry

    def _save_settings(self):
        config = self.config
        config["telegram"] = {
            "api_id": self.tg_api_id.get().strip(),
            "api_hash": self.tg_api_hash.get().strip(),
            "phone": self.tg_phone.get().strip(),
            "group_id": self.tg_group.get().strip()
        }
        config["google_sheets"] = {
            "service_account_json": self.gs_json.get().strip(),
            "spreadsheet_id": self.gs_sheet_id.get().strip(),
            "sheet_name": "Trades"
        }
        config["angelone"] = {
            "api_key": self.ao_api_key.get().strip(),
            "client_id": self.ao_client_id.get().strip(),
            "password": self.ao_password.get().strip(),
            "totp_secret": self.ao_totp.get().strip()
        }

        if save_config(config):
            messagebox.showinfo("Success", "Settings saved successfully!\nRestart app or re-connect services if required.")
        else:
            messagebox.showerror("Error", "Failed to save settings.")