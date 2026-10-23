from pathlib import Path

from pypdf import PdfReader, PdfWriter

from pdf_merger import OperationState, reorder_pages


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


def test_reorder_pages_applies_requested_permutation(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "reordered.pdf"
    create_pdf(source, [100, 200, 300, 400])

    result = reorder_pages(
        source,
        output,
        order=[4, 2, 1, 3],
    )

    assert result.state is OperationState.SUCCESS
    assert result.outputs == (output,)
    assert result.pages_processed == 4
    assert page_widths(output) == [400.0, 200.0, 100.0, 300.0]


def test_reorder_pages_rejects_missing_page(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "reordered.pdf"
    create_pdf(source, [100, 200, 300])

    result = reorder_pages(
        source,
        output,
        order=[1, 2],
    )

    assert result.failed is True
    assert "exactly 3 entries" in result.error
    assert not output.exists()


def test_reorder_pages_rejects_duplicate_page(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "reordered.pdf"
    create_pdf(source, [100, 200, 300])

    result = reorder_pages(
        source,
        output,
        order=[1, 2, 2],
    )

    assert result.failed is True
    assert "each page from 1 to 3 exactly once" in result.error
    assert not output.exists()


def test_reorder_pages_rejects_out_of_bounds_page(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "reordered.pdf"
    create_pdf(source, [100, 200, 300])

    result = reorder_pages(
        source,
        output,
        order=[1, 2, 4],
    )

    assert result.failed is True
    assert "each page from 1 to 3 exactly once" in result.error
    assert not output.exists()


def test_reorder_pages_reports_progress(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "reordered.pdf"
    create_pdf(source, [100, 200, 300])
    progress = []

    result = reorder_pages(
        source,
        output,
        order=[3, 1, 2],
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


def test_reorder_pages_cancellation_leaves_no_output(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "reordered.pdf"
    create_pdf(source, [100, 200, 300])
    progress = []

    result = reorder_pages(
        source,
        output,
        order=[3, 2, 1],
        progress_callback=lambda current, total, path: progress.append(current),
        cancel_callback=lambda: len(progress) >= 1,
    )

    assert result.cancelled is True
    assert result.pages_processed == 1
    assert not output.exists()
    assert list(tmp_path.glob(f".{output.name}.*.tmp.pdf")) == []


def test_reorder_pages_preserves_existing_output(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "reordered.pdf"
    create_pdf(source, [100, 200])
    output.write_bytes(b"keep")

    result = reorder_pages(
        source,
        output,
        order=[2, 1],
    )

    assert result.failed is True
    assert "Output already exists" in result.error
    assert output.read_bytes() == b"keep"


def test_reorder_pages_does_not_overwrite_late_conflict(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "reordered.pdf"
    create_pdf(source, [100, 200])

    def create_conflict(current, total, path):
        if current == total:
            output.write_bytes(b"external")

    result = reorder_pages(
        source,
        output,
        order=[2, 1],
        progress_callback=create_conflict,
    )

    assert result.failed is True
    assert output.read_bytes() == b"external"
    assert list(tmp_path.glob(f".{output.name}.*.tmp.pdf")) == []
