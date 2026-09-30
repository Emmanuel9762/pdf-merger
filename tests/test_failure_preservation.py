from pypdf import PdfWriter

from pdf_merger import merge_files


def create_pdf(path):
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)

    with path.open("wb") as file:
        writer.write(file)


def test_corrupt_input_preserves_existing_output(tmp_path):
    bad_pdf = tmp_path / "broken.pdf"
    output = tmp_path / "merged.pdf"
    bad_pdf.write_text("not a pdf")
    output.write_bytes(b"existing output")
    errors = []

    result = merge_files(
        [bad_pdf],
        output,
        error_callback=lambda message, current: errors.append((message, current)),
    )

    assert result is None
    assert output.read_bytes() == b"existing output"
    assert errors
    assert errors[0][1] == bad_pdf


def test_late_input_failure_preserves_existing_output(tmp_path):
    good_pdf = tmp_path / "good.pdf"
    bad_pdf = tmp_path / "broken.pdf"
    output = tmp_path / "merged.pdf"
    create_pdf(good_pdf)
    bad_pdf.write_text("not a pdf")
    output.write_bytes(b"existing output")

    result = merge_files([good_pdf, bad_pdf], output)

    assert result is None
    assert output.read_bytes() == b"existing output"
    assert not list(tmp_path.glob(f".{output.name}.*.tmp.pdf"))
