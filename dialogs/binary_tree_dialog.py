from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


class BinaryTreeDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Create Binary Tree")
        self.setModal(True)
        self.resize(420, 140)

        self.values_input = QLineEdit(self)
        self.values_input.setPlaceholderText("Example: 1,2,3,4,5,null,6")

        form_layout = QFormLayout()
        form_layout.addRow(
            "Level-order values:",
            self.values_input,
        )

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        button_box.accepted.connect(self._validate_and_accept)

        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addWidget(button_box)

    def _validate_and_accept(self) -> None:
        values = self.get_values()

        if not values:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter at least one node.",
            )
            return

        if values[0] is None:
            QMessageBox.warning(
                self,
                "Invalid Root",
                "The root node cannot be null.",
            )
            return

        self.accept()

    def get_values(self) -> list[str | None]:
        raw_text = self.values_input.text().strip()

        if not raw_text:
            return []

        result: list[str | None] = []

        null_tokens = {
            "null",
            "none",
            "nil",
            "#",
            "",
        }

        for token in raw_text.split(","):
            cleaned = token.strip()

            if cleaned.lower() in null_tokens:
                result.append(None)
            else:
                result.append(cleaned)

        return result
