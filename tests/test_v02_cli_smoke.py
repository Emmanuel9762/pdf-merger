"""End-to-end CLI smoke coverage for all six PDF operations."""

import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def make_pdf(path: Path, widths: list[int]) -> None:
    writer = PdfWriter()
    try:
        for width in widths:
            writer.add_blank_page(width=width, height=200)
        writer.write(path)
    finally:
        writer.close()


def widths_of(path: Path) -> list[int]:
    return [
        int(float(page.mediabox.width))
        for page in PdfReader(path).pages
    ]


def invoke(*args: object) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(PROJECT_ROOT / "main.py")]
    command.extend(str(arg) for arg in args)
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, (
        f"Command: {command}\n"
        f"Exit: {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
    return result


def test_six_cli_operations_end_to_end(tmp_path):
    source = tmp_path / "source.pdf"
    second = tmp_path / "second.pdf"
    make_pdf(source, [100, 200, 300, 400])
    make_pdf(second, [500])

    merged = tmp_path / "merged.pdf"
    invoke(source, second, "--output", merged)
    assert widths_of(merged) == [100, 200, 300, 400, 500]

    parts_dir = tmp_path / "parts"
    invoke(
        "split", source,
        "--range", "1-2",
        "--range", "3-4",
        "--output", parts_dir,
    )
    parts = sorted(parts_dir.glob("*.pdf"))
    assert len(parts) == 2
    assert [widths_of(part) for part in parts] == [
        [100, 200],
        [300, 400],
    ]

    extracted = tmp_path / "extracted.pdf"
    invoke(
        "extract", source,
        "--range", "4",
        "--range", "2",
        "--output", extracted,
    )
    assert widths_of(extracted) == [400, 200]

    rotated = tmp_path / "rotated.pdf"
    invoke(
        "rotate", source,
        "--degrees", "90",
        "--range", "2",
        "--output", rotated,
    )
    rotated_pages = PdfReader(rotated).pages
    assert [int(page.get("/Rotate", 0)) % 360 for page in rotated_pages] == [
        0, 90, 0, 0,
    ]

    trimmed = tmp_path / "trimmed.pdf"
    invoke("delete", source, "--range", "2-3", "--output", trimmed)
    assert widths_of(trimmed) == [100, 400]

    reordered = tmp_path / "reordered.pdf"
    invoke(
        "reorder", source,
        "--order", "4", "2", "1", "3",
        "--output", reordered,
    )
    assert widths_of(reordered) == [400, 200, 100, 300]


def test_cli_page_operations_do_not_overwrite_existing_files(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "reordered.pdf"
    make_pdf(source, [100, 200])
    output.write_bytes(b"existing content")

    result = subprocess.run(
        [
            sys.executable, str(PROJECT_ROOT / "main.py"),
            "reorder", str(source),
            "--order", "2", "1",
            "--output", str(output),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 1
    assert output.read_bytes() == b"existing content"
