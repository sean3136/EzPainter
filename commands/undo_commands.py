from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QPointF
from PySide6.QtGui import QUndoCommand
from PySide6.QtWidgets import QGraphicsItem

if TYPE_CHECKING:
    from canvas.canvas_view import CanvasView
    from models.binary_tree_node import BinaryTreeNode
    from models.red_black_tree import RedBlackNode
    from models.bst import BSTNode
    from models.heap import Heap


class AddItemsCommand(QUndoCommand):
    def __init__(
        self,
        canvas: CanvasView,
        items: list[QGraphicsItem],
        text: str = "Add item",
    ) -> None:
        super().__init__(text)

        self.canvas = canvas
        self.items = items

        self.first_redo = True

    def redo(self) -> None:
        if self.first_redo:
            self.first_redo = False
            return

        for item in self.items:
            if item.scene() is None:
                self.canvas.scene.addItem(item)

        self.canvas.scene.clearSelection()

        for item in self.items:
            if item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable:
                item.setSelected(True)

    def undo(self) -> None:
        self.canvas.scene.clearSelection()

        for item in reversed(self.items):
            if item.scene() is self.canvas.scene:
                self.canvas.scene.removeItem(item)


class DeleteItemsCommand(QUndoCommand):
    def __init__(
        self,
        canvas: CanvasView,
        items: list[QGraphicsItem],
        text: str = "Delete item",
    ) -> None:
        super().__init__(text)

        self.canvas = canvas
        self.items = items

        self.original_positions = {item: QPointF(item.pos()) for item in items}

    def redo(self) -> None:
        self.canvas.scene.clearSelection()

        for item in reversed(self.items):
            if item.scene() is self.canvas.scene:
                self.canvas.scene.removeItem(item)

    def undo(self) -> None:
        for item in self.items:
            if item.scene() is None:
                self.canvas.scene.addItem(item)

            item.setPos(self.original_positions[item])

        self.canvas.scene.clearSelection()

        for item in self.items:
            if item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable:
                item.setSelected(True)


class MoveItemsCommand(QUndoCommand):
    def __init__(
        self,
        items: list[QGraphicsItem],
        old_positions: dict[QGraphicsItem, QPointF],
        new_positions: dict[QGraphicsItem, QPointF],
    ) -> None:
        super().__init__("Move item")

        self.items = items
        self.old_positions = old_positions
        self.new_positions = new_positions

        self.first_redo = True

    def redo(self) -> None:
        if self.first_redo:
            self.first_redo = False
            return

        for item in self.items:
            if item.scene() is not None:
                item.setPos(self.new_positions[item])

    def undo(self) -> None:
        for item in self.items:
            if item.scene() is not None:
                item.setPos(self.old_positions[item])


class ResizeItemCommand(QUndoCommand):
    def __init__(
        self,
        item,
        old_state: dict[str, Any],
        new_state: dict[str, Any],
        text: str = "Resize item",
    ) -> None:
        super().__init__(text)

        self.item = item
        self.old_state = old_state
        self.new_state = new_state

        self.first_redo = True

    def redo(self) -> None:
        if self.first_redo:
            self.first_redo = False
            return

        if self.item.scene() is not None:
            self.item.apply_resize_state(self.new_state)

    def undo(self) -> None:
        if self.item.scene() is not None:
            self.item.apply_resize_state(self.old_state)


