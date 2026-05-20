from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication


DARK_COLORS = {
    "bg": "#121212",
    "surface": "#1E1E28",
    "surface_hover": "#2A2A36",
    "surface_secondary": "#24242E",
    "accent": "#D4AF37",
    "accent_hover": "#E6C24F",
    "accent_darker": "#B8962E",
    "success": "#4CAF50",
    "danger": "#EF5350",
    "warning": "#FFB74D",
    "info": "#29B6F6",
    "text_primary": "#E0E0E0",
    "text_secondary": "#9E9E9E",
    "text_muted": "#616161",
    "border": "#2C2C3A",
    "border_focus": "#D4AF37",
    "input_bg": "#1A1A24",
    "input_border": "#4A4A5A",
    "input_border_focus": "#D4AF37",
    "disabled_bg": "#1A1A24",
    "disabled_text": "#4A4A5A",
    "card_bg": "#1E1E28",
    "card_border": "#2C2C3A",
    "card_header_bg": "#24242E",
    "readonly_bg": "#181820",
    "readonly_border": "#2A2A36",
    "button_gold_bg": "#D4AF37",
    "button_gold_hover": "#E6C24F",
    "button_gold_text": "#121212",
    "scrollbar_bg": "#121212",
    "scrollbar_handle": "#2C2C3A",
    "scrollbar_hover": "#3A3A4A",
    "nav_active_bg": "#2A2A36",
    "nav_active_border": "#D4AF37",
    "badge_blue": "#1565C0",
    "badge_teal": "#00897B",
    "badge_gray": "#616161",
    "badge_green": "#2E7D32",
    "badge_red": "#C62828",
    "badge_yellow": "#F9A825",
    "reward_green": "#4CAF50",
    "risk_red": "#EF5350",
}

LIGHT_COLORS = {
    "bg": "#F5F5F5",
    "surface": "#FFFFFF",
    "surface_hover": "#EEEEF0",
    "surface_secondary": "#F0F0F5",
    "accent": "#B8962E",
    "accent_hover": "#D4AF37",
    "accent_darker": "#9A7D26",
    "success": "#2E7D32",
    "danger": "#C62828",
    "warning": "#F9A825",
    "info": "#0288D1",
    "text_primary": "#1A1A2E",
    "text_secondary": "#666680",
    "text_muted": "#9E9E9E",
    "border": "#D0D0DD",
    "border_focus": "#B8962E",
    "input_bg": "#FFFFFF",
    "input_border": "#C0C0D0",
    "input_border_focus": "#B8962E",
    "disabled_bg": "#F0F0F5",
    "disabled_text": "#9E9E9E",
    "card_bg": "#FFFFFF",
    "card_border": "#D0D0DD",
    "card_header_bg": "#F5F5FA",
    "readonly_bg": "#F5F5FA",
    "readonly_border": "#E0E0E8",
    "button_gold_bg": "#B8962E",
    "button_gold_hover": "#D4AF37",
    "button_gold_text": "#FFFFFF",
    "scrollbar_bg": "#F5F5F5",
    "scrollbar_handle": "#C0C0D0",
    "scrollbar_hover": "#A0A0B0",
    "nav_active_bg": "#F0EDE0",
    "nav_active_border": "#B8962E",
    "badge_blue": "#1565C0",
    "badge_teal": "#00897B",
    "badge_gray": "#757575",
    "badge_green": "#2E7D32",
    "badge_red": "#C62828",
    "badge_yellow": "#F9A825",
    "reward_green": "#2E7D32",
    "risk_red": "#C62828",
}

_current_colors = DARK_COLORS
_current_theme = "dark"


def get_color(name):
    return _current_colors.get(name, "#000000")


def current_theme():
    return _current_theme


