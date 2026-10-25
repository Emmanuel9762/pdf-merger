import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from gui.app import MainWindow
from pdf_merger import parse_page_ranges


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


def test_delete_range_input_accepts_multiple_ranges(window):
    window.delete_ranges_input.setText("2-3, 5")

    assert parse_page_ranges(window.delete_ranges_input.text()) == (
        (2, 3),
        (5, 5),
    )


def test_delete_controls_disable_during_operation(window):
    window.set_operation_state(True)

    assert not window.delete_button.isEnabled()
    assert not window.delete_ranges_input.isEnabled()


def test_delete_requires_range_before_file_dialog(window, monkeypatch):
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

    window.delete_ranges_input.setText("")
    window.start_delete()

    assert warnings
    assert dialogs == []


def test_delete_rejects_invalid_ranges_before_file_dialog(window, monkeypatch):
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

    window.delete_ranges_input.setText("3-1")
    window.start_delete()

    assert warnings
    assert dialogs == []
