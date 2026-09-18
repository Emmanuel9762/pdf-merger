import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from gui.app import MainWindow
from gui.worker import MergeWorker


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    return app


def wait_for_condition(condition, qapp, timeout=3000):
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
    assert window.cancel_button.isEnabled() is False
    assert window.file_list.isEnabled()


def test_merge_state_disables_controls(window):
    window.set_merge_state(True)

    assert not window.add_button.isEnabled()
    assert not window.remove_button.isEnabled()
    assert not window.clear_button.isEnabled()
    assert not window.choose_output_button.isEnabled()
    assert not window.merge_button.isEnabled()
    assert window.cancel_button.isEnabled()
    assert not window.file_list.isEnabled()


def test_merge_state_restores_controls(window):
    window.set_merge_state(True)
    window.set_merge_state(False)

    assert window.add_button.isEnabled()
    assert window.remove_button.isEnabled()
    assert window.clear_button.isEnabled()
    assert window.choose_output_button.isEnabled()
    assert window.merge_button.isEnabled()
    assert not window.cancel_button.isEnabled()
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


def test_merge_worker_success_emits_finished_and_total_pages():
    pdf_files = [Path("input/a.pdf"), Path("input/b.pdf")]
    output_file = Path("output/merged.pdf")
    worker = MergeWorker(pdf_files, output_file)

    saw_merge_files = {}
    progress_events = []
    finished_events = []

    def fake_merge_files(files, target, progress_callback=None, error_callback=None, cancel_callback=None):
        saw_merge_files["files"] = list(files)
        saw_merge_files["target"] = target
        assert cancel_callback is not None
        assert cancel_callback() is False
        progress_callback(1, 2, files[0])
        return 12

    worker.progress.connect(lambda current, total, pdf_file: progress_events.append((current, total, pdf_file)))
    worker.finished.connect(lambda total_pages, result_path: finished_events.append((total_pages, result_path)))

    monkeypatch = pytest.MonkeyPatch()
    try:
        import gui.worker as worker_module

        monkeypatch.setattr(worker_module, "merge_files", fake_merge_files)
        worker.run()
    finally:
        monkeypatch.undo()

    assert saw_merge_files == {"files": pdf_files, "target": output_file}
    assert progress_events == [(1, 2, pdf_files[0])]
    assert finished_events == [(12, output_file)]


def test_merge_worker_tracks_cancellation_state():
    pdf_files = [Path("input/a.pdf")]
    output_file = Path("output/merged.pdf")
    worker = MergeWorker(pdf_files, output_file)

    assert not worker.is_cancelled()

    worker.cancel()

    assert worker.is_cancelled()


def test_merge_worker_does_not_emit_finished_when_cancelled():
    pdf_files = [Path("input/a.pdf"), Path("input/b.pdf")]
    output_file = Path("output/merged.pdf")
    worker = MergeWorker(pdf_files, output_file)

    finished_events = []
    cancelled_events = []
    worker.finished.connect(lambda total_pages, result_path: finished_events.append((total_pages, result_path)))
    worker.cancelled.connect(lambda: cancelled_events.append(True))

    def fake_merge_files(files, target, progress_callback=None, error_callback=None, cancel_callback=None):
        assert cancel_callback is not None
        assert cancel_callback() is True
        return None

    worker.cancel()

    monkeypatch = pytest.MonkeyPatch()
    try:
        import gui.worker as worker_module

        monkeypatch.setattr(worker_module, "merge_files", fake_merge_files)
        worker.run()
    finally:
        monkeypatch.undo()

    assert finished_events == []
    assert cancelled_events == [True]


def test_merge_worker_failure_emits_detailed_error_and_file():
    pdf_files = [Path("input/bad.pdf")]
    output_file = Path("output/merged.pdf")
    worker = MergeWorker(pdf_files, output_file)

    failed_events = []
    worker.failed.connect(lambda error_message, current_file: failed_events.append((error_message, current_file)))

    def fake_merge_files(files, target, progress_callback=None, error_callback=None, cancel_callback=None):
        error_callback("Password required", files[0])
        return None

    monkeypatch = pytest.MonkeyPatch()
    try:
        import gui.worker as worker_module

        monkeypatch.setattr(worker_module, "merge_files", fake_merge_files)
        worker.run()
    finally:
        monkeypatch.undo()

    assert failed_events == [("Password required", pdf_files[0])]


