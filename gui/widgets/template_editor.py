"""Reusable template-editor widget with toolbar, variable picker, and live preview.

Used by the Settings page's Message Formatting tab.
"""

import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QScrollArea, QFrame, QTextBrowser,
    QSplitter, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor

from gui.theme import get_color
from utils.message_templates import (
    build_trade_context, build_update_context,
    get_available_variables, load_template, render_template,
)
from database.settings_db import set_template, delete_template
from utils.constants import DATE_FMT_DB

_logger = logging.getLogger(__name__)

_SAMPLE_TRADE = {
    "action": "LONG",
    "stock_name": "RELIANCE",
    "segment": "Cash",
    "entry_price": 2450.00,
    "target": 2600.00,
    "stop_loss": 2350.00,
    "trade_type": "INTRADAY",
    "approx_time": "2-3 days",
    "zone_start": 2400.00,
    "zone_end": 2500.00,
    "reward": 150.00,
    "reward_pct": 6.12,
    "risk": 100.00,
    "risk_pct": 4.08,
    "risk_reward": "1 : 1.50",
    "cmp_at_entry": 2440.00,
    "remarks": "Enter on dip near support",
    "created_at": "2026-05-24 14:30:00",
    "trade_code": "TRD-20260524-A1B2C3",
}

_SAMPLE_UPDATE = {
    "update_type": "TARGET_HIT",
    "details": "Target Achieved! Book Profits at ₹2,600.",
    "new_value": {"entry_price": 2600.0, "exit_price": 2600.0},
    "old_value": {"entry_price": 2450.0},
}

_FIELD_GROUP_LABELS = {
    "stock_name": "Trade Info",
    "action": "Trade Info",
    "segment": "Trade Info",
    "trade_type": "Trade Info",
    "approx_time": "Trade Info",
    "entry_price": "Prices",
    "zone": "Prices",
    "zone_start": "Prices",
    "zone_end": "Prices",
    "target": "Prices",
    "stop_loss": "Prices",
    "exit_price": "Prices",
    "cmp_at_entry": "Prices",
    "reward": "Risk/Reward",
    "reward_pct": "Risk/Reward",
    "risk": "Risk/Reward",
    "risk_pct": "Risk/Reward",
    "risk_reward": "Risk/Reward",
    "latest_sl_price": "Prices",
    "latest_target": "Prices",
    "created_at": "Meta",
    "updated_at": "Meta",
    "exit_datetime": "Meta",
    "trade_code": "Meta",
    "remarks": "Meta",
    "status": "Meta",
    "update_type": "Update",
    "details": "Update",
    "field_changes": "Update",
    "current_time": "Update",
}


