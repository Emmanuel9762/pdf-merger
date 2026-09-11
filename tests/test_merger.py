from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from main import get_merge_order
from pdf_merger import (
    find_pdfs,
    get_cli_files,
    is_valid_pdf,
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

    inputs = iter(["3 1 4 2"])

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    selected_files = get_merge_order(pdf_files)

    monkeypatch.undo()

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

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    selected_files = get_merge_order(pdf_files)

    monkeypatch.undo()

    assert selected_files == [
        pdf_files[2],
        pdf_files[0],
        pdf_files[3],
        pdf_files[1],
    ]