def test_merge_worker_progress_forwards_values_unchanged():
    pdf_files = [Path("input/test.pdf")]
    output_file = Path("output/merged.pdf")
    worker = MergeWorker(pdf_files, output_file)

    progress_events = []
    worker.progress.connect(lambda current, total, pdf_file: progress_events.append((current, total, pdf_file)))

    def fake_merge_files(files, target, progress_callback=None, error_callback=None, cancel_callback=None):
        progress_callback(3, 7, files[0])
        return 7

    monkeypatch = pytest.MonkeyPatch()
    try:
        import gui.worker as worker_module

        monkeypatch.setattr(worker_module, "merge_files", fake_merge_files)
        worker.run()
    finally:
        monkeypatch.undo()

    assert progress_events == [(3, 7, pdf_files[0])]


def test_merge_progress_updates_gui_status_and_value(window):
    pdf_file = Path("input/example.pdf")

    window.merge_progress(2, 4, pdf_file)

    assert window.progress_bar.maximum() == 4
    assert window.progress_bar.value() == 2
    assert window.status_label.text() == "Processing: example.pdf (2 of 4)"


def test_merge_succeeded_updates_status_and_presents_result(window, monkeypatch):
    captured = {}

    def fake_information(parent, title, message):
        captured["title"] = title
        captured["message"] = message

    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.information", fake_information)

    window.progress_bar.setRange(0, 4)
    window.progress_bar.setValue(0)

    window.merge_succeeded(12, Path("output/merged.pdf"))

    assert window.progress_bar.value() == 4
    assert window.status_label.text() == "Merge completed successfully."
    assert captured["title"] == "Merge Complete"
    assert "Files: 4" in captured["message"]
    assert "Pages: 12" in captured["message"]
    assert "Output: output/merged.pdf" in captured["message"]


def test_merge_failed_updates_status_and_shows_error_details(window, monkeypatch):
    captured = {}

    def fake_critical(parent, title, message):
        captured["title"] = title
        captured["message"] = message

    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.critical", fake_critical)

    window.progress_bar.setRange(0, 4)
    window.progress_bar.setValue(4)

    window.merge_failed("Password required", Path("input/bad.pdf"))

    assert window.status_label.text() == "Merge failed."
    assert window.progress_bar.value() == 0
    assert captured["title"] == "Merge Failed"
    assert "Could not process:" in captured["message"]
    assert "bad.pdf" in captured["message"]
    assert "Password required" in captured["message"]


def test_cancel_merge_requests_worker_cancellation(window):
    worker = MergeWorker([Path("input/a.pdf")], Path("output/merged.pdf"))
    window.merge_worker = worker
    window.cancel_button.setEnabled(True)

    window.cancel_merge()

    assert not window.cancel_button.isEnabled()
    assert window.status_label.text() == "Cancelling merge..."
    assert worker.is_cancelled()


def test_merge_cancelled_updates_status_and_progress(window):
    window.progress_bar.setRange(0, 4)
    window.progress_bar.setValue(4)

    window.merge_cancelled()

    assert window.status_label.text() == "Merge cancelled."
    assert window.progress_bar.value() == 0


