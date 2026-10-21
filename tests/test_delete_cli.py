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


def test_delete_cli_parses_repeatable_ranges():
    args = parse_args([
        "delete",
        "report.pdf",
        "--range",
        "2-3",
        "--range",
        "5",
        "--output",
        "trimmed.pdf",
    ])

    assert args.operation == "delete"
    assert args.file == "report.pdf"
    assert args.ranges == [(2, 3), (5, 5)]
    assert args.output == "trimmed.pdf"


def test_delete_cli_removes_selected_pages(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "trimmed.pdf"
    create_pdf(source, [100, 200, 300, 400])

    args = parse_args([
        "delete",
        str(source),
        "--range",
        "2-3",
        "--output",
        str(output),
    ])

    result = run(args)

    assert result == 0
    assert page_widths(output) == [100.0, 400.0]


def test_delete_cli_uses_default_output_location(tmp_path, monkeypatch):
    source = tmp_path / "source.pdf"
    create_pdf(source, [100, 200])
    monkeypatch.chdir(tmp_path)

    args = parse_args([
        "delete",
        str(source),
        "--range",
        "2",
    ])

    result = run(args)
    output = tmp_path / "output" / "source-trimmed.pdf"

    assert result == 0
    assert page_widths(output) == [100.0]


def test_delete_cli_rejects_deleting_every_page(tmp_path, capsys):
    source = tmp_path / "source.pdf"
    output = tmp_path / "trimmed.pdf"
    create_pdf(source, [100, 200])

    args = parse_args([
        "delete",
        str(source),
        "--range",
        "1-2",
        "--output",
        str(output),
    ])

    result = run(args)

    assert result == 1
    assert not output.exists()
    captured = capsys.readouterr().out
    assert "Delete failed." in captured
    assert "Cannot delete every page" in captured


def test_delete_cli_preserves_existing_output(tmp_path, capsys):
    source = tmp_path / "source.pdf"
    output = tmp_path / "trimmed.pdf"
    create_pdf(source, [100, 200])
    output.write_bytes(b"keep")

    args = parse_args([
        "delete",
        str(source),
        "--range",
        "2",
        "--output",
        str(output),
    ])

    result = run(args)

    assert result == 1
    assert output.read_bytes() == b"keep"
    captured = capsys.readouterr().out
    assert "Delete failed." in captured
    assert "Output already exists" in captured
