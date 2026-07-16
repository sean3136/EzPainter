from typing import Any
from enum import Enum, auto

from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QUndoStack
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsRectItem,
)

from items.resize_handle import ResizeHandle
from commands.undo_commands import ResizeItemCommand


class ShapeType(Enum):
    RECTANGLE = auto()
    ELLIPSE = auto()


class BaseResizableShape:
    MINIMUM_WIDTH = 20.0
    MINIMUM_HEIGHT = 20.0

    def initialize_shape(self, color: QColor, undo_stack: QUndoStack | None) -> None:
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.setPen(QPen(color, 2))
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.undo_stack = undo_stack
        self.resize_before_state: dict[str, Any] | None = None

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

        self._resize_anchor_scene = None

        self.update_handle_positions()
        self.set_handles_visible(False)

    def update_handle_positions(self) -> None:
        rect = self.rect()

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

    def begin_resize(self, corner: str, scene_position) -> None:
        self.resize_before_state = self.capture_resize_state()
        rect = self.rect()

        opposite_points = {
            ResizeHandle.TOP_LEFT: rect.bottomRight(),
            ResizeHandle.TOP_RIGHT: rect.bottomLeft(),
            ResizeHandle.BOTTOM_LEFT: rect.topRight(),
            ResizeHandle.BOTTOM_RIGHT: rect.topLeft(),
        }

        self._resize_anchor_scene = self.mapToScene(opposite_points[corner])

    def resize_from_handle(
        self,
        corner: str,
        scene_position,
    ) -> None:
        if self._resize_anchor_scene is None:
            return

        anchor_x = self._resize_anchor_scene.x()
        anchor_y = self._resize_anchor_scene.y()

        mouse_x = scene_position.x()
        mouse_y = scene_position.y()

        if corner == ResizeHandle.TOP_LEFT:
            left = min(
                mouse_x,
                anchor_x - self.MINIMUM_WIDTH,
            )
            top = min(
                mouse_y,
                anchor_y - self.MINIMUM_HEIGHT,
            )
            right = anchor_x
            bottom = anchor_y

        elif corner == ResizeHandle.TOP_RIGHT:
            left = anchor_x
            top = min(
                mouse_y,
                anchor_y - self.MINIMUM_HEIGHT,
            )
            right = max(
                mouse_x,
                anchor_x + self.MINIMUM_WIDTH,
            )
            bottom = anchor_y

        elif corner == ResizeHandle.BOTTOM_LEFT:
            left = min(
                mouse_x,
                anchor_x - self.MINIMUM_WIDTH,
            )
            top = anchor_y
            right = anchor_x
            bottom = max(
                mouse_y,
                anchor_y + self.MINIMUM_HEIGHT,
            )

        else:
            left = anchor_x
            top = anchor_y
            right = max(
                mouse_x,
                anchor_x + self.MINIMUM_WIDTH,
            )
            bottom = max(
                mouse_y,
                anchor_y + self.MINIMUM_HEIGHT,
            )

        width = right - left
        height = bottom - top

        self.setPos(left, top)
        self.setRect(0, 0, width, height)

        self.update_handle_positions()

    def end_resize(self) -> None:
        self._resize_anchor_scene = None

    def capture_resize_state(self) -> dict[str, Any]:
        return {
            "position": QPointF(self.pos()),
            "rect": QRectF(self.rect()),
        }

    def apply_resize_state(
        self,
        state: dict[str, Any],
    ) -> None:
        self.setPos(state["position"])
        self.setRect(state["rect"])

        self.update_handle_positions()
        self.update()

    def end_resize(self) -> None:
        if self.resize_before_state is None:
            return

        new_state = self.capture_resize_state()

        if new_state != self.resize_before_state and self.undo_stack is not None:
            shape_name = "rectangle" if isinstance(self, RectangleItem) else "ellipse"

            self.undo_stack.push(
                ResizeItemCommand(
                    item=self,
                    old_state=self.resize_before_state,
                    new_state=new_state,
                    text=f"Resize {shape_name}",
                )
            )

        self.resize_before_state = None


class RectangleItem(
    BaseResizableShape,
    QGraphicsRectItem,
):
    def __init__(self, rect: QRectF, color: QColor = QColor("#000000"), undo_stack: QUndoStack | None = None) -> None:
        super().__init__(
            0,
            0,
            rect.width(),
            rect.height(),
        )

        self.setPos(rect.topLeft())
        self.initialize_shape(color, undo_stack)


class EllipseItem(
    BaseResizableShape,
    QGraphicsEllipseItem,
):
    def __init__(self, rect: QRectF, color: QColor = QColor("#000000"), undo_stack: QUndoStack | None = None) -> None:
        super().__init__(
            0,
            0,
            rect.width(),
            rect.height(),
        )

        self.setPos(rect.topLeft())
        self.initialize_shape(color, undo_stack)
