from pathlib import Path

from pypdf import PdfReader, PdfWriter

from main import find_pdfs, get_cli_files, merge_pdfs


def test_find_pdfs(tmp_path):
    (tmp_path / "first.pdf").touch()
    (tmp_path / "second.PDF").touch()
    (tmp_path / "notes.txt").touch()

    pdfs = find_pdfs(tmp_path)

    assert len(pdfs) == 2
    assert all(file.suffix.lower() == ".pdf" for file in pdfs)


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


def create_test_pdf(path, page_count):
    writer = PdfWriter()

    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)

    with open(path, "wb") as file:
        writer.write(file)


def test_merge_pdfs(tmp_path):
    pdf_1 = tmp_path / "first.pdf"
    pdf_2 = tmp_path / "second.pdf"
    output = tmp_path / "merged.pdf"

    create_test_pdf(pdf_1, 2)
    create_test_pdf(pdf_2, 3)

    total_pages = merge_pdfs(
        [pdf_1, pdf_2],
        output
    )

    assert total_pages == 5
    assert output.exists()

    reader = PdfReader(output)

    assert len(reader.pages) == 5