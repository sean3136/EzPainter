import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from main_window import MainWindow

import os


def get_resource_path(file_name: str) -> str:
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, file_name)


app = QApplication(sys.argv)

window = MainWindow()
logo_path = get_resource_path(os.path.join("logos", "EzPainter_logo.png"))
window.setWindowIcon(QIcon(logo_path))

window.show()

app.exec()