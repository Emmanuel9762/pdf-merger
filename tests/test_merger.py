from argparse import Namespace
from pathlib import Path

import pdf_merger.merger as merger_module
import pytest
from pypdf import PdfReader, PdfWriter

from main import run
from pdf_merger import (
    apply_merge_order,
    find_pdfs,
    get_cli_files,
    get_merge_order,
    is_valid_pdf,
    merge_files,
    merge_pdfs,
)


def test_find_pdfs(tmp_path):
    (tmp_path / "first.pdf").touch()
    (tmp_path / "second.PDF").touch()
    (tmp_path / "notes.txt").touch()

    pdfs = find_pdfs(tmp_path)

    assert len(pdfs) == 2
    assert all(file.suffix.lower() == ".pdf" for file in pdfs)


def test_is_valid_pdf(tmp_path):
    pdf_file = tmp_path / "test.pdf"
    pdf_file.touch()

    assert is_valid_pdf(pdf_file)


def test_is_valid_pdf_rejects_invalid_file(tmp_path):
    text_file = tmp_path / "notes.txt"
    text_file.touch()

    missing_file = tmp_path / "missing.pdf"

    assert not is_valid_pdf(text_file)
    assert not is_valid_pdf(missing_file)


def test_get_cli_files():
    files = get_cli_files([
        "input/mock_pdf_1.pdf",
        "input/mock_pdf_2.pdf",
    ])

    assert files is not None
    assert len(files) == 2
    assert all(isinstance(file, Path) for file in files)


def test_get_cli_files_missing_file():
    files = get_cli_files([
        "input/does-not-exist.pdf",
    ])

    assert files is None


def test_get_cli_files_invalid_extension():
    files = get_cli_files([
        "input/notes.txt",
    ])

    assert files is None


def create_test_pdf(path, page_count, width):
    writer = PdfWriter()

    for _ in range(page_count):
        writer.add_blank_page(width=width, height=792)

    with open(path, "wb") as file:
        writer.write(file)


@pytest.fixture
def mock_pdf_1(tmp_path):
    pdf_file = tmp_path / "mock_pdf_1.pdf"
    create_test_pdf(pdf_file, 1, 612)
    return pdf_file


@pytest.fixture
def mock_pdf_2(tmp_path):
    pdf_file = tmp_path / "mock_pdf_2.pdf"
    create_test_pdf(pdf_file, 2, 612)
    return pdf_file


@pytest.fixture
def mock_pdf_3(tmp_path):
    pdf_file = tmp_path / "mock_pdf_3.pdf"
    create_test_pdf(pdf_file, 3, 612)
    return pdf_file


@pytest.fixture
def mock_pdf_4(tmp_path):
    pdf_file = tmp_path / "mock_pdf_4.pdf"
    create_test_pdf(pdf_file, 4, 612)
    return pdf_file


def test_merge_pdfs(tmp_path):
    pdf_1 = tmp_path / "first.pdf"
    pdf_2 = tmp_path / "second.pdf"
    output = tmp_path / "merged.pdf"

    create_test_pdf(pdf_1, 2, 612)
    create_test_pdf(pdf_2, 3, 612)

    total_pages = merge_pdfs(
        [pdf_1, pdf_2],
        output
    )

    assert total_pages == 5
    assert output.exists()

    reader = PdfReader(output)

    assert len(reader.pages) == 5


def test_merge_preserves_order(tmp_path):
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    third = tmp_path / "third.pdf"
    output = tmp_path / "merged.pdf"

    create_test_pdf(first, 1, 100)
    create_test_pdf(second, 2, 200)
    create_test_pdf(third, 3, 300)

    total_pages = merge_pdfs(
        [third, first, second],
        output
    )

    assert total_pages == 6

    reader = PdfReader(output)

    widths = [
        float(page.mediabox.width)
        for page in reader.pages
    ]

    assert widths == [
        300.0,
        300.0,
        300.0,
        100.0,
        200.0,
        200.0,
    ]


