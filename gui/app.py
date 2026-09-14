from pathlib import Path
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pdf_merger import merge_files


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

        self.pdf_files = set()

        self.file_list = PDFListWidget()

        add_button = QPushButton("Add PDFs")
        remove_button = QPushButton("Remove Selected")
        clear_button = QPushButton("Clear")
        merge_button = QPushButton("Merge PDFs")

        add_button.clicked.connect(self.add_pdfs)
        remove_button.clicked.connect(self.remove_selected)
        clear_button.clicked.connect(self.clear_files)
        merge_button.clicked.connect(self.merge_pdfs)

        layout = QVBoxLayout()
        layout.addWidget(self.file_list)
        layout.addWidget(add_button)
        layout.addWidget(remove_button)
        layout.addWidget(clear_button)
        layout.addWidget(merge_button)

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

            self.pdf_files.add(pdf_file)

            item = QListWidgetItem(pdf_file.name)
            item.setData(Qt.UserRole, pdf_file)

            self.file_list.addItem(item)

    def remove_selected(self):
        selected_items = self.file_list.selectedItems()

        for item in selected_items:
            pdf_file = item.data(Qt.UserRole)

            row = self.file_list.row(item)

            self.file_list.takeItem(row)
            self.pdf_files.remove(pdf_file)

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

    def merge_pdfs(self):
        pdf_files = self.get_ordered_files()

        if not pdf_files:
            QMessageBox.warning(
                self,
                "No PDFs",
                "Add at least one PDF before merging."
            )
            return

        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save merged PDF",
            "",
            "PDF Files (*.pdf)"
        )

        if not output_file:
            return

        output_file = Path(output_file)

        if output_file.suffix.lower() != ".pdf":
            output_file = output_file.with_suffix(".pdf")

        if output_file.exists():
            choice = QMessageBox.question(
                self,
                "File already exists",
                f"{output_file}\n\nOverwrite this file?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if choice != QMessageBox.Yes:
                return

        output_file.parent.mkdir(parents=True, exist_ok=True)

        total_pages = merge_files(
            pdf_files,
            output_file
        )

        if total_pages is None:
            QMessageBox.critical(
                self,
                "Merge failed",
                "The PDFs could not be merged."
            )
            return

        QMessageBox.information(
            self,
            "Merge complete",
            f"PDFs merged successfully.\n\n"
            f"Files merged: {len(pdf_files)}\n"
            f"Total pages: {total_pages}\n\n"
            f"Output:\n{output_file}"
        )


def run_gui():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    return app.exec()