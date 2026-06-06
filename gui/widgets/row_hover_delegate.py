from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QTableView
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from gui.theme import get_color


class RowHoverDelegate(QStyledItemDelegate):
    def __init__(self, table: QTableView, parent=None):
        super().__init__(parent)
        self._table = table
        self._hover_row: int = -1
        self._pressed_row: int = -1

    @property
    def hover_row(self) -> int:
        return self._hover_row

    @hover_row.setter
    def hover_row(self, row: int):
        if self._hover_row == row:
            return
        old = self._hover_row
        self._hover_row = row
        self._update_row(old)
        self._update_row(row)

    @property
    def pressed_row(self) -> int:
        return self._pressed_row

    @pressed_row.setter
    def pressed_row(self, row: int):
        old = self._pressed_row
        self._pressed_row = row
        self._update_row(old)
        self._update_row(row)

    def clear_hover(self):
        self.hover_row = -1

    def clear_pressed(self):
        self.pressed_row = -1

    def _update_row(self, row: int):
        if row < 0:
            return
        for col in range(self._table.model().columnCount()):
            idx = self._table.model().index(row, col)
            self._table.update(idx)

    def paint(self, painter, option, index):
        row = index.row()
        is_selected = option.state & QStyle.State_Selected
        is_hovered = row == self._hover_row
        is_pressed = row == self._pressed_row and is_hovered

        if is_pressed:
            bg = QColor(get_color("accent_darker"))
        elif is_selected:
            bg = QColor(get_color("accent"))
        elif is_hovered:
            bg = QColor(get_color("surface_hover"))

        if is_pressed or is_selected or is_hovered:
            painter.save()
            painter.fillRect(option.rect, bg)
            painter.restore()
            option.palette.setBrush(
                option.palette.ColorRole.Highlight, bg
            )

        super().paint(painter, option, index)