from pathlib import Path

from pypdf import PdfReader, PdfWriter

from main import parse_args, run


def create_pdf(path: Path, page_count: int) -> None:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=100, height=200)
    writer.write(path)
    writer.close()


def rotations(path: Path) -> list[int]:
    return [int(page.get("/Rotate", 0)) % 360 for page in PdfReader(path).pages]


def test_rotate_cli_parses_degrees_and_repeatable_ranges():
    args = parse_args([
        "rotate",
        "report.pdf",
        "--degrees",
        "90",
        "--range",
        "1-2",
        "--range",
        "4",
        "--output",
        "rotated.pdf",
    ])

    assert args.operation == "rotate"
    assert args.file == "report.pdf"
    assert args.degrees == 90
    assert args.ranges == [(1, 2), (4, 4)]
    assert args.output == "rotated.pdf"


def test_rotate_cli_rotates_selected_pages(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "rotated.pdf"
    create_pdf(source, 4)

    args = parse_args([
        "rotate",
        str(source),
        "--degrees",
        "180",
        "--range",
        "2-3",
        "--output",
        str(output),
    ])

    result = run(args)

    assert result == 0
    assert rotations(output) == [0, 180, 180, 0]


def test_rotate_cli_rotates_all_pages_when_ranges_omitted(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "rotated.pdf"
    create_pdf(source, 2)

    args = parse_args([
        "rotate",
        str(source),
        "--degrees",
        "270",
        "--output",
        str(output),
    ])

    result = run(args)

    assert result == 0
    assert rotations(output) == [270, 270]


def test_rotate_cli_uses_default_output_location(tmp_path, monkeypatch):
    source = tmp_path / "source.pdf"
    create_pdf(source, 1)
    monkeypatch.chdir(tmp_path)

    args = parse_args([
        "rotate",
        str(source),
        "--degrees",
        "90",
    ])

    result = run(args)
    output = tmp_path / "output" / "source-rotated.pdf"

    assert result == 0
    assert rotations(output) == [90]


def test_rotate_cli_preserves_existing_output(tmp_path, capsys):
    source = tmp_path / "source.pdf"
    output = tmp_path / "rotated.pdf"
    create_pdf(source, 1)
    output.write_bytes(b"keep")

    args = parse_args([
        "rotate",
        str(source),
        "--degrees",
        "90",
        "--output",
        str(output),
    ])

    result = run(args)

    assert result == 1
    assert output.read_bytes() == b"keep"
    captured = capsys.readouterr().out
    assert "Rotate failed." in captured
    assert "Output already exists" in captured
