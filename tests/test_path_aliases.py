from pathlib import Path

from pypdf import PdfWriter

from pdf_merger import merge_files


def create_pdf(path):
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)

    with path.open("wb") as file:
        writer.write(file)


def test_merge_rejects_duplicate_input_through_symlink(tmp_path):
    original = tmp_path / "original.pdf"
    alias = tmp_path / "alias.pdf"
    output = tmp_path / "merged.pdf"
    create_pdf(original)
    alias.symlink_to(original)
    errors = []

    result = merge_files(
        [original, alias],
        output,
        error_callback=lambda message, current: errors.append((message, current)),
    )

    assert result is None
    assert not output.exists()
    assert errors == [(f"Duplicate input file: {alias}", alias)]


def test_merge_rejects_output_aliasing_an_input(tmp_path):
    input_file = tmp_path / "source.pdf"
    output_alias = tmp_path / "output.pdf"
    create_pdf(input_file)
    output_alias.symlink_to(input_file)
    errors = []

    result = merge_files(
        [input_file],
        output_alias,
        error_callback=lambda message, current: errors.append((message, current)),
    )

    assert result is None
    assert errors == [(
        f"Output file cannot be the same as an input file: {output_alias}",
        input_file,
    )]
    assert output_alias.resolve() == input_file.resolve()
