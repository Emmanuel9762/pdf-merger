from pathlib import Path

from pypdf import PdfReader, PdfWriter

from main import parse_args, run


def create_pdf(path: Path, widths: list[int]) -> None:
    writer = PdfWriter()
    for width in widths:
        writer.add_blank_page(width=width, height=200)
    writer.write(path)
    writer.close()


def page_widths(path: Path) -> list[float]:
    return [
        float(page.mediabox.width)
        for page in PdfReader(path).pages
    ]


def test_reorder_cli_parses_order():
    args = parse_args([
        "reorder",
        "report.pdf",
        "--order",
        "4",
        "2",
        "1",
        "3",
        "--output",
        "reordered.pdf",
    ])

    assert args.operation == "reorder"
    assert args.file == "report.pdf"
    assert args.order == [4, 2, 1, 3]
    assert args.output == "reordered.pdf"


def test_reorder_cli_applies_requested_order(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "reordered.pdf"
    create_pdf(source, [100, 200, 300, 400])

    args = parse_args([
        "reorder",
        str(source),
        "--order",
        "4",
        "2",
        "1",
        "3",
        "--output",
        str(output),
    ])

    result = run(args)

    assert result == 0
    assert page_widths(output) == [400.0, 200.0, 100.0, 300.0]


def test_reorder_cli_uses_default_output_location(tmp_path, monkeypatch):
    source = tmp_path / "source.pdf"
    create_pdf(source, [100, 200])
    monkeypatch.chdir(tmp_path)

    args = parse_args([
        "reorder",
        str(source),
        "--order",
        "2",
        "1",
    ])

    result = run(args)
    output = tmp_path / "output" / "source-reordered.pdf"

    assert result == 0
    assert page_widths(output) == [200.0, 100.0]


def test_reorder_cli_rejects_invalid_permutation(tmp_path, capsys):
    source = tmp_path / "source.pdf"
    output = tmp_path / "reordered.pdf"
    create_pdf(source, [100, 200, 300])

    args = parse_args([
        "reorder",
        str(source),
        "--order",
        "1",
        "2",
        "2",
        "--output",
        str(output),
    ])

    result = run(args)

    assert result == 1
    assert not output.exists()
    captured = capsys.readouterr().out
    assert "Reorder failed." in captured
    assert "exactly once" in captured


def test_reorder_cli_preserves_existing_output(tmp_path, capsys):
    source = tmp_path / "source.pdf"
    output = tmp_path / "reordered.pdf"
    create_pdf(source, [100, 200])
    output.write_bytes(b"keep")

    args = parse_args([
        "reorder",
        str(source),
        "--order",
        "2",
        "1",
        "--output",
        str(output),
    ])

    result = run(args)

    assert result == 1
    assert output.read_bytes() == b"keep"
    captured = capsys.readouterr().out
    assert "Reorder failed." in captured
    assert "Output already exists" in captured
