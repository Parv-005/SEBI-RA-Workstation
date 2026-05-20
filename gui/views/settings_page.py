from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QInputDialog, QMessageBox,
    QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from gui.signals import get_signals
from gui.theme import get_color
from gui.widgets.toast import ToastWidget
from gui.widgets.section_card import SectionCard
from core.config import Config
from utils.config_manager import save_config, load_config


class SettingsView(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._signals = get_signals()
        self._config = {}
        self._entries = {}

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        form_layout = QVBoxLayout(scroll_content)
        form_layout.setContentsMargins(32, 24, 32, 24)
        form_layout.setSpacing(20)

        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet(f"color: {get_color('text_primary')}; background: transparent;")
        form_layout.addWidget(title)

        self._tg_card = SectionCard("Telegram API (Telethon)")
        self._build_tg_section()
        form_layout.addWidget(self._tg_card)

        self._gs_card = SectionCard("Google Sheets Integration")
        self._build_gs_section()
        form_layout.addWidget(self._gs_card)

        self._ao_card = SectionCard("AngelOne SmartAPI")
        self._build_ao_section()
        form_layout.addWidget(self._ao_card)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()

        self._save_btn = QPushButton("Save Settings")
        self._save_btn.setObjectName("success")
        self._save_btn.setMinimumWidth(200)
        self._save_btn.setMinimumHeight(44)
        self._save_btn.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self._save_btn.setCursor(Qt.PointingHandCursor)
        self._save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self._save_btn)

        form_layout.addLayout(btn_row)
        form_layout.addStretch()

        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll, 1)

    def _add_entry(self, card, label_text, key, default="", placeholder="", browse=False):
        row = QHBoxLayout()
        row.setSpacing(12)

        label = QLabel(label_text)
        label.setFixedWidth(160)
        label.setStyleSheet(f"color: {get_color('text_secondary')}; font-size: 13px; "
                           f"font-weight: 500; background: transparent;")
        row.addWidget(label)

        entry = QLineEdit()
        entry.setText(str(default))
        if placeholder:
            entry.setPlaceholderText(placeholder)
        row.addWidget(entry, 1)

        if browse:
            browse_btn = QPushButton("Browse")
            browse_btn.setObjectName("ghost")
            browse_btn.setCursor(Qt.PointingHandCursor)

            def on_browse():
                path, _ = QFileDialog.getOpenFileName(
                    self, "Select Service Account JSON",
                    "", "JSON Files (*.json);;All Files (*)"
                )
                if path:
                    entry.setText(path)

            browse_btn.clicked.connect(on_browse)
            row.addWidget(browse_btn)

        card.add_layout(row)
        self._entries[key] = entry

    def _build_tg_section(self):
        c = self._config.get("telegram", {})
        self._add_entry(self._tg_card, "API ID", "tg_api_id", c.get("api_id", ""),
                       "Your Telegram API ID")
        self._add_entry(self._tg_card, "API Hash", "tg_api_hash", c.get("api_hash", ""),
                       "Your Telegram API Hash")
        self._add_entry(self._tg_card, "Phone Number", "tg_phone", c.get("phone", ""),
                       "e.g. +919XXXXXXXXX")
        self._add_entry(self._tg_card, "Group/Channel ID", "tg_group", c.get("group_id", ""),
                       "Channel ID (e.g. -1001234567890)")

        auth_row = QHBoxLayout()
        auth_row.setSpacing(12)
        auth_spacer = QLabel()
        auth_spacer.setFixedWidth(160)
        auth_row.addWidget(auth_spacer)

        self._auth_btn = QPushButton("Authenticate Telegram")
        self._auth_btn.setObjectName("ghost")
        self._auth_btn.setCursor(Qt.PointingHandCursor)
        self._auth_btn.clicked.connect(self._on_auth_telegram)
        auth_row.addWidget(self._auth_btn)

        auth_row.addStretch()
        self._tg_card.add_layout(auth_row)

    def _build_gs_section(self):
        c = self._config.get("google_sheets", {})
        self._add_entry(self._gs_card, "Service Account JSON", "gs_json",
                       c.get("service_account_json", ""), "", browse=True)
        self._add_entry(self._gs_card, "Spreadsheet ID", "gs_sheet_id",
                       c.get("spreadsheet_id", ""), "Google Sheets spreadsheet ID")

    def _build_ao_section(self):
        c = self._config.get("angelone", {})
        self._add_entry(self._ao_card, "API Key", "ao_api_key", c.get("api_key", ""))
        self._add_entry(self._ao_card, "Client ID", "ao_client_id", c.get("client_id", ""))
        self._add_entry(self._ao_card, "Password (PIN)", "ao_password", c.get("password", ""))
        self._add_entry(self._ao_card, "TOTP Secret", "ao_totp", c.get("totp_secret", ""))

    def _connect_signals(self):
        self._signals.telegram_auth_needs_otp.connect(self._on_needs_otp)
        self._signals.telegram_auth_needs_2fa.connect(self._on_needs_2fa)
        self._signals.telegram_auth_success.connect(self._on_auth_success)
        self._signals.telegram_auth_error.connect(self._on_auth_error)

    def on_show(self):
        self._load_config_data()

    def _load_config_data(self):
        try:
            self._config = Config.get()
        except Exception:
            self._config = {}
            from utils.config_manager import load_config
            try:
                self._config = load_config()
            except Exception:
                self._config = {}

        self._entries.clear()
        self._tg_card = SectionCard("Telegram API (Telethon)")
        self._build_tg_section()

        self._gs_card = SectionCard("Google Sheets Integration")
        self._build_gs_section()

        self._ao_card = SectionCard("AngelOne SmartAPI")
        self._build_ao_section()

    def _on_save(self):
        config = self._assemble_config()
        self._controller.save_settings(config)

    def _assemble_config(self):
        current = dict(self._config)

        telegram = current.get("telegram", {})
        telegram["api_id"] = self._entries.get("tg_api_id", QLineEdit()).text().strip()
        telegram["api_hash"] = self._entries.get("tg_api_hash", QLineEdit()).text().strip()
        telegram["phone"] = self._entries.get("tg_phone", QLineEdit()).text().strip()
        telegram["group_id"] = self._entries.get("tg_group", QLineEdit()).text().strip()
        current["telegram"] = telegram

        google = current.get("google_sheets", {})
        google["service_account_json"] = self._entries.get("gs_json", QLineEdit()).text().strip()
        google["spreadsheet_id"] = self._entries.get("gs_sheet_id", QLineEdit()).text().strip()
        current["google_sheets"] = google

        angelone = current.get("angelone", {})
        angelone["api_key"] = self._entries.get("ao_api_key", QLineEdit()).text().strip()
        angelone["client_id"] = self._entries.get("ao_client_id", QLineEdit()).text().strip()
        angelone["password"] = self._entries.get("ao_password", QLineEdit()).text().strip()
        angelone["totp_secret"] = self._entries.get("ao_totp", QLineEdit()).text().strip()
        current["angelone"] = angelone

        return current

    def _on_auth_telegram(self):
        self._on_save()
        self._auth_btn.setEnabled(False)
        self._auth_btn.setText("Authenticating...")

        self._signals.notification.emit(
            "Starting Telegram authentication...",
            ToastWidget.INFO,
            3000
        )
        self._controller.auth_telegram()

    def _on_needs_otp(self):
        code, ok = QInputDialog.getText(
            self, "Telegram OTP",
            "Enter the OTP sent to your Telegram:"
        )
        if ok and code:
            self._controller.submit_auth_input(code.strip())
        else:
            self._controller.cancel_auth()
            self._reset_auth_btn()

    def _on_needs_2fa(self):
        password, ok = QInputDialog.getText(
            self, "Telegram 2FA",
            "Enter your Telegram 2FA password:",
            echo=QInputDialog.Password
        )
        if ok and password:
            self._controller.submit_auth_input(password)
        else:
            self._controller.cancel_auth()
            self._reset_auth_btn()

    def _on_auth_success(self):
        self._signals.notification.emit(
            "Telegram authenticated successfully!",
            ToastWidget.SUCCESS,
            4000
        )
        self._reset_auth_btn()

    def _on_auth_error(self, err):
        self._signals.notification.emit(
            f"Telegram authentication failed: {err}",
            ToastWidget.ERROR,
            5000
        )
        self._reset_auth_btn()

    def _reset_auth_btn(self):
        self._auth_btn.setEnabled(True)
        self._auth_btn.setText("Authenticate Telegram")
