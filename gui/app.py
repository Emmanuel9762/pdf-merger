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

        self.apply_styles()
        self.build_ui()

    def apply_styles(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background: #181a1f;
            }

            QWidget {
                color: #f2f4f7;
                font-size: 13px;
            }

            QLabel {
                color: #f2f4f7;
            }

            QListWidget {
                background: #22252b;
                border: 1px solid #3a3f47;
                border-radius: 10px;
                padding: 8px;
                color: #f2f4f7;
                outline: none;
            }

            QListWidget::item {
                padding: 11px 10px;
                border-radius: 7px;
                color: #e9edf2;
            }

            QListWidget::item:hover {
                background: #2d323a;
            }

            QListWidget::item:selected {
                background: #365d91;
                color: #ffffff;
            }

            QPushButton {
                background: #292d34;
                border: 1px solid #454b55;
                border-radius: 7px;
                padding: 9px 15px;
                color: #f2f4f7;
                min-height: 18px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #343a43;
                border-color: #5b6470;
            }

            QPushButton:pressed {
                background: #22262c;
            }

            QPushButton:disabled {
                background: #25282e;
                border-color: #363a41;
                color: #9aa1aa;
            }

            QProgressBar {
                background: #22252b;
                border: 1px solid #3a3f47;
                border-radius: 7px;
                min-height: 20px;
                text-align: center;
                color: #f2f4f7;
                font-weight: 600;
            }

            QProgressBar::chunk {
                background: #4f8cff;
                border-radius: 6px;
            }

            QMessageBox {
                background: #181a1f;
                color: #f2f4f7;
            }

            QToolTip {
                background: #292d34;
                color: #f2f4f7;
                border: 1px solid #454b55;
                padding: 6px;
            }
            """
        )

    def build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 22, 24, 22)
        main_layout.setSpacing(14)

        title = QLabel("PDF Merger")
        title.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                font-size: 28px;
                font-weight: 700;
            }
            """
        )

        subtitle = QLabel(
            "Combine PDF files in the order you choose."
        )
        subtitle.setStyleSheet(
            """
            QLabel {
                color: #b7bec8;
                font-size: 13px;
            }
            """
        )

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        self.file_list = PDFListWidget(self)
        self.file_list.setMinimumHeight(260)

        self.file_list.setSelectionMode(
            QListWidget.SingleSelection
        )

        self.file_list.setAlternatingRowColors(False)
        self.file_list.setSpacing(3)

        self.file_list.model().rowsMoved.connect(
            self.refresh_metadata
        )

        main_layout.addWidget(self.file_list)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add PDFs")
        self.add_button.clicked.connect(self.select_files)

        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_selected)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_files)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.clear_button)

        main_layout.addLayout(button_layout)

        self.summary_label = QLabel(
            "0 PDFs  •  0 pages  •  0 B"
        )
        self.summary_label.setStyleSheet(
            """
            QLabel {
                color: #b7bec8;
                font-size: 12px;
                padding: 2px 2px;
            }
            """
        )

        main_layout.addWidget(self.summary_label)

        output_layout = QHBoxLayout()
        output_layout.setSpacing(10)

        output_label = QLabel("Output")
        output_label.setStyleSheet(
            """
            QLabel {
                color: #9fa7b2;
                font-weight: 600;
            }
            """
        )

        output_layout.addWidget(output_label)

        self.output_name = QLabel("merged.pdf")
        self.output_name.setStyleSheet(
            """
            QLabel {
                color: #e4e8ed;
                font-weight: 600;
            }
            """
        )

        output_layout.addWidget(self.output_name)

        self.choose_output_button = QPushButton(
            "Choose Location"
        )

        self.choose_output_button.clicked.connect(
            self.choose_output_location
        )

        output_layout.addWidget(
            self.choose_output_button
        )

        main_layout.addLayout(output_layout)

        self.status_label = QLabel("Ready.")
        self.status_label.setStyleSheet(
            """
            QLabel {
                color: #dce1e7;
                font-weight: 600;
                padding: 2px;
            }
            """
        )

        main_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        main_layout.addWidget(self.progress_bar)

        self.merge_button = QPushButton("Merge PDFs")
        self.merge_button.setMinimumHeight(40)
        self.merge_button.setStyleSheet(
            """
            QPushButton {
                background: #4f8cff;
                border: 1px solid #5d97ff;
                border-radius: 7px;
                padding: 9px 16px;
                color: #ffffff;
                font-size: 14px;
                font-weight: 700;
            }

            QPushButton:hover {
                background: #5d97ff;
            }

            QPushButton:pressed {
                background: #3d78e6;
            }

            QPushButton:disabled {
                background: #34445f;
                border-color: #3b4d6a;
                color: #a3afc1;
            }
            """
        )
        self.merge_button.clicked.connect(self.start_merge)

        main_layout.addWidget(self.merge_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setStyleSheet(
            """
            QPushButton {
                background: #3a2d30;
                border: 1px solid #69454b;
                color: #f0dfe2;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #49363a;
                border-color: #80545c;
            }

            QPushButton:pressed {
                background: #302427;
            }

            QPushButton:disabled {
                background: #25282e;
                border-color: #363a41;
                color: #9aa1aa;
            }
            """
        )
        self.cancel_button.clicked.connect(self.cancel_merge)

        main_layout.addWidget(self.cancel_button)

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
            f"{len(ordered_files)} PDFs  •  "
            f"{total_pages} pages  •  "
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

        if output_path.suffix.lower() != ".pdf":
            output_path = output_path.with_suffix(".pdf")

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

        self.merge_worker.cancelled.connect(
            self.merge_cancelled
        )

        self.merge_worker.finished.connect(
            self.merge_thread.quit
        )

        self.merge_worker.failed.connect(
            self.merge_thread.quit
        )

        self.merge_worker.cancelled.connect(
            self.merge_thread.quit
        )

        self.merge_worker.finished.connect(
            self.merge_worker.deleteLater
        )

        self.merge_worker.failed.connect(
            self.merge_worker.deleteLater
        )

        self.merge_worker.cancelled.connect(
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

    def merge_failed(self, error_message, current_file):
        self.status_label.setText(
            "Merge failed."
        )

        self.progress_bar.setValue(0)

        if current_file:
            file_name = Path(current_file).name

            message = (
                f"Could not process:\n"
                f"{file_name}\n\n"
                f"Reason:\n"
                f"{error_message}"
            )
        else:
            message = (
                "The PDFs could not be merged.\n\n"
                f"Reason:\n"
                f"{error_message}"
            )

        QMessageBox.critical(
            self,
            "Merge Failed",
            message
        )

    def cancel_merge(self):
        if self.merge_worker is None:
            return

        self.cancel_button.setEnabled(False)
        self.status_label.setText("Cancelling merge...")
        self.merge_worker.cancel()

    def merge_cancelled(self):
        self.status_label.setText("Merge cancelled.")
        self.progress_bar.setValue(0)

    def merge_finished(self):
        self.set_merge_state(False)

        self.merge_thread = None
        self.merge_worker = None

    def set_merge_state(self, merging):
        enabled = not merging

        self.add_button.setEnabled(enabled)
        self.remove_button.setEnabled(enabled)
        self.clear_button.setEnabled(enabled)
        self.choose_output_button.setEnabled(enabled)
        self.merge_button.setEnabled(enabled)
        self.file_list.setEnabled(enabled)
        self.cancel_button.setEnabled(merging)

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


def run_gui():
    app = QApplication([])

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run_gui())