def test_start_merge_runs_worker_and_restores_gui_state(
    window,
    mock_pdfs,
    tmp_path,
    monkeypatch,
    qapp,
):
    window.add_pdf_files(mock_pdfs)

    output_file = tmp_path / "merged.pdf"
    window.output_name.setText(str(output_file))

    captured = {}

    def fake_information(parent, title, message):
        captured["title"] = title
        captured["message"] = message

    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.information", fake_information)

    def fake_merge_files(files, target, progress_callback=None, error_callback=None, cancel_callback=None):
        progress_callback(1, len(files), files[0])
        progress_callback(2, len(files), files[1])
        return 10

    monkeypatch.setattr("gui.worker.merge_files", fake_merge_files)

    window.start_merge()

    assert window.merge_thread is not None
    assert window.merge_worker is not None
    assert not window.merge_button.isEnabled()
    assert not window.file_list.isEnabled()

    completed = wait_for_condition(
        lambda: window.merge_thread is None and window.merge_worker is None,
        qapp,
    )

    assert completed is True
    assert window.status_label.text() == "Merge completed successfully."
    assert window.progress_bar.value() == window.progress_bar.maximum()
    assert window.merge_button.isEnabled()
    assert window.file_list.isEnabled()
    assert window.add_button.isEnabled()
    assert window.remove_button.isEnabled()
    assert window.clear_button.isEnabled()
    assert window.choose_output_button.isEnabled()
    assert captured["title"] == "Merge Complete"
    assert "Pages: 10" in captured["message"]


def test_start_merge_failure_lifecycle_restores_gui_state(
    window,
    mock_pdfs,
    tmp_path,
    monkeypatch,
    qapp,
):
    window.add_pdf_files(mock_pdfs)

    output_file = tmp_path / "merged.pdf"
    window.output_name.setText(str(output_file))

    captured = {}

    def fake_critical(parent, title, message):
        captured["title"] = title
        captured["message"] = message

    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.critical", fake_critical)

    def fake_merge_files(files, target, progress_callback=None, error_callback=None, cancel_callback=None):
        if progress_callback:
            progress_callback(1, len(files), files[0])

        if error_callback:
            error_callback("Password required", files[0])

        return None

    monkeypatch.setattr("gui.worker.merge_files", fake_merge_files)

    window.start_merge()

    assert window.merge_thread is not None
    assert window.merge_worker is not None

    completed = wait_for_condition(
        lambda: window.merge_thread is None and window.merge_worker is None,
        qapp,
    )

    assert completed is True
    assert window.status_label.text() == "Merge failed."
    assert window.progress_bar.value() == 0
    assert window.add_button.isEnabled()
    assert window.remove_button.isEnabled()
    assert window.clear_button.isEnabled()
    assert window.choose_output_button.isEnabled()
    assert window.merge_button.isEnabled()
    assert window.file_list.isEnabled()
    assert captured["title"] == "Merge Failed"
    assert "Password required" in captured["message"]
    assert mock_pdfs[0].name in captured["message"]


def test_start_merge_cancellation_lifecycle_restores_gui_state(
    window,
    mock_pdfs,
    tmp_path,
    monkeypatch,
    qapp,
):
    window.add_pdf_files(mock_pdfs)

    output_file = tmp_path / "merged.pdf"
    window.output_name.setText(str(output_file))

    def fake_merge_files(
        files,
        target,
        progress_callback=None,
        error_callback=None,
        cancel_callback=None,
    ):
        if progress_callback:
            progress_callback(1, len(files), files[0])

        assert cancel_callback is not None
        assert cancel_callback() is True

        return None

    monkeypatch.setattr(
        "gui.worker.merge_files",
        fake_merge_files,
    )

    window.start_merge()

    assert window.merge_thread is not None
    assert window.merge_worker is not None
    assert not window.merge_button.isEnabled()
    assert not window.file_list.isEnabled()
    assert window.cancel_button.isEnabled()

    window.cancel_merge()

    completed = wait_for_condition(
        lambda: window.merge_thread is None and window.merge_worker is None,
        qapp,
    )

    assert completed is True
    assert window.status_label.text() == "Merge cancelled."
    assert window.progress_bar.value() == 0
    assert window.add_button.isEnabled()
    assert window.remove_button.isEnabled()
    assert window.clear_button.isEnabled()
    assert window.choose_output_button.isEnabled()
    assert window.merge_button.isEnabled()
    assert window.file_list.isEnabled()
    assert not window.cancel_button.isEnabled()
