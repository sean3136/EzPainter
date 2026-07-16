from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from canvas.tool_mode import ToolMode


class ToolPanel(QWidget):
    tool_selected = Signal(object)
    brush_width_changed = Signal(int)
    graph_directed_changed = Signal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.buttons: dict[ToolMode, QPushButton] = {}

        self.setStyleSheet("""
            QPushButton {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f8f9fa;
                color: #212529;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e2e6ea;
                border-color: #dae0e5;
            }
            QPushButton:checked {
                background-color: #007bff;
                color: white;
                border-color: #007bff;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
                border-color: #ced4da;
            }
        """)

        tabs = QTabWidget(self)

        tabs.addTab(
            self._create_draw_tab(),
            "Draw",
        )

        tabs.addTab(
            self._create_data_structure_tab(),
            "Data Structure",
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(tabs)

    def _create_tool_button(
        self,
        text: str,
        tool: ToolMode,
    ) -> QPushButton:
        button = QPushButton(text)
        button.setCheckable(True)
        button.clicked.connect(lambda: self.tool_selected.emit(tool))
        self.buttons[tool] = button
        return button

    def _create_draw_tab(self) -> QWidget:
        widget = QWidget()
        layout = QGridLayout(widget)

        layout.addWidget(
            self._create_tool_button(
                "Brush",
                ToolMode.BRUSH,
            ),
            0,
            0,
            1,
            2,
        )

        layout.addWidget(
            QLabel("Brush size:"),
            1,
            0,
        )

        brush_layout = QHBoxLayout()
        self.brush_width_spinbox = QSpinBox()
        self.brush_width_spinbox.setRange(1, 100)
        self.brush_width_spinbox.setValue(4)
        self.brush_width_spinbox.valueChanged.connect(self.brush_width_changed.emit)

        px_label = QLabel("px")
        brush_layout.addWidget(self.brush_width_spinbox)
        brush_layout.addWidget(px_label)
        brush_layout.addStretch()

        layout.addLayout(
            brush_layout,
            1,
            1,
        )

        layout.addWidget(
            self._create_tool_button(
                "Rectangle",
                ToolMode.RECTANGLE,
            ),
            2,
            0,
        )

        layout.addWidget(
            self._create_tool_button(
                "Ellipse",
                ToolMode.ELLIPSE,
            ),
            2,
            1,
        )

        layout.addWidget(
            self._create_tool_button(
                "Table",
                ToolMode.TABLE,
            ),
            3,
            0,
            1,
            2,
        )

        layout.setRowStretch(4, 1)

        return widget

    def _create_data_structure_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Generators"))

        layout.addWidget(
            self._create_tool_button(
                "Binary Tree",
                ToolMode.BINARY_TREE,
            )
        )

        layout.addWidget(
            self._create_tool_button(
                "Red-Black Tree",
                ToolMode.RED_BLACK_TREE,
            )
        )

        layout.addWidget(
            self._create_tool_button(
                "Binary Search Tree",
                ToolMode.BST,
            )
        )

        layout.addWidget(
            self._create_tool_button(
                "Min-Heap",
                ToolMode.MIN_HEAP,
            )
        )

        layout.addWidget(
            self._create_tool_button(
                "Max-Heap",
                ToolMode.MAX_HEAP,
            )
        )

        layout.addWidget(QLabel("Manual Graph"))

        layout.addWidget(
            self._create_tool_button(
                "Add Node",
                ToolMode.GRAPH_NODE,
            )
        )

        layout.addWidget(
            self._create_tool_button(
                "Connect Nodes",
                ToolMode.CONNECT_NODES,
            )
        )
        directed_checkbox = QCheckBox("Directed edges")
        directed_checkbox.setChecked(False)

        directed_checkbox.toggled.connect(self._emit_directed_changed)

        layout.addWidget(directed_checkbox)
        layout.addStretch()

        return widget

    def _emit_directed_changed(
        self,
        checked: bool,
    ) -> None:
        self.graph_directed_changed.emit(checked)

    def set_active_tool(self, tool: ToolMode) -> None:
        for btn_tool, button in self.buttons.items():
            button.blockSignals(True)
            button.setChecked(btn_tool == tool)
            button.blockSignals(False)
