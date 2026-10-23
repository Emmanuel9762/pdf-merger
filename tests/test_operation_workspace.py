import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

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


def test_operation_workspace_has_expected_tabs(window):
    assert window.operation_tabs.count() == 5
    assert [
        window.operation_tabs.tabText(index)
        for index in range(window.operation_tabs.count())
    ] == ["Merge", "Split", "Extract", "Rotate", "Delete"]


def test_operation_workspace_defaults_to_merge(window):
    assert window.operation_tabs.currentIndex() == 0
    assert window.operation_tabs.tabText(
        window.operation_tabs.currentIndex()
    ) == "Merge"


def test_operation_workspace_disables_during_active_job(window):
    window.set_merge_state(True)

    assert not window.operation_tabs.isEnabled()

    window.set_merge_state(False)

    assert window.operation_tabs.isEnabled()
