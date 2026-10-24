from pathlib import Path

from PySide6.QtCore import QMimeData, QThread, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QLineEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pdf_merger import get_pdf_info, parse_page_ranges, resolve_output_path
from gui.worker import DeleteWorker, ExtractWorker, MergeWorker, ReorderWorker, RotateWorker, SplitWorker


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
        self.parentWidget().refresh_file_list()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Toolkit")
        self.resize(700, 600)

        self.pdf_files = set()

        self.operation_thread = None
        self.operation_worker = None

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

        title = QLabel("PDF Toolkit")
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
            "Merge, split, extract, rotate, delete, and reorder PDF pages."
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
            self.refresh_file_list
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

        self.merge_output_layout = output_layout

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

        split_layout = QHBoxLayout()
        self.split_ranges_input = QLineEdit()
        self.split_ranges_input.setPlaceholderText(
            "Split ranges, e.g. 1-3, 5, 7-9 (blank = every page)"
        )
        self.split_ranges_input.setToolTip(
            "Comma-separated pages or inclusive ranges. "
            "Leave blank to create one PDF per page."
        )

        self.split_button = QPushButton("Split Selected PDF")
        self.split_button.setMinimumHeight(40)
        self.split_button.clicked.connect(self.start_split)

        split_layout.addWidget(self.split_ranges_input)
        split_layout.addWidget(self.split_button)

        extract_layout = QHBoxLayout()
        self.extract_ranges_input = QLineEdit()
        self.extract_ranges_input.setPlaceholderText(
            "Extract ranges, e.g. 1-3, 5, 7-9"
        )
        self.extract_ranges_input.setToolTip(
            "Comma-separated pages or inclusive ranges. "
            "At least one range is required."
        )

        self.extract_button = QPushButton("Extract Selected Pages")
        self.extract_button.setMinimumHeight(40)
        self.extract_button.clicked.connect(self.start_extract)

        extract_layout.addWidget(self.extract_ranges_input)
        extract_layout.addWidget(self.extract_button)

        rotate_layout = QHBoxLayout()

        self.rotate_ranges_input = QLineEdit()
        self.rotate_ranges_input.setPlaceholderText(
            "Rotate ranges, e.g. 1-3, 5 (blank = every page)"
        )
        self.rotate_ranges_input.setToolTip(
            "Comma-separated pages or inclusive ranges. "
            "Leave blank to rotate every page."
        )

        self.rotate_degrees = QComboBox()
        self.rotate_degrees.addItems(["90°", "180°", "270°"])
        self.rotate_degrees.setCurrentIndex(0)

        self.rotate_button = QPushButton("Rotate Selected Pages")
        self.rotate_button.setMinimumHeight(40)
        self.rotate_button.clicked.connect(self.start_rotate)

        rotate_layout.addWidget(self.rotate_ranges_input)
        rotate_layout.addWidget(self.rotate_degrees)
        rotate_layout.addWidget(self.rotate_button)

        delete_layout = QHBoxLayout()

        self.delete_ranges_input = QLineEdit()
        self.delete_ranges_input.setPlaceholderText(
            "Delete ranges, e.g. 2-3, 5"
        )
        self.delete_ranges_input.setToolTip(
            "Comma-separated pages or inclusive ranges. "
            "At least one range is required."
        )

        self.delete_button = QPushButton("Delete Selected Pages")
        self.delete_button.setMinimumHeight(40)
        self.delete_button.clicked.connect(self.start_delete)

        delete_layout.addWidget(self.delete_ranges_input)
        delete_layout.addWidget(self.delete_button)

        reorder_layout = QHBoxLayout()

        self.reorder_order_input = QLineEdit()
        self.reorder_order_input.setPlaceholderText(
            "Page order, e.g. 4, 2, 1, 3"
        )
        self.reorder_order_input.setToolTip(
            "Enter every page number exactly once, separated by commas."
        )

        self.reorder_button = QPushButton("Reorder Pages")
        self.reorder_button.setMinimumHeight(40)
        self.reorder_button.clicked.connect(self.start_reorder)

        reorder_layout.addWidget(self.reorder_order_input)
        reorder_layout.addWidget(self.reorder_button)

        self.operation_tabs = QTabWidget()
        self.operation_tabs.setDocumentMode(True)

        merge_tab = QWidget()
        merge_tab_layout = QVBoxLayout(merge_tab)
        merge_tab_layout.setContentsMargins(10, 10, 10, 10)
        merge_tab_layout.addLayout(self.merge_output_layout)
        merge_tab_layout.addWidget(self.merge_button)

        split_tab = QWidget()
        split_tab_layout = QVBoxLayout(split_tab)
        split_tab_layout.setContentsMargins(10, 10, 10, 10)
        split_tab_layout.addLayout(split_layout)

        extract_tab = QWidget()
        extract_tab_layout = QVBoxLayout(extract_tab)
        extract_tab_layout.setContentsMargins(10, 10, 10, 10)
        extract_tab_layout.addLayout(extract_layout)

        rotate_tab = QWidget()
        rotate_tab_layout = QVBoxLayout(rotate_tab)
        rotate_tab_layout.setContentsMargins(10, 10, 10, 10)
        rotate_tab_layout.addLayout(rotate_layout)

        delete_tab = QWidget()
        delete_tab_layout = QVBoxLayout(delete_tab)
        delete_tab_layout.setContentsMargins(10, 10, 10, 10)
        delete_tab_layout.addLayout(delete_layout)

        reorder_tab = QWidget()
        reorder_tab_layout = QVBoxLayout(reorder_tab)
        reorder_tab_layout.setContentsMargins(10, 10, 10, 10)
        reorder_tab_layout.addLayout(reorder_layout)

        self.operation_tabs.addTab(merge_tab, "Merge")
        self.operation_tabs.addTab(split_tab, "Split")
        self.operation_tabs.addTab(extract_tab, "Extract")
        self.operation_tabs.addTab(rotate_tab, "Rotate")
        self.operation_tabs.addTab(delete_tab, "Delete")
        self.operation_tabs.addTab(reorder_tab, "Reorder")

        main_layout.addWidget(self.operation_tabs)

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
        self.cancel_button.clicked.connect(self.cancel_operation)

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

            item = QListWidgetItem()
            item.setData(
                Qt.UserRole,
                pdf_file
            )

            self.file_list.addItem(item)

        self.refresh_file_list()

    def format_pdf_item(self, pdf_file, position):
        info = get_pdf_info(pdf_file)

        return (
            f"{position:02d}   "
            f"{pdf_file.name}    "
            f"{info.pages} pages    "
            f"{self.format_size(info.size_bytes)}"
        )

    def refresh_file_list(self):
        for index in range(self.file_list.count()):
            item = self.file_list.item(index)
            pdf_file = item.data(Qt.UserRole)

            if pdf_file:
                item.setText(
                    self.format_pdf_item(
                        Path(pdf_file),
                        index + 1,
                    )
                )

        self.refresh_metadata()

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

        self.refresh_file_list()

    def clear_files(self):
        self.file_list.clear()
        self.pdf_files.clear()
        self.refresh_file_list()

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

    def resolve_output_file(self):
        return resolve_output_path(self.output_name.text())

    def get_output_file(self):
        return self.resolve_output_file()

    def _start_operation_worker(
        self,
        worker,
        progress_slot,
        success_slot,
        failure_slot,
        cancelled_slot,
    ):
        self.operation_thread = QThread()
        self.operation_worker = worker

        self.operation_worker.moveToThread(self.operation_thread)
        self.operation_thread.started.connect(self.operation_worker.run)

        self.operation_worker.progress.connect(progress_slot)
        self.operation_worker.finished.connect(success_slot)
        self.operation_worker.failed.connect(failure_slot)
        self.operation_worker.cancelled.connect(cancelled_slot)

        for signal in (
            self.operation_worker.finished,
            self.operation_worker.failed,
            self.operation_worker.cancelled,
        ):
            signal.connect(self.operation_thread.quit)
            signal.connect(self.operation_worker.deleteLater)

        self.operation_thread.finished.connect(self.operation_thread.deleteLater)
        self.operation_thread.finished.connect(self.operation_finished)
        self.operation_thread.start()

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

        self.set_operation_state(True)

        self.progress_bar.setRange(
            0,
            len(pdf_files)
        )

        self.progress_bar.setValue(0)

        self.status_label.setText(
            f"Preparing to merge {len(pdf_files)} files..."
        )

        self._start_operation_worker(
            MergeWorker(pdf_files, output_file),
            self.merge_progress,
            self.merge_succeeded,
            self.merge_failed,
            self.merge_cancelled,
        )


    def start_split(self):
        item = self.file_list.currentItem()

        if item is None:
            QMessageBox.warning(
                self,
                "No PDF Selected",
                "Select one PDF to split."
            )
            return

        pdf_file = Path(item.data(Qt.UserRole))

        try:
            ranges = parse_page_ranges(self.split_ranges_input.text())
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Invalid Page Ranges",
                str(error),
            )
            return

        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Choose split output directory",
            str(Path("output") / f"{pdf_file.stem}-parts"),
        )

        if not output_dir:
            return

        self.set_operation_state(True)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Preparing to split {pdf_file.name}...")

        self._start_operation_worker(
            SplitWorker(
                pdf_file,
                Path(output_dir),
                ranges=ranges,
            ),
            self.split_progress,
            self.split_succeeded,
            self.split_failed,
            self.split_cancelled,
        )


    def start_extract(self):
        item = self.file_list.currentItem()

        if item is None:
            QMessageBox.warning(
                self,
                "No PDF Selected",
                "Select one PDF to extract pages from."
            )
            return

        pdf_file = Path(item.data(Qt.UserRole))

        try:
            ranges = parse_page_ranges(self.extract_ranges_input.text())
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Invalid Page Ranges",
                str(error),
            )
            return

        if not ranges:
            QMessageBox.warning(
                self,
                "Page Ranges Required",
                "Enter at least one page or page range to extract."
            )
            return

        default_output = Path("output") / f"{pdf_file.stem}-extracted.pdf"
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Choose extracted PDF output",
            str(default_output),
            "PDF Files (*.pdf)",
        )

        if not output_file:
            return

        output_path = Path(output_file)

        if output_path.suffix.lower() != ".pdf":
            output_path = output_path.with_suffix(".pdf")

        self.set_operation_state(True)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.status_label.setText(
            f"Preparing to extract pages from {pdf_file.name}..."
        )

        self._start_operation_worker(
            ExtractWorker(
                pdf_file,
                output_path,
                ranges=ranges,
            ),
            self.extract_progress,
            self.extract_succeeded,
            self.extract_failed,
            self.extract_cancelled,
        )


    def extract_progress(self, current, total, pdf_file):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(
            f"Extracting pages from {Path(pdf_file).name} "
            f"({current} of {total})"
        )

    def extract_succeeded(self, result):
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_label.setText("Extraction completed successfully.")

        output = result.outputs[0] if result.outputs else ""

        QMessageBox.information(
            self,
            "Extraction Complete",
            f"Pages extracted successfully.\n\n"
            f"Pages: {result.pages_processed}\n"
            f"Output: {output}"
        )

    def extract_failed(self, error_message, current_file):
        self.status_label.setText("Extraction failed.")
        self.progress_bar.setValue(0)

        file_name = Path(current_file).name if current_file else "PDF"

        QMessageBox.critical(
            self,
            "Extraction Failed",
            f"Could not extract pages from:\n{file_name}\n\n"
            f"Reason:\n{error_message}"
        )

    def extract_cancelled(self):
        self.status_label.setText("Extraction cancelled.")
        self.progress_bar.setValue(0)

    def start_rotate(self):
        item = self.file_list.currentItem()

        if item is None:
            QMessageBox.warning(
                self,
                "No PDF Selected",
                "Select one PDF to rotate."
            )
            return

        pdf_file = Path(item.data(Qt.UserRole))

        try:
            ranges = parse_page_ranges(self.rotate_ranges_input.text())
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Invalid Page Ranges",
                str(error),
            )
            return

        degrees = int(self.rotate_degrees.currentText().rstrip("°"))

        default_output = Path("output") / f"{pdf_file.stem}-rotated.pdf"
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Choose rotated PDF output",
            str(default_output),
            "PDF Files (*.pdf)",
        )

        if not output_file:
            return

        output_path = Path(output_file)

        if output_path.suffix.lower() != ".pdf":
            output_path = output_path.with_suffix(".pdf")

        self.set_operation_state(True)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.status_label.setText(
            f"Preparing to rotate {pdf_file.name}..."
        )

        self._start_operation_worker(
            RotateWorker(
                pdf_file,
                output_path,
                degrees=degrees,
                ranges=ranges,
            ),
            self.rotate_progress,
            self.rotate_succeeded,
            self.rotate_failed,
            self.rotate_cancelled,
        )


    def rotate_progress(self, current, total, pdf_file):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(
            f"Rotating pages in {Path(pdf_file).name} "
            f"({current} of {total})"
        )

    def rotate_succeeded(self, result):
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_label.setText("Rotation completed successfully.")

        output = result.outputs[0] if result.outputs else ""

        QMessageBox.information(
            self,
            "Rotation Complete",
            f"Pages rotated successfully.\n\n"
            f"Pages processed: {result.pages_processed}\n"
            f"Output: {output}"
        )

    def rotate_failed(self, error_message, current_file):
        self.status_label.setText("Rotation failed.")
        self.progress_bar.setValue(0)

        file_name = Path(current_file).name if current_file else "PDF"

        QMessageBox.critical(
            self,
            "Rotation Failed",
            f"Could not rotate:\n{file_name}\n\n"
            f"Reason:\n{error_message}"
        )

    def rotate_cancelled(self):
        self.status_label.setText("Rotation cancelled.")
        self.progress_bar.setValue(0)

    def start_delete(self):
        item = self.file_list.currentItem()

        if item is None:
            QMessageBox.warning(
                self,
                "No PDF Selected",
                "Select one PDF to delete pages from."
            )
            return

        pdf_file = Path(item.data(Qt.UserRole))

        try:
            ranges = parse_page_ranges(self.delete_ranges_input.text())
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Invalid Page Ranges",
                str(error),
            )
            return

        if not ranges:
            QMessageBox.warning(
                self,
                "Page Ranges Required",
                "Enter at least one page or page range to delete."
            )
            return

        default_output = Path("output") / f"{pdf_file.stem}-trimmed.pdf"
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Choose trimmed PDF output",
            str(default_output),
            "PDF Files (*.pdf)",
        )

        if not output_file:
            return

        output_path = Path(output_file)

        if output_path.suffix.lower() != ".pdf":
            output_path = output_path.with_suffix(".pdf")

        self.set_operation_state(True)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.status_label.setText(
            f"Preparing to delete pages from {pdf_file.name}..."
        )

        self._start_operation_worker(
            DeleteWorker(
                pdf_file,
                output_path,
                ranges=ranges,
            ),
            self.delete_progress,
            self.delete_succeeded,
            self.delete_failed,
            self.delete_cancelled,
        )


    def delete_progress(self, current, total, pdf_file):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(
            f"Deleting pages from {Path(pdf_file).name} "
            f"({current} of {total})"
        )

    def delete_succeeded(self, result):
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_label.setText("Page deletion completed successfully.")

        output = result.outputs[0] if result.outputs else ""

        QMessageBox.information(
            self,
            "Page Deletion Complete",
            f"Pages deleted successfully.\n\n"
            f"Pages processed: {result.pages_processed}\n"
            f"Output: {output}"
        )

    def delete_failed(self, error_message, current_file):
        self.status_label.setText("Page deletion failed.")
        self.progress_bar.setValue(0)

        file_name = Path(current_file).name if current_file else "PDF"

        QMessageBox.critical(
            self,
            "Page Deletion Failed",
            f"Could not delete pages from:\n{file_name}\n\n"
            f"Reason:\n{error_message}"
        )

    def delete_cancelled(self):
        self.status_label.setText("Page deletion cancelled.")
        self.progress_bar.setValue(0)

    def start_reorder(self):
        item = self.file_list.currentItem()

        if item is None:
            QMessageBox.warning(
                self,
                "No PDF Selected",
                "Select one PDF to reorder."
            )
            return

        pdf_file = Path(item.data(Qt.UserRole))
        raw_order = self.reorder_order_input.text().strip()

        if not raw_order:
            QMessageBox.warning(
                self,
                "Page Order Required",
                "Enter the complete page order, for example: 4, 2, 1, 3."
            )
            return

        try:
            order = [int(part.strip()) for part in raw_order.split(",")]
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Page Order",
                "Use comma-separated page numbers, for example: 4, 2, 1, 3."
            )
            return

        if any(page < 1 for page in order):
            QMessageBox.warning(
                self,
                "Invalid Page Order",
                "Page numbers must be positive integers."
            )
            return

        default_output = Path("output") / f"{pdf_file.stem}-reordered.pdf"
        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Choose reordered PDF output",
            str(default_output),
            "PDF Files (*.pdf)",
        )

        if not output_file:
            return

        output_path = Path(output_file)

        if output_path.suffix.lower() != ".pdf":
            output_path = output_path.with_suffix(".pdf")

        self.set_operation_state(True)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.status_label.setText(
            f"Preparing to reorder {pdf_file.name}..."
        )

        self._start_operation_worker(
            ReorderWorker(
                pdf_file,
                output_path,
                order=order,
            ),
            self.reorder_progress,
            self.reorder_succeeded,
            self.reorder_failed,
            self.reorder_cancelled,
        )

    def reorder_progress(self, current, total, pdf_file):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(
            f"Reordering pages in {Path(pdf_file).name} "
            f"({current} of {total})"
        )

    def reorder_succeeded(self, result):
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_label.setText("Reordering completed successfully.")

        output = result.outputs[0] if result.outputs else ""

        QMessageBox.information(
            self,
            "Reorder Complete",
            f"Pages reordered successfully.\n\n"
            f"Pages processed: {result.pages_processed}\n"
            f"Output: {output}"
        )

    def reorder_failed(self, error_message, current_file):
        self.status_label.setText("Reordering failed.")
        self.progress_bar.setValue(0)

        file_name = Path(current_file).name if current_file else "PDF"

        QMessageBox.critical(
            self,
            "Reorder Failed",
            f"Could not reorder:\n{file_name}\n\n"
            f"Reason:\n{error_message}"
        )

    def reorder_cancelled(self):
        self.status_label.setText("Reordering cancelled.")
        self.progress_bar.setValue(0)

    def split_progress(self, current, total, output_file):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(
            f"Creating: {Path(output_file).name} ({current} of {total})"
        )

    def split_succeeded(self, result):
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_label.setText("Split completed successfully.")

        QMessageBox.information(
            self,
            "Split Complete",
            f"PDF split successfully.\n\n"
            f"Parts: {len(result.outputs)}\n"
            f"Pages: {result.pages_processed}\n"
            f"Output: {result.outputs[0].parent if result.outputs else ''}"
        )

    def split_failed(self, error_message, current_file):
        self.status_label.setText("Split failed.")
        self.progress_bar.setValue(0)

        file_name = Path(current_file).name if current_file else "PDF"

        QMessageBox.critical(
            self,
            "Split Failed",
            f"Could not split:\n{file_name}\n\n"
            f"Reason:\n{error_message}"
        )

    def split_cancelled(self):
        self.status_label.setText("Split cancelled.")
        self.progress_bar.setValue(0)

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

    def cancel_operation(self):
        if self.operation_worker is None:
            return

        self.cancel_button.setEnabled(False)
        self.status_label.setText("Cancelling operation...")
        self.operation_worker.cancel()

    def merge_cancelled(self):
        self.status_label.setText("Merge cancelled.")
        self.progress_bar.setValue(0)

    def operation_finished(self):
        self.set_operation_state(False)

        self.operation_thread = None
        self.operation_worker = None

    def set_operation_state(self, running):
        enabled = not running

        self.add_button.setEnabled(enabled)
        self.remove_button.setEnabled(enabled)
        self.clear_button.setEnabled(enabled)
        self.choose_output_button.setEnabled(enabled)
        self.merge_button.setEnabled(enabled)
        self.split_button.setEnabled(enabled)
        self.split_ranges_input.setEnabled(enabled)
        self.extract_button.setEnabled(enabled)
        self.extract_ranges_input.setEnabled(enabled)
        self.rotate_button.setEnabled(enabled)
        self.rotate_ranges_input.setEnabled(enabled)
        self.rotate_degrees.setEnabled(enabled)
        self.operation_tabs.setEnabled(enabled)
        self.delete_button.setEnabled(enabled)
        self.delete_ranges_input.setEnabled(enabled)
        self.reorder_button.setEnabled(enabled)
        self.reorder_order_input.setEnabled(enabled)
        self.file_list.setEnabled(enabled)
        self.cancel_button.setEnabled(running)

    def format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"

        if size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"

        if size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.1f} MB"

        return f"{size_bytes / (1024 ** 3):.1f} GB"

    def closeEvent(self, event):
        if self.operation_thread and self.operation_thread.isRunning():
            QMessageBox.warning(
                self,
                "Operation In Progress",
                "Please wait for the current operation to finish or cancel it."
            )
            event.ignore()
            return

        event.accept()
