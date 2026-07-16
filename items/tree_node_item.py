from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QStyleOptionGraphicsItem,
    QWidget,
)

from items.graph_node_item import GraphNodeItem

if TYPE_CHECKING:
    from canvas.canvas_view import CanvasView


class TreeNodeItem(GraphNodeItem):
    def __init__(
        self,
        value: str,
        canvas: CanvasView,
        fill_color: QColor,
        text_color: QColor = QColor("#ffffff"),
    ) -> None:
        super().__init__(value=value)
        self.canvas = canvas
        self.fill_color = fill_color
        self.text_color = text_color

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        border_color = QColor("#1976d2") if self.isSelected() else QColor("#111111")
        painter.setBrush(self.fill_color)
        painter.setPen(
            QPen(
                border_color,
                3 if self.isSelected() else 2,
            )
        )

        painter.drawEllipse(self.rect())

        painter.setFont(self.font)
        painter.setPen(QPen(self.text_color))

        text_rect = self.rect().adjusted(6, 6, -6, -6)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            self.value,
        )

        painter.restore()