def _build_qss(c):
    return f"""
QMainWindow {{
    background-color: {c['bg']};
    color: {c['text_primary']};
    font-family: "Segoe UI", "Inter", "Roboto", "Arial", sans-serif;
    font-size: 13px;
}}

QWidget {{
    color: {c['text_primary']};
}}

QLabel {{
    color: {c['text_primary']};
    background-color: transparent;
    border: none;
    padding: 0px;
    margin: 0px;
}}

QPushButton {{
    background-color: {c['accent']};
    color: {c['button_gold_text']};
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 600;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {c['accent_hover']};
}}

QPushButton:pressed {{
    background-color: {c['accent_darker']};
}}

QPushButton:disabled {{
    background-color: {c['disabled_bg']};
    color: {c['disabled_text']};
}}

QPushButton#danger {{
    background-color: {c['danger']};
    color: #FFFFFF;
}}

QPushButton#danger:hover {{
    background-color: #C62828;
}}

QPushButton#success {{
    background-color: {c['success']};
    color: #FFFFFF;
}}

QPushButton#success:hover {{
    background-color: #388E3C;
}}

QPushButton#ghost {{
    background-color: transparent;
    color: {c['text_secondary']};
    border: 1px solid {c['border']};
}}

QPushButton#ghost:hover {{
    background-color: {c['surface_hover']};
    color: {c['text_primary']};
    border-color: {c['text_muted']};
}}

QPushButton#gold {{
    background-color: {c['button_gold_bg']};
    color: {c['button_gold_text']};
    font-weight: 700;
    border: none;
    border-radius: 6px;
}}

QPushButton#gold:hover {{
    background-color: {c['button_gold_hover']};
}}

QLineEdit {{
    background-color: {c['input_bg']};
    color: {c['text_primary']};
    border: 1px solid {c['input_border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: {c['accent']};
    selection-color: {c['button_gold_text']};
}}

QLineEdit:focus {{
    border: 2px solid {c['input_border_focus']};
    padding: 7px 11px;
}}

QLineEdit:disabled {{
    background-color: {c['disabled_bg']};
    color: {c['disabled_text']};
    border: 1px solid {c['border']};
}}

QLineEdit:disabled:focus {{
    border: 1px solid {c['border']};
    padding: 8px 12px;
}}

QLineEdit#error {{
    border: 1px solid {c['danger']};
}}

QLineEdit#readonly {{
    background-color: {c['readonly_bg']};
    color: {c['text_secondary']};
    border: 1px solid {c['readonly_border']};
    font-weight: 600;
    border-radius: 6px;
    padding: 8px 12px;
}}

QTextEdit {{
    background-color: {c['input_bg']};
    color: {c['text_primary']};
    border: 1px solid {c['input_border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: {c['accent']};
    selection-color: {c['button_gold_text']};
}}

QTextEdit:focus {{
    border: 2px solid {c['input_border_focus']};
    padding: 7px 11px;
}}

QComboBox {{
    background-color: {c['input_bg']};
    color: {c['text_primary']};
    border: 1px solid {c['input_border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 20px;
}}

QComboBox:hover {{
    border: 1px solid {c['text_muted']};
}}

QComboBox:focus {{
    border: 2px solid {c['input_border_focus']};
}}

QComboBox::drop-down {{
    border: none;
    width: 28px;
    padding-right: 8px;
}}

QComboBox::down-arrow {{
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {c['text_secondary']};
    width: 0px;
    height: 0px;
}}

QComboBox QAbstractItemView {{
    background-color: {c['surface']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 4px;
    selection-background-color: {c['accent']};
    selection-color: {c['button_gold_text']};
    outline: none;
}}

QComboBox QAbstractItemView::item {{
    padding: 6px 12px;
    border-radius: 4px;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {c['surface_hover']};
}}

QTableView {{
    background-color: {c['bg']};
    alternate-background-color: {c['surface']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    gridline-color: {c['border']};
    selection-background-color: {c['accent']};
    selection-color: {c['button_gold_text']};
    font-size: 13px;
}}

QTableView::item {{
    padding: 6px 10px;
    border-right: 1px solid {c['border']};
    border-bottom: none;
}}

QTableView::item:hover {{
    background-color: {c['surface_hover']};
}}

QHeaderView::section {{
    background-color: {c['card_header_bg']};
    color: {c['text_secondary']};
    border: none;
    border-bottom: 1px solid {c['border']};
    border-right: 1px solid {c['border']};
    padding: 8px 10px;
    font-weight: 600;
    font-size: 12px;
}}

QHeaderView::section:hover {{
    background-color: {c['surface_hover']};
    color: {c['text_primary']};
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background-color: {c['scrollbar_bg']};
    width: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background-color: {c['scrollbar_handle']};
    min-height: 30px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {c['scrollbar_hover']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {c['scrollbar_bg']};
    height: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal {{
    background-color: {c['scrollbar_handle']};
    min-width: 30px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {c['scrollbar_hover']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

QFrame#card {{
    background-color: {c['card_bg']};
    border: 1px solid {c['card_border']};
    border-radius: 8px;
}}

QFrame#card_header {{
    background-color: transparent;
    border: none;
    font-weight: 600;
    font-size: 14px;
    padding: 0px;
}}

QFrame#separator {{
    background-color: {c['border']};
    max-height: 1px;
}}

QFrame#badge {{
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
}}

QDialog {{
    background-color: {c['bg']};
    color: {c['text_primary']};
}}

QGroupBox {{
    border: 1px solid {c['border']};
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px 12px 12px 12px;
    font-size: 13px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    color: {c['accent']};
    font-size: 12px;
    font-weight: 700;
}}

QCheckBox {{
    color: {c['text_primary']};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {c['border']};
    background-color: {c['input_bg']};
}}

QCheckBox::indicator:checked {{
    background-color: {c['accent']};
    border-color: {c['accent']};
}}

QMessageBox {{
    background-color: {c['bg']};
}}

QMessageBox QLabel {{
    color: {c['text_primary']};
    font-size: 13px;
}}

QToolTip {{
    background-color: {c['surface']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}
"""