def test_merge_invalid_pdf(tmp_path):
    invalid_pdf = tmp_path / "invalid.pdf"
    output = tmp_path / "merged.pdf"

    invalid_pdf.write_text("This is not a PDF.")

    total_pages = merge_pdfs(
        [invalid_pdf],
        output
    )

    assert total_pages is None
    assert not output.exists()


def test_merge_failure_cleans_up_temp_file(tmp_path):
    invalid_pdf = tmp_path / "invalid.pdf"
    output = tmp_path / "merged.pdf"
    temp_file = output.with_suffix(".tmp.pdf")

    invalid_pdf.write_text("This is not a PDF.")

    total_pages = merge_pdfs(
        [invalid_pdf],
        output
    )

    assert total_pages is None
    assert not output.exists()
    assert not temp_file.exists()


def test_get_merge_order():
    pdf_files = [
        Path("mock_pdf_1.pdf"),
        Path("mock_pdf_2.pdf"),
        Path("mock_pdf_3.pdf"),
        Path("mock_pdf_4.pdf"),
    ]

    selected_files = get_merge_order(
        pdf_files,
        input_func=lambda _: "3 1 4 2"
    )

    assert selected_files == [
        pdf_files[2],
        pdf_files[0],
        pdf_files[3],
        pdf_files[1],
    ]


@pytest.mark.parametrize(
    "invalid_input",
    [
        "1 2 2 4",
        "1 2 3",
        "1 2 3 9",
        "1 2 banana 4",
    ],
)
def test_get_merge_order_rejects_invalid_input(invalid_input):
    pdf_files = [
        Path("mock_pdf_1.pdf"),
        Path("mock_pdf_2.pdf"),
        Path("mock_pdf_3.pdf"),
        Path("mock_pdf_4.pdf"),
    ]

    inputs = iter([
        invalid_input,
        "3 1 4 2",
    ])

    selected_files = get_merge_order(
        pdf_files,
        input_func=lambda _: next(inputs)
    )

    assert selected_files == [
        pdf_files[2],
        pdf_files[0],
        pdf_files[3],
        pdf_files[1],
    ]


def test_run_cli_merge(tmp_path):
    pdf_1 = tmp_path / "first.pdf"
    pdf_2 = tmp_path / "second.pdf"
    output = tmp_path / "merged.pdf"

    create_test_pdf(pdf_1, 2, 612)
    create_test_pdf(pdf_2, 3, 612)

    args = Namespace(
        files=[str(pdf_1), str(pdf_2)],
        input="input",
        output=str(output),
    )

    result = run(args)

    assert result == 0
    assert output.exists()

    reader = PdfReader(output)

    assert len(reader.pages) == 5


def test_run_rejects_missing_cli_file(tmp_path):
    output = tmp_path / "merged.pdf"

    args = Namespace(
        files=[str(tmp_path / "missing.pdf")],
        input="input",
        output=str(output),
    )

    result = run(args)

    assert result == 1
    assert not output.exists()


def test_run_rejects_missing_input_folder(tmp_path):
    output = tmp_path / "merged.pdf"

    args = Namespace(
        files=[],
        input=str(tmp_path / "missing"),
        output=str(output),
    )

    result = run(args)

    assert result == 1
    assert not output.exists()


def test_run_rejects_empty_input_folder(tmp_path):
    input_folder = tmp_path / "input"
    input_folder.mkdir()

    output = tmp_path / "merged.pdf"

    args = Namespace(
        files=[],
        input=str(input_folder),
        output=str(output),
    )

    result = run(args)

    assert result == 1
    assert not output.exists()


