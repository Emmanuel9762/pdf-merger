from pathlib import Path

from pypdf import PdfReader, PdfWriter

from pdf_merger import OperationState, delete_pages


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


def test_delete_pages_removes_selected_ranges(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "trimmed.pdf"
    create_pdf(source, [100, 200, 300, 400, 500])

    result = delete_pages(
        source,
        output,
        ranges=[(2, 3), (5, 5)],
    )

    assert result.state is OperationState.SUCCESS
    assert result.outputs == (output,)
    assert result.pages_processed == 5
    assert page_widths(output) == [100.0, 400.0]


def test_delete_pages_deduplicates_overlapping_ranges(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "trimmed.pdf"
    create_pdf(source, [100, 200, 300, 400])

    result = delete_pages(
        source,
        output,
        ranges=[(2, 3), (3, 3)],
    )

    assert result.succeeded is True
    assert page_widths(output) == [100.0, 400.0]


def test_delete_pages_rejects_missing_ranges(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "trimmed.pdf"
    create_pdf(source, [100, 200])

    result = delete_pages(source, output, ranges=[])

    assert result.failed is True
    assert "At least one page range is required" in result.error
    assert not output.exists()


def test_delete_pages_rejects_deleting_every_page(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "trimmed.pdf"
    create_pdf(source, [100, 200])

    result = delete_pages(source, output, ranges=[(1, 2)])

    assert result.failed is True
    assert "Cannot delete every page" in result.error
    assert not output.exists()


def test_delete_pages_rejects_out_of_bounds_range(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "trimmed.pdf"
    create_pdf(source, [100, 200])

    result = delete_pages(source, output, ranges=[(3, 3)])

    assert result.failed is True
    assert "Invalid page range" in result.error
    assert not output.exists()


def test_delete_pages_reports_progress_for_every_source_page(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "trimmed.pdf"
    create_pdf(source, [100, 200, 300])
    progress = []

    result = delete_pages(
        source,
        output,
        ranges=[(2, 2)],
        progress_callback=lambda current, total, path: progress.append(
            (current, total, path)
        ),
    )

    assert result.succeeded is True
    assert progress == [
        (1, 3, source),
        (2, 3, source),
        (3, 3, source),
    ]


def test_delete_pages_cancellation_leaves_no_output(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "trimmed.pdf"
    create_pdf(source, [100, 200, 300])
    progress = []

    result = delete_pages(
        source,
        output,
        ranges=[(2, 2)],
        progress_callback=lambda current, total, path: progress.append(current),
        cancel_callback=lambda: len(progress) >= 1,
    )

    assert result.cancelled is True
    assert result.pages_processed == 1
    assert not output.exists()
    assert list(tmp_path.glob(f".{output.name}.*.tmp.pdf")) == []


def test_delete_pages_preserves_existing_output(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "trimmed.pdf"
    create_pdf(source, [100, 200])
    output.write_bytes(b"keep")

    result = delete_pages(source, output, ranges=[(2, 2)])

    assert result.failed is True
    assert "Output already exists" in result.error
    assert output.read_bytes() == b"keep"


def test_delete_pages_does_not_overwrite_late_conflict(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "trimmed.pdf"
    create_pdf(source, [100, 200])

    def create_conflict(current, total, path):
        if current == total:
            output.write_bytes(b"external")

    result = delete_pages(
        source,
        output,
        ranges=[(2, 2)],
        progress_callback=create_conflict,
    )

    assert result.failed is True
    assert output.read_bytes() == b"external"
    assert list(tmp_path.glob(f".{output.name}.*.tmp.pdf")) == []
