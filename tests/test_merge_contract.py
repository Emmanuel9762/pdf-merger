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


@pytest.mark.xfail(strict=True, reason="CP68: cancellation after final append is ignored")
def test_cancel_after_final_progress_does_not_publish(request_files):
    files, output = request_files
    events, errors = [], []
    assert merge_files(files, output, lambda *args: events.append(args),
                       lambda *args: errors.append(args),
                       lambda: len(events) == len(files)) is None
    assert errors == []
    assert output.read_bytes() == b"previous output"


@pytest.mark.xfail(strict=True, reason="CP68: fixed temporary name overwrites unrelated files")
def test_unrelated_temporary_file_is_preserved(request_files):
    files, output = request_files
    unrelated = output.with_suffix(".tmp.pdf")
    unrelated.write_bytes(b"unrelated")
    assert merge_files(files, output) == 2
    assert unrelated.read_bytes() == b"unrelated"