def apply_theme(appearance_mode="dark"):
    global _current_colors, _current_theme
    if appearance_mode == "light":
        _current_colors = LIGHT_COLORS
        _current_theme = "light"
    else:
        _current_colors = DARK_COLORS
        _current_theme = "dark"

    c = _current_colors
    qss = _build_qss(c)
    app = QApplication.instance()
    if app:
        app.setStyleSheet(qss)
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(c["bg"]))
        palette.setColor(QPalette.WindowText, QColor(c["text_primary"]))
        palette.setColor(QPalette.Base, QColor(c["input_bg"]))
        palette.setColor(QPalette.AlternateBase, QColor(c["surface"]))
        palette.setColor(QPalette.Text, QColor(c["text_primary"]))
        palette.setColor(QPalette.Button, QColor(c["surface"]))
        palette.setColor(QPalette.ButtonText, QColor(c["text_primary"]))
        palette.setColor(QPalette.Highlight, QColor(c["accent"]))
        palette.setColor(QPalette.HighlightedText, QColor(c["button_gold_text"]))
        palette.setColor(QPalette.ToolTipBase, QColor(c["surface"]))
        palette.setColor(QPalette.ToolTipText, QColor(c["text_primary"]))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(c["text_muted"]))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(c["text_muted"]))
        app.setPalette(palette)

    from gui.widgets.sidebar import Sidebar
    from gui.views.trade_form import NewTradeView
    from gui.widgets.section_card import SectionCard
    from gui.widgets.toast import ToastWidget
    from gui.views.trade_detail import TradeDetailView
    from gui.views.trade_list import TradeListView

    for widget_cls in [Sidebar, NewTradeView, SectionCard, ToastWidget,
                       TradeDetailView, TradeListView]:
        for instance in app.allWidgets():
            if isinstance(instance, widget_cls):
                if hasattr(instance, 'refresh_style'):
                    instance.refresh_style()