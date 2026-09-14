from pathlib import Path
import sys

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QListWidget,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Merger")
        self.resize(900, 600)

        self.pdf_files = []

        self.file_list = QListWidget()

        add_button = QPushButton("Add PDFs")
        remove_button = QPushButton("Remove Selected")
        clear_button = QPushButton("Clear")

        add_button.clicked.connect(self.add_pdfs)
        remove_button.clicked.connect(self.remove_selected)
        clear_button.clicked.connect(self.clear_files)

        button_layout = QVBoxLayout()
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addWidget(clear_button)

        layout = QVBoxLayout()
        layout.addWidget(self.file_list)
        layout.addLayout(button_layout)

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

            if pdf_file not in self.pdf_files:
                self.pdf_files.append(pdf_file)
                self.file_list.addItem(pdf_file.name)

    def remove_selected(self):
        selected_items = self.file_list.selectedItems()

        for item in selected_items:
            row = self.file_list.row(item)

            self.file_list.takeItem(row)
            self.pdf_files.pop(row)

    def clear_files(self):
        self.pdf_files.clear()
        self.file_list.clear()


def run_gui():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    return app.exec()