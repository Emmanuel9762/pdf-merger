import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
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


def test_reorder_controls_disable_during_operation(window):
    window.set_merge_state(True)

    assert not window.reorder_button.isEnabled()
    assert not window.reorder_order_input.isEnabled()


def test_reorder_requires_order_before_file_dialog(window, monkeypatch):
    warnings = []
    dialogs = []

    window.file_list.addItem("placeholder")
    item = window.file_list.item(0)
    item.setData(Qt.UserRole, Path("input/source.pdf"))
    window.file_list.setCurrentRow(0)

    monkeypatch.setattr(
        "gui.app.QMessageBox.warning",
        lambda *args: warnings.append(args),
    )
    monkeypatch.setattr(
        "gui.app.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: dialogs.append(True) or ("", ""),
    )

    window.reorder_order_input.setText("")
    window.start_reorder()

    assert warnings
    assert dialogs == []


def test_reorder_rejects_non_numeric_order_before_file_dialog(window, monkeypatch):
    warnings = []
    dialogs = []

    window.file_list.addItem("placeholder")
    item = window.file_list.item(0)
    item.setData(Qt.UserRole, Path("input/source.pdf"))
    window.file_list.setCurrentRow(0)

    monkeypatch.setattr(
        "gui.app.QMessageBox.warning",
        lambda *args: warnings.append(args),
    )
    monkeypatch.setattr(
        "gui.app.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: dialogs.append(True) or ("", ""),
    )

    window.reorder_order_input.setText("3, nope, 1")
    window.start_reorder()

    assert warnings
    assert dialogs == []
