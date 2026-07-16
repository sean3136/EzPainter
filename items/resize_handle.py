from typing import Protocol

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QCursor, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
)


class ResizableItemProtocol(Protocol):
    def begin_resize(
        self,
        corner: str,
        scene_position,
    ) -> None:
        ...

    def resize_from_handle(
        self,
        corner: str,
        scene_position,
    ) -> None:
        ...

    def end_resize(self) -> None:
        ...


class ResizeHandle(QGraphicsRectItem):
    SIZE = 10.0

    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"

    def __init__(
        self,
        corner: str,
        owner: ResizableItemProtocol,
    ) -> None:
        half_size = self.SIZE / 2

        super().__init__(
            QRectF(
                -half_size,
                -half_size,
                self.SIZE,
                self.SIZE,
            ),
            owner,
        )

        self.corner = corner
        self.owner = owner

        self.setBrush(QColor("#ffffff"))
        self.setPen(QPen(QColor("#1976d2"), 1.5))

        self.setZValue(1000)

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations,
            True,
        )

        self.setAcceptHoverEvents(True)

        self.setAcceptedMouseButtons(
            Qt.MouseButton.LeftButton
        )

        self.setVisible(False)

        self._update_cursor()

    def _update_cursor(self) -> None:
        if self.corner in (
            self.TOP_LEFT,
            self.BOTTOM_RIGHT,
        ):
            self.setCursor(
                QCursor(Qt.CursorShape.SizeFDiagCursor)
            )
        else:
            self.setCursor(
                QCursor(Qt.CursorShape.SizeBDiagCursor)
            )

    def hoverEnterEvent(
        self,
        event: QGraphicsSceneHoverEvent,
    ) -> None:
        self.setBrush(QColor("#1976d2"))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(
        self,
        event: QGraphicsSceneHoverEvent,
    ) -> None:
        self.setBrush(QColor("#ffffff"))
        super().hoverLeaveEvent(event)

    def mousePressEvent(
        self,
        event: QGraphicsSceneMouseEvent,
    ) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.owner.begin_resize(
                self.corner,
                event.scenePos(),
            )

            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(
        self,
        event: QGraphicsSceneMouseEvent,
    ) -> None:
        self.owner.resize_from_handle(
            self.corner,
            event.scenePos(),
        )

        event.accept()

    def mouseReleaseEvent(
        self,
        event: QGraphicsSceneMouseEvent,
    ) -> None:
        self.owner.end_resize()

        event.accept()