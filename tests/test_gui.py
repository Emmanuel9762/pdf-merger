import os
from pathlib import Path

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


@pytest.fixture
def mock_pdfs():
    input_dir = Path("input")

    return [
        input_dir / "mock_pdf_1.pdf",
        input_dir / "mock_pdf_2.pdf",
    ]


def test_initial_gui_state(window):
    assert window.file_list.count() == 0
    assert window.summary_label.text() == "0 PDFs | 0 pages | 0 B"
    assert window.status_label.text() == "Ready."
    assert window.progress_bar.value() == 0

    assert window.add_button.isEnabled()
    assert window.remove_button.isEnabled()
    assert window.clear_button.isEnabled()
    assert window.choose_output_button.isEnabled()
    assert window.merge_button.isEnabled()
    assert window.file_list.isEnabled()


def test_merge_state_disables_controls(window):
    window.set_merge_state(True)

    assert not window.add_button.isEnabled()
    assert not window.remove_button.isEnabled()
    assert not window.clear_button.isEnabled()
    assert not window.choose_output_button.isEnabled()
    assert not window.merge_button.isEnabled()
    assert not window.file_list.isEnabled()


def test_merge_state_restores_controls(window):
    window.set_merge_state(True)
    window.set_merge_state(False)

    assert window.add_button.isEnabled()
    assert window.remove_button.isEnabled()
    assert window.clear_button.isEnabled()
    assert window.choose_output_button.isEnabled()
    assert window.merge_button.isEnabled()
    assert window.file_list.isEnabled()


def test_add_pdf_files(window, mock_pdfs):
    window.add_pdf_files(mock_pdfs)

    assert window.file_list.count() == 2
    assert window.pdf_files == set(mock_pdfs)
    assert window.summary_label.text().startswith("2 PDFs |")


def test_duplicate_pdf_files_are_ignored(window, mock_pdfs):
    window.add_pdf_files(mock_pdfs)
    window.add_pdf_files([mock_pdfs[0]])

    assert window.file_list.count() == 2
    assert window.pdf_files == set(mock_pdfs)


def test_remove_selected_pdf(window, mock_pdfs):
    window.add_pdf_files(mock_pdfs)

    window.file_list.setCurrentRow(0)
    removed_file = mock_pdfs[0]

    window.remove_selected()

    assert window.file_list.count() == 1
    assert removed_file not in window.pdf_files
    assert mock_pdfs[1] in window.pdf_files


def test_remove_selected_without_selection_does_nothing(
    window,
    mock_pdfs,
):
    window.add_pdf_files(mock_pdfs)

    window.file_list.clearSelection()
    window.remove_selected()

    assert window.file_list.count() == 2
    assert window.pdf_files == set(mock_pdfs)


def test_clear_files(window, mock_pdfs):
    window.add_pdf_files(mock_pdfs)

    window.clear_files()

    assert window.file_list.count() == 0
    assert window.pdf_files == set()
    assert window.summary_label.text() == "0 PDFs | 0 pages | 0 B"


def test_get_output_file_adds_pdf_extension(window, tmp_path):
    output_path = tmp_path / "merged"

    window.output_name.setText(str(output_path))

    result = window.get_output_file()

    assert result == tmp_path / "merged.pdf"


def test_get_output_file_preserves_pdf_extension(window, tmp_path):
    output_path = tmp_path / "result.pdf"

    window.output_name.setText(str(output_path))

    result = window.get_output_file()

    assert result == output_path
