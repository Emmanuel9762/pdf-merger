from pathlib import Path

from pypdf import PdfReader, PdfWriter

from main import parse_args, run


def create_pdf(path: Path, widths: list[int]) -> None:
    writer = PdfWriter()
    for width in widths:
        writer.add_blank_page(width=width, height=200)
    writer.write(path)
    writer.close()


def test_extract_cli_parses_repeatable_ranges():
    args = parse_args([
        "extract",
        "report.pdf",
        "--range",
        "4-5",
        "--range",
        "2",
        "--output",
        "selected.pdf",
    ])

    assert args.operation == "extract"
    assert args.file == "report.pdf"
    assert args.ranges == [(4, 5), (2, 2)]
    assert args.output == "selected.pdf"


def test_extract_cli_creates_selected_output(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "selected.pdf"
    create_pdf(source, [100, 200, 300, 400])

    args = parse_args([
        "extract",
        str(source),
        "--range",
        "4",
        "--range",
        "2-3",
        "--output",
        str(output),
    ])

    result = run(args)

    assert result == 0
    assert output.exists()
    widths = [
        float(page.mediabox.width)
        for page in PdfReader(output).pages
    ]
    assert widths == [400.0, 200.0, 300.0]


def test_extract_cli_uses_default_output_location(tmp_path, monkeypatch):
    source = tmp_path / "source.pdf"
    create_pdf(source, [100, 200])
    monkeypatch.chdir(tmp_path)

    args = parse_args([
        "extract",
        str(source),
        "--range",
        "2",
    ])

    result = run(args)
    output = tmp_path / "output" / "source-extracted.pdf"

    assert result == 0
    assert output.exists()
    assert len(PdfReader(output).pages) == 1


def test_extract_cli_preserves_existing_output(tmp_path, capsys):
    source = tmp_path / "source.pdf"
    output = tmp_path / "selected.pdf"
    create_pdf(source, [100])
    output.write_bytes(b"keep")

    args = parse_args([
        "extract",
        str(source),
        "--range",
        "1",
        "--output",
        str(output),
    ])

    result = run(args)

    assert result == 1
    assert output.read_bytes() == b"keep"
    captured = capsys.readouterr().out
    assert "Extract failed." in captured
    assert "Output already exists" in captured