class AddBinaryChildCommand(QUndoCommand):
    def __init__(
        self,
        canvas: CanvasView,
        parent_model: BinaryTreeNode,
        value: str,
        is_left: bool,
    ) -> None:
        super().__init__("Add left child" if is_left else "Add right child")

        from items.binary_tree_node_item import (
            BinaryTreeNodeItem,
        )
        from items.graph_edge_item import GraphEdgeItem
        from models.binary_tree_node import BinaryTreeNode

        self.canvas = canvas
        self.parent_model = parent_model
        self.is_left = is_left

        self.child_model = BinaryTreeNode(value)

        self.child_item = BinaryTreeNodeItem(
            model=self.child_model,
            canvas=canvas,
        )

        parent_item = canvas.binary_tree_node_items[id(parent_model)]

        self.edge = GraphEdgeItem(
            source_node=parent_item,
            target_node=self.child_item,
            directed=False,
        )

        self.edge_key = (
            id(parent_model),
            id(self.child_model),
        )

    def redo(self) -> None:
        if self.is_left:
            self.parent_model.set_left(self.child_model)
        else:
            self.parent_model.set_right(self.child_model)

        if self.child_item.scene() is None:
            self.canvas.scene.addItem(self.child_item)

        if self.edge.scene() is None:
            self.canvas.scene.addItem(self.edge)

        self.canvas.binary_tree_node_items[id(self.child_model)] = self.child_item

        self.canvas.binary_tree_edges[self.edge_key] = self.edge

        self.canvas.relayout_binary_tree(self.canvas.binary_tree_root)

    def undo(self) -> None:
        if self.is_left:
            self.parent_model.left = None
        else:
            self.parent_model.right = None

        self.child_model.parent = None

        self.canvas.binary_tree_node_items.pop(
            id(self.child_model),
            None,
        )

        self.canvas.binary_tree_edges.pop(
            self.edge_key,
            None,
        )

        if self.edge.scene() is self.canvas.scene:
            self.canvas.scene.removeItem(self.edge)

        if self.child_item.scene() is self.canvas.scene:
            self.canvas.scene.removeItem(self.child_item)

        self.canvas.relayout_binary_tree(self.canvas.binary_tree_root)


class DeleteBinarySubtreeCommand(QUndoCommand):
    def __init__(
        self,
        canvas: CanvasView,
        subtree_root: BinaryTreeNode,
    ) -> None:
        super().__init__("Delete binary subtree")

        self.canvas = canvas
        self.subtree_root = subtree_root
        self.parent = subtree_root.parent

        self.was_left_child = (
            self.parent is not None and self.parent.left is subtree_root
        )

        self.was_tree_root = canvas.binary_tree_root is subtree_root

        self.models: list[BinaryTreeNode] = []
        self._collect_models(subtree_root)

        self.model_ids = {id(model) for model in self.models}

        self.node_items = {
            id(model): canvas.binary_tree_node_items[id(model)] for model in self.models
        }

        self.edges = {
            key: edge
            for key, edge in canvas.binary_tree_edges.items()
            if (key[0] in self.model_ids or key[1] in self.model_ids)
        }

    def _collect_models(
        self,
        node: BinaryTreeNode | None,
    ) -> None:
        if node is None:
            return

        self.models.append(node)

        self._collect_models(node.left)
        self._collect_models(node.right)

    def redo(self) -> None:
        if self.was_tree_root:
            self.canvas.binary_tree_root = None

        elif self.parent is not None:
            if self.was_left_child:
                self.parent.left = None
            else:
                self.parent.right = None

        self.subtree_root.parent = None

        for key, edge in self.edges.items():
            self.canvas.binary_tree_edges.pop(
                key,
                None,
            )

            if edge.scene() is self.canvas.scene:
                self.canvas.scene.removeItem(edge)

        for model_id, item in self.node_items.items():
            self.canvas.binary_tree_node_items.pop(
                model_id,
                None,
            )

            if item.scene() is self.canvas.scene:
                self.canvas.scene.removeItem(item)

        self.canvas.relayout_binary_tree(self.canvas.binary_tree_root)

    def undo(self) -> None:
        if self.was_tree_root:
            self.canvas.binary_tree_root = self.subtree_root

        elif self.parent is not None:
            if self.was_left_child:
                self.parent.set_left(self.subtree_root)
            else:
                self.parent.set_right(self.subtree_root)

        for model_id, item in self.node_items.items():
            if item.scene() is None:
                self.canvas.scene.addItem(item)

            self.canvas.binary_tree_node_items[model_id] = item

        for key, edge in self.edges.items():
            if edge.scene() is None:
                self.canvas.scene.addItem(edge)

            self.canvas.binary_tree_edges[key] = edge

        self.canvas.relayout_binary_tree(self.canvas.binary_tree_root)


