from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsSceneMouseEvent,
    QInputDialog,
    QStyleOptionGraphicsItem,
    QWidget,
)

if TYPE_CHECKING:
    from items.graph_edge_item import GraphEdgeItem


class GraphNodeItem(QGraphicsEllipseItem):
    DEFAULT_DIAMETER = 64.0

    def __init__(
        self,
        value: str = "Node",
        diameter: float = DEFAULT_DIAMETER,
    ) -> None:
        self.diameter = float(diameter)
        self.radius = self.diameter / 2

        super().__init__(
            0,
            0,
            self.diameter,
            self.diameter,
        )

        self.value = value
        self.edges: list[GraphEdgeItem] = []

        self.normal_brush = QBrush(QColor("#ffffff"))
        self.selected_brush = QBrush(QColor("#e3f2fd"))

        self.normal_pen = QPen(QColor("#222222"), 2)
        self.selected_pen = QPen(QColor("#1976d2"), 3)

        self.font = QFont()
        self.font.setPointSize(12)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.setAcceptHoverEvents(True)
        self.setZValue(10)

    def add_edge(self, edge: GraphEdgeItem) -> None:
        if edge not in self.edges:
            self.edges.append(edge)

    def remove_edge(self, edge: GraphEdgeItem) -> None:
        if edge in self.edges:
            self.edges.remove(edge)

    def scene_center(self) -> QPointF:
        return self.mapToScene(
            self.boundingRect().center()
        )

    def itemChange(self, change, value):
        if change in (
            QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged,
            QGraphicsItem.GraphicsItemChange.ItemTransformHasChanged,
        ):
            for edge in list(self.edges):
                edge.update_position()

        return super().itemChange(change, value)

    def mouseDoubleClickEvent(
        self,
        event: QGraphicsSceneMouseEvent,
    ) -> None:
        text, accepted = QInputDialog.getText(
            None,
            "Edit Node",
            "Node value:",
            text=self.value,
        )

        if accepted:
            self.value = text.strip() or "Node"
            self.update()

        event.accept()

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        painter.save()

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        if self.isSelected():
            painter.setBrush(self.selected_brush)
            painter.setPen(self.selected_pen)
        else:
            painter.setBrush(self.normal_brush)
            painter.setPen(self.normal_pen)

        painter.drawEllipse(self.rect())

        painter.setFont(self.font)
        painter.setPen(QPen(QColor("#111111")))

        text_rect = self.rect().adjusted(
            6,
            6,
            -6,
            -6,
        )

        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignCenter
            | Qt.TextFlag.TextWordWrap,
            self.value,
        )

        painter.restore()