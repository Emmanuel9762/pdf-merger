import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

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


def test_extract_range_input_accepts_multiple_ranges(window):
    window.extract_ranges_input.setText("4-5, 2")

    assert parse_page_ranges(window.extract_ranges_input.text()) == (
        (4, 5),
        (2, 2),
    )


def test_extract_controls_disable_during_operation(window):
    window.set_merge_state(True)

    assert not window.extract_button.isEnabled()
    assert not window.extract_ranges_input.isEnabled()


def test_extract_requires_range_before_file_dialog(window, monkeypatch):
    warnings = []
    dialogs = []

    window.file_list.addItem("placeholder")
    item = window.file_list.item(0)
    from PySide6.QtCore import Qt
    from pathlib import Path
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

    window.extract_ranges_input.setText("")
    window.start_extract()

    assert warnings
    assert dialogs == []
