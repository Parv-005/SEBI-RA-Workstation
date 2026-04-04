import customtkinter as ctk
import tkinter.messagebox as messagebox
from database.db_manager import update_trade, insert_trade_update
from utils.logger import setup_logger
import asyncio
import threading
from services.image_generator import ImageGenerator
from services.telegram_service import TelegramService
from services.google_sheets_service import GoogleSheetsService

logger = setup_logger("UpdateForm")

class UpdateForm(ctk.CTkToplevel):
    def __init__(self, master, trade, on_success_callback=None, **kwargs):
        super().__init__(master, **kwargs)

        self.trade = trade
        self.on_success = on_success_callback

        self.title(f"Update Trade - {trade['stock_name']} ({trade['action']})")
        self.geometry("600x500")
        self.resizable(False, False)

        # Make it modal
        # self.attributes("-topmost", True)
        self.wait_visibility()
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        # Header Info
        info_text = (
            f"Segment: {trade['segment']} | "
            f"Entry: {trade['entry_price']} | "
            f"Target: {trade['target']} | "
            f"SL: {trade['stop_loss']}"
        )
        ctk.CTkLabel(self, text=info_text, font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=20, padx=20)

        # Update Type Dropdown
        ctk.CTkLabel(self, text="Select Update Type:").grid(row=1, column=0, sticky="w", padx=40)
        self.update_type_var = ctk.StringVar(value="TARGET_HIT")
        self.update_type_menu = ctk.CTkOptionMenu(
            self, variable=self.update_type_var,
            values=["TARGET_HIT", "SL_HIT", "PARTIAL_PROFIT", "TRAIL_SL", "COST_TO_COST", "EXIT", "MODIFY_TARGET", "MODIFY_SL"],
            command=self.on_update_type_change
        )
        self.update_type_menu.grid(row=2, column=0, sticky="ew", padx=40, pady=(5, 20))

        # Dynamic Fields Frame
        self.dynamic_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dynamic_frame.grid(row=3, column=0, sticky="nsew", padx=40)
        self.dynamic_frame.grid_columnconfigure(1, weight=1)

        # Input variables
        self.new_value_label = ctk.CTkLabel(self.dynamic_frame, text="")
        self.new_value_entry = ctk.CTkEntry(self.dynamic_frame, placeholder_text="0.00")

        # Remarks
        ctk.CTkLabel(self, text="Remarks / Details for Message:").grid(row=4, column=0, sticky="w", padx=40, pady=(20, 5))
        self.remarks_entry = ctk.CTkTextbox(self, height=80)
        self.remarks_entry.grid(row=5, column=0, sticky="ew", padx=40)

        # Buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=6, column=0, pady=30, padx=40, sticky="e")

        self.cancel_btn = ctk.CTkButton(self.btn_frame, text="Cancel", fg_color="gray", command=self.destroy)
        self.cancel_btn.grid(row=0, column=0, padx=10)

        self.submit_btn = ctk.CTkButton(self.btn_frame, text="Broadcast Update", command=self.submit_update)
        self.submit_btn.grid(row=0, column=1)

        # Initialize UI state
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

        # Auto-fill defaults for remarks based on type
        defaults = {
            "TARGET_HIT": "Target Achieved! Book Profits.",
            "SL_HIT": "Stop Loss Hit. Exit trade.",
            "COST_TO_COST": "Trail SL to Cost. Hold rest.",
            "PARTIAL_PROFIT": "Book partial profits here. Trail SL for rest.",
            "TRAIL_SL": "Update Stop Loss to protect profits.",
            "EXIT": "Exit position at CMP.",
        }
        self.remarks_entry.delete("1.0", "end")
        self.remarks_entry.insert("1.0", defaults.get(update_type, ""))

    def submit_update(self):
        update_type = self.update_type_var.get()
        remarks = self.remarks_entry.get("1.0", "end-1c").strip()
        new_val_str = self.new_value_entry.get().strip()

        # Database updates
        trade_updates = {}
        old_value = None
        new_value = None

        try:
            if update_type in ["TRAIL_SL", "MODIFY_SL"]:
                if not new_val_str: raise ValueError("New Stop Loss is required.")
                new_sl = float(new_val_str)
                old_value = {"stop_loss": self.trade["stop_loss"]}
                new_value = {"stop_loss": new_sl}
                trade_updates["stop_loss"] = new_sl

            elif update_type == "MODIFY_TARGET":
                if not new_val_str: raise ValueError("New Target is required.")
                new_tgt = float(new_val_str)
                old_value = {"target": self.trade["target"]}
                new_value = {"target": new_tgt}
                trade_updates["target"] = new_tgt

            elif update_type == "TARGET_HIT":
                trade_updates["status"] = "TARGET_HIT"

            elif update_type == "SL_HIT":
                trade_updates["status"] = "SL_HIT"

            elif update_type == "EXIT":
                trade_updates["status"] = "EXITED"
                if new_val_str:
                    new_value = {"exit_price": float(new_val_str)}

            elif update_type == "COST_TO_COST":
                old_value = {"stop_loss": self.trade["stop_loss"]}
                new_value = {"stop_loss": self.trade["entry_price"]}
                trade_updates["stop_loss"] = self.trade["entry_price"]

            elif update_type == "PARTIAL_PROFIT":
                if new_val_str:
                    new_value = {"booked_price": float(new_val_str)}

            # Recalculate Risk & Reward if SL or Target was modified
            if update_type in ["TRAIL_SL", "MODIFY_SL", "MODIFY_TARGET", "COST_TO_COST"]:
                entry = float(self.trade.get("entry_price", 0))
                current_tgt = float(self.trade.get("target", 0))
                current_sl = float(self.trade.get("stop_loss", 0))

                mod_tgt = trade_updates.get("target", current_tgt)
                mod_sl = trade_updates.get("stop_loss", current_sl)
                action = self.trade.get("action", "LONG")

                if action == "LONG":
                    calc_reward = mod_tgt - entry
                    calc_risk = entry - mod_sl
                else:
                    calc_reward = entry - mod_tgt
                    calc_risk = mod_sl - entry

                trade_updates["reward"] = calc_reward
                trade_updates["risk"] = calc_risk

                if entry > 0:
                    trade_updates["reward_pct"] = (calc_reward / entry) * 100
                    trade_updates["risk_pct"] = (calc_risk / entry) * 100
                else:
                    trade_updates["reward_pct"] = 0.0
                    trade_updates["risk_pct"] = 0.0

                if calc_risk <= 0 or calc_reward < 0:
                    trade_updates["risk_reward"] = ""
                else:
                    trade_updates["risk_reward"] = f"1 : {(calc_reward / calc_risk):.2f}"

            # 1. Save to SQLite
            self.submit_btn.configure(text="Processing...", state="disabled")

            # Log update event
            insert_trade_update({
                "trade_id": self.trade["id"],
                "update_type": update_type,
                "details": remarks,
                "old_value": old_value,
                "new_value": new_value
            })

            # Apply changes to trade
            if trade_updates:
                update_trade(self.trade["id"], trade_updates)

            # Integrate Services
            update_data_dict = {
                "update_type": update_type,
                "details": remarks,
                "old_value": old_value,
                "new_value": new_value
            }
            # Optional: propagate recalculations dynamically so updates are fully seen across platforms
            for k in ["reward", "risk", "reward_pct", "risk_pct", "risk_reward"]:
                if k in trade_updates:
                    update_data_dict[k] = trade_updates[k]

            def process_update():
                # 2. Generate Image
                img_gen = ImageGenerator()
                img_path = img_gen.generate_update_image(self.trade, update_data_dict)

                # 3. Update Google Sheets
                try:
                    gs = GoogleSheetsService()
                    if gs.is_configured():
                        gs.update_trade_row(self.trade["id"], update_data_dict, trade_updates)
                except Exception as e:
                    logger.error(f"Sheets Update Error: {e}", exc_info=True)

                # 4. Send Telegram Update
                try:
                    tg = TelegramService()
                    if tg.is_configured():
                        async def send_tg():
                            await tg.connect()
                            from utils.message_formatter import format_trade_update
                            msg = format_trade_update(self.trade, update_data_dict)
                            await tg.send_update_message(msg, img_path)
                            await tg.disconnect()

                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(send_tg())
                        loop.close()
                except Exception as e:
                    logger.error(f"Telegram Update Error: {e}", exc_info=True)

                self.after(0, self._on_success)

            threading.Thread(target=process_update, daemon=True).start()

        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            self.submit_btn.configure(text="Broadcast Update", state="normal")
        except Exception as e:
            logger.error(f"Failed to process update form: {e}", exc_info=True)
            messagebox.showerror("Database Error", f"Failed to save update: {e}")
            self.submit_btn.configure(text="Broadcast Update", state="normal")

    def _on_success(self):
        messagebox.showinfo("Success", "Update saved and broadcasted successfully!")
        if self.on_success:
            self.on_success()
        self.destroy()
