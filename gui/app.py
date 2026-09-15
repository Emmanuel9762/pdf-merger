from pathlib import Path
import sys

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pdf_merger import get_pdf_info
from gui.worker import MergeWorker


class PDFListWidget(QListWidget):
    def __init__(self, add_files_callback):
        super().__init__()

        self.add_files_callback = add_files_callback

        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            pdf_files = [
                Path(url.toLocalFile())
                for url in event.mimeData().urls()
                if url.isLocalFile()
            ]

            if any(
                file.is_file()
                and file.suffix.lower() == ".pdf"
                for file in pdf_files
            ):
                event.acceptProposedAction()
                return

        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return

        super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            pdf_files = [
                Path(url.toLocalFile())
                for url in event.mimeData().urls()
                if url.isLocalFile()
            ]

            pdf_files = [
                file
                for file in pdf_files
                if file.is_file()
                and file.suffix.lower() == ".pdf"
            ]

            if pdf_files:
                self.add_files_callback(pdf_files)
                event.acceptProposedAction()
                return

        super().dropEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF Merger")
        self.resize(1000, 650)

        self.pdf_files = set()

        self.merge_thread = None
        self.merge_worker = None

        self.setup_ui()
        self.update_status()

    def setup_ui(self):
        title_label = QLabel("Merge PDF files")
        title_label.setObjectName("title")

        subtitle_label = QLabel(
            "Add PDF files, arrange them in the order you want, "
            "and merge them into a single document."
        )
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setWordWrap(True)

        self.file_list = PDFListWidget(
            self.add_pdf_files
        )

        self.count_label = QLabel("Files: 0")
        self.count_label.setObjectName("count")

        self.status_label = QLabel("No PDFs selected.")
        self.status_label.setObjectName("status")

        add_button = QPushButton("Add PDFs")
        remove_button = QPushButton("Remove Selected")
        clear_button = QPushButton("Clear")

        add_button.setObjectName("primaryButton")

        add_button.clicked.connect(self.add_pdfs)
        remove_button.clicked.connect(self.remove_selected)
        clear_button.clicked.connect(self.clear_files)

        file_button_layout = QHBoxLayout()
        file_button_layout.addWidget(add_button)
        file_button_layout.addWidget(remove_button)
        file_button_layout.addWidget(clear_button)
        file_button_layout.addStretch()

        files_group = QGroupBox("PDF files")
        files_layout = QVBoxLayout()
        files_layout.addWidget(self.file_list)
        files_layout.addWidget(self.count_label)
        files_layout.addLayout(file_button_layout)
        files_group.setLayout(files_layout)

        self.output_name = QLineEdit(
            "merged-document.pdf"
        )
        self.output_name.setPlaceholderText(
            "merged-document.pdf"
        )

        self.output_folder = QLineEdit(
            str(Path.home() / "Documents")
        )
        self.output_folder.setReadOnly(True)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(
            self.select_output_folder
        )

        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.output_folder)
        folder_layout.addWidget(browse_button)

        output_form = QFormLayout()
        output_form.addRow(
            "File name",
            self.output_name
        )
        output_form.addRow(
            "Save to",
            folder_layout
        )

        self.merge_button = QPushButton("Merge PDFs")
        self.merge_button.setObjectName("mergeButton")
        self.merge_button.clicked.connect(
            self.merge_pdfs
        )

        output_layout = QVBoxLayout()
        output_layout.addLayout(output_form)
        output_layout.addSpacing(16)
        output_layout.addWidget(self.merge_button)
        output_layout.addStretch()

        output_group = QGroupBox("Output")
        output_group.setLayout(output_layout)

        content_layout = QHBoxLayout()
        content_layout.addWidget(files_group, 2)
        content_layout.addWidget(output_group, 1)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(
            24,
            20,
            24,
            20
        )
        main_layout.setSpacing(16)

        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)
        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(main_layout)

        self.setCentralWidget(container)

        self.setStyleSheet(
            """
            QMainWindow {
                background: #f5f7fa;
            }

            QLabel#title {
                font-size: 28px;
                font-weight: 700;
                color: #1f2937;
            }

            QLabel#subtitle {
                font-size: 14px;
                color: #6b7280;
                padding-bottom: 4px;
            }

            QLabel#count {
                font-size: 13px;
                color: #6b7280;
            }

            QLabel#status {
                background: #eef4ff;
                border: 1px solid #d7e5ff;
                border-radius: 8px;
                color: #315b9d;
                padding: 10px 12px;
            }

            QGroupBox {
                background: white;
                border: 1px solid #d9dee7;
                border-radius: 10px;
                margin-top: 10px;
                padding: 16px;
                font-size: 15px;
                font-weight: 600;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #27364d;
                background: #f5f7fa;
            }

            QListWidget {
                background: white;
                border: 1px solid #d9dee7;
                border-radius: 8px;
                padding: 6px;
                font-size: 14px;
            }

            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #edf0f4;
            }

            QListWidget::item:selected {
                background: #e8f1ff;
                color: #174ea6;
            }

            QLineEdit {
                background: white;
                border: 1px solid #cfd6e2;
                border-radius: 7px;
                padding: 9px;
                font-size: 13px;
            }

            QPushButton {
                background: white;
                border: 1px solid #cfd6e2;
                border-radius: 7px;
                padding: 9px 14px;
                font-size: 13px;
            }

            QPushButton:hover {
                background: #f1f5f9;
            }

            QPushButton#primaryButton {
                background: #2563eb;
                border: none;
                color: white;
                font-weight: 600;
            }

            QPushButton#primaryButton:hover {
                background: #1d4ed8;
            }

            QPushButton#mergeButton {
                background: #2563eb;
                border: none;
                color: white;
                font-size: 15px;
                font-weight: 700;
                padding: 13px;
            }

            QPushButton#mergeButton:hover {
                background: #1d4ed8;
            }

            QPushButton#mergeButton:disabled {
                background: #9ca3af;
            }
            """
        )

    def add_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select PDF files",
            "",
            "PDF Files (*.pdf)"
        )

        if not files:
            return

        pdf_files = [
            Path(file)
            for file in files
        ]

        self.add_pdf_files(pdf_files)

    def add_pdf_files(self, pdf_files):
        added = 0
        failed = 0

        for pdf_file in pdf_files:
            if not pdf_file.is_file():
                continue

            if pdf_file.suffix.lower() != ".pdf":
                continue

            if pdf_file in self.pdf_files:
                continue

            try:
                info = get_pdf_info(pdf_file)
            except Exception:
                failed += 1
                continue

            self.pdf_files.add(pdf_file)

            item = QListWidgetItem()

            item.setData(
                Qt.UserRole,
                pdf_file
            )

            item.setText(
                f"{pdf_file.name}\n"
                f"{info.pages} "
                f"{'page' if info.pages == 1 else 'pages'}"
                f" • "
                f"{self.format_size(info.size_bytes)}"
            )

            self.file_list.addItem(item)

            added += 1

        self.update_status()

        if added and failed:
            self.status_label.setText(
                f"Added {added} PDF"
                f"{'s' if added != 1 else ''}; "
                f"{failed} could not be read."
            )
        elif added:
            self.status_label.setText(
                f"Added {added} PDF"
                f"{'s' if added != 1 else ''}."
            )
        elif failed:
            self.status_label.setText(
                "The selected PDFs could not be read."
            )
        else:
            self.status_label.setText(
                "No new PDF files were added."
            )

    def remove_selected(self):
        selected_items = self.file_list.selectedItems()

        if not selected_items:
            self.status_label.setText(
                "Select at least one PDF to remove."
            )
            return

        count = len(selected_items)

        for item in selected_items:
            pdf_file = item.data(Qt.UserRole)
            row = self.file_list.row(item)

            self.file_list.takeItem(row)
            self.pdf_files.remove(pdf_file)

        self.update_status()

        self.status_label.setText(
            f"Removed {count} PDF"
            f"{'s' if count != 1 else ''}."
        )

    def clear_files(self):
        if not self.pdf_files:
            self.status_label.setText(
                "The list is already empty."
            )
            return

        self.pdf_files.clear()
        self.file_list.clear()

        self.update_status()
        self.status_label.setText(
            "PDF list cleared."
        )

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select output folder",
            self.output_folder.text()
        )

        if folder:
            self.output_folder.setText(folder)

    def get_ordered_files(self):
        ordered_files = []

        for index in range(self.file_list.count()):
            item = self.file_list.item(index)
            pdf_file = item.data(Qt.UserRole)

            ordered_files.append(pdf_file)

        return ordered_files

    def get_output_file(self):
        filename = self.output_name.text().strip()

        if not filename:
            self.status_label.setText(
                "Output filename cannot be empty."
            )
            return None

        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        folder = Path(
            self.output_folder.text()
        )

        if not folder.exists():
            try:
                folder.mkdir(
                    parents=True,
                    exist_ok=True
                )
            except OSError:
                QMessageBox.critical(
                    self,
                    "Invalid output folder",
                    "The selected output folder could not be created."
                )
                return None

        return folder / filename

    @staticmethod
    def format_size(size_bytes):
        units = [
            "B",
            "KB",
            "MB",
            "GB",
        ]

        size = float(size_bytes)

        for unit in units:
            if size < 1024 or unit == units[-1]:
                if unit == "B":
                    return f"{int(size)} {unit}"

                return f"{size:.1f} {unit}"

            size /= 1024

    def update_status(self):
        count = self.file_list.count()

        total_pages = 0
        total_size = 0

        for index in range(count):
            item = self.file_list.item(index)
            pdf_file = item.data(Qt.UserRole)

            try:
                info = get_pdf_info(pdf_file)
            except Exception:
                continue

            total_pages += info.pages
            total_size += info.size_bytes

        self.count_label.setText(
            f"{count} PDF"
            f"{'s' if count != 1 else ''}"
            f" • {total_pages} "
            f"{'page' if total_pages == 1 else 'pages'}"
            f" • {self.format_size(total_size)}"
        )

        if count == 0:
            self.status_label.setText(
                "No PDFs selected."
            )
        elif count == 1:
            self.status_label.setText(
                "1 PDF ready."
            )
        else:
            self.status_label.setText(
                f"{count} PDFs ready to merge."
            )

    def merge_pdfs(self):
        pdf_files = self.get_ordered_files()

        if not pdf_files:
            QMessageBox.warning(
                self,
                "No PDFs",
                "Add at least one PDF before merging."
            )
            return

        output_file = self.get_output_file()

        if output_file is None:
            return

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

        self.start_merge(
            pdf_files,
            output_file
        )

    def start_merge(self, pdf_files, output_file):
        self.merge_button.setEnabled(False)
        self.file_list.setEnabled(False)
        self.status_label.setText(
            "Merging PDFs..."
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

    def merge_succeeded(self, total_pages, output_file):
        self.status_label.setText(
            f"Merge complete. {total_pages} pages written."
        )

        QMessageBox.information(
            self,
            "Merge complete",
            f"PDFs merged successfully.\n\n"
            f"Files merged: "
            f"{self.file_list.count()}\n"
            f"Total pages: {total_pages}\n\n"
            f"Output:\n{output_file}"
        )

    def merge_failed(self):
        self.status_label.setText(
            "Merge failed."
        )

        QMessageBox.critical(
            self,
            "Merge failed",
            "The PDFs could not be merged."
        )

    def merge_finished(self):
        self.merge_button.setEnabled(True)
        self.file_list.setEnabled(True)

        self.merge_thread = None
        self.merge_worker = None

    def closeEvent(self, event):
        if self.merge_thread and self.merge_thread.isRunning():
            QMessageBox.warning(
                self,
                "Merge in progress",
                "Wait for the current merge to finish "
                "before closing the application."
            )
            event.ignore()
            return

        event.accept()


def run_gui():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    return app.exec()