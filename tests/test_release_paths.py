from pypdf import PdfReader, PdfWriter

from pdf_merger import merge_files, resolve_output_path


def create_pdf(path, pages=1):
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    with path.open("wb") as handle:
        writer.write(handle)


def test_merge_supports_spaces_and_unicode_paths(tmp_path):
    first = tmp_path / "source files" / "Résumé one.pdf"
    second = tmp_path / "source files" / "ikhaya ezimbini.pdf"
    output = tmp_path / "exports folder" / "combined résumé.pdf"

    create_pdf(first, 1)
    create_pdf(second, 2)

    assert merge_files([first, second], output) == 3
    assert output.exists()
    assert len(PdfReader(output).pages) == 3


def test_output_policy_preserves_unicode_absolute_path(tmp_path):
    target = tmp_path / "iziphumo" / "uhlanganisiwe résumé"

    resolved = resolve_output_path(target)

    assert resolved == target.with_suffix(".pdf")
    assert resolved.parent.is_dir()
