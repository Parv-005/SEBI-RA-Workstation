from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, Property
from PySide6.QtGui import QFont

from gui.theme import get_color


class ToastWidget(QFrame):
    INFO = 0
    SUCCESS = 1
    WARNING = 2
    ERROR = 3

    _STYLES = {}
    _ICONS = {
        0: "i",
        1: "\u2713",
        2: "!",
        3: "\u2717",
    }

    def __init__(self, message, level=INFO, duration_ms=4000, parent=None):
        super().__init__(parent)
        self._duration = duration_ms
        self._level = level
        self._anim_in = None
        self._anim_out = None
        self._is_dismissing = False
        self._offset_y = 0

        self.setObjectName("toast")
        self.setFixedWidth(360)
        self.setMinimumHeight(48)

        self._setup_ui(message, level)

        self.setGraphicsEffect(None)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        QTimer.singleShot(50, self._slide_in)

    def _setup_ui(self, message, level):
        c = get_color("surface")
        text_c = get_color("text_primary")
        accent = [get_color("info"), get_color("success"),
                  get_color("warning"), get_color("danger")][level]

        bg_color = c
        border_color = accent

        self.setStyleSheet(f"""
        #toast {{
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-left: 4px solid {border_color};
            border-radius: 8px;
        }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        icon = QLabel(self._ICONS[level])
        icon.setStyleSheet(f"color: {accent}; font-size: 16px; font-weight: bold; "
                           f"background: transparent; border: none;")
        icon.setFixedWidth(20)
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(
            f"color: {text_c}; font-size: 12px; background: transparent; border: none;"
        )
        msg_label.setFont(QFont("Segoe UI", 12))
        layout.addWidget(msg_label, 1)

        close_btn = QLabel("\u2716")
        close_btn.setStyleSheet(
            f"color: {get_color('text_muted')}; background: transparent; "
            f"border: none; font-size: 14px;"
        )
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedWidth(16)
        close_btn.mousePressEvent = lambda e: self.dismiss()
        layout.addWidget(close_btn)

    def _slide_in(self):
        parent = self.parent()
        if not parent:
            return
        self._anim_in = QPropertyAnimation(self, b"geometry")
        self._anim_in.setDuration(250)
        self._anim_in.setEasingCurve(QEasingCurve.OutCubic)

        start_rect = self.geometry()
        end_rect = start_rect
        start_rect.moveLeft(parent.width())
        self.setGeometry(start_rect)

        self._anim_in.setStartValue(start_rect)
        self._anim_in.setEndValue(end_rect)
        self._anim_in.finished.connect(self._on_slide_in_done)
        self._anim_in.start()

    def _on_slide_in_done(self):
        if self._duration > 0:
            QTimer.singleShot(self._duration, self.dismiss)

    def dismiss(self):
        if self._is_dismissing:
            return
        self._is_dismissing = True
        parent = self.parent()
        if not parent:
            self.deleteLater()
            return

        self._anim_out = QPropertyAnimation(self, b"geometry")
        self._anim_out.setDuration(200)
        self._anim_out.setEasingCurve(QEasingCurve.InCubic)
        self._anim_out.setStartValue(self.geometry())

        end_rect = self.geometry()
        end_rect.moveLeft(parent.width() + 20)
        self._anim_out.setEndValue(end_rect)
        self._anim_out.finished.connect(self._on_slide_out_done)
        self._anim_out.start()

    def _on_slide_out_done(self):
        self.deleteLater()


class ToastManager(QWidget):
    _instance = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)
        self._layout.setAlignment(Qt.AlignBottom | Qt.AlignRight)

    def show_toast(self, message, level=ToastWidget.INFO, duration_ms=4000):
        toast = ToastWidget(message, level, duration_ms, self)
        self._layout.insertWidget(0, toast)

    @classmethod
    def instance(cls, parent=None):
        if cls._instance is None and parent is not None:
            cls._instance = ToastManager(parent)
        return cls._instance

    @classmethod
    def show(cls, message, level=ToastWidget.INFO, duration_ms=4000):
        mgr = cls._instance
        if mgr:
            mgr.show_toast(message, level, duration_ms)
