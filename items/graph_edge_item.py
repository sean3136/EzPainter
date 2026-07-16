from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import QLineF, QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsLineItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

if TYPE_CHECKING:
    from items.graph_node_item import GraphNodeItem


class GraphEdgeItem(QGraphicsLineItem):
    def __init__(
        self,
        source_node: GraphNodeItem,
        target_node: GraphNodeItem,
        directed: bool = False,
    ) -> None:
        super().__init__()

        self.source_node = source_node
        self.target_node = target_node
        self.directed = directed

        self.normal_pen = QPen(QColor("#333333"), 2)
        self.selected_pen = QPen(QColor("#1976d2"), 3)

        self.setPen(self.normal_pen)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )

        self.setZValue(-1)

        self.source_node.add_edge(self)
        self.target_node.add_edge(self)

        self.update_position()

    def update_position(self) -> None:
        source_center = self.source_node.scene_center()
        target_center = self.target_node.scene_center()

        start, end = self._calculate_boundary_points(
            source_center,
            target_center,
        )

        self.setLine(QLineF(start, end))

    def _calculate_boundary_points(
        self,
        source_center: QPointF,
        target_center: QPointF,
    ) -> tuple[QPointF, QPointF]:
        line = QLineF(source_center, target_center)

        if line.length() == 0:
            return source_center, target_center

        dx = target_center.x() - source_center.x()
        dy = target_center.y() - source_center.y()

        distance = math.hypot(dx, dy)

        unit_x = dx / distance
        unit_y = dy / distance

        source_radius = self.source_node.radius
        target_radius = self.target_node.radius

        start = QPointF(
            source_center.x() + unit_x * source_radius,
            source_center.y() + unit_y * source_radius,
        )

        end = QPointF(
            target_center.x() - unit_x * target_radius,
            target_center.y() - unit_y * target_radius,
        )

        return start, end

    def detach(self) -> None:
        self.source_node.remove_edge(self)
        self.target_node.remove_edge(self)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        painter.save()

        painter.setPen(
            self.selected_pen
            if self.isSelected()
            else self.normal_pen
        )

        painter.drawLine(self.line())

        if self.directed:
            self._draw_arrow_head(painter)

        painter.restore()

    def _draw_arrow_head(self, painter: QPainter) -> None:
        line = self.line()

        if line.length() == 0:
            return

        arrow_size = 12.0
        angle = math.atan2(
            -line.dy(),
            line.dx(),
        )

        end = line.p2()

        left_point = end - QPointF(
            math.cos(angle + math.pi / 6) * arrow_size,
            -math.sin(angle + math.pi / 6) * arrow_size,
        )

        right_point = end - QPointF(
            math.cos(angle - math.pi / 6) * arrow_size,
            -math.sin(angle - math.pi / 6) * arrow_size,
        )

        arrow = QPolygonF(
            [
                end,
                left_point,
                right_point,
            ]
        )

        painter.setBrush(
            self.selected_pen.color()
            if self.isSelected()
            else self.normal_pen.color()
        )

        painter.drawPolygon(arrow)