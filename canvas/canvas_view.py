from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QKeyEvent,
    QKeySequence,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPixmap,
    QWheelEvent,
    QUndoStack,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QGraphicsScene,
    QGraphicsView,
    QCheckBox,
    QDialog,
    QGraphicsItem,
)
from collections import deque
from dialogs.table_dialog import TableDialog
from items.table_item import TableItem
from items.brush_stroke_item import BrushStrokeItem
from items.image_item import ImageItem
from items.shape_item import EllipseItem, RectangleItem
from items.graph_edge_item import GraphEdgeItem
from items.graph_node_item import GraphNodeItem
from items.binary_tree_node_item import BinaryTreeNodeItem

from .tool_mode import ToolMode
from dialogs.binary_tree_dialog import BinaryTreeDialog
from layouts.binary_tree_layout import (
    calculate_binary_tree_positions,
)
from layouts.complete_tree_layout import (
    calculate_complete_tree_positions,
)
from models.binary_tree_node import BinaryTreeNode
from commands.undo_commands import (
    AddItemsCommand,
    DeleteItemsCommand,
    MoveItemsCommand,
    AddBinaryChildCommand,
    DeleteBinarySubtreeCommand,
    ModifyRedBlackTreeCommand,
    ModifyBSTCommand,
    ModifyHeapCommand,
)

from dialogs.red_black_tree_dialog import (
    RedBlackTreeDialog,
)
from dialogs.bst_dialog import (
    BSTDialog,
)
from dialogs.heap_dialog import (
    HeapDialog,
)
from items.red_black_node_item import (
    RedBlackNodeItem,
)
from items.bst_node_item import (
    BSTNodeItem,
)
from items.heap_node_item import (
    HeapNodeItem,
)
from models.red_black_tree import (
    RedBlackNode,
    RedBlackTree,
    clone_rb_tree,
)
from models.bst import (
    BSTNode,
    BST,
    clone_bst,
)
from models.heap import (
    HeapNode,
    Heap,
    clone_heap,
)


