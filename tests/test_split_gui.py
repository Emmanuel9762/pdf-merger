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


def test_split_range_input_defaults_to_every_page(window):
    assert window.split_ranges_input.text() == ""
    assert parse_page_ranges(window.split_ranges_input.text()) is None


def test_split_range_input_accepts_multiple_ranges(window):
    window.split_ranges_input.setText("1-3, 5, 7-9")

    assert parse_page_ranges(window.split_ranges_input.text()) == (
        (1, 3),
        (5, 5),
        (7, 9),
    )


def test_split_controls_disable_during_operation(window):
    window.set_merge_state(True)

    assert not window.split_button.isEnabled()
    assert not window.split_ranges_input.isEnabled()
