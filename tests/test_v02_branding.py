import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from gui.app import MainWindow


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


def test_v02_gui_branding_and_six_operation_tabs(qapp):
    window = MainWindow()
    try:
        assert window.windowTitle() == "PDF Toolkit"
        assert [window.operation_tabs.tabText(i) for i in range(
            window.operation_tabs.count()
        )] == ["Merge", "Split", "Extract", "Rotate", "Delete", "Reorder"]
        assert any(
            label.text() == "PDF Toolkit"
            for label in window.findChildren(QLabel)
        )
    finally:
        window.close()