class CanvasView(QGraphicsView):
    tool_changed = Signal(object)
    zoom_changed = Signal(float)

    def __init__(self) -> None:
        super().__init__()

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 1600, 900)
        self.setScene(self.scene)

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.current_tool = ToolMode.SELECT

        self.brush_color = QColor("#000000")
        self.brush_width = 4

        self.current_path: QPainterPath | None = None
        self.current_stroke_item: BrushStrokeItem | None = None

        self.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
        )

        self.setBackgroundBrush(QColor("#d9d9d9"))

        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.is_space_pressed = False
        self.previous_drag_mode = None

        self.setMouseTracking(True)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.shape_start_position: QPointF | None = None
        self.preview_shape = None
        self.pending_connection_node: GraphNodeItem | None = None
        self.graph_node_counter = 1
        self.graph_directed = False
        self.binary_tree_root: BinaryTreeNode | None = None

        self.binary_tree_node_items: dict[
            int,
            BinaryTreeNodeItem,
        ] = {}

        self.binary_tree_edges: dict[
            tuple[int, int],
            GraphEdgeItem,
        ] = {}
        self.undo_stack = QUndoStack(self)
        self._move_start_positions: dict[
            QGraphicsItem,
            QPointF,
        ] = {}
        self.rb_tree_root: RedBlackNode | None = None

        self.rb_tree_node_items: dict[
            int,
            RedBlackNodeItem,
        ] = {}

        self.rb_tree_edges: dict[
            tuple[int, int],
            GraphEdgeItem,
        ] = {}

        self.bst_root: BSTNode | None = None
        self.bst_node_items: dict[
            int,
            BSTNodeItem,
        ] = {}
        self.bst_edges: dict[
            tuple[int, int],
            GraphEdgeItem,
        ] = {}

        self.heap_root: HeapNode | None = None
        self.heap_model: Heap | None = None
        self.heap_node_items: dict[
            int,
            HeapNodeItem,
        ] = {}
        self.heap_edges: dict[
            tuple[int, int],
            GraphEdgeItem,
        ] = {}

    def animate_item_positions(
        self,
        item_positions: dict[QGraphicsItem, QPointF],
        duration: int = 350,
    ) -> None:
        if not item_positions:
            return

        from PySide6.QtCore import QTimeLine

        start_positions = {item: QPointF(item.pos()) for item in item_positions.keys()}

        if not hasattr(self, "_active_timelines"):
            self._active_timelines = set()

        timeline = QTimeLine(duration, self)
        self._active_timelines.add(timeline)
        timeline.setFrameRange(0, 100)

        def update_frame(frame: int) -> None:
            t = frame / 100.0
            factor = 1.0 - (1.0 - t) ** 3
            for item, end_pos in item_positions.items():
                if item.scene() is not None:
                    start_pos = start_positions[item]
                    current_pos = start_pos + (end_pos - start_pos) * factor
                    item.setPos(current_pos)

        def clean_up() -> None:
            self._active_timelines.discard(timeline)
            timeline.deleteLater()

        timeline.frameChanged.connect(update_frame)
        timeline.finished.connect(clean_up)
        timeline.start()

    def set_tool(self, tool: ToolMode) -> None:
        if tool != ToolMode.CONNECT_NODES:
            self.cancel_pending_connection()
        self.current_tool = tool

        if tool == ToolMode.SELECT:
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)

        elif tool in (
            ToolMode.BRUSH,
            ToolMode.RECTANGLE,
            ToolMode.ELLIPSE,
            ToolMode.TABLE,
            ToolMode.BINARY_TREE,
            ToolMode.RED_BLACK_TREE,
            ToolMode.BST,
            ToolMode.MIN_HEAP,
            ToolMode.MAX_HEAP,
            ToolMode.GRAPH_NODE,
            ToolMode.CONNECT_NODES,
        ):
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)

        self.tool_changed.emit(tool)

    def set_brush_color(self, color: QColor) -> None:
        self.brush_color = color

    def set_brush_width(self, width: int) -> None:
        self.brush_width = width

    def paste_from_clipboard(self) -> None:
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        if not mime_data.hasImage():
            return

        image = clipboard.image()

        if image.isNull():
            return

        pixmap = QPixmap.fromImage(image)

        image_item = ImageItem(
            pixmap,
            undo_stack=self.undo_stack,
        )

        viewport_center = self.viewport().rect().center()
        scene_center = self.mapToScene(viewport_center)

        item_rect = image_item.boundingRect()

        image_item.setPos(
            scene_center.x() - item_rect.width() / 2,
            scene_center.y() - item_rect.height() / 2,
        )

        maximum_width = 600.0
        maximum_height = 500.0

        if item_rect.width() > maximum_width or item_rect.height() > maximum_height:
            scale_x = maximum_width / item_rect.width()
            scale_y = maximum_height / item_rect.height()

            image_item.setScale(min(scale_x, scale_y))

        self.scene.clearSelection()
        self.scene.clearSelection()

        self.add_item_with_undo(
            image_item,
            "Paste image",
        )

        image_item.setSelected(True)

    def delete_selected_items(self) -> None:
        selected_items = list(self.scene.selectedItems())

        if not selected_items:
            return

        rb_node_items: list[RedBlackNodeItem] = []
        for item in selected_items:
            top_item = item
            while top_item.parentItem() is not None:
                top_item = top_item.parentItem()
            if isinstance(top_item, RedBlackNodeItem) and top_item not in rb_node_items:
                rb_node_items.append(top_item)

        for rb_item in rb_node_items:
            self.delete_red_black_value(rb_item.model.value)

        bst_node_items: list[BSTNodeItem] = []
        for item in selected_items:
            top_item = item
            while top_item.parentItem() is not None:
                top_item = top_item.parentItem()
            if isinstance(top_item, BSTNodeItem) and top_item not in bst_node_items:
                bst_node_items.append(top_item)

        for bst_item in bst_node_items:
            self.delete_bst_value(bst_item.model.value)

        heap_node_items: list[HeapNodeItem] = []
        for item in selected_items:
            top_item = item
            while top_item.parentItem() is not None:
                top_item = top_item.parentItem()
            if isinstance(top_item, HeapNodeItem) and top_item not in heap_node_items:
                heap_node_items.append(top_item)

        for heap_item in heap_node_items:
            self.delete_heap_value(heap_item.model.value)

        items_to_delete: set[QGraphicsItem] = set()

        for item in selected_items:
            if item.parentItem() is not None:
                item = item.parentItem()

            if isinstance(item, (RedBlackNodeItem, BSTNodeItem, HeapNodeItem)):
                continue
            from items.graph_edge_item import GraphEdgeItem
            if isinstance(item, GraphEdgeItem) and (
                isinstance(item.source_node, (RedBlackNodeItem, BSTNodeItem, HeapNodeItem))
                or isinstance(item.target_node, (RedBlackNodeItem, BSTNodeItem, HeapNodeItem))
            ):
                continue

            items_to_delete.add(item)

            if isinstance(item, GraphNodeItem):
                for edge in item.edges:
                    if not (
                        isinstance(edge.source_node, (RedBlackNodeItem, BSTNodeItem, HeapNodeItem))
                        or isinstance(edge.target_node, (RedBlackNodeItem, BSTNodeItem, HeapNodeItem))
                    ):
                        items_to_delete.add(edge)

        if not items_to_delete:
            self.pending_connection_node = None
            return

        ordered_items = sorted(
            items_to_delete,
            key=lambda graphics_item: graphics_item.zValue(),
        )

        command = DeleteItemsCommand(
            canvas=self,
            items=ordered_items,
            text=(
                "Delete item"
                if len(ordered_items) == 1
                else f"Delete {len(ordered_items)} items"
            ),
        )

        self.undo_stack.push(command)

        self.pending_connection_node = None
        remaining_graph_nodes = [
            item
            for item in self.scene.items()
            if (
                isinstance(item, GraphNodeItem)
                and not isinstance(
                    item,
                    BinaryTreeNodeItem,
                )
            )
        ]

        if not remaining_graph_nodes:
            self.graph_node_counter = 1

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_pending_connection()

            self.set_tool(ToolMode.SELECT)

            event.accept()
            return

        if event.matches(QKeySequence.StandardKey.Paste):
            self.paste_from_clipboard()
            event.accept()
            return

        if event.key() in (
            Qt.Key.Key_Delete,
            Qt.Key.Key_Backspace,
        ):
            self.delete_selected_items()
            event.accept()
            return

        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            if not self.is_space_pressed:
                self.is_space_pressed = True
                self.previous_drag_mode = self.dragMode()
                self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
                event.accept()
                return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            if self.is_space_pressed:
                self.is_space_pressed = False
                if self.previous_drag_mode is not None:
                    self.setDragMode(self.previous_drag_mode)
                event.accept()
                return
        super().keyReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier):
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
            self.zoom_changed.emit(self.transform().m11())
            event.accept()
            return

        if self.current_tool == ToolMode.SELECT:
            selected_items = self.scene.selectedItems()

            selected_images = [
                item for item in selected_items if isinstance(item, ImageItem)
            ]

            if selected_images:
                factor = 1.1 if event.angleDelta().y() > 0 else 1 / 1.1

                for image_item in selected_images:
                    image_item.scale_by(factor)

                event.accept()
                return

        super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if (
            self.current_tool == ToolMode.BINARY_TREE
            and event.button() == Qt.MouseButton.LeftButton
        ):
            scene_position = self.mapToScene(event.position().toPoint())

            self.create_binary_tree(scene_position)

            event.accept()
            return
        if (
            self.current_tool == ToolMode.GRAPH_NODE
            and event.button() == Qt.MouseButton.LeftButton
        ):
            scene_position = self.mapToScene(event.position().toPoint())

            self.create_graph_node(scene_position)

            event.accept()
            return
        if (
            self.current_tool == ToolMode.CONNECT_NODES
            and event.button() == Qt.MouseButton.LeftButton
        ):
            clicked_node = self.graph_node_at(event.position().toPoint())

            if clicked_node is None:
                self.cancel_pending_connection()

                event.accept()
                return

            if self.pending_connection_node is None:
                self.pending_connection_node = clicked_node

                self.scene.clearSelection()
                clicked_node.setSelected(True)

            else:
                source_node = self.pending_connection_node
                target_node = clicked_node

                self.create_graph_edge(
                    source_node,
                    target_node,
                )

                self.pending_connection_node = None

                self.scene.clearSelection()
                target_node.setSelected(True)

            event.accept()
            return
        if (
            self.current_tool == ToolMode.BRUSH
            and event.button() == Qt.MouseButton.LeftButton
        ):
            scene_position = self.mapToScene(event.position().toPoint())

            self.current_path = QPainterPath()
            self.current_path.moveTo(scene_position)

            self.current_stroke_item = BrushStrokeItem(
                path=self.current_path,
                color=self.brush_color,
                width=self.brush_width,
            )

            self.scene.addItem(self.current_stroke_item)

            event.accept()
            return

        if (
            self.current_tool
            in (
                ToolMode.RECTANGLE,
                ToolMode.ELLIPSE,
            )
            and event.button() == Qt.MouseButton.LeftButton
        ):
            scene_position = self.mapToScene(event.position().toPoint())

            self.shape_start_position = scene_position

            initial_rect = QRectF(
                scene_position,
                scene_position,
            ).normalized()

            if self.current_tool == ToolMode.RECTANGLE:
                self.preview_shape = RectangleItem(
                    initial_rect,
                    color=self.brush_color,
                    undo_stack=self.undo_stack,
                )
            else:
                self.preview_shape = EllipseItem(
                    initial_rect,
                    color=self.brush_color,
                    undo_stack=self.undo_stack,
                )

            self.preview_shape.setSelected(False)
            self.scene.addItem(self.preview_shape)

            event.accept()
            return

        if (
            self.current_tool == ToolMode.TABLE
            and event.button() == Qt.MouseButton.LeftButton
        ):
            scene_position = self.mapToScene(event.position().toPoint())

            self.create_table(scene_position)

            event.accept()
            return

        super().mousePressEvent(event)

        if (
            self.current_tool == ToolMode.SELECT
            and event.button() == Qt.MouseButton.LeftButton
        ):
            movable_items = self._get_movable_top_level_items()

            self._move_start_positions = {
                item: QPointF(item.pos()) for item in movable_items
            }

        if (
            self.current_tool == ToolMode.RED_BLACK_TREE
            and event.button() == Qt.MouseButton.LeftButton
        ):
            scene_position = self.mapToScene(event.position().toPoint())

            self.create_red_black_tree(scene_position)

            event.accept()
            return

        if (
            self.current_tool in (ToolMode.BST, ToolMode.MIN_HEAP, ToolMode.MAX_HEAP)
            and event.button() == Qt.MouseButton.LeftButton
        ):
            scene_position = self.mapToScene(event.position().toPoint())

            if self.current_tool == ToolMode.BST:
                self.create_bst(scene_position)
            elif self.current_tool == ToolMode.MIN_HEAP:
                self.create_heap(scene_position, is_min_heap=True)
            elif self.current_tool == ToolMode.MAX_HEAP:
                self.create_heap(scene_position, is_min_heap=False)

            event.accept()
            return

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if (
            self.current_tool == ToolMode.BRUSH
            and self.current_path is not None
            and self.current_stroke_item is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            scene_position = self.mapToScene(event.position().toPoint())

            self.current_path.lineTo(scene_position)

            self.current_stroke_item.setPath(self.current_path)

            event.accept()
            return
        if (
            self.current_tool
            in (
                ToolMode.RECTANGLE,
                ToolMode.ELLIPSE,
            )
            and self.shape_start_position is not None
            and self.preview_shape is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            current_position = self.mapToScene(event.position().toPoint())

            rect = QRectF(
                self.shape_start_position,
                current_position,
            ).normalized()

            self.preview_shape.setPos(rect.topLeft())
            self.preview_shape.setRect(
                0,
                0,
                rect.width(),
                rect.height(),
            )

            self.preview_shape.update_handle_positions()

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if (
            self.current_tool == ToolMode.BRUSH
            and event.button() == Qt.MouseButton.LeftButton
            and self.current_path is not None
            and self.current_stroke_item is not None
        ):
            scene_position = self.mapToScene(event.position().toPoint())

            self.current_path.lineTo(scene_position)

            self.current_stroke_item.setPath(self.current_path)

            completed_stroke = self.current_stroke_item

            self.current_path = None
            self.current_stroke_item = None

            command = AddItemsCommand(
                canvas=self,
                items=[completed_stroke],
                text="Draw stroke",
            )

            self.undo_stack.push(command)

            event.accept()
            return

        if (
            self.current_tool
            in (
                ToolMode.RECTANGLE,
                ToolMode.ELLIPSE,
            )
            and event.button() == Qt.MouseButton.LeftButton
            and self.preview_shape is not None
        ):
            minimum_size = 5

            if (
                self.preview_shape.rect().width() < minimum_size
                or self.preview_shape.rect().height() < minimum_size
            ):
                self.scene.removeItem(self.preview_shape)
            else:
                completed_shape = self.preview_shape

                self.scene.clearSelection()
                completed_shape.setSelected(True)

                command_text = (
                    "Create rectangle"
                    if self.current_tool == ToolMode.RECTANGLE
                    else "Create ellipse"
                )

                command = AddItemsCommand(
                    canvas=self,
                    items=[completed_shape],
                    text=command_text,
                )

                self.undo_stack.push(command)

            self.shape_start_position = None
            self.preview_shape = None

            self.set_tool(ToolMode.SELECT)

            event.accept()
            return

        super().mouseReleaseEvent(event)

        if (
            self.current_tool == ToolMode.SELECT
            and event.button() == Qt.MouseButton.LeftButton
            and self._move_start_positions
        ):
            moved_items: list[QGraphicsItem] = []
            old_positions: dict[QGraphicsItem, QPointF] = {}
            new_positions: dict[QGraphicsItem, QPointF] = {}

            for item, old_position in self._move_start_positions.items():
                if item.scene() is not self.scene:
                    continue

                new_position = QPointF(item.pos())

                if new_position != old_position:
                    moved_items.append(item)
                    old_positions[item] = old_position
                    new_positions[item] = new_position

            if moved_items:
                command = MoveItemsCommand(
                    items=moved_items,
                    old_positions=old_positions,
                    new_positions=new_positions,
                )

                self.undo_stack.push(command)

            self._move_start_positions.clear()

    def create_table(self, scene_position) -> None:
        dialog = TableDialog(self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        rows, columns, cell_width, cell_height = dialog.get_table_settings()

        table_item = TableItem(
            rows=rows,
            columns=columns,
            cell_width=cell_width,
            cell_height=cell_height,
            color=self.brush_color,
            undo_stack=self.undo_stack,
        )

        table_item.setPos(scene_position)

        self.scene.clearSelection()

        self.add_item_with_undo(
            table_item,
            "Create table",
        )

        table_item.setSelected(True)
        self.set_tool(ToolMode.SELECT)

    def create_graph_node(
        self,
        scene_position: QPointF,
        value: str | None = None,
    ) -> GraphNodeItem:
        if value is None:
            value = str(self.graph_node_counter)
            self.graph_node_counter += 1

        node = GraphNodeItem(value=value)

        node_rect = node.boundingRect()

        node.setPos(
            scene_position.x() - node_rect.width() / 2,
            scene_position.y() - node_rect.height() / 2,
        )

        self.scene.clearSelection()
        self.add_item_with_undo(
            node,
            "Create graph node",
        )
        node.setSelected(True)

        return node

    def create_graph_edge(
        self,
        source_node: GraphNodeItem,
        target_node: GraphNodeItem,
        directed: bool | None = None,
    ) -> GraphEdgeItem | None:
        if source_node is target_node:
            return None

        for edge in source_node.edges:
            same_direction = (
                edge.source_node is source_node and edge.target_node is target_node
            )

            reverse_direction = (
                not edge.directed
                and edge.source_node is target_node
                and edge.target_node is source_node
            )

            if same_direction or reverse_direction:
                return None

        if directed is None:
            directed = self.graph_directed

        edge = GraphEdgeItem(
            source_node=source_node,
            target_node=target_node,
            directed=directed,
        )

        self.add_item_with_undo(
            edge,
            "Connect nodes",
        )

        return edge

    def graph_node_at(
        self,
        view_position,
    ) -> GraphNodeItem | None:
        item = self.itemAt(view_position)

        while item is not None:
            if isinstance(item, GraphNodeItem):
                return item

            item = item.parentItem()

        return None

    def cancel_pending_connection(self) -> None:
        self.pending_connection_node = None
        self.scene.clearSelection()

    def set_graph_directed(self, directed: bool) -> None:
        self.graph_directed = directed

    def build_binary_tree_model(
        self,
        values: list[str | None],
    ) -> BinaryTreeNode | None:
        if not values or values[0] is None:
            return None

        root = BinaryTreeNode(values[0])

        queue = deque([root])
        index = 1

        while queue and index < len(values):
            parent = queue.popleft()

            if index < len(values):
                left_value = values[index]
                index += 1

                if left_value is not None:
                    left_node = BinaryTreeNode(left_value)
                    parent.set_left(left_node)
                    queue.append(left_node)

            if index < len(values):
                right_value = values[index]
                index += 1

                if right_value is not None:
                    right_node = BinaryTreeNode(right_value)
                    parent.set_right(right_node)
                    queue.append(right_node)

        return root

    def create_binary_tree(
        self,
        scene_position,
    ) -> None:
        dialog = BinaryTreeDialog(self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        values = dialog.get_values()

        root = self.build_binary_tree_model(values)

        if root is None:
            return

        self.binary_tree_root = root

        created_items = self._create_binary_tree_items(root)

        self.relayout_binary_tree(
            root,
            origin=scene_position,
        )

        command = AddItemsCommand(
            canvas=self,
            items=created_items,
            text="Create binary tree",
        )

        self.undo_stack.push(command)

        self.set_tool(ToolMode.SELECT)

    def _create_binary_tree_items(
        self,
        root: BinaryTreeNode,
    ) -> list[QGraphicsItem]:
        created_items: list[QGraphicsItem] = []

        def traverse(
            node: BinaryTreeNode | None,
        ) -> None:
            if node is None:
                return

            node_item = BinaryTreeNodeItem(
                model=node,
                canvas=self,
            )

            self.scene.addItem(node_item)
            created_items.append(node_item)

            self.binary_tree_node_items[id(node)] = node_item

            traverse(node.left)
            traverse(node.right)

        traverse(root)

        created_edges = self._rebuild_binary_tree_edges(root)

        created_items.extend(created_edges)

        return created_items

    def _rebuild_binary_tree_edges(
        self,
        root: BinaryTreeNode,
    ) -> list[GraphEdgeItem]:
        created_edges: list[GraphEdgeItem] = []
        for edge in list(self.binary_tree_edges.values()):
            edge.detach()

            if edge.scene() is self.scene:
                self.scene.removeItem(edge)

        self.binary_tree_edges.clear()

        def traverse(
            node: BinaryTreeNode | None,
        ) -> None:
            if node is None:
                return

            parent_item = self.binary_tree_node_items[id(node)]

            for child in (
                node.left,
                node.right,
            ):
                if child is None:
                    continue

                child_item = self.binary_tree_node_items[id(child)]

                edge = GraphEdgeItem(
                    source_node=parent_item,
                    target_node=child_item,
                    directed=False,
                )

                self.scene.addItem(edge)
                created_edges.append(edge)

                self.binary_tree_edges[(id(node), id(child))] = edge

            traverse(node.left)
            traverse(node.right)

        traverse(root)

        return created_edges

    def relayout_binary_tree(
        self,
        root: BinaryTreeNode | None,
        origin=None,
    ) -> None:
        if root is None:
            return

        if origin is None:
            root_item = self.binary_tree_node_items.get(id(root))

            if root_item is None:
                return

            origin = root_item.pos()

        positions = calculate_binary_tree_positions(
            root=root,
            horizontal_gap=110.0,
            vertical_gap=110.0,
        )

        minimum_x = min(x for x, _ in positions.values())

        root_x, root_y = positions[root]

        origin_x = origin.x()
        origin_y = origin.y()

        targets = {}
        for model, (x, y) in positions.items():
            item = self.binary_tree_node_items[id(model)]
            if item is not None:
                target_x = origin_x + x - root_x
                target_y = origin_y + y - root_y
                targets[item] = QPointF(target_x, target_y)

        self.animate_item_positions(targets)

    def relayout_rb_tree(
        self,
        root: RedBlackNode | None,
        origin=None,
    ) -> None:
        if root is None:
            return

        if origin is None:
            root_item = self.rb_tree_node_items.get(id(root))

            if root_item is None:
                return

            origin = root_item.pos()

        positions = calculate_binary_tree_positions(
            root=root,
            horizontal_gap=110.0,
            vertical_gap=110.0,
        )

        root_x, root_y = positions[root]

        origin_x = origin.x()
        origin_y = origin.y()

        targets = {}
        for model, (x, y) in positions.items():
            item = self.rb_tree_node_items.get(id(model))
            if item is not None:
                target_x = origin_x + x - root_x
                target_y = origin_y + y - root_y
                targets[item] = QPointF(target_x, target_y)

        self.animate_item_positions(targets)

    def add_binary_tree_child(
        self,
        parent_model: BinaryTreeNode,
        value: str,
        is_left: bool,
    ) -> None:
        if is_left and parent_model.left is not None:
            return

        if not is_left and parent_model.right is not None:
            return

        self.undo_stack.push(
            AddBinaryChildCommand(
                canvas=self,
                parent_model=parent_model,
                value=value,
                is_left=is_left,
            )
        )

    def delete_binary_subtree(
        self,
        node: BinaryTreeNode,
    ) -> None:
        self.undo_stack.push(
            DeleteBinarySubtreeCommand(
                canvas=self,
                subtree_root=node,
            )
        )

    def _delete_entire_binary_tree(self) -> None:
        for edge in list(self.binary_tree_edges.values()):
            edge.detach()

            if edge.scene() is self.scene:
                self.scene.removeItem(edge)

        for item in list(self.binary_tree_node_items.values()):
            if item.scene() is self.scene:
                self.scene.removeItem(item)

        self.binary_tree_edges.clear()
        self.binary_tree_node_items.clear()

        self.binary_tree_root = None

    def add_items_with_undo(
        self,
        items: list[QGraphicsItem],
        command_text: str = "Add item",
    ) -> None:
        if not items:
            return

        for item in items:
            if item.scene() is None:
                self.scene.addItem(item)

        command = AddItemsCommand(
            canvas=self,
            items=items,
            text=command_text,
        )

        self.undo_stack.push(command)

    def add_item_with_undo(
        self,
        item: QGraphicsItem,
        command_text: str = "Add item",
    ) -> None:
        self.add_items_with_undo(
            [item],
            command_text,
        )

    def _get_movable_top_level_items(
        self,
    ) -> list[QGraphicsItem]:
        result: list[QGraphicsItem] = []

        for item in self.scene.selectedItems():
            top_level_item = item

            while top_level_item.parentItem() is not None:
                top_level_item = top_level_item.parentItem()

            if not (
                top_level_item.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            ):
                continue

            if top_level_item not in result:
                result.append(top_level_item)

        return result

    def reset_document_state(self) -> None:
        self.graph_node_counter = 1
        self.pending_connection_node = None

        self.binary_tree_root = None
        self.binary_tree_node_items.clear()
        self.binary_tree_edges.clear()

        self.rb_tree_root = None
        self.rb_tree_node_items.clear()
        self.rb_tree_edges.clear()

        self.bst_root = None
        self.bst_node_items.clear()
        self.bst_edges.clear()

        self.heap_root = None
        self.heap_model = None
        self.heap_node_items.clear()
        self.heap_edges.clear()

        self.resetTransform()
        self.zoom_changed.emit(1.0)

    def create_red_black_tree(
        self,
        scene_position: QPointF,
    ) -> None:
        dialog = RedBlackTreeDialog(self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        values = dialog.get_values()

        tree = RedBlackTree()

        for value in values:
            tree.insert(value)

        if tree.root is None:
            return

        old_root = clone_rb_tree(self.rb_tree_root)

        self._rebuild_rb_tree_items(tree.root, scene_position)

        command = ModifyRedBlackTreeCommand(
            canvas=self,
            old_root=old_root,
            new_root=tree.root,
            origin=scene_position,
            text="Create red-black tree",
        )
        self.undo_stack.push(command)

        self.set_tool(ToolMode.SELECT)

    def _rebuild_rb_tree_items(
        self,
        root: RedBlackNode | None,
        origin: QPointF,
    ) -> list[QGraphicsItem]:
        old_positions = {item.model.value: item.pos() for item in self.rb_tree_node_items.values()}
        old_parents = {}
        for item in self.rb_tree_node_items.values():
            if item.model.parent is not None:
                old_parents[item.model.value] = item.model.parent.value

        for edge in list(self.rb_tree_edges.values()):
            edge.detach()

            if edge.scene() is self.scene:
                self.scene.removeItem(edge)

        self.rb_tree_edges.clear()

        for item in list(self.rb_tree_node_items.values()):
            if item.scene() is self.scene:
                self.scene.removeItem(item)

        self.rb_tree_node_items.clear()

        self.rb_tree_root = root

        if root is None:
            return []

        created_items: list[QGraphicsItem] = []

        def create_nodes(
            node: RedBlackNode | None,
        ) -> None:
            if node is None:
                return

            item = RedBlackNodeItem(node, self)

            self.scene.addItem(item)
            created_items.append(item)

            self.rb_tree_node_items[id(node)] = item

            create_nodes(node.left)
            create_nodes(node.right)

        create_nodes(root)

        def create_edges(
            node: RedBlackNode | None,
        ) -> None:
            if node is None:
                return

            parent_item = self.rb_tree_node_items[id(node)]

            for child in (
                node.left,
                node.right,
            ):
                if child is None:
                    continue

                child_item = self.rb_tree_node_items[id(child)]

                edge = GraphEdgeItem(
                    source_node=parent_item,
                    target_node=child_item,
                    directed=False,
                )

                self.scene.addItem(edge)
                created_items.append(edge)

                self.rb_tree_edges[(id(node), id(child))] = edge

            create_edges(node.left)
            create_edges(node.right)

        create_edges(root)

        for id_val, item in self.rb_tree_node_items.items():
            val = item.model.value
            if val in old_positions:
                item.setPos(old_positions[val])
            else:
                parent_val = old_parents.get(val)
                if parent_val is None and item.model.parent is not None:
                    parent_val = item.model.parent.value
                if parent_val is not None and parent_val in old_positions:
                    item.setPos(old_positions[parent_val])
                else:
                    item.setPos(origin)

        positions = calculate_binary_tree_positions(
            root,
            horizontal_gap=110,
            vertical_gap=110,
        )

        root_x, root_y = positions[root]

        targets = {}
        for model, (x, y) in positions.items():
            item = self.rb_tree_node_items[id(model)]
            targets[item] = QPointF(
                origin.x() + x - root_x,
                origin.y() + y - root_y,
            )

        self.animate_item_positions(targets)

        return created_items

    def insert_red_black_value(
        self,
        value: int,
    ) -> None:
        if self.rb_tree_root is None:
            origin = QPointF(400, 300)
        else:
            root_item = self.rb_tree_node_items.get(id(self.rb_tree_root))
            origin = root_item.pos() if root_item is not None else QPointF(400, 300)

        old_root = clone_rb_tree(self.rb_tree_root)

        tree = RedBlackTree()
        tree.root = clone_rb_tree(self.rb_tree_root)

        tree.insert(value)

        self._rebuild_rb_tree_items(tree.root, origin)

        command = ModifyRedBlackTreeCommand(
            canvas=self,
            old_root=old_root,
            new_root=tree.root,
            origin=origin,
            text=f"Insert {value} into red-black tree",
        )
        self.undo_stack.push(command)

    def delete_red_black_value(
        self,
        value: int,
    ) -> None:
        if self.rb_tree_root is None:
            return

        root_item = self.rb_tree_node_items.get(id(self.rb_tree_root))
        origin = root_item.pos() if root_item is not None else QPointF(400, 300)

        old_root = clone_rb_tree(self.rb_tree_root)

        tree = RedBlackTree()
        tree.root = clone_rb_tree(self.rb_tree_root)

        tree.delete(value)

        self._rebuild_rb_tree_items(tree.root, origin)

        command = ModifyRedBlackTreeCommand(
            canvas=self,
            old_root=old_root,
            new_root=tree.root,
            origin=origin,
            text=f"Delete {value} from red-black tree",
        )
        self.undo_stack.push(command)

    def create_bst(self, scene_position: QPointF) -> None:
        dialog = BSTDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.get_values()
        tree = BST()
        for value in values:
            tree.insert(value)
        if tree.root is None:
            return

        old_root = clone_bst(self.bst_root)
        self._rebuild_bst_items(tree.root, scene_position)

        command = ModifyBSTCommand(
            canvas=self,
            old_root=old_root,
            new_root=tree.root,
            origin=scene_position,
            text="Create BST",
        )
        self.undo_stack.push(command)
        self.set_tool(ToolMode.SELECT)

    def _rebuild_bst_items(self, root: BSTNode | None, origin: QPointF) -> list[QGraphicsItem]:
        old_positions = {item.model.value: item.pos() for item in self.bst_node_items.values()}
        old_parents = {}
        for item in self.bst_node_items.values():
            if item.model.parent is not None:
                old_parents[item.model.value] = item.model.parent.value

        for edge in list(self.bst_edges.values()):
            edge.detach()
            if edge.scene() is self.scene:
                self.scene.removeItem(edge)
        self.bst_edges.clear()

        for item in list(self.bst_node_items.values()):
            if item.scene() is self.scene:
                self.scene.removeItem(item)
        self.bst_node_items.clear()

        self.bst_root = root
        if root is None:
            return []

        created_items: list[QGraphicsItem] = []

        def create_nodes(node: BSTNode | None) -> None:
            if node is None:
                return
            item = BSTNodeItem(node, self)
            self.scene.addItem(item)
            created_items.append(item)
            self.bst_node_items[id(node)] = item
            create_nodes(node.left)
            create_nodes(node.right)

        create_nodes(root)

        def create_edges(node: BSTNode | None) -> None:
            if node is None:
                return
            parent_item = self.bst_node_items[id(node)]
            for child in (node.left, node.right):
                if child is None:
                    continue
                child_item = self.bst_node_items[id(child)]
                edge = GraphEdgeItem(
                    source_node=parent_item,
                    target_node=child_item,
                    directed=False,
                )
                self.scene.addItem(edge)
                created_items.append(edge)
                self.bst_edges[(id(node), id(child))] = edge
            create_edges(node.left)
            create_edges(node.right)

        create_edges(root)

        for id_val, item in self.bst_node_items.items():
            val = item.model.value
            if val in old_positions:
                item.setPos(old_positions[val])
            else:
                parent_val = old_parents.get(val)
                if parent_val is None and item.model.parent is not None:
                    parent_val = item.model.parent.value
                if parent_val is not None and parent_val in old_positions:
                    item.setPos(old_positions[parent_val])
                else:
                    item.setPos(origin)

        positions = calculate_binary_tree_positions(
            root,
            horizontal_gap=110,
            vertical_gap=110,
        )
        root_x, root_y = positions[root]

        targets = {}
        for model, (x, y) in positions.items():
            item = self.bst_node_items[id(model)]
            targets[item] = QPointF(
                origin.x() + x - root_x,
                origin.y() + y - root_y,
            )

        self.animate_item_positions(targets)

        return created_items

    def insert_bst_value(self, value: int) -> None:
        if self.bst_root is None:
            origin = QPointF(400, 300)
        else:
            root_item = self.bst_node_items.get(id(self.bst_root))
            origin = root_item.pos() if root_item is not None else QPointF(400, 300)

        old_root = clone_bst(self.bst_root)

        tree = BST()
        tree.root = clone_bst(self.bst_root)
        tree.insert(value)

        self._rebuild_bst_items(tree.root, origin)

        command = ModifyBSTCommand(
            canvas=self,
            old_root=old_root,
            new_root=tree.root,
            origin=origin,
            text=f"Insert {value} into BST",
        )
        self.undo_stack.push(command)

    def delete_bst_value(self, value: int) -> None:
        if self.bst_root is None:
            return
        root_item = self.bst_node_items.get(id(self.bst_root))
        origin = root_item.pos() if root_item is not None else QPointF(400, 300)

        old_root = clone_bst(self.bst_root)

        tree = BST()
        tree.root = clone_bst(self.bst_root)
        tree.delete(value)

        self._rebuild_bst_items(tree.root, origin)

        command = ModifyBSTCommand(
            canvas=self,
            old_root=old_root,
            new_root=tree.root,
            origin=origin,
            text=f"Delete {value} from BST",
        )
        self.undo_stack.push(command)

    def relayout_bst(self, root: BSTNode | None, origin=None) -> None:
        if root is None:
            return
        if origin is None:
            root_item = self.bst_node_items.get(id(root))
            if root_item is None:
                return
            origin = root_item.pos()

        positions = calculate_binary_tree_positions(
            root=root,
            horizontal_gap=110.0,
            vertical_gap=110.0,
        )
        root_x, root_y = positions[root]
        origin_x = origin.x()
        origin_y = origin.y()
        targets = {}
        for model, (x, y) in positions.items():
            item = self.bst_node_items[id(model)]
            if item is not None:
                targets[item] = QPointF(origin_x + x - root_x, origin_y + y - root_y)

        self.animate_item_positions(targets)

    def create_heap(self, scene_position: QPointF, is_min_heap: bool) -> None:
        dialog = HeapDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.get_values()
        heap = Heap(is_min_heap=is_min_heap)
        for value in values:
            heap.insert(value)
        if not heap.nodes:
            return

        old_heap = clone_heap(self.heap_model) if self.heap_model is not None else Heap(is_min_heap=is_min_heap)
        self._rebuild_heap_items(heap, scene_position)

        command = ModifyHeapCommand(
            canvas=self,
            old_heap=old_heap,
            new_heap=heap,
            origin=scene_position,
            text="Create Min-Heap" if is_min_heap else "Create Max-Heap",
        )
        self.undo_stack.push(command)
        self.set_tool(ToolMode.SELECT)

    def _rebuild_heap_items(self, heap: Heap, origin: QPointF) -> list[QGraphicsItem]:
        old_positions = {item.model.value: item.pos() for item in self.heap_node_items.values()}
        old_parents = {}
        for item in self.heap_node_items.values():
            if item.model.parent is not None:
                old_parents[item.model.value] = item.model.parent.value

        for edge in list(self.heap_edges.values()):
            edge.detach()
            if edge.scene() is self.scene:
                self.scene.removeItem(edge)
        self.heap_edges.clear()

        for item in list(self.heap_node_items.values()):
            if item.scene() is self.scene:
                self.scene.removeItem(item)
        self.heap_node_items.clear()

        self.heap_model = heap
        self.heap_root = heap.rebuild_tree()

        if self.heap_root is None:
            return []

        created_items: list[QGraphicsItem] = []

        def create_nodes(node: HeapNode | None) -> None:
            if node is None:
                return
            item = HeapNodeItem(node, self, is_min_heap=heap.is_min_heap)
            self.scene.addItem(item)
            created_items.append(item)
            self.heap_node_items[id(node)] = item
            create_nodes(node.left)
            create_nodes(node.right)

        create_nodes(self.heap_root)

        def create_edges(node: HeapNode | None) -> None:
            if node is None:
                return
            parent_item = self.heap_node_items[id(node)]
            for child in (node.left, node.right):
                if child is None:
                    continue
                child_item = self.heap_node_items[id(child)]
                edge = GraphEdgeItem(
                    source_node=parent_item,
                    target_node=child_item,
                    directed=False,
                )
                self.scene.addItem(edge)
                created_items.append(edge)
                self.heap_edges[(id(node), id(child))] = edge
            create_edges(node.left)
            create_edges(node.right)

        create_edges(self.heap_root)

        for id_val, item in self.heap_node_items.items():
            val = item.model.value
            if val in old_positions:
                item.setPos(old_positions[val])
            else:
                parent_val = old_parents.get(val)
                if parent_val is None and item.model.parent is not None:
                    parent_val = item.model.parent.value
                if parent_val is not None and parent_val in old_positions:
                    item.setPos(old_positions[parent_val])
                else:
                    item.setPos(origin)

        positions = calculate_complete_tree_positions(
            self.heap_root,
            horizontal_gap=80,
            vertical_gap=100,
        )
        root_x, root_y = positions[self.heap_root]

        targets = {}
        for model, (x, y) in positions.items():
            item = self.heap_node_items[id(model)]
            targets[item] = QPointF(
                origin.x() + x - root_x,
                origin.y() + y - root_y,
            )

        self.animate_item_positions(targets)

        return created_items

    def insert_heap_value(self, value: int) -> None:
        if self.heap_model is None:
            return
        origin = QPointF(400, 300)
        if self.heap_root is not None:
            root_item = self.heap_node_items.get(id(self.heap_root))
            if root_item is not None:
                origin = root_item.pos()

        old_heap = clone_heap(self.heap_model)
        heap = clone_heap(self.heap_model)
        heap.insert(value)

        self._rebuild_heap_items(heap, origin)

        command = ModifyHeapCommand(
            canvas=self,
            old_heap=old_heap,
            new_heap=heap,
            origin=origin,
            text=f"Insert {value} into Heap",
        )
        self.undo_stack.push(command)

    def extract_heap_root(self) -> None:
        if self.heap_model is None or not self.heap_model.nodes:
            return
        origin = QPointF(400, 300)
        if self.heap_root is not None:
            root_item = self.heap_node_items.get(id(self.heap_root))
            if root_item is not None:
                origin = root_item.pos()

        old_heap = clone_heap(self.heap_model)
        heap = clone_heap(self.heap_model)
        extracted = heap.extract_root()

        self._rebuild_heap_items(heap, origin)

        command = ModifyHeapCommand(
            canvas=self,
            old_heap=old_heap,
            new_heap=heap,
            origin=origin,
            text=f"Extract root ({extracted}) from Heap",
        )
        self.undo_stack.push(command)

    def delete_heap_value(self, value: int) -> None:
        if self.heap_model is None:
            return
        origin = QPointF(400, 300)
        if self.heap_root is not None:
            root_item = self.heap_node_items.get(id(self.heap_root))
            if root_item is not None:
                origin = root_item.pos()

        old_heap = clone_heap(self.heap_model)
        heap = clone_heap(self.heap_model)
        heap.delete(value)

        self._rebuild_heap_items(heap, origin)

        command = ModifyHeapCommand(
            canvas=self,
            old_heap=old_heap,
            new_heap=heap,
            origin=origin,
            text=f"Delete {value} from Heap",
        )
        self.undo_stack.push(command)

    def relayout_heap(self, root: HeapNode | None, origin=None) -> None:
        if root is None:
            return
        if origin is None:
            root_item = self.heap_node_items.get(id(root))
            if root_item is None:
                return
            origin = root_item.pos()

        positions = calculate_complete_tree_positions(
            root=root,
            horizontal_gap=80.0,
            vertical_gap=100.0,
        )
        root_x, root_y = positions[root]
        origin_x = origin.x()
        origin_y = origin.y()
        targets = {}
        for model, (x, y) in positions.items():
            item = self.heap_node_items.get(id(model))
            if item is not None:
                targets[item] = QPointF(origin_x + x - root_x, origin_y + y - root_y)

        self.animate_item_positions(targets)

    def merge_selected_items(self) -> None:
        selected_items = list(self.scene.selectedItems())

        if len(selected_items) < 2:
            return

        from PySide6.QtGui import QTransform, QPainter, QPixmap
        from PySide6.QtWidgets import QStyleOptionGraphicsItem
        from items.image_item import ImageItem
        from commands.undo_commands import MergeItemsCommand

        rect = QRectF()
        for item in selected_items:
            top_level = item
            while top_level.parentItem() is not None:
                top_level = top_level.parentItem()
            rect = rect.united(top_level.sceneBoundingRect())

        w = int(rect.width())
        h = int(rect.height())
        if w <= 0 or h <= 0:
            return

        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        painter.translate(-rect.topLeft())

        top_level_items: set[QGraphicsItem] = set()
        for item in selected_items:
            top_level = item
            while top_level.parentItem() is not None:
                top_level = top_level.parentItem()
            top_level_items.add(top_level)

        sorted_items = sorted(list(top_level_items), key=lambda x: x.zValue())

        handles_to_show = []
        for item in sorted_items:
            if hasattr(item, "resize_handles"):
                for handle in item.resize_handles.values():
                    if handle.isVisible():
                        handles_to_show.append(handle)
                        handle.hide()
            item.setSelected(False)

        for item in sorted_items:
            painter.save()
            painter.setTransform(item.sceneTransform(), True)
            option = QStyleOptionGraphicsItem()
            item.paint(painter, option)
            painter.restore()

        painter.end()

        for handle in handles_to_show:
            handle.show()

        merged_item = ImageItem(pixmap, undo_stack=self.undo_stack)
        merged_item.setPos(rect.topLeft())

        command = MergeItemsCommand(
            canvas=self,
            old_items=sorted_items,
            new_item=merged_item,
            text=f"Merge {len(sorted_items)} items",
        )
        self.undo_stack.push(command)

    def clear_canvas_state(self) -> None:
        self.scene.clear()
        self.undo_stack.clear()
        self.reset_document_state()

        self.pending_connection_node = None
        self.binary_tree_root = None
        self.binary_tree_node_items.clear()
        self.binary_tree_edges.clear()

        self.rb_tree_root = None
        self.rb_tree_node_items.clear()
        self.rb_tree_edges.clear()

        self.bst_root = None
        self.bst_node_items.clear()
        self.bst_edges.clear()

        self.heap_root = None
        self.heap_model = None
        self.heap_node_items.clear()
        self.heap_edges.clear()
