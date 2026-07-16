from typing import Any
from PySide6.QtCore import QPointF, Qt, QRectF
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPen,
    QUndoStack,
)
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

from items.resize_handle import ResizeHandle
from commands.undo_commands import ResizeItemCommand


class TableItem(QGraphicsRectItem):
    MINIMUM_CELL_WIDTH = 20.0
    MINIMUM_CELL_HEIGHT = 20.0

    def __init__(
        self,
        rows: int,
        columns: int,
        cell_width: float = 100,
        cell_height: float = 40,
        color: QColor = QColor("#000000"),
        undo_stack: QUndoStack | None = None,
    ) -> None:
        self.rows = rows
        self.columns = columns
        self.cell_width = float(cell_width)
        self.cell_height = float(cell_height)
        self.undo_stack = undo_stack
        self._resize_before_state: dict[str, Any] | None = None

        width = columns * cell_width
        height = rows * cell_height

        super().__init__(
            0,
            0,
            width,
            height,
        )

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.setBrush(QBrush(QColor("#ffffff")))

        self.setPen(QPen(color, 1))

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

        self.update_handle_positions()

    @property
    def minimum_width(self) -> float:
        return self.columns * self.MINIMUM_CELL_WIDTH

    @property
    def minimum_height(self) -> float:
        return self.rows * self.MINIMUM_CELL_HEIGHT

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

    def begin_resize(
        self,
        corner: str,
        scene_position: QPointF,
    ) -> None:
        rect = self.rect()
        self._resize_before_state = self.capture_resize_state()

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
        anchor_x = self._resize_anchor_scene.x()
        anchor_y = self._resize_anchor_scene.y()

        mouse_x = scene_position.x()
        mouse_y = scene_position.y()

        if corner == ResizeHandle.TOP_LEFT:
            right = anchor_x
            bottom = anchor_y

            left = min(
                mouse_x,
                right - self.minimum_width,
            )

            top = min(
                mouse_y,
                bottom - self.minimum_height,
            )

        elif corner == ResizeHandle.TOP_RIGHT:
            left = anchor_x
            bottom = anchor_y

            right = max(
                mouse_x,
                left + self.minimum_width,
            )

            top = min(
                mouse_y,
                bottom - self.minimum_height,
            )

        elif corner == ResizeHandle.BOTTOM_LEFT:
            right = anchor_x
            top = anchor_y

            left = min(
                mouse_x,
                right - self.minimum_width,
            )

            bottom = max(
                mouse_y,
                top + self.minimum_height,
            )

        else:
            left = anchor_x
            top = anchor_y

            right = max(
                mouse_x,
                left + self.minimum_width,
            )

            bottom = max(
                mouse_y,
                top + self.minimum_height,
            )

        new_width = right - left
        new_height = bottom - top

        self.prepareGeometryChange()

        self.setPos(left, top)

        self.setRect(
            0,
            0,
            new_width,
            new_height,
        )

        self.cell_width = new_width / self.columns

        self.cell_height = new_height / self.rows

        self.update_handle_positions()
        self.update()

    def end_resize(self) -> None:
        pass

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        painter.save()

        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRect(self.rect())

        width = self.rect().width()
        height = self.rect().height()

        for row in range(1, self.rows):
            y = row * self.cell_height

            painter.drawLine(
                0,
                y,
                width,
                y,
            )

        for column in range(1, self.columns):
            x = column * self.cell_width

            painter.drawLine(
                x,
                0,
                x,
                height,
            )

        if self.isSelected():
            selection_pen = QPen(QColor("#1976d2"))

            selection_pen.setWidthF(1.5)
            selection_pen.setStyle(Qt.PenStyle.DashLine)

            painter.setBrush(Qt.BrushStyle.NoBrush)

            painter.setPen(selection_pen)
            painter.drawRect(self.rect())

        painter.restore()

    def capture_resize_state(self) -> dict[str, Any]:
        return {
            "position": QPointF(self.pos()),
            "rect": QRectF(self.rect()),
            "cell_width": float(self.cell_width),
            "cell_height": float(self.cell_height),
        }

    def apply_resize_state(
        self,
        state: dict[str, Any],
    ) -> None:
        self.setPos(state["position"])
        self.setRect(state["rect"])

        self.cell_width = state["cell_width"]
        self.cell_height = state["cell_height"]

        self.update_handle_positions()
        self.update()

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
                    text="Resize table",
                )
            )

        self._resize_before_state = None