def test_run_merges_files_from_input_folder(tmp_path):
    input_folder = tmp_path / "input"
    input_folder.mkdir()

    pdf_1 = input_folder / "mock_pdf_1.pdf"
    pdf_2 = input_folder / "mock_pdf_2.pdf"
    pdf_3 = input_folder / "mock_pdf_3.pdf"
    pdf_4 = input_folder / "mock_pdf_4.pdf"

    create_test_pdf(pdf_1, 1, 100)
    create_test_pdf(pdf_2, 2, 200)
    create_test_pdf(pdf_3, 3, 300)
    create_test_pdf(pdf_4, 4, 400)

    output = tmp_path / "merged.pdf"

    args = Namespace(
        files=[],
        input=str(input_folder),
        output=str(output),
    )

    result = run(
        args,
        input_func=lambda _: "3 1 4 2"
    )

    assert result == 0
    assert output.exists()

    reader = PdfReader(output)

    assert len(reader.pages) == 10

def test_apply_merge_order():
    pdf_files = [
        Path("mock_pdf_1.pdf"),
        Path("mock_pdf_2.pdf"),
        Path("mock_pdf_3.pdf"),
        Path("mock_pdf_4.pdf"),
    ]

    selected_files = apply_merge_order(
        pdf_files,
        [3, 1, 4, 2]
    )

    assert selected_files == [
        pdf_files[2],
        pdf_files[0],
        pdf_files[3],
        pdf_files[1],
    ]

@pytest.mark.parametrize(
    "order",
    [
        [1, 2, 2, 4],
        [1, 2, 3],
        [1, 2, 3, 5],
    ],
)
def test_apply_merge_order_rejects_invalid_order(order):
    pdf_files = [
        Path("mock_pdf_1.pdf"),
        Path("mock_pdf_2.pdf"),
        Path("mock_pdf_3.pdf"),
        Path("mock_pdf_4.pdf"),
    ]

    assert apply_merge_order(pdf_files, order) is None


def test_run_accepts_cli_order(tmp_path):
    input_folder = tmp_path / "input"
    input_folder.mkdir()

    for index, page_count in enumerate([1, 2, 3, 4], start=1):
        create_test_pdf(
            input_folder / f"mock_pdf_{index}.pdf",
            page_count,
            612
        )

    output = tmp_path / "merged.pdf"

    args = Namespace(
        files=[],
        input=str(input_folder),
        output=str(output),
        order=[3, 1, 4, 2],
    )

    result = run(args)

    assert result == 0
    assert output.exists()

    reader = PdfReader(output)

    assert len(reader.pages) == 10


def test_merge_files(tmp_path):
    pdf_1 = tmp_path / "first.pdf"
    pdf_2 = tmp_path / "second.pdf"
    output = tmp_path / "merged.pdf"

    create_test_pdf(pdf_1, 2, 612)
    create_test_pdf(pdf_2, 3, 612)

    total_pages = merge_files(
        [pdf_1, pdf_2],
        output
    )

    assert total_pages == 5
    assert output.exists()

    reader = PdfReader(output)

    assert len(reader.pages) == 5


def test_merge_pdfs_reports_progress(
    tmp_path,
    mock_pdf_1,
    mock_pdf_2,
    mock_pdf_3,
    mock_pdf_4,
):
    output_file = tmp_path / "merged.pdf"

    pdf_files = [
        mock_pdf_3,
        mock_pdf_1,
        mock_pdf_4,
        mock_pdf_2,
    ]

    progress = []

    def callback(current, total, pdf_file):
        progress.append(
            (current, total, pdf_file)
        )

    result = merge_pdfs(
        pdf_files,
        output_file,
        progress_callback=callback
    )

    assert result == 4
    assert progress == [
        (1, 4, mock_pdf_3),
        (2, 4, mock_pdf_1),
        (3, 4, mock_pdf_4),
        (4, 4, mock_pdf_2),
    ]


def test_merge_files_forwards_progress_callback(
    tmp_path,
    mock_pdf_1,
    mock_pdf_2,
):
    output_file = tmp_path / "merged.pdf"

    progress = []

    def callback(current, total, pdf_file):
        progress.append(
            (current, total, pdf_file)
        )

    result = merge_files(
        [mock_pdf_1, mock_pdf_2],
        output_file,
        progress_callback=callback
    )

    assert result == 2
    assert progress == [
        (1, 2, mock_pdf_1),
        (2, 2, mock_pdf_2),
    ]


