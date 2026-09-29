from pathlib import Path

from pdf_merger import find_pdfs


def test_find_pdfs_returns_stable_name_order(tmp_path):
    for name in ("zeta.pdf", "Alpha.PDF", "middle.pdf", "notes.txt"):
        (tmp_path / name).touch()

    assert [path.name for path in find_pdfs(tmp_path)] == [
        "Alpha.PDF",
        "middle.pdf",
        "zeta.pdf",
    ]


def test_find_pdfs_ignores_pdf_named_directories(tmp_path):
    (tmp_path / "document.pdf").mkdir()
    real_pdf = tmp_path / "real.pdf"
    real_pdf.touch()

    assert find_pdfs(tmp_path) == [Path(real_pdf)]
