from pathlib import Path

from pypdf import PdfReader, PdfWriter

from pdf_merger import OperationState, rotate_pages


def create_pdf(path: Path, widths: list[int]) -> None:
    writer = PdfWriter()
    for width in widths:
        writer.add_blank_page(width=width, height=200)
    writer.write(path)
    writer.close()


def rotations(path: Path) -> list[int]:
    return [int(page.get("/Rotate", 0)) % 360 for page in PdfReader(path).pages]


def test_rotate_pages_defaults_to_all_pages(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "rotated.pdf"
    create_pdf(source, [100, 200, 300])

    result = rotate_pages(source, output, degrees=90)

    assert result.state is OperationState.SUCCESS
    assert result.outputs == (output,)
    assert result.pages_processed == 3
    assert rotations(output) == [90, 90, 90]


def test_rotate_pages_only_rotates_selected_ranges(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "rotated.pdf"
    create_pdf(source, [100, 200, 300, 400])

    result = rotate_pages(
        source,
        output,
        degrees=180,
        ranges=[(2, 3)],
    )

    assert result.succeeded is True
    assert rotations(output) == [0, 180, 180, 0]


def test_rotate_pages_overlapping_ranges_rotate_once(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "rotated.pdf"
    create_pdf(source, [100, 200, 300])

    result = rotate_pages(
        source,
        output,
        degrees=90,
        ranges=[(1, 2), (2, 3)],
    )

    assert result.succeeded is True
    assert rotations(output) == [90, 90, 90]


def test_rotate_pages_rejects_invalid_degrees(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "rotated.pdf"
    create_pdf(source, [100])

    result = rotate_pages(source, output, degrees=45)

    assert result.failed is True
    assert "90, 180, or 270" in result.error
    assert not output.exists()


def test_rotate_pages_rejects_out_of_bounds_range(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "rotated.pdf"
    create_pdf(source, [100, 200])

    result = rotate_pages(
        source,
        output,
        degrees=90,
        ranges=[(2, 3)],
    )

    assert result.failed is True
    assert "Invalid page range" in result.error
    assert not output.exists()


def test_rotate_pages_reports_progress_for_every_page(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "rotated.pdf"
    create_pdf(source, [100, 200])
    progress = []

    result = rotate_pages(
        source,
        output,
        degrees=270,
        ranges=[(2, 2)],
        progress_callback=lambda current, total, path: progress.append(
            (current, total, path)
        ),
    )

    assert result.succeeded is True
    assert progress == [
        (1, 2, source),
        (2, 2, source),
    ]


def test_rotate_pages_cancellation_leaves_no_output(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "rotated.pdf"
    create_pdf(source, [100, 200, 300])
    progress = []

    result = rotate_pages(
        source,
        output,
        degrees=90,
        progress_callback=lambda current, total, path: progress.append(current),
        cancel_callback=lambda: len(progress) >= 1,
    )

    assert result.cancelled is True
    assert result.pages_processed == 1
    assert not output.exists()
    assert list(tmp_path.glob(f".{output.name}.*.tmp.pdf")) == []


def test_rotate_pages_preserves_existing_output(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "rotated.pdf"
    create_pdf(source, [100])
    output.write_bytes(b"keep")

    result = rotate_pages(source, output, degrees=90)

    assert result.failed is True
    assert "Output already exists" in result.error
    assert output.read_bytes() == b"keep"


def test_rotate_pages_does_not_overwrite_late_conflict(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "rotated.pdf"
    create_pdf(source, [100])

    def create_conflict(current, total, path):
        output.write_bytes(b"external")

    result = rotate_pages(
        source,
        output,
        degrees=90,
        progress_callback=create_conflict,
    )

    assert result.failed is True
    assert output.read_bytes() == b"external"
    assert list(tmp_path.glob(f".{output.name}.*.tmp.pdf")) == []
