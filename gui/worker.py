from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, Signal, Slot

from pdf_merger import merge_files


class MergeWorker(QObject):
    progress = Signal(int, int, object)
    finished = Signal(int, Path)
    failed = Signal(str, object)
    cancelled = Signal()

    def __init__(self, pdf_files, output_file):
        super().__init__()

        self.pdf_files = pdf_files
        self.output_file = output_file
        self._cancel_event = Event()

    def cancel(self):
        self._cancel_event.set()

    def is_cancelled(self):
        return self._cancel_event.is_set()

    @Slot()
    def run(self):
        def report_progress(current, total, pdf_file):
            self.progress.emit(
                current,
                total,
                pdf_file
            )

        def report_error(error_message, current_file):
            self.failed.emit(
                error_message,
                current_file
            )

        total_pages = merge_files(
            self.pdf_files,
            self.output_file,
            progress_callback=report_progress,
            error_callback=report_error,
            cancel_callback=self.is_cancelled,
        )

        if total_pages is not None:
            self.finished.emit(
                total_pages,
                self.output_file
            )
            return

        if self.is_cancelled():
            self.cancelled.emit()