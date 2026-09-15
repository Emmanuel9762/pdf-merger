from pathlib import Path

from pypdf import PdfWriter

from pdf_merger import (
    PDFInfo,
    get_pdf_info,
    get_total_pages,
    get_total_size,
)


def create_pdf(path, page_count):
    writer = PdfWriter()

    for _ in range(page_count):
        writer.add_blank_page(
            width=612,
            height=792
        )

    with path.open("wb") as file:
        writer.write(file)


def test_get_pdf_info(tmp_path):
    pdf_file = tmp_path / "test.pdf"

    create_pdf(pdf_file, 3)

    info = get_pdf_info(pdf_file)

    assert isinstance(info, PDFInfo)
    assert info.path == pdf_file
    assert info.pages == 3
    assert info.size_bytes == pdf_file.stat().st_size


def test_get_total_pages(tmp_path):
    first_pdf = tmp_path / "first.pdf"
    second_pdf = tmp_path / "second.pdf"

    create_pdf(first_pdf, 2)
    create_pdf(second_pdf, 4)

    total_pages = get_total_pages(
        [first_pdf, second_pdf]
    )

    assert total_pages == 6


def test_get_total_size(tmp_path):
    first_pdf = tmp_path / "first.pdf"
    second_pdf = tmp_path / "second.pdf"

    create_pdf(first_pdf, 2)
    create_pdf(second_pdf, 4)

    total_size = get_total_size(
        [first_pdf, second_pdf]
    )

    expected_size = (
        first_pdf.stat().st_size
        + second_pdf.stat().st_size
    )

    assert total_size == expected_size