from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSpinBox,
    QVBoxLayout,
)


class TableDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Create Table")
        self.setModal(True)

        self.rows_spinbox = QSpinBox(self)
        self.rows_spinbox.setRange(1, 50)
        self.rows_spinbox.setValue(3)

        self.columns_spinbox = QSpinBox(self)
        self.columns_spinbox.setRange(1, 50)
        self.columns_spinbox.setValue(4)

        self.cell_width_spinbox = QSpinBox(self)
        self.cell_width_spinbox.setRange(20, 500)
        self.cell_width_spinbox.setValue(100)
        self.cell_width_spinbox.setSuffix(" px")

        self.cell_height_spinbox = QSpinBox(self)
        self.cell_height_spinbox.setRange(20, 300)
        self.cell_height_spinbox.setValue(40)
        self.cell_height_spinbox.setSuffix(" px")

        form_layout = QFormLayout()
        form_layout.addRow("Rows:", self.rows_spinbox)
        form_layout.addRow("Columns:", self.columns_spinbox)
        form_layout.addRow("Cell width:", self.cell_width_spinbox)
        form_layout.addRow("Cell height:", self.cell_height_spinbox)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

    def get_table_settings(self) -> tuple[int, int, int, int]:
        return (
            self.rows_spinbox.value(),
            self.columns_spinbox.value(),
            self.cell_width_spinbox.value(),
            self.cell_height_spinbox.value(),
        )