def test_merge_pdfs_without_progress_callback(
    tmp_path,
    mock_pdf_1,
    mock_pdf_2,
):
    output_file = tmp_path / "merged.pdf"

    result = merge_pdfs(
        [mock_pdf_1, mock_pdf_2],
        output_file
    )

    assert result == 2
    assert output_file.exists()


def test_merge_files_rejects_empty_file_list(tmp_path):
    output = tmp_path / "merged.pdf"

    result = merge_files([], output)

    assert result is None
    assert not output.exists()


def test_merge_files_can_be_cancelled(tmp_path, mock_pdf_1, mock_pdf_2):
    output = tmp_path / "merged.pdf"
    temp_file = output.with_suffix(".tmp.pdf")

    cancelled = False

    def cancel_callback():
        nonlocal cancelled
        cancelled = True
        return True

    result = merge_files(
        [mock_pdf_1, mock_pdf_2],
        output,
        cancel_callback=cancel_callback,
    )

    assert result is None
    assert cancelled is True
    assert not output.exists()
    assert not temp_file.exists()


def test_merge_files_rejects_missing_input_file(tmp_path):
    good_file = tmp_path / "good.pdf"
    missing_file = tmp_path / "missing.pdf"
    output = tmp_path / "merged.pdf"

    create_test_pdf(good_file, 2, 612)

    errors = []

    result = merge_files(
        [good_file, missing_file],
        output,
        error_callback=lambda message, current_file: errors.append((message, current_file)),
    )

    assert result is None
    assert errors == [(f"Input file does not exist: {missing_file}", missing_file)]
    assert not output.exists()


def test_merge_files_rejects_duplicate_input_files(tmp_path):
    pdf_file = tmp_path / "duplicate.pdf"
    output = tmp_path / "merged.pdf"

    create_test_pdf(pdf_file, 2, 612)

    errors = []

    result = merge_files(
        [pdf_file, pdf_file],
        output,
        error_callback=lambda message, current_file: errors.append((message, current_file)),
    )

    assert result is None
    assert errors == [(f"Duplicate input file: {pdf_file}", pdf_file)]
    assert not output.exists()


def test_merge_files_rejects_output_equal_to_input(tmp_path):
    pdf_file = tmp_path / "same.pdf"
    create_test_pdf(pdf_file, 2, 612)

    errors = []

    result = merge_files(
        [pdf_file],
        pdf_file,
        error_callback=lambda message, current_file: errors.append((message, current_file)),
    )

    assert result is None
    assert errors == [(f"Output file cannot be the same as an input file: {pdf_file}", pdf_file)]
    assert pdf_file.exists()


def test_merge_files_rejects_invalid_output_parent(tmp_path):
    pdf_file = tmp_path / "input.pdf"
    create_test_pdf(pdf_file, 2, 612)

    output_parent = tmp_path / "not_a_directory"
    output_parent.write_text("not a directory")
    output = output_parent / "merged.pdf"

    errors = []

    result = merge_files(
        [pdf_file],
        output,
        error_callback=lambda message, current_file: errors.append((message, current_file)),
    )

    assert result is None
    assert errors == [(f"Output parent is not a directory: {output_parent}", pdf_file)]
    assert not output.exists()


def test_merge_files_does_not_overwrite_existing_output_on_validation_failure(tmp_path):
    pdf_file = tmp_path / "input.pdf"
    output = tmp_path / "merged.pdf"

    create_test_pdf(pdf_file, 2, 612)
    output.write_text("old output")

    errors = []

    result = merge_files(
        [pdf_file, pdf_file],
        output,
        error_callback=lambda message, current_file: errors.append((message, current_file)),
    )

    assert result is None
    assert errors == [(f"Duplicate input file: {pdf_file}", pdf_file)]
    assert output.read_text() == "old output"


