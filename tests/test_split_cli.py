from argparse import Namespace
from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from main import parse_args, parse_page_range, run


def create_pdf(path: Path, widths: list[int]) -> None:
    writer = PdfWriter()
    for width in widths:
        writer.add_blank_page(width=width, height=200)
    writer.write(path)
    writer.close()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1", (1, 1)),
        ("2-5", (2, 5)),
        ("10-10", (10, 10)),
    ],
)
def test_parse_page_range(raw, expected):
    assert parse_page_range(raw) == expected


@pytest.mark.parametrize("raw", ["0", "3-2", "1-2-3", "abc", "1-x"])
def test_parse_page_range_rejects_invalid_values(raw):
    with pytest.raises(Exception):
        parse_page_range(raw)


def test_parse_args_preserves_legacy_merge_mode():
    args = parse_args(["first.pdf", "second.pdf", "--output", "merged.pdf"])

    assert args.operation == "merge"
    assert args.files == ["first.pdf", "second.pdf"]
    assert args.output == "merged.pdf"


def test_parse_args_accepts_split_operation():
    args = parse_args(
        [
            "split",
            "report.pdf",
            "--range",
            "1-3",
            "--range",
            "5",
            "--output",
            "parts",
        ]
    )

    assert args.operation == "split"
    assert args.file == "report.pdf"
    assert args.ranges == [(1, 3), (5, 5)]
    assert args.output == "parts"


def test_run_split_creates_requested_ranges(tmp_path):
    source = tmp_path / "report.pdf"
    output_dir = tmp_path / "parts"
    create_pdf(source, [100, 200, 300, 400])

    args = Namespace(
        operation="split",
        file=str(source),
        ranges=[(1, 2), (3, 4)],
        output=str(output_dir),
    )

    assert run(args) == 0

    outputs = sorted(output_dir.glob("*.pdf"))
    assert [len(PdfReader(path).pages) for path in outputs] == [2, 2]
    assert [path.name for path in outputs] == [
        "report_part-001_pages-1-2.pdf",
        "report_part-002_pages-3-4.pdf",
    ]


def test_run_split_defaults_to_page_per_file(tmp_path):
    source = tmp_path / "report.pdf"
    output_dir = tmp_path / "parts"
    create_pdf(source, [100, 200])

    args = Namespace(
        operation="split",
        file=str(source),
        ranges=None,
        output=str(output_dir),
    )

    assert run(args) == 0
    assert len(list(output_dir.glob("*.pdf"))) == 2


def test_run_split_reports_failure(tmp_path, capsys):
    args = Namespace(
        operation="split",
        file=str(tmp_path / "missing.pdf"),
        ranges=None,
        output=str(tmp_path / "parts"),
    )

    assert run(args) == 1
    output = capsys.readouterr().out
    assert "Split failed." in output
    assert "Input file does not exist" in output
