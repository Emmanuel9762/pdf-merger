from pathlib import Path

from pypdf import PdfReader, PdfWriter

from pdf_merger import OperationState, extract_pages


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


def test_extract_pages_combines_ranges_in_supplied_order(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "selected.pdf"
    create_pdf(source, [100, 200, 300, 400, 500])

    result = extract_pages(
        source,
        output,
        ranges=[(4, 5), (2, 2)],
    )

    assert result.state is OperationState.SUCCESS
    assert result.outputs == (output,)
    assert result.pages_processed == 3
    assert page_widths(output) == [400.0, 500.0, 200.0]


def test_extract_pages_allows_overlapping_ranges(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "selected.pdf"
    create_pdf(source, [100, 200, 300])

    result = extract_pages(
        source,
        output,
        ranges=[(1, 2), (2, 3)],
    )

    assert result.succeeded is True
    assert page_widths(output) == [100.0, 200.0, 200.0, 300.0]


def test_extract_pages_reports_page_progress(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "selected.pdf"
    create_pdf(source, [100, 200, 300])
    progress = []

    result = extract_pages(
        source,
        output,
        ranges=[(1, 1), (3, 3)],
        progress_callback=lambda current, total, path: progress.append(
            (current, total, path)
        ),
    )

    assert result.succeeded is True
    assert progress == [
        (1, 2, source),
        (2, 2, source),
    ]


def test_extract_pages_rejects_missing_ranges_without_output(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "selected.pdf"
    create_pdf(source, [100, 200])

    result = extract_pages(source, output, ranges=[])

    assert result.failed is True
    assert "At least one page range is required" in result.error
    assert not output.exists()


def test_extract_pages_rejects_out_of_bounds_range(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "selected.pdf"
    create_pdf(source, [100, 200])

    result = extract_pages(source, output, ranges=[(2, 3)])

    assert result.failed is True
    assert "Invalid page range" in result.error
    assert not output.exists()


def test_extract_pages_preserves_existing_output(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "selected.pdf"
    create_pdf(source, [100])
    output.write_bytes(b"keep me")

    result = extract_pages(source, output, ranges=[(1, 1)])

    assert result.failed is True
    assert "Output already exists" in result.error
    assert output.read_bytes() == b"keep me"


def test_extract_pages_cancellation_leaves_no_output(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "selected.pdf"
    create_pdf(source, [100, 200, 300])
    progress = []

    result = extract_pages(
        source,
        output,
        ranges=[(1, 3)],
        progress_callback=lambda current, total, path: progress.append(current),
        cancel_callback=lambda: len(progress) >= 1,
    )

    assert result.cancelled is True
    assert result.pages_processed == 1
    assert not output.exists()
    assert list(tmp_path.glob(f".{output.name}.*.tmp.pdf")) == []


def test_extract_pages_does_not_overwrite_late_conflict(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "selected.pdf"
    create_pdf(source, [100])

    def create_conflict(current, total, path):
        output.write_bytes(b"external")

    result = extract_pages(
        source,
        output,
        ranges=[(1, 1)],
        progress_callback=create_conflict,
    )

    assert result.failed is True
    assert output.read_bytes() == b"external"
    assert list(tmp_path.glob(f".{output.name}.*.tmp.pdf")) == []
