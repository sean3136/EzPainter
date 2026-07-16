from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QColor, QKeySequence
from PySide6.QtWidgets import (
    QColorDialog,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QToolBar,
    QDockWidget,
    QLabel,
    QLineEdit,
)
from panels.tool_panel import ToolPanel

from canvas.canvas_view import CanvasView
from canvas.tool_mode import ToolMode


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("EzPainter")
        self.resize(1200, 800)

        self.canvas = CanvasView()
        self.setCentralWidget(self.canvas)

        self._create_toolbar()
        self._create_tool_panel()
        self.canvas.tool_changed.connect(self._sync_tool_action)
        self.canvas.zoom_changed.connect(self.update_zoom_indicator)
        self._create_status_bar()

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Tools", self)
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        toolbar.setStyleSheet("QToolBar { font-size: 14px; } QToolBar QToolButton { font-size: 14px; }")

        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)

        self.select_action = QAction("Select", self)
        self.select_action.setCheckable(True)
        self.select_action.setChecked(True)
        self.select_action.setShortcut("V")
        self.select_action.triggered.connect(lambda: self.set_tool(ToolMode.SELECT))

        self.tool_group.addAction(self.select_action)
        self.addAction(self.select_action)

        toolbar.addAction(self.select_action)

        self.brush_action = QAction("Brush", self)
        self.brush_action.setCheckable(True)
        self.brush_action.setShortcut("B")
        self.brush_action.triggered.connect(lambda: self.set_tool(ToolMode.BRUSH))
        self.tool_group.addAction(self.brush_action)
        self.addAction(self.brush_action)

        self.table_action = QAction("Table", self)
        self.table_action.setCheckable(True)
        self.table_action.setShortcut("T")
        self.table_action.triggered.connect(lambda: self.set_tool(ToolMode.TABLE))
        self.tool_group.addAction(self.table_action)
        self.addAction(self.table_action)

        toolbar.addSeparator()

        color_action = QAction("Color", self)
        color_action.triggered.connect(self.choose_brush_color)
        toolbar.addAction(color_action)

        toolbar.addSeparator()

        delete_action = QAction("Delete", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_selected_items)
        self.addAction(delete_action)
        toolbar.addAction(delete_action)

        clear_action = QAction("Clear Canvas", self)
        clear_action.triggered.connect(self.clear_canvas)
        self.addAction(clear_action)
        toolbar.addAction(clear_action)

        toolbar.addSeparator()

        merge_action = QAction("Merge", self)
        merge_action.setShortcut("M")
        merge_action.triggered.connect(self.merge_selected_objects)
        self.addAction(merge_action)
        toolbar.addAction(merge_action)

        toolbar.addSeparator()
        zoom_title = QLabel("Zoom: ", self)
        zoom_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        toolbar.addWidget(zoom_title)

        self.zoom_input = QLineEdit("100", self)
        self.zoom_input.setFixedWidth(50)
        self.zoom_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_input.setStyleSheet("font-size: 14px; padding: 2px; border: 1px solid #cccccc; border-radius: 3px;")
        self.zoom_input.returnPressed.connect(self.on_zoom_input_submitted)
        toolbar.addWidget(self.zoom_input)

        zoom_percent_label = QLabel("%", self)
        zoom_percent_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-left: 2px; margin-right: 5px;")
        toolbar.addWidget(zoom_percent_label)

        toolbar.addSeparator()

        undo_action = self.canvas.undo_stack.createUndoAction(
            self,
            "Undo",
        )
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.addAction(undo_action)

        redo_action = self.canvas.undo_stack.createRedoAction(
            self,
            "Redo",
        )
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.addAction(redo_action)

        toolbar.addAction(undo_action)
        toolbar.addAction(redo_action)

    def _create_status_bar(self) -> None:
        self.statusBar().showMessage("Tool: Select")

    def set_tool(self, tool: ToolMode) -> None:
        self.canvas.set_tool(tool)
        self.statusBar().showMessage(f"Tool: {tool.name.title()}")
        if hasattr(self, "tool_panel"):
            self.tool_panel.set_active_tool(tool)

    def update_zoom_indicator(self, zoom: float) -> None:
        self.zoom_input.blockSignals(True)
        self.zoom_input.setText(f"{round(zoom * 100)}")
        self.zoom_input.blockSignals(False)

    def on_zoom_input_submitted(self) -> None:
        text = self.zoom_input.text().strip().replace("%", "")
        try:
            percentage = float(text)
            if percentage <= 0:
                raise ValueError
        except ValueError:
            self.update_zoom_indicator(self.canvas.transform().m11())
            return

        zoom_factor = percentage / 100.0
        current_zoom = self.canvas.transform().m11()
        if current_zoom > 0:
            scale_factor = zoom_factor / current_zoom
            self.canvas.scale(scale_factor, scale_factor)
            self.canvas.zoom_changed.emit(zoom_factor)

    def choose_brush_color(self) -> None:
        selected_color = QColorDialog.getColor(
            self.canvas.brush_color,
            self,
            "Choose Brush Color",
        )

        if selected_color.isValid():
            self.canvas.set_brush_color(selected_color)
            self.statusBar().showMessage(f"Brush color: {selected_color.name()}")

    def delete_selected_items(self) -> None:
        selected_count = len(self.canvas.scene.selectedItems())

        self.canvas.delete_selected_items()

        if selected_count:
            self.statusBar().showMessage(f"Deleted {selected_count} item(s)")

    def merge_selected_objects(self) -> None:
        selected_count = len(self.canvas.scene.selectedItems())
        if selected_count < 2:
            self.statusBar().showMessage("Select at least 2 items to merge")
            return

        self.canvas.merge_selected_items()
        self.statusBar().showMessage(f"Merged {selected_count} items into a single image layer")

    def clear_canvas(self) -> None:
        answer = QMessageBox.question(
            self,
            "Clear Canvas",
            "Are you sure you want to remove everything from the canvas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer == QMessageBox.StandardButton.Yes:
            self.canvas.clear_canvas_state()
            self.statusBar().showMessage("Canvas cleared")

    def _sync_tool_action(
        self,
        tool: ToolMode,
    ) -> None:
        if tool == ToolMode.SELECT:
            self.select_action.setChecked(True)
        elif tool == ToolMode.BRUSH:
            self.brush_action.setChecked(True)
        elif tool == ToolMode.TABLE:
            self.table_action.setChecked(True)
        else:
            checked = self.tool_group.checkedAction()
            if checked is not None:
                self.tool_group.setExclusive(False)
                checked.setChecked(False)
                self.tool_group.setExclusive(True)

        if hasattr(self, "tool_panel"):
            self.tool_panel.set_active_tool(tool)
        self.statusBar().showMessage(f"Tool: {tool.name.replace('_', ' ').title()}")

    def _create_tool_panel(self) -> None:
        self.tool_panel = ToolPanel(self)

        self.tool_panel.tool_selected.connect(self.set_tool)

        self.tool_panel.brush_width_changed.connect(self.canvas.set_brush_width)

        dock = QDockWidget(
            "Tools",
            self,
        )

        dock.setWidget(self.tool_panel)

        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

        dock.setMinimumWidth(210)

        self.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea,
            dock,
        )

        self.tool_panel.graph_directed_changed.connect(self.canvas.set_graph_directed)
