from pathlib import Path

from pypdf import PdfReader, PdfWriter

from pdf_merger import OperationState, split_pdf


def create_pdf(path: Path, widths: list[int]) -> None:
    writer = PdfWriter()
    for width in widths:
        writer.add_blank_page(width=width, height=200)
    writer.write(path)
    writer.close()


def test_split_pdf_defaults_to_one_file_per_page(tmp_path):
    source = tmp_path / "source.pdf"
    output_dir = tmp_path / "parts"
    create_pdf(source, [100, 200, 300])

    result = split_pdf(source, output_dir)

    assert result.state is OperationState.SUCCESS
    assert result.pages_processed == 3
    assert [path.name for path in result.outputs] == [
        "source_part-001_page-1.pdf",
        "source_part-002_page-2.pdf",
        "source_part-003_page-3.pdf",
    ]
    assert [
        float(PdfReader(path).pages[0].mediabox.width)
        for path in result.outputs
    ] == [100.0, 200.0, 300.0]


def test_split_pdf_accepts_explicit_ranges(tmp_path):
    source = tmp_path / "report.pdf"
    output_dir = tmp_path / "parts"
    create_pdf(source, [100, 200, 300, 400])

    result = split_pdf(source, output_dir, ranges=[(1, 2), (3, 4)])

    assert result.succeeded is True
    assert result.pages_processed == 4
    assert [len(PdfReader(path).pages) for path in result.outputs] == [2, 2]
    assert [
        [float(page.mediabox.width) for page in PdfReader(path).pages]
        for path in result.outputs
    ] == [[100.0, 200.0], [300.0, 400.0]]


def test_split_pdf_reports_part_progress(tmp_path):
    source = tmp_path / "source.pdf"
    output_dir = tmp_path / "parts"
    create_pdf(source, [100, 200])
    progress = []

    result = split_pdf(
        source,
        output_dir,
        progress_callback=lambda current, total, output: progress.append(
            (current, total, output.name)
        ),
    )

    assert result.succeeded is True
    assert progress == [
        (1, 2, "source_part-001_page-1.pdf"),
        (2, 2, "source_part-002_page-2.pdf"),
    ]


def test_split_pdf_rejects_invalid_ranges_without_outputs(tmp_path):
    source = tmp_path / "source.pdf"
    output_dir = tmp_path / "parts"
    create_pdf(source, [100, 200])

    result = split_pdf(source, output_dir, ranges=[(1, 3)])

    assert result.failed is True
    assert "Invalid page range" in result.error
    assert not output_dir.exists()


def test_split_pdf_cancellation_removes_staged_outputs(tmp_path):
    source = tmp_path / "source.pdf"
    output_dir = tmp_path / "parts"
    create_pdf(source, [100, 200, 300])
    completed_parts = []

    def progress(current, total, output):
        completed_parts.append(output)

    result = split_pdf(
        source,
        output_dir,
        progress_callback=progress,
        cancel_callback=lambda: len(completed_parts) >= 1,
    )

    assert result.cancelled is True
    assert result.outputs == ()
    assert list(output_dir.iterdir()) == []


def test_split_pdf_preserves_existing_conflicting_output(tmp_path):
    source = tmp_path / "source.pdf"
    output_dir = tmp_path / "parts"
    output_dir.mkdir()
    create_pdf(source, [100])
    existing = output_dir / "source_part-001_page-1.pdf"
    existing.write_bytes(b"keep me")

    result = split_pdf(source, output_dir)

    assert result.failed is True
    assert "Output already exists" in result.error
    assert existing.read_bytes() == b"keep me"
    assert list(output_dir.iterdir()) == [existing]
