from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor,
    QPainter,
    QAction,
)
from PySide6.QtWidgets import (
    QStyleOptionGraphicsItem,
    QWidget,
    QMenu,
    QInputDialog,
    QGraphicsSceneContextMenuEvent,
)

from items.tree_node_item import TreeNodeItem
from models.red_black_tree import (
    BLACK,
    RedBlackNode,
)

if TYPE_CHECKING:
    from canvas.canvas_view import CanvasView


class RedBlackNodeItem(TreeNodeItem):
    def __init__(
        self,
        model: RedBlackNode,
        canvas: CanvasView,
    ) -> None:
        super().__init__(
            value=str(model.value),
            canvas=canvas,
            fill_color=QColor("#d93025"),
        )
        self.model = model

    def contextMenuEvent(
        self,
        event: QGraphicsSceneContextMenuEvent,
    ) -> None:
        menu = QMenu()

        insert_action = QAction("Insert Value", menu)
        delete_action = QAction("Delete Node", menu)
        relayout_action = QAction("Re-layout Tree", menu)

        menu.addAction(insert_action)
        menu.addAction(delete_action)
        menu.addSeparator()
        menu.addAction(relayout_action)

        selected_action = menu.exec(event.screenPos())

        if selected_action == insert_action:
            self._insert_value()
        elif selected_action == delete_action:
            self.canvas.delete_red_black_value(self.model.value)
        elif selected_action == relayout_action:
            self.canvas.relayout_rb_tree(self.canvas.rb_tree_root)

        event.accept()

    def _insert_value(self) -> None:
        val_str, accepted = QInputDialog.getText(
            None,
            "Insert Value",
            "Integer value to insert:",
        )
        if not accepted:
            return
        try:
            val = int(val_str.strip())
        except ValueError:
            return
        self.canvas.insert_red_black_value(val)

    def mouseDoubleClickEvent(self, event) -> None:
        self._insert_value()
        event.accept()

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        is_black = self.model.color == BLACK
        self.fill_color = QColor("#202124") if is_black else QColor("#d93025")
        super().paint(painter, option, widget)
