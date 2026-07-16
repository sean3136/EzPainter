from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QColor, QAction
from PySide6.QtWidgets import (
    QMenu,
    QInputDialog,
    QGraphicsSceneContextMenuEvent,
)

from items.tree_node_item import TreeNodeItem
from models.heap import HeapNode

if TYPE_CHECKING:
    from canvas.canvas_view import CanvasView


class HeapNodeItem(TreeNodeItem):
    def __init__(
        self,
        model: HeapNode,
        canvas: CanvasView,
        is_min_heap: bool,
    ) -> None:
        fill_color = QColor("#009688") if is_min_heap else QColor("#673ab7")
        super().__init__(
            value=str(model.value),
            canvas=canvas,
            fill_color=fill_color,
        )
        self.model = model
        self.is_min_heap = is_min_heap

    def contextMenuEvent(
        self,
        event: QGraphicsSceneContextMenuEvent,
    ) -> None:
        menu = QMenu()

        insert_action = QAction("Insert Value", menu)
        extract_action = QAction("Extract Min" if self.is_min_heap else "Extract Max", menu)
        delete_action = QAction("Delete Node", menu)
        relayout_action = QAction("Re-layout Tree", menu)

        menu.addAction(insert_action)
        menu.addAction(extract_action)
        menu.addAction(delete_action)
        menu.addSeparator()
        menu.addAction(relayout_action)

        selected_action = menu.exec(event.screenPos())

        if selected_action == insert_action:
            self._insert_value()
        elif selected_action == extract_action:
            self.canvas.extract_heap_root()
        elif selected_action == delete_action:
            self.canvas.delete_heap_value(self.model.value)
        elif selected_action == relayout_action:
            self.canvas.relayout_heap(self.canvas.heap_root)

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
        self.canvas.insert_heap_value(val)

    def mouseDoubleClickEvent(self, event) -> None:
        self._insert_value()
        event.accept()
