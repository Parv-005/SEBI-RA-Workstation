from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication


DARK_COLORS = {
    "bg": "#1a1a2e",
    "surface": "#16213e",
    "surface_hover": "#1a2744",
    "surface_secondary": "#1e2d50",
    "accent": "#0f3460",
    "accent_hover": "#144a80",
    "success": "#28a745",
    "danger": "#e94560",
    "warning": "#f0ad4e",
    "info": "#17a2b8",
    "text_primary": "#e6e6e6",
    "text_secondary": "#a0a0b0",
    "text_muted": "#6c6c80",
    "border": "#2a2a4a",
    "input_bg": "#12122a",
    "disabled_bg": "#14142a",
    "scrollbar_bg": "#1a1a2e",
    "scrollbar_handle": "#2a2a4a",
    "scrollbar_hover": "#3a3a5a",
    "badge_blue": "#0f3460",
    "badge_teal": "#17a2b8",
    "badge_gray": "#6c757d",
    "badge_green": "#28a745",
    "badge_red": "#e94560",
    "badge_yellow": "#f0ad4e",
}

LIGHT_COLORS = {
    "bg": "#f0f0f5",
    "surface": "#ffffff",
    "surface_hover": "#e8e8f0",
    "surface_secondary": "#f5f5fa",
    "accent": "#0f3460",
    "accent_hover": "#144a80",
    "success": "#28a745",
    "danger": "#e94560",
    "warning": "#f0ad4e",
    "info": "#17a2b8",
    "text_primary": "#1a1a2e",
    "text_secondary": "#666680",
    "text_muted": "#9999aa",
    "border": "#d0d0dd",
    "input_bg": "#ffffff",
    "disabled_bg": "#f0f0f5",
    "scrollbar_bg": "#f0f0f5",
    "scrollbar_handle": "#c0c0d0",
    "scrollbar_hover": "#a0a0b0",
    "badge_blue": "#0f3460",
    "badge_teal": "#17a2b8",
    "badge_gray": "#6c757d",
    "badge_green": "#28a745",
    "badge_red": "#e94560",
    "badge_yellow": "#f0ad4e",
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
    font-family: "Segoe UI", "Arial", sans-serif;
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
    color: {c['text_primary']};
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 500;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {c['accent_hover']};
}}

QPushButton:pressed {{
    background-color: {c['accent']};
}}

QPushButton:disabled {{
    background-color: {c['disabled_bg']};
    color: {c['text_muted']};
}}

QPushButton#danger {{
    background-color: {c['danger']};
}}

QPushButton#danger:hover {{
    background-color: #d63851;
}}

QPushButton#success {{
    background-color: {c['success']};
}}

QPushButton#success:hover {{
    background-color: #23923d;
}}

QPushButton#ghost {{
    background-color: transparent;
    color: {c['text_secondary']};
    border: 1px solid {c['border']};
}}

QPushButton#ghost:hover {{
    background-color: {c['surface_hover']};
    color: {c['text_primary']};
}}

QLineEdit {{
    background-color: {c['input_bg']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: {c['accent']};
}}

QLineEdit:focus {{
    border: 1px solid {c['accent']};
}}

QLineEdit:disabled {{
    background-color: {c['disabled_bg']};
    color: {c['text_muted']};
}}

QLineEdit#error {{
    border: 1px solid {c['danger']};
}}

QTextEdit {{
    background-color: {c['input_bg']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: {c['accent']};
}}

QTextEdit:focus {{
    border: 1px solid {c['accent']};
}}

QComboBox {{
    background-color: {c['input_bg']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 20px;
}}

QComboBox:hover {{
    border: 1px solid {c['accent']};
}}

QComboBox::drop-down {{
    border: none;
    width: 28px;
    padding-right: 8px;
}}

QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {c['surface']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 4px;
    padding: 4px;
    selection-background-color: {c['accent']};
    selection-color: {c['text_primary']};
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
    selection-color: {c['text_primary']};
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
    background-color: {c['surface_secondary']};
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
    background-color: {c['surface']};
    border: 1px solid {c['border']};
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
    color: {c['text_secondary']};
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
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
        palette.setColor(QPalette.HighlightedText, QColor(c["text_primary"]))
        palette.setColor(QPalette.ToolTipBase, QColor(c["surface"]))
        palette.setColor(QPalette.ToolTipText, QColor(c["text_primary"]))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(c["text_muted"]))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(c["text_muted"]))
        app.setPalette(palette)
