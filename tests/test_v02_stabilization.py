import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QThread
from PySide6.QtGui import QCloseEvent
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

    if window.operation_thread and window.operation_thread.isRunning():
        window.operation_thread.quit()
        window.operation_thread.wait()

    window.close()


def test_generic_operation_state_names_are_initialized(window):
    assert window.operation_thread is None
    assert window.operation_worker is None


def test_close_event_uses_operation_neutral_message(window, monkeypatch):
    captured = {}

    monkeypatch.setattr(
        "gui.app.QMessageBox.warning",
        lambda parent, title, message: captured.update(
            title=title,
            message=message,
        ),
    )

    window.operation_thread = QThread()
    window.operation_thread.start()

    event = QCloseEvent()
    window.closeEvent(event)

    assert not event.isAccepted()
    assert captured["title"] == "Operation In Progress"
    assert "current operation" in captured["message"]

    window.operation_thread.quit()
    window.operation_thread.wait()
    window.operation_thread = None


def test_operation_state_disables_shared_workspace(window):
    window.set_operation_state(True)

    assert not window.file_list.isEnabled()
    assert not window.operation_tabs.isEnabled()
    assert window.cancel_button.isEnabled()

    window.set_operation_state(False)

    assert window.file_list.isEnabled()
    assert window.operation_tabs.isEnabled()
    assert not window.cancel_button.isEnabled()
