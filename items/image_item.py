from typing import Any
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QUndoStack
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPixmapItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

from items.resize_handle import ResizeHandle
from commands.undo_commands import ResizeItemCommand


class ImageItem(QGraphicsPixmapItem):
    MINIMUM_SCALE = 0.05
    MAXIMUM_SCALE = 10.0

    def __init__(
        self,
        pixmap: QPixmap,
        undo_stack: QUndoStack | None = None,
    ) -> None:
        super().__init__(pixmap)

        self.undo_stack = undo_stack
        self._resize_before_state: dict[str, Any] | None = None
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)

        self.setTransformOriginPoint(self.boundingRect().center())

        self.resize_handles = {
            ResizeHandle.TOP_LEFT: ResizeHandle(
                ResizeHandle.TOP_LEFT,
                self,
            ),
            ResizeHandle.TOP_RIGHT: ResizeHandle(
                ResizeHandle.TOP_RIGHT,
                self,
            ),
            ResizeHandle.BOTTOM_LEFT: ResizeHandle(
                ResizeHandle.BOTTOM_LEFT,
                self,
            ),
            ResizeHandle.BOTTOM_RIGHT: ResizeHandle(
                ResizeHandle.BOTTOM_RIGHT,
                self,
            ),
        }

        self._resize_anchor_scene = QPointF()
        self._resize_corner = ""

        self.update_handle_positions()

    def update_handle_positions(self) -> None:
        rect = self.boundingRect()

        self.resize_handles[ResizeHandle.TOP_LEFT].setPos(rect.topLeft())

        self.resize_handles[ResizeHandle.TOP_RIGHT].setPos(rect.topRight())

        self.resize_handles[ResizeHandle.BOTTOM_LEFT].setPos(rect.bottomLeft())

        self.resize_handles[ResizeHandle.BOTTOM_RIGHT].setPos(rect.bottomRight())

    def set_handles_visible(self, visible: bool) -> None:
        for handle in self.resize_handles.values():
            handle.setVisible(visible)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.set_handles_visible(bool(value))

        return super().itemChange(change, value)

    def begin_resize(
        self,
        corner: str,
        scene_position: QPointF,
    ) -> None:
        self._resize_corner = corner
        self._resize_before_state = self.capture_resize_state()

        rect = self.boundingRect()

        opposite_points = {
            ResizeHandle.TOP_LEFT: rect.bottomRight(),
            ResizeHandle.TOP_RIGHT: rect.bottomLeft(),
            ResizeHandle.BOTTOM_LEFT: rect.topRight(),
            ResizeHandle.BOTTOM_RIGHT: rect.topLeft(),
        }

        opposite_local = opposite_points[corner]

        self._resize_anchor_scene = self.mapToScene(opposite_local)

    def resize_from_handle(
        self,
        corner: str,
        scene_position: QPointF,
    ) -> None:
        rect = self.boundingRect()

        original_width = rect.width()
        original_height = rect.height()

        if original_width <= 0 or original_height <= 0:
            return

        distance_x = abs(scene_position.x() - self._resize_anchor_scene.x())

        distance_y = abs(scene_position.y() - self._resize_anchor_scene.y())

        width_scale = distance_x / original_width
        height_scale = distance_y / original_height

        new_scale = min(width_scale, height_scale)

        new_scale = max(
            self.MINIMUM_SCALE,
            min(new_scale, self.MAXIMUM_SCALE),
        )

        opposite_points = {
            ResizeHandle.TOP_LEFT: rect.bottomRight(),
            ResizeHandle.TOP_RIGHT: rect.bottomLeft(),
            ResizeHandle.BOTTOM_LEFT: rect.topRight(),
            ResizeHandle.BOTTOM_RIGHT: rect.topLeft(),
        }

        opposite_local = opposite_points[corner]

        self.setScale(new_scale)

        current_anchor_scene = self.mapToScene(opposite_local)

        anchor_difference = self._resize_anchor_scene - current_anchor_scene

        self.setPos(self.pos() + anchor_difference)

    def end_resize(self) -> None:
        if self._resize_before_state is None:
            return

        new_state = self.capture_resize_state()

        if new_state != self._resize_before_state and self.undo_stack is not None:
            self.undo_stack.push(
                ResizeItemCommand(
                    item=self,
                    old_state=self._resize_before_state,
                    new_state=new_state,
                    text="Resize image",
                )
            )

        self._resize_before_state = None
        self._resize_corner = ""

    def scale_by(self, factor: float) -> None:
        new_scale = self.scale() * factor

        new_scale = max(
            self.MINIMUM_SCALE,
            min(new_scale, self.MAXIMUM_SCALE),
        )

        self.setScale(new_scale)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        super().paint(painter, option, widget)

        if self.isSelected():
            painter.save()

            selection_pen = QPen(QColor("#1976d2"))
            selection_pen.setWidthF(1.5)
            selection_pen.setStyle(Qt.PenStyle.DashLine)

            painter.setPen(selection_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            painter.drawRect(self.boundingRect())

            painter.restore()

    def capture_resize_state(self) -> dict[str, Any]:
        return {
            "position": QPointF(self.pos()),
            "scale": float(self.scale()),
        }

    def apply_resize_state(
        self,
        state: dict[str, Any],
    ) -> None:
        self.setPos(state["position"])
        self.setScale(state["scale"])
        self.update_handle_positions()
        self.update()

    def shape(self) -> Any:
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path
