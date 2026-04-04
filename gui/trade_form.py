import customtkinter as ctk
import tkinter.messagebox as messagebox
from database.db_manager import insert_trade
from utils.logger import setup_logger
import asyncio
import threading
from services.image_generator import ImageGenerator
from services.telegram_service import TelegramService
from services.google_sheets_service import GoogleSheetsService

logger = setup_logger("TradeForm")

# ─────────────────── helpers ────────────────────
def _section_label(parent, text, row, col=0, colspan=4, pady_top=20):
    """A subtle section divider label."""
    lbl = ctk.CTkLabel(
        parent, text=f"  {text}",
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color=("gray50", "gray60"),
        anchor="w",
    )
    lbl.grid(row=row, column=col, columnspan=colspan,
             padx=10, pady=(pady_top, 2), sticky="ew")
    return lbl

def _field_label(parent, text, row, col, pady_top=12):
    lbl = ctk.CTkLabel(parent, text=text, anchor="w")
    lbl.grid(row=row, column=col, padx=(14, 4), pady=(pady_top, 0), sticky="w")
    return lbl

# ─────────────────── main class ────────────────────

class TradeForm(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=0, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)

        # ── Title ──────────────────────────────────────────────
        self.title_label = ctk.CTkLabel(
            self, text="New Trade Entry",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(0, 10), sticky="w")

        # ── Scrollable Form ────────────────────────────────────
        self.form_frame = ctk.CTkScrollableFrame(self)
        self.form_frame.grid(row=1, column=0, sticky="nsew")
        self.grid_rowconfigure(1, weight=1)

        ff = self.form_frame
        ff.grid_columnconfigure(0, weight=0, minsize=130)
        ff.grid_columnconfigure(1, weight=1)
        ff.grid_columnconfigure(2, weight=0, minsize=130)
        ff.grid_columnconfigure(3, weight=1)

        r = 0  # running row counter

        # ════════════════════════════════════════
        # SECTION: Basic Info
        # ════════════════════════════════════════
        _section_label(ff, "TRADE IDENTITY", r, pady_top=10); r += 1

        # Segment & Action
        _field_label(ff, "Segment:", r, 0)
        self.segment_var = ctk.StringVar(value="Cash")
        self.segment_menu = ctk.CTkOptionMenu(
            ff, variable=self.segment_var,
            values=["Cash", "F&O", "MCX", "Currency", "Index"]
        )
        self.segment_menu.grid(row=r, column=1, padx=8, pady=(12, 0), sticky="ew")

        _field_label(ff, "Action:", r, 2)
        self.action_var = ctk.StringVar(value="LONG")
        self.action_menu = ctk.CTkOptionMenu(
            ff, variable=self.action_var,
            values=["LONG", "SHORT"],
            fg_color="#28a745", button_color="#218838", button_hover_color="#1e7e34"
        )
        self.action_menu.grid(row=r, column=3, padx=8, pady=(12, 0), sticky="ew")
        r += 1

        # Stock Name
        _field_label(ff, "Stock / Symbol:", r, 0)
        self.stock_entry = ctk.CTkEntry(ff, placeholder_text="e.g. RELIANCE, BANKNIFTY")
        self.stock_entry.grid(row=r, column=1, columnspan=2, padx=8, pady=(12, 0), sticky="ew")
        self.fetch_cmp_btn = ctk.CTkButton(ff, text="Fetch CMP", command=self.fetch_cmp)
        self.fetch_cmp_btn.grid(row=r, column=3, padx=8, pady=(12, 0), sticky="ew")
        r += 1

        # Trade Type
        _field_label(ff, "Trade Type:", r, 0)
        self.trade_type_var = ctk.StringVar(value="Intraday")
        self.trade_type_menu = ctk.CTkOptionMenu(
            ff, variable=self.trade_type_var,
            values=["Intraday", "BTST", "Positional", "Short-term", "Long-term"]
        )
        self.trade_type_menu.grid(row=r, column=1, padx=8, pady=(12, 0), sticky="ew")

        # Approx Time
        _field_label(ff, "Approx Time:", r, 2)
        self.approx_time_entry = ctk.CTkEntry(ff, placeholder_text="e.g. 2-3 days, 1 week")
        self.approx_time_entry.grid(row=r, column=3, padx=8, pady=(12, 0), sticky="ew")
        r += 1

        # ════════════════════════════════════════
        # SECTION: Price Levels
        # ════════════════════════════════════════
        _section_label(ff, "PRICE LEVELS", r); r += 1

        # Entry Price & CMP placeholder
        _field_label(ff, "Entry Price:", r, 0)
        self.price_var = ctk.StringVar()
        self.price_entry = ctk.CTkEntry(ff, textvariable=self.price_var, placeholder_text="0.00")
        self.price_entry.grid(row=r, column=1, padx=8, pady=(12, 0), sticky="ew")

        _field_label(ff, "Target Price:", r, 2)
        self.target_var = ctk.StringVar()
        self.target_entry = ctk.CTkEntry(ff, textvariable=self.target_var, placeholder_text="0.00")
        self.target_entry.grid(row=r, column=3, padx=8, pady=(12, 0), sticky="ew")
        r += 1

        # Entry Zone
        _field_label(ff, "Zone Start:", r, 0)
        self.zone_start_entry = ctk.CTkEntry(ff, placeholder_text="Lower bound")
        self.zone_start_entry.grid(row=r, column=1, padx=8, pady=(12, 0), sticky="ew")

        _field_label(ff, "Zone End:", r, 2)
        self.zone_end_entry = ctk.CTkEntry(ff, placeholder_text="Upper bound")
        self.zone_end_entry.grid(row=r, column=3, padx=8, pady=(12, 0), sticky="ew")
        r += 1

        # Stop Loss
        _field_label(ff, "Stop Loss:", r, 0)
        self.sl_var = ctk.StringVar()
        self.sl_entry = ctk.CTkEntry(ff, textvariable=self.sl_var, placeholder_text="0.00")
        self.sl_entry.grid(row=r, column=1, padx=8, pady=(12, 0), sticky="ew")
        r += 1

        # ════════════════════════════════════════
        # SECTION: Risk & Reward Analysis
        # ════════════════════════════════════════
        _section_label(ff, "RISK & REWARD ANALYSIS", r); r += 1

        _field_label(ff, "Reward:", r, 0)
        self.reward_var = ctk.StringVar(value="0.00")
        self.reward_display = ctk.CTkEntry(
            ff, textvariable=self.reward_var, state="disabled", fg_color=("gray90", "gray20"), text_color=("gray30", "gray70")
        )
        self.reward_display.grid(row=r, column=1, padx=8, pady=(12, 0), sticky="ew")

        _field_label(ff, "Risk:", r, 2)
        self.risk_var = ctk.StringVar(value="0.00")
        self.risk_display = ctk.CTkEntry(
            ff, textvariable=self.risk_var, state="disabled", fg_color=("gray90", "gray20"), text_color=("gray30", "gray70")
        )
        self.risk_display.grid(row=r, column=3, padx=8, pady=(12, 0), sticky="ew")
        r += 1

        _field_label(ff, "Reward %:", r, 0)
        self.reward_pct_var = ctk.StringVar(value="0.00%")
        self.reward_pct_display = ctk.CTkEntry(
            ff, textvariable=self.reward_pct_var, state="disabled", fg_color=("gray90", "gray20"), text_color=("gray30", "gray70")
        )
        self.reward_pct_display.grid(row=r, column=1, padx=8, pady=(12, 0), sticky="ew")

        _field_label(ff, "Risk %:", r, 2)
        self.risk_pct_var = ctk.StringVar(value="0.00%")
        self.risk_pct_display = ctk.CTkEntry(
            ff, textvariable=self.risk_pct_var, state="disabled", fg_color=("gray90", "gray20"), text_color=("gray30", "gray70")
        )
        self.risk_pct_display.grid(row=r, column=3, padx=8, pady=(12, 0), sticky="ew")
        r += 1

        _field_label(ff, "Risk : Reward:", r, 0)
        self.rr_var = ctk.StringVar(value="—")
        self.rr_display = ctk.CTkEntry(
            ff, textvariable=self.rr_var, state="disabled", fg_color=("gray90", "gray20"), text_color=("gray30", "gray70")
        )
        self.rr_display.grid(row=r, column=1, columnspan=3, padx=8, pady=(12, 0), sticky="ew")
        r += 1

        # ════════════════════════════════════════
        # SECTION: Notes
        # ════════════════════════════════════════
        _section_label(ff, "NOTES", r); r += 1

        _field_label(ff, "Remarks:", r, 0)
        self.remarks_entry = ctk.CTkTextbox(ff, height=80)
        self.remarks_entry.grid(row=r, column=1, columnspan=3, padx=8, pady=(12, 0), sticky="ew")
        r += 1

        # ── Submit ──────────────────────────────────────────────
        self.submit_btn = ctk.CTkButton(
            ff, text="✦  Submit Trade & Broadcast",
            font=ctk.CTkFont(size=16, weight="bold"), height=52,
            command=self.submit_trade
        )
        self.submit_btn.grid(row=r, column=0, columnspan=4, padx=10, pady=(32, 24), sticky="ew")

        # ── Wire up events ──────────────────────────────────────
        self.action_var.trace_add("write", self.update_action_color)
        self.price_var.trace_add("write", self._auto_calc_rr)
        self.target_var.trace_add("write", self._auto_calc_rr)
        self.sl_var.trace_add("write", self._auto_calc_rr)

    # ─────────────────── UI helpers ────────────────────

    def update_action_color(self, *args):
        if self.action_var.get() == "LONG":
            self.action_menu.configure(
                fg_color="#28a745", button_color="#218838", button_hover_color="#1e7e34"
            )
        else:
            self.action_menu.configure(
                fg_color="#dc3545", button_color="#c82333", button_hover_color="#bd2130"
            )

    def _auto_calc_rr(self, *args):
        """Auto-calculate and display the Risk:Reward ratio."""
        try:
            entry = float(self.price_var.get())
            target = float(self.target_var.get())
            sl = float(self.sl_var.get())

            if self.action_var.get() == "LONG":
                reward = target - entry
                risk = entry - sl
            else:  # SHORT
                reward = entry - target
                risk = sl - entry

            self.reward_var.set(f"{reward:.2f}")
            self.risk_var.set(f"{risk:.2f}")

            if entry > 0:
                self.reward_pct_var.set(f"{(reward / entry) * 100:.2f}%")
                self.risk_pct_var.set(f"{(risk / entry) * 100:.2f}%")
            else:
                self.reward_pct_var.set("0.00%")
                self.risk_pct_var.set("0.00%")

            if risk <= 0 or reward < 0:
                self.rr_var.set("—")
                return

            ratio = reward / risk
            self.rr_var.set(f"1 : {ratio:.2f}")
        except (ValueError, ZeroDivisionError):
            self.rr_var.set("—")
            self.reward_var.set("0.00")
            self.risk_var.set("0.00")
            self.reward_pct_var.set("0.00%")
            self.risk_pct_var.set("0.00%")

    # ─────────────────── Fetch CMP ────────────────────

    def fetch_cmp(self):
        symbol = self.stock_entry.get().strip().upper()
        if not symbol:
            messagebox.showwarning("Warning", "Please enter a Stock/Symbol name first.")
            return

        self.fetch_cmp_btn.configure(text="Searching...", state="disabled")
        segment = self.segment_var.get()

        def background_fetch():
            try:
                from services.angelone_service import AngelOneService
                ao = AngelOneService()

                if not ao.is_configured():
                    self.after(0, lambda: messagebox.showwarning(
                        "Not Configured",
                        "AngelOne API credentials are not configured in Settings."
                    ))
                    return

                results = ao.search_symbol(symbol, segment=segment)
                if not results:
                    self.after(0, lambda: messagebox.showwarning(
                        "Not Found", f"Could not find symbol '{symbol}' in {segment} segment."
                    ))
                    return

                best_match = None
                for res in results:
                    if res.get('tradingsymbol', '').upper() == symbol or res.get('name', '').upper() == symbol:
                        best_match = res
                        break
                if not best_match:
                    best_match = results[0]

                token = best_match.get("symboltoken")
                exchange = best_match.get("exch_seg")
                actual_symbol = best_match.get("tradingsymbol")

                self.after(0, lambda: self.fetch_cmp_btn.configure(text="Fetching LTP..."))

                ltp = ao.get_ltp(actual_symbol, exchange, token)

                if ltp is not None:
                    def update_ui():
                        self.stock_entry.delete(0, "end")
                        self.stock_entry.insert(0, actual_symbol)
                        self.price_var.set(str(ltp))
                        messagebox.showinfo("Success", f"CMP for {actual_symbol} is ₹{ltp}")
                    self.after(0, update_ui)
                else:
                    self.after(0, lambda: messagebox.showerror(
                        "Error", f"Failed to fetch live price for {actual_symbol}"
                    ))

            except Exception as e:
                logger.error(f"Error in fetch_cmp: {e}", exc_info=True)
                err_msg = str(e)
                self.after(0, lambda: messagebox.showerror("API Error", f"An error occurred: {err_msg}"))
            finally:
                self.after(0, lambda: self.fetch_cmp_btn.configure(text="Fetch CMP", state="normal"))

        threading.Thread(target=background_fetch, daemon=True).start()

    # ─────────────────── Submit ────────────────────

    def submit_trade(self):
        try:
            action_map = {"LONG": "BUY", "SHORT": "SELL"}

            def _float_or_none(val):
                v = val.strip() if val else ""
                return float(v) if v else None

            def _float_or_zero(val_str):
                try:
                    return float(val_str.replace('%', ''))
                except ValueError:
                    return 0.0

            trade_data = {
                "stock_name":  self.stock_entry.get().strip().upper(),
                "segment":     self.segment_var.get(),
                "action":      action_map.get(self.action_var.get(), self.action_var.get()),
                "entry_price": float(self.price_var.get() or 0),
                "target":      float(self.target_var.get() or 0),
                "stop_loss":   float(self.sl_var.get() or 0),
                "trade_type":  self.trade_type_var.get(),
                "approx_time": self.approx_time_entry.get().strip(),
                "zone_start":  _float_or_none(self.zone_start_entry.get()),
                "zone_end":    _float_or_none(self.zone_end_entry.get()),
                "reward":      _float_or_zero(self.reward_var.get()),
                "risk":        _float_or_zero(self.risk_var.get()),
                "reward_pct":  _float_or_zero(self.reward_pct_var.get()),
                "risk_pct":    _float_or_zero(self.risk_pct_var.get()),
                "risk_reward": self.rr_var.get() if self.rr_var.get() != "—" else "",
                "remarks":     self.remarks_entry.get("1.0", "end-1c").strip(),
                "status":      "ACTIVE",
                "cmp_at_entry": float(self.price_var.get() or 0),
            }

            if not trade_data["stock_name"]:
                raise ValueError("Stock Name cannot be empty.")
            if trade_data["entry_price"] <= 0 or trade_data["target"] <= 0 or trade_data["stop_loss"] <= 0:
                raise ValueError("Entry Price, Target, and Stop Loss must be greater than 0.")

        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return

        self.submit_btn.configure(text="Processing...", state="disabled")

        try:
            # insert_trade now also fetches the row back and merges created_at, trade_code, etc.
            trade_id = insert_trade(trade_data)

            def process_services():
                # 2. Generate Image
                img_gen = ImageGenerator()
                img_path = img_gen.generate_trade_image(trade_data)

                # 3. Update Google Sheets
                try:
                    gs = GoogleSheetsService()
                    if gs.is_configured():
                        gs.append_trade(trade_data)
                except Exception as e:
                    logger.error(f"Sheets Error: {e}", exc_info=True)

                # 4. Send Telegram Message
                try:
                    tg = TelegramService()
                    if tg.is_configured():
                        async def send_tg():
                            await tg.connect()
                            from utils.message_formatter import format_new_trade
                            msg = format_new_trade(trade_data)
                            await tg.send_trade_message(msg, img_path)
                            await tg.disconnect()

                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(send_tg())
                        loop.close()
                except Exception as e:
                    logger.error(f"Telegram Error: {e}", exc_info=True)

                self.after(0, self._on_submit_success, trade_data.get("trade_code", str(trade_id)))

            threading.Thread(target=process_services, daemon=True).start()

        except Exception as e:
            logger.error(f"Failed to save trade to DB: {e}", exc_info=True)
            messagebox.showerror("Database Error", f"Failed to save trade: {e}")
            self.submit_btn.configure(text="✦  Submit Trade & Broadcast", state="normal")

    def _on_submit_success(self, trade_code):
        messagebox.showinfo("Success", f"Trade {trade_code} saved and broadcasted successfully!")
        self.clear_form()
        self.submit_btn.configure(text="✦  Submit Trade & Broadcast", state="normal")
        self.master.show_active_trades()

    def clear_form(self):
        self.stock_entry.delete(0, "end")
        self.price_var.set("")
        self.target_var.set("")
        self.sl_var.set("")
        self.approx_time_entry.delete(0, "end")
        self.zone_start_entry.delete(0, "end")
        self.zone_end_entry.delete(0, "end")
        self.remarks_entry.delete("1.0", "end")
        self.reward_var.set("0.00")
        self.risk_var.set("0.00")
        self.reward_pct_var.set("0.00%")
        self.risk_pct_var.set("0.00%")
        self.rr_var.set("—")
