from pathlib import Path
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PDFListWidget(QListWidget):
    def __init__(self):
        super().__init__()

        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Merger")
        self.resize(900, 600)

        self.pdf_files = []

        self.file_list = PDFListWidget()

        add_button = QPushButton("Add PDFs")
        remove_button = QPushButton("Remove Selected")
        clear_button = QPushButton("Clear")

        add_button.clicked.connect(self.add_pdfs)
        remove_button.clicked.connect(self.remove_selected)
        clear_button.clicked.connect(self.clear_files)

        layout = QVBoxLayout()
        layout.addWidget(self.file_list)
        layout.addWidget(add_button)
        layout.addWidget(remove_button)
        layout.addWidget(clear_button)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)

    def add_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PDF files",
            "",
            "PDF Files (*.pdf)"
        )

        for file in files:
            pdf_file = Path(file)

            if pdf_file in self.pdf_files:
                continue

            self.pdf_files.append(pdf_file)

            item = QListWidgetItem(pdf_file.name)
            item.setData(Qt.UserRole, pdf_file)

            self.file_list.addItem(item)

    def remove_selected(self):
        selected_items = self.file_list.selectedItems()

        rows = sorted(
            [self.file_list.row(item) for item in selected_items],
            reverse=True
        )

        for row in rows:
            self.file_list.takeItem(row)
            self.pdf_files.pop(row)

    def clear_files(self):
        self.pdf_files.clear()
        self.file_list.clear()

    def get_ordered_files(self):
        ordered_files = []

        for index in range(self.file_list.count()):
            item = self.file_list.item(index)
            pdf_file = item.data(Qt.UserRole)

            ordered_files.append(pdf_file)

        return ordered_files


def run_gui():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    return app.exec()