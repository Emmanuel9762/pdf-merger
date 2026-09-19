import sys

from PySide6.QtWidgets import QApplication

from gui.app import MainWindow


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    return app.exec()
