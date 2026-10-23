from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, Signal, Slot

from pdf_merger import delete_pages, extract_pages, merge_files, reorder_pages, rotate_pages, split_pdf


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
        failure = None

        def report_progress(current, total, pdf_file):
            self.progress.emit(
                current,
                total,
                pdf_file
            )

        def report_error(error_message, current_file):
            nonlocal failure
            failure = (error_message, current_file)

        try:
            total_pages = merge_files(
                self.pdf_files,
                self.output_file,
                progress_callback=report_progress,
                error_callback=report_error,
                cancel_callback=self.is_cancelled,
            )
        except Exception as error:
            failure = (str(error), None)
            total_pages = None

        if failure is not None:
            self.failed.emit(*failure)
            return

        if total_pages is not None:
            self.finished.emit(
                total_pages,
                self.output_file
            )
            return

        if self.is_cancelled():
            self.cancelled.emit()
            return

        self.failed.emit("Merge failed without an error detail.", None)



class SplitWorker(QObject):
    progress = Signal(int, int, object)
    finished = Signal(object)
    failed = Signal(str, object)
    cancelled = Signal()

    def __init__(self, pdf_file, output_dir, ranges=None):
        super().__init__()

        self.pdf_file = Path(pdf_file)
        self.output_dir = Path(output_dir)
        self.ranges = ranges
        self._cancel_event = Event()

    def cancel(self):
        self._cancel_event.set()

    def is_cancelled(self):
        return self._cancel_event.is_set()

    @Slot()
    def run(self):
        try:
            result = split_pdf(
                self.pdf_file,
                self.output_dir,
                ranges=self.ranges,
                progress_callback=lambda current, total, output: self.progress.emit(
                    current,
                    total,
                    output,
                ),
                cancel_callback=self.is_cancelled,
            )
        except Exception as error:
            self.failed.emit(str(error), self.pdf_file)
            return

        if result.succeeded:
            self.finished.emit(result)
            return

        if result.cancelled:
            self.cancelled.emit()
            return

        self.failed.emit(
            result.error or "Split failed without an error detail.",
            result.current_file,
        )



class ExtractWorker(QObject):
    progress = Signal(int, int, object)
    finished = Signal(object)
    failed = Signal(str, object)
    cancelled = Signal()

    def __init__(self, pdf_file, output_file, ranges):
        super().__init__()

        self.pdf_file = Path(pdf_file)
        self.output_file = Path(output_file)
        self.ranges = ranges
        self._cancel_event = Event()

    def cancel(self):
        self._cancel_event.set()

    def is_cancelled(self):
        return self._cancel_event.is_set()

    @Slot()
    def run(self):
        try:
            result = extract_pages(
                self.pdf_file,
                self.output_file,
                ranges=self.ranges,
                progress_callback=lambda current, total, path: self.progress.emit(
                    current,
                    total,
                    path,
                ),
                cancel_callback=self.is_cancelled,
            )
        except Exception as error:
            self.failed.emit(str(error), self.pdf_file)
            return

        if result.succeeded:
            self.finished.emit(result)
            return

        if result.cancelled:
            self.cancelled.emit()
            return

        self.failed.emit(
            result.error or "Extract failed without an error detail.",
            result.current_file,
        )



class RotateWorker(QObject):
    progress = Signal(int, int, object)
    finished = Signal(object)
    failed = Signal(str, object)
    cancelled = Signal()

    def __init__(self, pdf_file, output_file, degrees, ranges=None):
        super().__init__()

        self.pdf_file = Path(pdf_file)
        self.output_file = Path(output_file)
        self.degrees = degrees
        self.ranges = ranges
        self._cancel_event = Event()

    def cancel(self):
        self._cancel_event.set()

    def is_cancelled(self):
        return self._cancel_event.is_set()

    @Slot()
    def run(self):
        try:
            result = rotate_pages(
                self.pdf_file,
                self.output_file,
                degrees=self.degrees,
                ranges=self.ranges,
                progress_callback=lambda current, total, path: self.progress.emit(
                    current,
                    total,
                    path,
                ),
                cancel_callback=self.is_cancelled,
            )
        except Exception as error:
            self.failed.emit(str(error), self.pdf_file)
            return

        if result.succeeded:
            self.finished.emit(result)
            return

        if result.cancelled:
            self.cancelled.emit()
            return

        self.failed.emit(
            result.error or "Rotate failed without an error detail.",
            result.current_file,
        )



class DeleteWorker(QObject):
    progress = Signal(int, int, object)
    finished = Signal(object)
    failed = Signal(str, object)
    cancelled = Signal()

    def __init__(self, pdf_file, output_file, ranges):
        super().__init__()

        self.pdf_file = Path(pdf_file)
        self.output_file = Path(output_file)
        self.ranges = ranges
        self._cancel_event = Event()

    def cancel(self):
        self._cancel_event.set()

    def is_cancelled(self):
        return self._cancel_event.is_set()

    @Slot()
    def run(self):
        try:
            result = delete_pages(
                self.pdf_file,
                self.output_file,
                ranges=self.ranges,
                progress_callback=lambda current, total, path: self.progress.emit(
                    current,
                    total,
                    path,
                ),
                cancel_callback=self.is_cancelled,
            )
        except Exception as error:
            self.failed.emit(str(error), self.pdf_file)
            return

        if result.succeeded:
            self.finished.emit(result)
            return

        if result.cancelled:
            self.cancelled.emit()
            return

        self.failed.emit(
            result.error or "Delete failed without an error detail.",
            result.current_file,
        )



class ReorderWorker(QObject):
    progress = Signal(int, int, object)
    finished = Signal(object)
    failed = Signal(str, object)
    cancelled = Signal()

    def __init__(self, pdf_file, output_file, order):
        super().__init__()

        self.pdf_file = Path(pdf_file)
        self.output_file = Path(output_file)
        self.order = order
        self._cancel_event = Event()

    def cancel(self):
        self._cancel_event.set()

    def is_cancelled(self):
        return self._cancel_event.is_set()

    @Slot()
    def run(self):
        try:
            result = reorder_pages(
                self.pdf_file,
                self.output_file,
                order=self.order,
                progress_callback=lambda current, total, path: self.progress.emit(
                    current,
                    total,
                    path,
                ),
                cancel_callback=self.is_cancelled,
            )
        except Exception as error:
            self.failed.emit(str(error), self.pdf_file)
            return

        if result.succeeded:
            self.finished.emit(result)
            return

        if result.cancelled:
            self.cancelled.emit()
            return

        self.failed.emit(
            result.error or "Reorder failed without an error detail.",
            result.current_file,
        )