class ModifyRedBlackTreeCommand(QUndoCommand):
    def __init__(
        self,
        canvas: CanvasView,
        old_root: RedBlackNode | None,
        new_root: RedBlackNode | None,
        origin: QPointF,
        text: str = "Modify Red-Black Tree",
    ) -> None:
        super().__init__(text)
        from models.red_black_tree import clone_rb_tree

        self.canvas = canvas
        self.old_root = clone_rb_tree(old_root)
        self.new_root = clone_rb_tree(new_root)
        self.origin = origin
        self.first_redo = True

    def redo(self) -> None:
        if self.first_redo:
            self.first_redo = False
            return
        from models.red_black_tree import clone_rb_tree
        self.canvas._rebuild_rb_tree_items(clone_rb_tree(self.new_root), self.origin)

    def undo(self) -> None:
        from models.red_black_tree import clone_rb_tree
        self.canvas._rebuild_rb_tree_items(clone_rb_tree(self.old_root), self.origin)


class ModifyBSTCommand(QUndoCommand):
    def __init__(
        self,
        canvas: CanvasView,
        old_root: BSTNode | None,
        new_root: BSTNode | None,
        origin: QPointF,
        text: str = "Modify BST",
    ) -> None:
        super().__init__(text)
        from models.bst import clone_bst

        self.canvas = canvas
        self.old_root = clone_bst(old_root)
        self.new_root = clone_bst(new_root)
        self.origin = origin
        self.first_redo = True

    def redo(self) -> None:
        if self.first_redo:
            self.first_redo = False
            return
        from models.bst import clone_bst
        self.canvas._rebuild_bst_items(clone_bst(self.new_root), self.origin)

    def undo(self) -> None:
        from models.bst import clone_bst
        self.canvas._rebuild_bst_items(clone_bst(self.old_root), self.origin)


class ModifyHeapCommand(QUndoCommand):
    def __init__(
        self,
        canvas: CanvasView,
        old_heap: Heap,
        new_heap: Heap,
        origin: QPointF,
        text: str = "Modify Heap",
    ) -> None:
        super().__init__(text)
        from models.heap import clone_heap

        self.canvas = canvas
        self.old_heap = clone_heap(old_heap)
        self.new_heap = clone_heap(new_heap)
        self.origin = origin
        self.first_redo = True

    def redo(self) -> None:
        if self.first_redo:
            self.first_redo = False
            return
        from models.heap import clone_heap
        self.canvas._rebuild_heap_items(clone_heap(self.new_heap), self.origin)

    def undo(self) -> None:
        from models.heap import clone_heap
        self.canvas._rebuild_heap_items(clone_heap(self.old_heap), self.origin)


class MergeItemsCommand(QUndoCommand):
    def __init__(
        self,
        canvas: CanvasView,
        old_items: list[QGraphicsItem],
        new_item: QGraphicsItem,
        text: str = "Merge Items",
    ) -> None:
        super().__init__(text)
        self.canvas = canvas
        self.old_items = list(old_items)
        self.new_item = new_item

    def redo(self) -> None:
        for item in self.old_items:
            if item.scene() is not None:
                self.canvas.scene.removeItem(item)

        self.canvas.scene.addItem(self.new_item)
        self.canvas.scene.clearSelection()
        self.new_item.setSelected(True)

    def undo(self) -> None:
        if self.new_item.scene() is not None:
            self.canvas.scene.removeItem(self.new_item)

        for item in self.old_items:
            self.canvas.scene.addItem(item)

        self.canvas.scene.clearSelection()
        for item in self.old_items:
            item.setSelected(True)


