#!/usr/bin/env python3
"""
Integration Test Script — SEBI RA Automation Software
======================================================
Tests every integration to confirm it is connected and working correctly.

Run from the project root:
    python test_integrations.py

Exit codes:
    0  — all tests passed
    1  — one or more tests failed
"""

import asyncio
import sys
import tempfile
import traceback
from pathlib import Path

# ── colour helpers ────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"


def pass_(msg: str):  print(f"  {GREEN}✔  PASS{RESET}  {msg}")
def fail_(msg: str):  print(f"  {RED}✘  FAIL{RESET}  {msg}")
def skip_(msg: str):  print(f"  {YELLOW}⚠  SKIP{RESET}  {msg}")
def info_(msg: str):  print(f"       {CYAN}{msg}{RESET}")


# ── result tracker ────────────────────────────────────────────────────────────
results: dict[str, str] = {}   # integration → "PASS" | "FAIL" | "SKIP"


def record(name: str, status: str):
    results[name] = status


# ═════════════════════════════════════════════════════════════════════════════
# 1. DATABASE
# ═════════════════════════════════════════════════════════════════════════════

def test_database():
    print(f"\n{BOLD}[1] SQLite Database{RESET}")
    name = "Database"
    try:
        from database.db_manager import (
            init_db, insert_trade, get_trade,
            update_trade, insert_trade_update, get_trade_updates,
            get_setting, set_setting,
        )

        # initialise schema
        init_db()
        pass_("init_db() — schema applied")

        # insert a synthetic trade
        dummy = dict(
            stock_name="TEST_STOCK", segment="Cash", action="BUY",
            entry_price=100.0, target=110.0, stop_loss=95.0,
            quantity=10, timeframe="1D", risk_reward="2:1",
            remarks="integration-test", status="ACTIVE", cmp_at_entry=101.0,
        )
        trade_id = insert_trade(dummy)
        assert isinstance(trade_id, int) and trade_id > 0
        pass_(f"insert_trade() — new trade ID {trade_id}")

        # read it back
        trade = get_trade(trade_id)
        assert trade and trade["stock_name"] == "TEST_STOCK"
        pass_("get_trade() — data matches")

        # update it
        ok = update_trade(trade_id, {"status": "CLOSED", "remarks": "test-closed"})
        assert ok
        pass_("update_trade() — status set to CLOSED")

        # trade update log
        upd_id = insert_trade_update({
            "trade_id": trade_id,
            "update_type": "TARGET_HIT",
            "details": "Target achieved during integration test",
            "old_value": {"status": "ACTIVE"},
            "new_value": {"status": "CLOSED"},
        })
        assert isinstance(upd_id, int) and upd_id > 0
        pass_(f"insert_trade_update() — update ID {upd_id}")

        updates = get_trade_updates(trade_id)
        assert len(updates) >= 1
        pass_("get_trade_updates() — update record found")

        # settings table
        set_setting("_test_key", "integration_value")
        val = get_setting("_test_key")
        assert val == "integration_value"
        pass_("set_setting() / get_setting() — round-trip OK")

        record(name, "PASS")

    except Exception as e:
        fail_(f"Database test raised: {e}")
        traceback.print_exc()
        record(name, "FAIL")


# ═════════════════════════════════════════════════════════════════════════════
# 2. IMAGE GENERATOR
# ═════════════════════════════════════════════════════════════════════════════

def test_image_generator():
    print(f"\n{BOLD}[2] Image Generator (Pillow){RESET}")
    name = "ImageGenerator"
    try:
        from services.image_generator import ImageGenerator

        gen = ImageGenerator()
        pass_("ImageGenerator() instantiated")

        dummy_trade = dict(
            id=9999, stock_name="TEST_STOCK", segment="Cash", action="BUY",
            entry_price=100.0, target=110.0, stop_loss=95.0,
            quantity=10, timeframe="1D", risk_reward="2:1", cmp_at_entry=101.0,
        )

        path = gen.generate_trade_image(dummy_trade)
        assert path and Path(path).exists()
        info_(f"Trade image saved → {path}")
        pass_("generate_trade_image() — file created")

        upd = {"update_type": "TARGET_HIT", "details": "Integration test update"}
        path2 = gen.generate_update_image(dummy_trade, upd)
        assert path2 and Path(path2).exists()
        info_(f"Update image saved → {path2}")
        pass_("generate_update_image() — file created")

        record(name, "PASS")

    except Exception as e:
        fail_(f"ImageGenerator test raised: {e}")
        traceback.print_exc()
        record(name, "FAIL")


# ═════════════════════════════════════════════════════════════════════════════
# 3. ANGEL ONE
# ═════════════════════════════════════════════════════════════════════════════

