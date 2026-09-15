from pathlib import Path

from PySide6.QtCore import QMimeData, QThread, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pdf_merger import get_pdf_info
from gui.worker import MergeWorker


class PDFListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)

    def dragEnterEvent(self, event: QDragEnterEvent):
        mime_data = event.mimeData()

        if mime_data.hasUrls():
            event.acceptProposedAction()
            return

        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        mime_data = event.mimeData()

        if mime_data.hasUrls():
            event.acceptProposedAction()
            return

        super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        mime_data = event.mimeData()

        if mime_data.hasUrls():
            pdf_paths = []

            for url in mime_data.urls():
                if not url.isLocalFile():
                    continue

                path = Path(url.toLocalFile())

                if path.is_file() and path.suffix.lower() == ".pdf":
                    pdf_paths.append(path)

            if pdf_paths:
                self.parentWidget().add_pdf_files(pdf_paths)

            event.acceptProposedAction()
            return

        super().dropEvent(event)
        self.parentWidget().refresh_metadata()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Merger")
        self.resize(700, 600)

        self.pdf_files = set()

        self.merge_thread = None
        self.merge_worker = None

        self.build_ui()

    def build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        title = QLabel("PDF Merger")
        title.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
        )

        subtitle = QLabel(
            "Add PDFs, arrange them in the desired order, "
            "then merge them."
        )

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        self.file_list = PDFListWidget(self)

        self.file_list.setSelectionMode(
            QListWidget.SingleSelection
        )

        self.file_list.model().rowsMoved.connect(
            self.refresh_metadata
        )

        main_layout.addWidget(self.file_list)

        button_layout = QHBoxLayout()

        add_button = QPushButton("Add PDFs")
        add_button.clicked.connect(self.select_files)

        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_selected)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_files)

        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addWidget(clear_button)

        main_layout.addLayout(button_layout)

        self.summary_label = QLabel(
            "0 PDFs | 0 pages | 0 B"
        )

        main_layout.addWidget(self.summary_label)

        output_layout = QHBoxLayout()

        output_layout.addWidget(QLabel("Output:"))

        self.output_name = QLabel("merged.pdf")

        output_layout.addWidget(self.output_name)

        choose_output_button = QPushButton("Choose Location")
        choose_output_button.clicked.connect(
            self.choose_output_location
        )

        output_layout.addWidget(choose_output_button)

        main_layout.addLayout(output_layout)

        self.status_label = QLabel("Ready.")

        main_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        main_layout.addWidget(self.progress_bar)

        self.merge_button = QPushButton("Merge PDFs")
        self.merge_button.clicked.connect(self.start_merge)

        main_layout.addWidget(self.merge_button)

    def select_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PDF files",
            "",
            "PDF Files (*.pdf)"
        )

        if file_paths:
            self.add_pdf_files(
                [Path(path) for path in file_paths]
            )

    def add_pdf_files(self, file_paths):
        for pdf_file in file_paths:
            pdf_file = Path(pdf_file)

            if pdf_file in self.pdf_files:
                continue

            try:
                get_pdf_info(pdf_file)
            except Exception:
                QMessageBox.warning(
                    self,
                    "Invalid PDF",
                    f"Could not read:\n{pdf_file.name}"
                )
                continue

            self.pdf_files.add(pdf_file)

            item = QListWidgetItem(
                self.format_pdf_item(pdf_file)
            )

            item.setData(
                Qt.UserRole,
                pdf_file
            )

            self.file_list.addItem(item)

        self.refresh_metadata()

    def format_pdf_item(self, pdf_file):
        info = get_pdf_info(pdf_file)

        return (
            f"{pdf_file.name}    "
            f"{info.pages} pages    "
            f"{self.format_size(info.size_bytes)}"
        )

    def refresh_metadata(self):
        ordered_files = self.get_ordered_files()

        total_pages = 0
        total_size = 0

        for pdf_file in ordered_files:
            try:
                info = get_pdf_info(pdf_file)
            except Exception:
                continue

            total_pages += info.pages
            total_size += info.size_bytes

        self.summary_label.setText(
            f"{len(ordered_files)} PDFs | "
            f"{total_pages} pages | "
            f"{self.format_size(total_size)}"
        )

    def get_ordered_files(self):
        pdf_files = []

        for index in range(self.file_list.count()):
            item = self.file_list.item(index)

            pdf_file = item.data(Qt.UserRole)

            if pdf_file:
                pdf_files.append(Path(pdf_file))

        return pdf_files

    def remove_selected(self):
        item = self.file_list.currentItem()

        if item is None:
            return

        pdf_file = item.data(Qt.UserRole)

        if pdf_file:
            self.pdf_files.discard(Path(pdf_file))

        row = self.file_list.row(item)

        self.file_list.takeItem(row)

        self.refresh_metadata()

    def clear_files(self):
        self.file_list.clear()
        self.pdf_files.clear()
        self.refresh_metadata()

    def choose_output_location(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Choose output file",
            "merged.pdf",
            "PDF Files (*.pdf)"
        )

        if not file_path:
            return

        output_path = Path(file_path)

        if output_path.suffix.lower() != ".pdf":
            output_path = output_path.with_suffix(".pdf")

        self.output_name.setText(str(output_path))

    def get_output_file(self):
        output_path = Path(self.output_name.text())

        if not output_path.is_absolute():
            output_path = Path("output") / output_path

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        return output_path

    def start_merge(self):
        pdf_files = self.get_ordered_files()

        if not pdf_files:
            QMessageBox.warning(
                self,
                "No PDFs",
                "Add at least one PDF before merging."
            )
            return

        output_file = self.get_output_file()

        if output_file.exists():
            result = QMessageBox.question(
                self,
                "Overwrite File?",
                f"{output_file} already exists.\n\n"
                "Do you want to overwrite it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if result != QMessageBox.Yes:
                return

        self.set_merge_state(True)

        self.progress_bar.setRange(
            0,
            len(pdf_files)
        )

        self.progress_bar.setValue(0)

        self.status_label.setText(
            f"Preparing to merge {len(pdf_files)} files..."
        )

        self.merge_thread = QThread()
        self.merge_worker = MergeWorker(
            pdf_files,
            output_file
        )

        self.merge_worker.moveToThread(
            self.merge_thread
        )

        self.merge_thread.started.connect(
            self.merge_worker.run
        )

        self.merge_worker.progress.connect(
            self.merge_progress
        )

        self.merge_worker.finished.connect(
            self.merge_succeeded
        )

        self.merge_worker.failed.connect(
            self.merge_failed
        )

        self.merge_worker.finished.connect(
            self.merge_thread.quit
        )

        self.merge_worker.failed.connect(
            self.merge_thread.quit
        )

        self.merge_worker.finished.connect(
            self.merge_worker.deleteLater
        )

        self.merge_worker.failed.connect(
            self.merge_worker.deleteLater
        )

        self.merge_thread.finished.connect(
            self.merge_thread.deleteLater
        )

        self.merge_thread.finished.connect(
            self.merge_finished
        )

        self.merge_thread.start()

    def merge_progress(self, current, total, pdf_file):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

        self.status_label.setText(
            f"Processing: {Path(pdf_file).name} "
            f"({current} of {total})"
        )

    def merge_succeeded(self, total_pages, output_file):
        self.progress_bar.setValue(
            self.progress_bar.maximum()
        )

        self.status_label.setText(
            "Merge completed successfully."
        )

        QMessageBox.information(
            self,
            "Merge Complete",
            f"PDFs merged successfully.\n\n"
            f"Files: {self.progress_bar.maximum()}\n"
            f"Pages: {total_pages}\n"
            f"Output: {output_file}"
        )

    def merge_failed(self):
        self.status_label.setText(
            "Merge failed."
        )

        self.progress_bar.setValue(0)

        QMessageBox.critical(
            self,
            "Merge Failed",
            "The PDFs could not be merged."
        )

    def merge_finished(self):
        self.set_merge_state(False)

        self.merge_thread = None
        self.merge_worker = None

    def set_merge_state(self, merging):
        self.merge_button.setEnabled(not merging)

        self.file_list.setEnabled(not merging)

        for widget in self.findChildren(QPushButton):
            if widget is self.merge_button:
                continue

            widget.setEnabled(not merging)

    def format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"

        if size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"

        if size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.1f} MB"

        return f"{size_bytes / (1024 ** 3):.1f} GB"

    def closeEvent(self, event):
        if self.merge_thread and self.merge_thread.isRunning():
            QMessageBox.warning(
                self,
                "Merge In Progress",
                "Please wait for the merge to finish."
            )

            event.ignore()
            return

        event.accept()


def main():
    app = QApplication([])

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())