import customtkinter as ctk
import tkinter.messagebox as messagebox
from datetime import datetime
from database.db_manager import update_trade, insert_trade_update
from utils.logger import setup_logger
import threading
from services.trade_service import (
    calculate_risk_reward,
    compute_update_fields,
    UPDATE_TYPES,
    UPDATE_TYPE_DEFAULTS,
)
from controllers.trade_controller import TradeController
from services.results import BroadcastResult

logger = setup_logger("UpdateForm")

controller = TradeController()


class UpdateForm(ctk.CTkToplevel):
    def __init__(self, master, trade, on_success_callback=None, **kwargs):
        super().__init__(master, **kwargs)

        self.trade = trade
        self.on_success = on_success_callback

        self.title(f"Update Trade - {self.trade.get('stock_name', '?')} ({self.trade.get('action', '?')})")
        self.geometry("600x500")
        self.resizable(False, False)

        self.wait_visibility()
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        info_text = (
            f"Segment: {self.trade.get('segment', '—')} | "
            f"Entry: {self.trade.get('entry_price', '—')} | "
            f"Target: {self.trade.get('target', '—')} | "
            f"SL: {self.trade.get('stop_loss', '—')}"
        )
        ctk.CTkLabel(self, text=info_text, font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, pady=20, padx=20
        )

        ctk.CTkLabel(self, text="Select Update Type:").grid(
            row=1, column=0, sticky="w", padx=40
        )
        self.update_type_var = ctk.StringVar(value="TARGET_HIT")
        self.update_type_menu = ctk.CTkOptionMenu(
            self,
            variable=self.update_type_var,
            values=UPDATE_TYPES,
            command=self.on_update_type_change,
        )
        self.update_type_menu.grid(row=2, column=0, sticky="ew", padx=40, pady=(5, 20))

        self.dynamic_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dynamic_frame.grid(row=3, column=0, sticky="nsew", padx=40)
        self.dynamic_frame.grid_columnconfigure(1, weight=1)

        self.new_value_label = ctk.CTkLabel(self.dynamic_frame, text="")
        self.new_value_entry = ctk.CTkEntry(self.dynamic_frame, placeholder_text="0.00")

        ctk.CTkLabel(self, text="Remarks / Details for Message:").grid(
            row=4, column=0, sticky="w", padx=40, pady=(20, 5)
        )
        self.remarks_entry = ctk.CTkTextbox(self, height=80)
        self.remarks_entry.grid(row=5, column=0, sticky="ew", padx=40)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=6, column=0, pady=30, padx=40, sticky="e")

        self.cancel_btn = ctk.CTkButton(
            self.btn_frame, text="Cancel", fg_color="gray", command=self.destroy
        )
        self.cancel_btn.grid(row=0, column=0, padx=10)

        self.submit_btn = ctk.CTkButton(
            self.btn_frame, text="Broadcast Update", command=self.submit_update
        )
        self.submit_btn.grid(row=0, column=1)

        self.on_update_type_change(self.update_type_var.get())

    def on_update_type_change(self, update_type):
        self.new_value_label.grid_forget()
        self.new_value_entry.grid_forget()
        self.new_value_entry.delete(0, "end")

        if update_type in ["TRAIL_SL", "MODIFY_SL"]:
            self.new_value_label.configure(text="New Stop Loss:")
            self.new_value_label.grid(row=0, column=0, sticky="w", pady=10)
            self.new_value_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=10)
        elif update_type == "MODIFY_TARGET":
            self.new_value_label.configure(text="New Target:")
            self.new_value_label.grid(row=0, column=0, sticky="w", pady=10)
            self.new_value_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=10)
        elif update_type in ["EXIT", "PARTIAL_PROFIT"]:
            self.new_value_label.configure(text="Exit/Booked Price:")
            self.new_value_label.grid(row=0, column=0, sticky="w", pady=10)
            self.new_value_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=10)

        self.remarks_entry.delete("1.0", "end")
        self.remarks_entry.insert("1.0", UPDATE_TYPE_DEFAULTS.get(update_type, ""))

    def submit_update(self):
        update_type = self.update_type_var.get()
        remarks = self.remarks_entry.get("1.0", "end-1c").strip()
        new_val_str = self.new_value_entry.get().strip()

        try:
            trade_updates, old_value, new_value, update_data_dict = compute_update_fields(
                self.trade, update_type, new_val_str, remarks
            )
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            self.submit_btn.configure(text="Broadcast Update", state="normal")
            return

        try:
            self.submit_btn.configure(text="Processing...", state="disabled")

            insert_trade_update(
                {
                    "trade_id": self.trade.get("id"),
                    "update_type": update_type,
                    "details": remarks,
                    "old_value": old_value,
                    "new_value": new_value,
                }
            )

            if trade_updates:
                update_trade(self.trade.get("id"), trade_updates)

            update_data_dict["_trade_updates"] = trade_updates

            def process_update():
                result = controller.broadcast_update(self.trade, update_data_dict)
                self.after(0, self._on_update_complete, result)

            threading.Thread(target=process_update, daemon=True).start()

        except Exception as e:
            logger.error(f"Failed to process update form: {e}", exc_info=True)
            messagebox.showerror("Database Error", f"Failed to save update: {e}")
            self.submit_btn.configure(text="Broadcast Update", state="normal")

    def _on_update_complete(self, result: BroadcastResult):
        errors = []

        if result.sheets_success == "not_configured":
            errors.append("Google Sheets: Not configured")
        elif not result.sheets_success:
            errors.append("Google Sheets: Failed")

        if result.telegram_success == "not_configured":
            errors.append("Telegram: Not configured")
        elif not result.telegram_success:
            errors.append("Telegram: Failed")

        if not errors:
            messagebox.showinfo("Success", "Update saved and broadcasted successfully!")
        elif len(errors) == 2:
            messagebox.showwarning(
                "Partial Success",
                "Update saved to database, but broadcasting failed:\n\n"
                + "\n".join(f"• {e}" for e in errors)
                + "\n\nConfigure services in Settings to enable broadcasting.",
            )
        else:
            messagebox.showwarning(
                "Partial Success",
                "Update saved, but some services failed:\n\n"
                + "\n".join(f"• {e}" for e in errors),
            )

        if self.on_success:
            self.on_success()
        self.destroy()