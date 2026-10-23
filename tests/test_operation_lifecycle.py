import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QEventLoop, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication

from gui.app import MainWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    return app


@pytest.fixture
def window(qapp):
    window = MainWindow()
    yield window
    window.close()


def wait_for_condition(condition, timeout=3000):
    loop = QEventLoop()
    timer = QTimer()
    timer.setInterval(10)

    def check():
        if condition():
            loop.quit()

    timer.timeout.connect(check)
    timer.start()
    QTimer.singleShot(timeout, loop.quit)
    loop.exec()
    timer.stop()
    return condition()


class DummyWorker(QObject):
    progress = Signal(int, int, object)
    finished = Signal(object)
    failed = Signal(str, object)
    cancelled = Signal()

    @Slot()
    def run(self):
        self.progress.emit(1, 1, "source.pdf")
        self.finished.emit("done")


def test_operation_worker_helper_wires_and_cleans_up(window):
    worker = DummyWorker()
    events = []

    window._start_operation_worker(
        worker,
        lambda current, total, value: events.append(
            ("progress", current, total, value)
        ),
        lambda result: events.append(("finished", result)),
        lambda message, current_file: events.append(
            ("failed", message, current_file)
        ),
        lambda: events.append(("cancelled",)),
    )

    completed = wait_for_condition(
        lambda: window.operation_thread is None and window.operation_worker is None
    )

    assert completed is True
    assert events == [
        ("progress", 1, 1, "source.pdf"),
        ("finished", "done"),
    ]


def test_operation_worker_helper_uses_shared_thread_state(window):
    worker = DummyWorker()

    window._start_operation_worker(
        worker,
        lambda *_: None,
        lambda *_: None,
        lambda *_: None,
        lambda: None,
    )

    assert window.operation_thread is not None
    assert window.operation_worker is worker

    assert wait_for_condition(
        lambda: window.operation_thread is None and window.operation_worker is None
    )
