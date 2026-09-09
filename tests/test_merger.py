from pathlib import Path

from main import find_pdfs, get_cli_files


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