def test_angelone():
    print(f"\n{BOLD}[3] AngelOne (SmartAPI){RESET}")
    name = "AngelOne"
    try:
        from services.angelone_service import AngelOneService

        svc = AngelOneService()
        pass_("AngelOneService() instantiated")

        if not svc.is_configured():
            skip_("Credentials not set in config.json — skipping live connection")
            record(name, "SKIP")
            return

        pass_("is_configured() — credentials present")

        connected = svc.connect()
        assert connected
        pass_("connect() — session established")

        # lightweight live check: search for a well-known symbol
        results_list = svc.search_symbol("RELIANCE", "Cash")
        assert isinstance(results_list, list)
        info_(f"search_symbol('RELIANCE', 'Cash') → {len(results_list)} result(s)")
        pass_("search_symbol() — API responded")

        svc.disconnect()
        pass_("disconnect() — session terminated")

        record(name, "PASS")

    except Exception as e:
        fail_(f"AngelOne test raised: {e}")
        traceback.print_exc()
        record(name, "FAIL")


# ═════════════════════════════════════════════════════════════════════════════
# 4. GOOGLE SHEETS
# ═════════════════════════════════════════════════════════════════════════════

def test_google_sheets():
    print(f"\n{BOLD}[4] Google Sheets (gspread){RESET}")
    name = "GoogleSheets"
    try:
        from services.google_sheets_service import GoogleSheetsService

        svc = GoogleSheetsService()
        pass_("GoogleSheetsService() instantiated")

        if not svc.is_configured():
            skip_("service_account_json / spreadsheet_id not set in config.json — skipping live check")
            record(name, "SKIP")
            return

        pass_("is_configured() — credentials & spreadsheet ID present")

        svc.connect()
        assert svc.sheet is not None
        pass_("connect() — worksheet opened successfully")

        info_(f"Worksheet: '{svc.sheet_name}' in spreadsheet {svc.spreadsheet_id}")
        record(name, "PASS")

    except Exception as e:
        fail_(f"GoogleSheets test raised: {e}")
        traceback.print_exc()
        record(name, "FAIL")


# ═════════════════════════════════════════════════════════════════════════════
# 5. TELEGRAM
# ═════════════════════════════════════════════════════════════════════════════

TELEGRAM_TIMEOUT = 20  # seconds


async def test_telegram_async():
    print(f"\n{BOLD}[5] Telegram (Telethon){RESET}")
    name = "Telegram"
    try:
        from services.telegram_service import TelegramService

        svc = TelegramService()
        pass_("TelegramService() instantiated")

        if not svc.is_configured():
            skip_("api_id / api_hash / phone not set in config.json — skipping live check")
            record(name, "SKIP")
            return

        # Extra guard: api_id must be numeric for Telethon
        if not str(svc.api_id).strip().lstrip("-").isdigit():
            skip_("api_id is not a valid integer — skipping live check")
            record(name, "SKIP")
            return

        pass_("is_configured() — credentials present")

        try:
            authorized = await asyncio.wait_for(svc.connect(), timeout=TELEGRAM_TIMEOUT)
        except asyncio.TimeoutError:
            fail_(f"connect() timed out after {TELEGRAM_TIMEOUT}s — check network / credentials")
            record(name, "FAIL")
            return

        if authorized is False:
            # Session not authorised yet — OTP would be needed interactively.
            skip_("Session not yet authorised (OTP required). Run the app once to log in.")
            record(name, "SKIP")
            await svc.disconnect()
            return

        pass_("connect() — client authorised")

        if svc.group_id:
            info_(f"group_id configured: {svc.group_id}")
            pass_("group_id present — ready to send messages")
        else:
            skip_("group_id not set — message-send step skipped")

        await svc.disconnect()
        pass_("disconnect() — client disconnected")

        record(name, "PASS")

    except Exception as e:
        fail_(f"Telegram test raised: {e}")
        traceback.print_exc()
        record(name, "FAIL")


def test_telegram():
    asyncio.run(test_telegram_async())


# ═════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════════════

def print_summary():
    print(f"\n{BOLD}{'═' * 55}{RESET}")
    print(f"{BOLD}  Integration Test Summary{RESET}")
    print(f"{BOLD}{'═' * 55}{RESET}")

    passed = failed = skipped = 0
    for integration, status in results.items():
        if status == "PASS":
            marker = f"{GREEN}✔ PASS{RESET}"
            passed += 1
        elif status == "FAIL":
            marker = f"{RED}✘ FAIL{RESET}"
            failed += 1
        else:
            marker = f"{YELLOW}⚠ SKIP{RESET}"
            skipped += 1
        print(f"  {marker}  {integration}")

    print(f"{BOLD}{'─' * 55}{RESET}")
    print(f"  {GREEN}{passed} passed{RESET}  |  {YELLOW}{skipped} skipped{RESET}  |  {RED}{failed} failed{RESET}")
    print(f"{BOLD}{'═' * 55}{RESET}\n")
    return failed


# ═════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"\n{BOLD}{CYAN}SEBI RA Automation — Integration Tests{RESET}")
    print(f"{CYAN}{'─' * 40}{RESET}")

    test_database()
    test_image_generator()
    test_angelone()
    test_google_sheets()
    test_telegram()

    failed = print_summary()
    sys.exit(1 if failed else 0)
