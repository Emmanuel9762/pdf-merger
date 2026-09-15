from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from pdf_merger import merge_files


class MergeWorker(QObject):
    finished = Signal(int, Path)
    failed = Signal()

    def __init__(self, pdf_files, output_file):
        super().__init__()

        self.pdf_files = pdf_files
        self.output_file = output_file

    @Slot()
    def run(self):
        total_pages = merge_files(
            self.pdf_files,
            self.output_file
        )

        if total_pages is None:
            self.failed.emit()
            return

        self.finished.emit(
            total_pages,
            self.output_file
        )
