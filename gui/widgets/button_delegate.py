from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QTableView
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QFont, QPainter

from gui.theme import get_color
from utils.constants import STATUS_CLOSED

_BTN_W = 68
_BTN_H = 28


class ButtonDelegate(QStyledItemDelegate):
    def __init__(self, table: QTableView, row_delegate, parent=None):
        super().__init__(parent)
        self._table = table
        self._row_delegate = row_delegate
        self._hover_row = -1
        self._press_row = -1

    @staticmethod
    def button_rect(cell_rect):
        x = cell_rect.x() + (cell_rect.width() - _BTN_W) // 2
        y = cell_rect.y() + (cell_rect.height() - _BTN_H) // 2
        return QRect(x, y, _BTN_W, _BTN_H)

    def paint(self, painter, option, index):
        row = index.row()
        is_selected = option.state & QStyle.State_Selected
        is_hovered = row == self._row_delegate.hover_row
        is_pressed = row == self._row_delegate.pressed_row and is_hovered

        if is_pressed:
            row_bg = QColor(get_color("accent_darker"))
        elif is_selected:
            row_bg = QColor(get_color("accent"))
        elif is_hovered:
            row_bg = QColor(get_color("surface_hover"))

        if is_pressed or is_selected or is_hovered:
            painter.fillRect(option.rect, row_bg)

        trade = index.data(Qt.UserRole)
        is_closed = (
            trade is not None
            and (trade.get("status") or "").upper() == STATUS_CLOSED
        )

        btn_rect = self.button_rect(option.rect)
        is_btn_hovered = row == self._hover_row and not is_closed
        is_btn_pressed = row == self._press_row and not is_closed

        if is_closed:
            btn_bg = QColor(get_color("disabled_bg"))
            btn_fg = QColor(get_color("disabled_text"))
        elif is_btn_pressed:
            btn_bg = QColor(get_color("accent_darker"))
            btn_fg = QColor(get_color("button_gold_text"))
        elif is_btn_hovered:
            btn_bg = QColor(get_color("accent_hover"))
            btn_fg = QColor(get_color("button_gold_text"))
        else:
            btn_bg = QColor(get_color("accent"))
            btn_fg = QColor(get_color("button_gold_text"))

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(btn_bg)
        painter.drawRoundedRect(btn_rect, 4, 4)
        painter.setPen(btn_fg)
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        text = "Closed" if is_closed else "Update"
        painter.drawText(btn_rect, Qt.AlignCenter, text)
        painter.restore()

    def set_hover(self, row):
        if self._hover_row == row:
            return
        old = self._hover_row
        self._hover_row = row
        self._repaint_btn_col(old)
        self._repaint_btn_col(row)

    def clear_hover(self):
        self.set_hover(-1)

    def set_pressed(self, row):
        old = self._press_row
        self._press_row = row
        self._repaint_btn_col(old)
        self._repaint_btn_col(row)

    def clear_pressed(self):
        if self._press_row == -1:
            return
        old = self._press_row
        self._press_row = -1
        self._repaint_btn_col(old)

    def _repaint_btn_col(self, row):
        if row < 0 or self._table.model() is None:
            return
        col = self._table.model().columnCount() - 1
        idx = self._table.model().index(row, col)
        self._table.update(idx)