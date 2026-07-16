from typing import TYPE_CHECKING

from PySide6.QtGui import QColor, QAction
from PySide6.QtWidgets import (
    QMenu,
    QInputDialog,
    QGraphicsSceneContextMenuEvent,
)

from items.tree_node_item import TreeNodeItem
from models.bst import BSTNode

if TYPE_CHECKING:
    from canvas.canvas_view import CanvasView


class BSTNodeItem(TreeNodeItem):
    def __init__(
        self,
        model: BSTNode,
        canvas: CanvasView,
    ) -> None:
        super().__init__(
            value=str(model.value),
            canvas=canvas,
            fill_color=QColor("#0f9d58"),
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
            self.canvas.delete_bst_value(self.model.value)
        elif selected_action == relayout_action:
            self.canvas.relayout_bst(self.canvas.bst_root)

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
        self.canvas.insert_bst_value(val)

    def mouseDoubleClickEvent(self, event) -> None:
        self._insert_value()
        event.accept()