class TemplateEditorWidget(QWidget):
    template_changed = Signal(str, str)
    template_saved = Signal()

    def __init__(self, template_type="trade", parent=None):
        super().__init__(parent)
        self._template_type = template_type
        self._template_key = "new_trade" if template_type == "trade" else "update"
        self._preview_visible = True
        self._updating = False

        self._setup_ui()
        self._reload_template()
        self._update_preview()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ── Toolbar ──────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        bold_btn = QPushButton("B")
        bold_btn.setToolTip("Wrap selection in **bold**")
        bold_btn.setObjectName("toolbar_btn")
        bold_btn.setFixedSize(32, 28)
        bold_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        bold_btn.setCursor(Qt.PointingHandCursor)
        bold_btn.clicked.connect(self._on_bold)
        toolbar.addWidget(bold_btn)

        toolbar.addStretch()

        self._preview_toggle = QPushButton("Hide Preview")
        self._preview_toggle.setObjectName("toolbar_btn")
        self._preview_toggle.setCursor(Qt.PointingHandCursor)
        self._preview_toggle.setStyleSheet(f"""
        #toolbar_btn {{
            color: {get_color('text_secondary')};
            background: transparent;
            border: 1px solid {get_color('border')};
            border-radius: 4px;
            padding: 2px 10px;
            font-size: 11px;
        }}
        #toolbar_btn:hover {{
            color: {get_color('text_primary')};
            border-color: {get_color('accent')};
        }}
        """)
        self._preview_toggle.clicked.connect(self._on_toggle_preview)
        toolbar.addWidget(self._preview_toggle)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # ── Editor + Variable panel ──────────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"""
        QSplitter::handle {{
            background-color: {get_color('border')};
        }}
        """)

        self._editor = QPlainTextEdit()
        self._editor.setObjectName("template_editor")
        self._editor.setPlaceholderText("Enter your message template here...")
        self._editor.setFont(QFont("Consolas", 12))
        self._editor.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self._editor.setStyleSheet(f"""
        #template_editor {{
            background-color: {get_color('input_bg')};
            color: {get_color('text_primary')};
            border: 1px solid {get_color('input_border')};
            border-radius: 6px;
            padding: 8px;
            selection-background-color: {get_color('accent')};
            selection-color: {get_color('bg')};
        }}
        """)
        self._editor.textChanged.connect(self._on_text_changed)
        splitter.addWidget(self._editor)

        var_panel = self._build_var_panel()
        splitter.addWidget(var_panel)
        splitter.setSizes([500, 200])

        layout.addWidget(splitter, 1)

        # ── Preview ──────────────────────────────────────────────────────
        self._preview = QTextBrowser()
        self._preview.setObjectName("template_preview")
        self._preview.setReadOnly(True)
        self._preview.setFont(QFont("Consolas", 11))
        self._preview.setMinimumHeight(80)
        self._preview.setMaximumHeight(200)
        self._preview.setStyleSheet(f"""
        #template_preview {{
            background-color: {get_color('readonly_bg')};
            color: {get_color('text_secondary')};
            border: 1px solid {get_color('readonly_border')};
            border-radius: 6px;
            padding: 8px;
        }}
        """)
        layout.addWidget(self._preview)

    def _build_var_panel(self):
        panel = QFrame()
        panel.setObjectName("var_panel")
        panel.setStyleSheet(f"""
        #var_panel {{
            background-color: {get_color('surface_secondary')};
            border: 1px solid {get_color('border')};
            border-radius: 6px;
        }}
        """)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        header = QLabel("Variables")
        header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        header.setStyleSheet(
            f"color: {get_color('accent')}; background: transparent; "
            f"padding: 8px 10px 4px 10px; border: none;"
        )
        panel_layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(8, 4, 8, 8)
        scroll_layout.setSpacing(2)

        variables = get_available_variables(self._template_type)
        groups: dict[str, list[dict]] = {}
        for var in variables:
            group = _FIELD_GROUP_LABELS.get(var["key"], "Other")
            groups.setdefault(group, []).append(var)

        group_order = ["Trade Info", "Prices", "Risk/Reward", "Meta", "Update", "Other", "Computed"]
        for group_name in group_order:
            if group_name not in groups:
                continue
            group_label = QLabel(group_name)
            group_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
            group_label.setStyleSheet(
                f"color: {get_color('text_muted')}; background: transparent; "
                f"padding: 6px 4px 2px 4px; border: none;"
            )
            scroll_layout.addWidget(group_label)

            for var in groups[group_name]:
                btn = QPushButton(f"{{{var['key']}}}")
                btn.setToolTip(var.get("description", var.get("label", "")))
                btn.setObjectName("var_tag")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setStyleSheet(f"""
                #var_tag {{
                    color: {get_color('accent')};
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 3px;
                    padding: 2px 6px;
                    font-size: 11px;
                    text-align: left;
                }}
                #var_tag:hover {{
                    background-color: {get_color('surface_hover')};
                    border-color: {get_color('accent')};
                }}
                """)
                btn.clicked.connect(lambda checked=False, k=var["key"]: self._insert_variable(k))
                scroll_layout.addWidget(btn)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        panel_layout.addWidget(scroll)
        return panel

    # ── Actions ──────────────────────────────────────────────────────────

    def _on_bold(self):
        cursor = self._editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"**{text}**")
        else:
            cursor.insertText("****")
            cursor.movePosition(QTextCursor.Left, QTextCursor.MoveAnchor, 2)
            self._editor.setTextCursor(cursor)

    def _insert_variable(self, var_name):
        self._editor.insertPlainText(f"{{{var_name}}}")
        self._editor.setFocus()

    def _on_toggle_preview(self):
        self._preview_visible = not self._preview_visible
        self._preview.setVisible(self._preview_visible)
        self._preview_toggle.setText(
            "Hide Preview" if self._preview_visible else "Show Preview"
        )

    def _on_text_changed(self):
        if self._updating:
            return
        QTimer.singleShot(200, self._update_preview)

    def _update_preview(self):
        if not self._preview_visible:
            return
        template = self.get_template()
        if not template.strip():
            self._preview.setPlainText("(empty template)")
            return

        if self._template_type == "trade":
            context = build_trade_context(_SAMPLE_TRADE)
        else:
            context = build_update_context(_SAMPLE_TRADE, _SAMPLE_UPDATE)

        result = render_template(template, context)
        self._preview.setPlainText(result if result.strip() else "(preview: all variables are empty)")

    # ── Public API ───────────────────────────────────────────────────────

    def get_template(self) -> str:
        return self._editor.toPlainText()

    def set_template(self, text: str):
        self._updating = True
        self._editor.setPlainText(text)
        self._updating = False

    def save(self):
        text = self.get_template()
        set_template(self._template_key, text)
        _logger.info(f"Saved template: {self._template_key}")
        self.template_saved.emit()

    def reset(self):
        delete_template(self._template_key)
        self._reload_template()
        self._update_preview()
        _logger.info(f"Reset template: {self._template_key}")

    def _reload_template(self):
        text = load_template(self._template_key)
        self.set_template(text)
