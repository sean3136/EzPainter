from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


class RedBlackTreeDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Create Red-Black Tree")

        self.values_input = QLineEdit()
        self.values_input.setPlaceholderText("Example: 10,20,30,15,25,5")

        form_layout = QFormLayout()
        form_layout.addRow(
            "Insertion order:",
            self.values_input,
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addWidget(buttons)

    def _validate(self) -> None:
        try:
            values = self.get_values()
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid input",
                "Please enter integers separated by commas.",
            )
            return

        if not values:
            QMessageBox.warning(
                self,
                "Invalid input",
                "Please enter at least one value.",
            )
            return

        self.accept()

    def get_values(self) -> list[int]:
        text = self.values_input.text().strip()

        if not text:
            return []

        return [int(token.strip()) for token in text.split(",") if token.strip()]
