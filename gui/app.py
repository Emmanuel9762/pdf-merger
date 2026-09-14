import sys

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Merger")
        self.resize(900, 600)

        label = QLabel("PDF Merger")
        label.setStyleSheet(
            "font-size: 28px; font-weight: bold;"
        )

        self.setCentralWidget(label)


def run_gui():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    return app.exec()