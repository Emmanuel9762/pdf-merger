"""Public service contract, including publication and callback ordering."""
from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from pdf_merger import merge_files
import pdf_merger.merger as merger


@pytest.fixture
def request_files(tmp_path):
    files = []
    for index in (1, 2):
        path = tmp_path / f"input{index}.pdf"
        with PdfWriter() as writer:
            writer.add_blank_page(width=100 * index, height=200)
            writer.write(path)
        files.append(path)
    output = tmp_path / "merged.pdf"
    output.write_bytes(b"previous output")
    return files, output


def test_success_progress_precedes_publication(request_files):
    files, output = request_files
    events, errors = [], []

    def progress(current, total, path):
        assert output.read_bytes() == b"previous output"
        events.append((current, total, path))

    result = merge_files(files, output, progress, lambda *args: errors.append(args))
    assert type(result) is int and result == 2
    assert events == [(1, 2, files[0]), (2, 2, files[1])]
    assert errors == []
    assert [page.mediabox.width for page in PdfReader(output).pages] == [100, 200]


@pytest.mark.parametrize("kind", ["missing", "unreadable", "malformed"])
def test_input_failure_reports_once_and_preserves_output(request_files, monkeypatch, kind):
    files, output = request_files
    if kind == "missing":
        files[1].unlink()
    elif kind == "unreadable":
        monkeypatch.setattr(merger.os, "access", lambda path, mode: path != files[1])
    else:
        files[1].write_bytes(b"not a pdf")
    events, errors = [], []
    result = merge_files(files, output, lambda *args: events.append(args),
                         lambda *args: errors.append(args))
    assert result is None
    assert len(errors) == 1 and errors[0][0] and errors[0][1] == files[1]
    assert events == ([(1, 2, files[0])] if kind == "malformed" else [])
    assert output.read_bytes() == b"previous output"
    assert set(output.parent.iterdir()) == set([output] + [p for p in files if p.exists()])


@pytest.mark.parametrize("after", [0, 1])
def test_cancellation_is_silent_and_preserves_output(request_files, after):
    files, output = request_files
    events, errors = [], []
    assert merge_files(files, output, lambda *args: events.append(args),
                       lambda *args: errors.append(args),
                       lambda: len(events) >= after) is None
    assert len(events) == after and errors == []
    assert output.read_bytes() == b"previous output"
    assert set(output.parent.iterdir()) == set(files + [output])


def test_partial_write_is_removed_before_error_callback(request_files, monkeypatch):
    files, output = request_files
    events, errors = [], []

    def broken_write(self, target):
        Path(target).write_bytes(b"partial")
        raise OSError("disk full")

    def error(message, path):
        assert set(output.parent.iterdir()) == set(files + [output])
        assert output.read_bytes() == b"previous output"
        errors.append((message, path))

    monkeypatch.setattr(PdfWriter, "write", broken_write)
    assert merge_files(files, output, lambda *args: events.append(args), error) is None
    assert len(events) == 2  # 100% input progress is not successful completion.
    assert errors == [("disk full", files[-1])]


def test_cancel_after_final_progress_does_not_publish(request_files):
    files, output = request_files
    events, errors = [], []
    assert merge_files(files, output, lambda *args: events.append(args),
                       lambda *args: errors.append(args),
                       lambda: len(events) == len(files)) is None
    assert errors == []
    assert output.read_bytes() == b"previous output"


def test_unrelated_temporary_file_is_preserved(request_files):
    files, output = request_files
    unrelated = output.with_suffix(".tmp.pdf")
    unrelated.write_bytes(b"unrelated")
    assert merge_files(files, output) == 2
    assert unrelated.read_bytes() == b"unrelated"


@pytest.mark.parametrize("outcome", ["cancel", "write_failure", "replace_failure"])
def test_publication_boundary_cleans_owned_file(request_files, monkeypatch, outcome):
    files, output = request_files
    original_write = PdfWriter.write
    cancelled = False
    errors = []

    def write(self, target):
        nonlocal cancelled
        original_write(self, target)
        if outcome == "cancel":
            cancelled = True
        elif outcome == "write_failure":
            raise OSError("write failed")

    def replace(self, target):
        raise OSError("replace failed")

    monkeypatch.setattr(PdfWriter, "write", write)
    if outcome == "replace_failure":
        monkeypatch.setattr(Path, "replace", replace)
    assert merge_files(files, output, error_callback=lambda *args: errors.append(args),
                       cancel_callback=lambda: cancelled) is None
    assert len(errors) == (0 if outcome == "cancel" else 1)
    assert output.read_bytes() == b"previous output"
    assert set(output.parent.iterdir()) == set(files + [output])


@pytest.mark.parametrize("cancel", [False, True])
def test_temporary_style_input_is_never_deleted(request_files, cancel):
    files, output = request_files
    renamed = output.with_suffix(".tmp.pdf")
    files[0].rename(renamed)
    files[0] = renamed
    original = renamed.read_bytes()
    result = merge_files(files, output, cancel_callback=lambda: cancel)
    assert result == (None if cancel else 2)
    assert renamed.read_bytes() == original


@pytest.mark.parametrize("outcome", ["success", "cancel", "failure"])
def test_real_service_emits_exactly_one_worker_terminal_result(request_files, outcome):
    from gui.worker import MergeWorker

    files, output = request_files
    worker = MergeWorker(files, output)
    events = []
    worker.finished.connect(lambda *_: events.append("success"))
    worker.failed.connect(lambda *_: events.append("failure"))
    worker.cancelled.connect(lambda: events.append("cancel"))
    if outcome == "cancel":
        worker.progress.connect(lambda current, total, _: worker.cancel() if current == total else None)
    elif outcome == "failure":
        files[-1].write_bytes(b"invalid pdf")
    worker.run()
    assert events == [outcome]
    if outcome != "success":
        assert output.read_bytes() == b"previous output"
