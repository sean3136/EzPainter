from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QGraphicsSceneContextMenuEvent,
    QInputDialog,
    QMenu,
)

from items.tree_node_item import TreeNodeItem
from models.binary_tree_node import BinaryTreeNode

if TYPE_CHECKING:
    from canvas.canvas_view import CanvasView


class BinaryTreeNodeItem(TreeNodeItem):
    def __init__(
        self,
        model: BinaryTreeNode,
        canvas: CanvasView,
    ) -> None:
        super().__init__(
            value=model.value,
            canvas=canvas,
            fill_color=QColor("#ffffff"),
            text_color=QColor("#111111"),
        )
        self.model = model

    def contextMenuEvent(
        self,
        event: QGraphicsSceneContextMenuEvent,
    ) -> None:
        menu = QMenu()

        add_left_action = QAction("Add Left Child", menu)
        add_right_action = QAction("Add Right Child", menu)
        edit_action = QAction("Edit Value", menu)
        delete_subtree_action = QAction("Delete Subtree", menu)
        relayout_action = QAction("Re-layout Tree", menu)

        add_left_action.setEnabled(self.model.left is None)
        add_right_action.setEnabled(self.model.right is None)

        menu.addAction(add_left_action)
        menu.addAction(add_right_action)
        menu.addSeparator()
        menu.addAction(edit_action)
        menu.addAction(delete_subtree_action)
        menu.addSeparator()
        menu.addAction(relayout_action)

        selected_action = menu.exec(event.screenPos())

        if selected_action == add_left_action:
            self._add_child(is_left=True)
        elif selected_action == add_right_action:
            self._add_child(is_left=False)
        elif selected_action == edit_action:
            self._edit_value()
        elif selected_action == delete_subtree_action:
            self.canvas.delete_binary_subtree(self.model)
        elif selected_action == relayout_action:
            self.canvas.relayout_binary_tree(self.canvas.binary_tree_root)

        event.accept()

    def _add_child(
        self,
        is_left: bool,
    ) -> None:
        text, accepted = QInputDialog.getText(
            None,
            "Add Child",
            "Node value:",
        )
        if not accepted:
            return
        value = text.strip() or "Node"
        self.canvas.add_binary_tree_child(
            parent_model=self.model,
            value=value,
            is_left=is_left,
        )

    def _edit_value(self) -> None:
        text, accepted = QInputDialog.getText(
            None,
            "Edit Node",
            "Node value:",
            text=self.model.value,
        )
        if not accepted:
            return
        value = text.strip() or "Node"
        self.model.value = value
        self.value = value
        self.update()

    def mouseDoubleClickEvent(self, event) -> None:
        self._edit_value()
        event.accept()
