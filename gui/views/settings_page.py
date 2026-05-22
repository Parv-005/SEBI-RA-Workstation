from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QInputDialog, QMessageBox,
    QFileDialog, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from gui.signals import get_signals
from gui.theme import get_color
from gui.widgets.toast import ToastWidget
from gui.widgets.section_card import SectionCard
from core.config import Config
from utils.config_manager import save_config, load_config
from utils.logger import setup_logger

logger = setup_logger("SettingsView")


class SettingsView(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._signals = get_signals()
        self._config = {}
        self._entries = {}
        self._group_rows = []

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
        scroll.setObjectName("settings_scroll")
        scroll.setStyleSheet("#settings_scroll { background-color: transparent; border: none; }")

        scroll_content = QWidget()
        scroll_content.setObjectName("settings_content")
        scroll_content.setStyleSheet("#settings_content { background-color: transparent; }")
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

        groups_label = QLabel("Telegram Groups")
        groups_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        groups_label.setStyleSheet(
            f"color: {get_color('accent')}; background: transparent; "
            f"border: none; letter-spacing: 1px;"
        )
        self._tg_card.add_widget(groups_label)

        self._groups_container = QWidget()
        self._groups_container.setStyleSheet("background-color: transparent;")
        self._groups_layout = QVBoxLayout(self._groups_container)
        self._groups_layout.setContentsMargins(0, 0, 0, 0)
        self._groups_layout.setSpacing(6)
        self._tg_card.add_widget(self._groups_container)

        groups_config = c.get("groups", {})
        if groups_config:
            for name, gid in groups_config.items():
                self._add_group_row(name, gid)
        elif c.get("group_id"):
            self._add_group_row("Default", c["group_id"])
        else:
            self._add_group_row("", "")

        add_group_btn = QPushButton("+ Add Group")
        add_group_btn.setObjectName("ghost")
        add_group_btn.setCursor(Qt.PointingHandCursor)
        add_group_btn.clicked.connect(self._on_add_group)
        self._tg_card.add_widget(add_group_btn)

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

    def _add_group_row(self, name="", group_id=""):
        row_widget = QWidget()
        row_widget.setStyleSheet("background-color: transparent;")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        name_entry = QLineEdit(name)
        name_entry.setPlaceholderText("Group name")
        name_entry.setMinimumWidth(140)
        row_layout.addWidget(name_entry, 1)

        id_entry = QLineEdit(group_id)
        id_entry.setPlaceholderText("Group ID (e.g. -100...)")
        row_layout.addWidget(id_entry, 2)

        remove_btn = QPushButton("X")
        remove_btn.setFixedWidth(32)
        remove_btn.setObjectName("ghost")
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.clicked.connect(lambda: self._remove_group_row(row_widget))
        row_layout.addWidget(remove_btn)

        self._groups_layout.addWidget(row_widget)
        self._group_rows.append({"widget": row_widget, "name": name_entry, "id": id_entry})

    def _remove_group_row(self, row_widget):
        self._group_rows = [r for r in self._group_rows if r["widget"] is not row_widget]
        row_widget.deleteLater()

    def _on_add_group(self):
        self._add_group_row("", "")

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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
        except Exception as e:
            logger.error(f"Config.get() failed: {e}", exc_info=True)
            self._config = {}
            from utils.config_manager import load_config
            try:
                self._config = load_config()
            except Exception as e2:
                logger.error(f"Fallback load_config also failed: {e2}", exc_info=True)
                self._config = {}

        self._group_rows.clear()

        self._clear_layout(self._groups_layout)

        c = self._config.get("telegram", {})

        def _set(key):
            if key in self._entries:
                return self._entries[key]
            return None

        e = _set("tg_api_id")
        if e is not None:
            e.setText(c.get("api_id", ""))
        e = _set("tg_api_hash")
        if e is not None:
            e.setText(c.get("api_hash", ""))
        e = _set("tg_phone")
        if e is not None:
            e.setText(c.get("phone", ""))

        groups_config = c.get("groups", {})
        if groups_config:
            for name, gid in groups_config.items():
                self._add_group_row(name, gid)
        elif c.get("group_id"):
            self._add_group_row("Default", c["group_id"])
        else:
            self._add_group_row("", "")

        e = _set("gs_json")
        if e is not None:
            e.setText(
                self._config.get("google_sheets", {}).get("service_account_json", "")
            )
        e = _set("gs_sheet_id")
        if e is not None:
            e.setText(
                self._config.get("google_sheets", {}).get("spreadsheet_id", "")
            )

        for key in ("ao_api_key", "ao_client_id", "ao_password", "ao_totp"):
            e = _set(key)
            if e is not None:
                field_map = {
                    "ao_api_key": "api_key", "ao_client_id": "client_id",
                    "ao_password": "password", "ao_totp": "totp_secret",
                }
                e.setText(
                    self._config.get("angelone", {}).get(field_map[key], "")
                )

    def _on_save(self):
        logger.info("Saving settings")
        config = self._assemble_config()
        self._controller.save_settings(config)

    def _entry_val(self, key, section, config_key):
        if key in self._entries:
            return self._entries[key].text().strip()
        return self._config.get(section, {}).get(config_key, "")

    def _assemble_config(self):
        current = dict(self._config)

        telegram = current.get("telegram", {})
        telegram["api_id"] = self._entry_val("tg_api_id", "telegram", "api_id")
        telegram["api_hash"] = self._entry_val("tg_api_hash", "telegram", "api_hash")
        telegram["phone"] = self._entry_val("tg_phone", "telegram", "phone")
        groups = {}
        for row in self._group_rows:
            name = row["name"].text().strip()
            gid = row["id"].text().strip()
            if name and gid:
                groups[name] = gid
        telegram["groups"] = groups
        if groups:
            first_id = next(iter(groups.values()))
            telegram["group_id"] = first_id
        current["telegram"] = telegram

        google = current.get("google_sheets", {})
        google["service_account_json"] = self._entry_val("gs_json", "google_sheets", "service_account_json")
        google["spreadsheet_id"] = self._entry_val("gs_sheet_id", "google_sheets", "spreadsheet_id")
        current["google_sheets"] = google

        angelone = current.get("angelone", {})
        angelone["api_key"] = self._entry_val("ao_api_key", "angelone", "api_key")
        angelone["client_id"] = self._entry_val("ao_client_id", "angelone", "client_id")
        angelone["password"] = self._entry_val("ao_password", "angelone", "password")
        angelone["totp_secret"] = self._entry_val("ao_totp", "angelone", "totp_secret")
        current["angelone"] = angelone

        return current

    def _on_auth_telegram(self):
        self._on_save()
        logger.info("Starting Telegram authentication")
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
        logger.info("Telegram authentication successful")
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