def test_merge_pdfs_does_not_leave_final_output_after_write_failure(tmp_path, monkeypatch):
    pdf_file = tmp_path / "input.pdf"
    output = tmp_path / "merged.pdf"
    temp_file = output.with_suffix(".tmp.pdf")

    create_test_pdf(pdf_file, 2, 612)

    def raise_write_error(self, target):
        raise RuntimeError("disk full")

    monkeypatch.setattr(merger_module.PdfWriter, "write", raise_write_error)

    errors = []

    result = merge_files(
        [pdf_file],
        output,
        error_callback=lambda message, current_file: errors.append((message, current_file)),
    )

    assert result is None
    assert errors == [("disk full", pdf_file)]
    assert not output.exists()
    assert not temp_file.exists()


def test_merge_pdfs_reports_progress(
    tmp_path,
    mock_pdf_1,
    mock_pdf_2,
    mock_pdf_3,
    mock_pdf_4,
):
    output_file = tmp_path / "merged.pdf"

    pdf_files = [
        mock_pdf_3,
        mock_pdf_1,
        mock_pdf_4,
        mock_pdf_2,
    ]

    progress = []

    def callback(current, total, pdf_file):
        progress.append(
            (current, total, pdf_file)
        )

    result = merge_pdfs(
        pdf_files,
        output_file,
        progress_callback=callback
    )

    assert result == 10
    assert progress == [
        (1, 4, mock_pdf_3),
        (2, 4, mock_pdf_1),
        (3, 4, mock_pdf_4),
        (4, 4, mock_pdf_2),
    ]


def test_merge_files_forwards_progress_callback(
    tmp_path,
    mock_pdf_1,
    mock_pdf_2,
):
    output_file = tmp_path / "merged.pdf"

    progress = []

    def callback(current, total, pdf_file):
        progress.append(
            (current, total, pdf_file)
        )

    result = merge_files(
        [mock_pdf_1, mock_pdf_2],
        output_file,
        progress_callback=callback
    )

    assert result == 3
    assert progress == [
        (1, 2, mock_pdf_1),
        (2, 2, mock_pdf_2),
    ]


def test_merge_pdfs_without_progress_callback(
    tmp_path,
    mock_pdf_1,
    mock_pdf_2,
):
    output_file = tmp_path / "merged.pdf"

    result = merge_pdfs(
        [mock_pdf_1, mock_pdf_2],
        output_file
    )

    assert result == 3
    assert output_file.exists()


def test_merge_pdfs_reports_error(
    tmp_path,
    monkeypatch,
):
    pdf_file = tmp_path / "broken.pdf"
    output_file = tmp_path / "merged.pdf"

    pdf_file.write_bytes(b"not a real pdf")

    def raise_error(self, file_path):
        raise RuntimeError("test merge failure")

    monkeypatch.setattr(
        merger_module.PdfWriter,
        "append",
        raise_error,
    )

    errors = []

    def error_callback(error_message, current_file):
        errors.append(
            (error_message, current_file)
        )

    result = merger_module.merge_pdfs(
        [pdf_file],
        output_file,
        error_callback=error_callback,
    )

    assert result is None

    assert errors == [
        ("test merge failure", pdf_file)
    ]

    assert not output_file.exists()


def test_merge_files_forwards_error_callback(
    tmp_path,
    monkeypatch,
):
    pdf_file = tmp_path / "broken.pdf"
    output_file = tmp_path / "merged.pdf"

    pdf_file.write_bytes(b"not a real pdf")

    def raise_error(self, file_path):
        raise RuntimeError("forwarded failure")

    monkeypatch.setattr(
        merger_module.PdfWriter,
        "append",
        raise_error,
    )

    errors = []

    def error_callback(error_message, current_file):
        errors.append(
            (error_message, current_file)
        )

    result = merger_module.merge_files(
        [pdf_file],
        output_file,
        error_callback=error_callback,
    )

    assert result is None

    assert errors == [
        ("forwarded failure", pdf_file)
    ]