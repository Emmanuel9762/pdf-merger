from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from pdf_merger import merge_files


class MergeWorker(QObject):
    progress = Signal(int, int, object)
    finished = Signal(int, Path)
    failed = Signal()

    def __init__(self, pdf_files, output_file):
        super().__init__()

        self.pdf_files = pdf_files
        self.output_file = output_file

    @Slot()
    def run(self):
        def report_progress(current, total, pdf_file):
            self.progress.emit(
                current,
                total,
                pdf_file
            )

        total_pages = merge_files(
            self.pdf_files,
            self.output_file,
            progress_callback=report_progress
        )

        if total_pages is None:
            self.failed.emit()
            return

        self.finished.emit(
            total_pages,
            self.output_file
        )