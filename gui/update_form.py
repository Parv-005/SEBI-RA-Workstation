# pyrefly: ignore [missing-import]
import customtkinter as ctk
import tkinter.messagebox as messagebox
from datetime import datetime
from database.db_manager import update_trade, insert_trade_update
from database.updates_db import get_formatted_updates_text
from utils.logger import setup_logger
import threading
import re
from services.trade_service import compute_update_fields, BLOCK_ON_MISSING_EXIT_PRICE
from utils.constants import UPDATE_TYPES, UPDATE_TYPES_DICT
from services.results import BroadcastResult

logger = setup_logger("UpdateForm")

_controller = None

def _get_controller():
    global _controller
    if _controller is None:
        from controllers.trade_controller import TradeController
        _controller = TradeController()
    return _controller


class UpdateForm(ctk.CTkToplevel):
    def __init__(self, master, trade, on_success_callback=None, **kwargs):
        super().__init__(master, **kwargs)

        self.trade = trade
        self.on_success = on_success_callback

        self.title(f"Update Trade - {self.trade.get('stock_name', '?')} ({self.trade.get('action', '?')})")
        self.geometry("620x560")
        self.resizable(False, False)

        self.wait_visibility()
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        # ── Trade info banner ──────────────────────────────────────────────────
        info_text = (
            f"Segment: {self.trade.get('segment', '—')} | "
            f"Entry: {self.trade.get('entry_price', '—')} | "
            f"Target: {self.trade.get('target', '—')} | "
            f"SL: {self.trade.get('stop_loss', '—')}"
        )
        ctk.CTkLabel(self, text=info_text, font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, pady=20, padx=20
        )

        # ── Update type selector ───────────────────────────────────────────────
        ctk.CTkLabel(self, text="Select Update Type:").grid(
            row=1, column=0, sticky="w", padx=40
        )
        self.update_type_var = ctk.StringVar(value=UPDATE_TYPES[0] if UPDATE_TYPES else "")
        self.update_type_menu = ctk.CTkOptionMenu(
            self,
            variable=self.update_type_var,
            values=UPDATE_TYPES,
            command=self.on_update_type_change,
        )
        self.update_type_menu.grid(row=2, column=0, sticky="ew", padx=40, pady=(5, 10))

        # ── Close trade indicator ──────────────────────────────────────────────
        self._close_trade_var = ctk.BooleanVar(value=False)
        self._close_trade_cb = ctk.CTkCheckBox(
            self,
            text="Closes Trade",
            variable=self._close_trade_var,
            state="disabled",   # read-only indicator; driven by config
            fg_color="#dc3545",
            checkmark_color="white",
        )
        self._close_trade_cb.grid(row=3, column=0, sticky="w", padx=40, pady=(0, 10))

        # ── Dynamic input fields frame ─────────────────────────────────────────
        self.dynamic_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dynamic_frame.grid(row=4, column=0, sticky="nsew", padx=40)
        self.dynamic_frame.grid_columnconfigure(1, weight=1)

        self.dynamic_inputs: dict[str, ctk.CTkEntry] = {}
        # Entry widget used when close_trade=True but exit_price not in set fields
        self._extra_exit_entry: ctk.CTkEntry | None = None

        # ── Remarks / message textbox ──────────────────────────────────────────
        ctk.CTkLabel(self, text="Message:").grid(
            row=5, column=0, sticky="w", padx=40, pady=(20, 5)
        )
        self.remarks_entry = ctk.CTkTextbox(self, height=80)
        self.remarks_entry.grid(row=6, column=0, sticky="ew", padx=40)

        # ── Buttons ────────────────────────────────────────────────────────────
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=7, column=0, pady=20, padx=40, sticky="e")

        self.cancel_btn = ctk.CTkButton(
            self.btn_frame, text="Cancel", fg_color="gray", command=self.destroy
        )
        self.cancel_btn.grid(row=0, column=0, padx=10)

        self.submit_btn = ctk.CTkButton(
            self.btn_frame, text="Broadcast Update", command=self.submit_update
        )
        self.submit_btn.grid(row=0, column=1)

        self.on_update_type_change(self.update_type_var.get())

    # ── Dynamic field rendering ────────────────────────────────────────────────

    def on_update_type_change(self, update_type: str):
        """Rebuild dynamic input fields based on the selected update type's config."""
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()
        self.dynamic_inputs = {}
        self._extra_exit_entry = None

        update_info = UPDATE_TYPES_DICT.get(update_type, {})
        close_trade: bool = update_info.get("close_trade", False)
        set_fields: dict = update_info.get("set", {})
        message_template: str = update_info.get("message", "")

        # Update the close-trade indicator checkbox
        self._close_trade_var.set(close_trade)

        # Extract <Placeholder> names from message template
        template_fields = re.findall(r"<(.*?)>", message_template)

        for i, field in enumerate(template_fields):
            lbl = ctk.CTkLabel(self.dynamic_frame, text=f"{field}:")
            lbl.grid(row=i, column=0, sticky="w", pady=8)
            entry = ctk.CTkEntry(self.dynamic_frame, placeholder_text="0.00")
            entry.grid(row=i, column=1, sticky="ew", padx=(10, 0), pady=8)

            entry.bind("<KeyRelease>", self._make_message_updater(message_template))
            self.dynamic_inputs[field] = entry

        # If close_trade=True and exit_price is NOT already covered by a set field,
        # show an extra mandatory "Exit Price" input.
        exit_price_in_set = "exit_price" in set_fields
        if close_trade and not exit_price_in_set:
            row_idx = len(template_fields)
            lbl = ctk.CTkLabel(
                self.dynamic_frame,
                text="Exit Price:  ✱",
                text_color="#f0ad4e",
            )
            lbl.grid(row=row_idx, column=0, sticky="w", pady=8)
            self._extra_exit_entry = ctk.CTkEntry(
                self.dynamic_frame,
                placeholder_text="required — closing price",
                border_color="#f0ad4e",
            )
            self._extra_exit_entry.grid(row=row_idx, column=1, sticky="ew", padx=(10, 0), pady=8)

        # Seed the remarks / message textbox with the template
        self.remarks_entry.delete("1.0", "end")
        self.remarks_entry.insert("1.0", message_template)

    def _make_message_updater(self, template: str):
        """Return a KeyRelease callback that live-fills the message textbox."""
        def _cb(event=None):
            msg = template
            for f_name, f_entry in self.dynamic_inputs.items():
                val = f_entry.get().strip() or f"<{f_name}>"
                msg = msg.replace(f"<{f_name}>", val)
            self.remarks_entry.delete("1.0", "end")
            self.remarks_entry.insert("1.0", msg)
        return _cb

    # ── Submit ─────────────────────────────────────────────────────────────────

    def submit_update(self):
        update_type = self.update_type_var.get()
        remarks = self.remarks_entry.get("1.0", "end-1c").strip()
        dynamic_values = {k: v.get().strip() for k, v in self.dynamic_inputs.items()}

        # Include extra exit price if present
        if self._extra_exit_entry is not None:
            dynamic_values["Exit Price"] = self._extra_exit_entry.get().strip()

        # ── Exit price validation when closing a trade ─────────────────────────
        update_info = UPDATE_TYPES_DICT.get(update_type, {})
        close_trade: bool = update_info.get("close_trade", False)
        set_fields: dict = update_info.get("set", {})

        if close_trade:
            # Find the dynamic key that maps to exit_price (from set fields or extra input)
            exit_price_key = None
            for field, placeholder in set_fields.items():
                if field == "exit_price":
                    exit_price_key = placeholder.strip("<>")
                    break
            if exit_price_key is None:
                exit_price_key = "Exit Price"   # fallback for extra entry

            exit_price_val = dynamic_values.get(exit_price_key, "")
            if not exit_price_val:
                if BLOCK_ON_MISSING_EXIT_PRICE:
                    messagebox.showerror(
                        "Validation Error",
                        "Exit Price is required when closing a trade.\n"
                        "Please enter the exit price before submitting.",
                    )
                    return
                else:
                    if not messagebox.askyesno(
                        "Exit Price Missing",
                        "Exit Price is empty. This trade will be closed without recording an exit price.\n\n"
                        "Continue anyway?",
                    ):
                        return

        try:
            trade_updates, old_value, new_value, update_data_dict = compute_update_fields(
                self.trade, update_type, dynamic_values, remarks
            )
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            self.submit_btn.configure(text="Broadcast Update", state="normal")
            return

        try:
            self.submit_btn.configure(text="Processing...", state="disabled")

            # Save update record
            insert_trade_update(
                {
                    "trade_code": self.trade.get("trade_code"),
                    "update_type": update_type,
                    "message": remarks,
                    "old_value": old_value,
                    "new_value": new_value,
                }
            )

            # Build fresh updates-column text after inserting the new record
            trade_code = self.trade.get("trade_code")
            trade_updates["updates"] = get_formatted_updates_text(trade_code)

            # Persist trade field changes
            if trade_updates:
                update_trade(trade_code, trade_updates)

            update_data_dict["_trade_updates"] = trade_updates

            def process_update():
                result = _get_controller().broadcast_update(self.trade, update_data_dict)
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
        elif result.sheets_success is not True:
            err_msg = result.sheets_success if isinstance(result.sheets_success, str) else "Failed"
            errors.append(f"Google Sheets: {err_msg}")

        if result.telegram_success in ("not_configured", "not_authorized"):
            reason = "Not configured" if result.telegram_success == "not_configured" else "OTP required — sign in via Settings"
            errors.append(f"Telegram: {reason}")
        elif result.telegram_success is not True:
            err_msg = result.telegram_success if isinstance(result.telegram_success, str) else "Failed"
            errors.append(f"Telegram: {err_msg}")

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