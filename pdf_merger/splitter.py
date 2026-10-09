from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from tempfile import NamedTemporaryFile

from pypdf import PdfReader, PdfWriter

from .operations import OperationResult, OperationState

PageRange = tuple[int, int]
ProgressCallback = Callable[[int, int, Path], None]
CancelCallback = Callable[[], bool]


def _normalize_ranges(page_count: int, ranges: Sequence[PageRange] | None) -> tuple[PageRange, ...]:
    if page_count < 1:
        raise ValueError("PDF contains no pages.")

    if ranges is None:
        return tuple((page, page) for page in range(1, page_count + 1))

    normalized = tuple(ranges)
    if not normalized:
        raise ValueError("At least one page range is required.")

    for start, end in normalized:
        if start < 1 or end < start or end > page_count:
            raise ValueError(
                f"Invalid page range {start}-{end}; PDF has {page_count} pages."
            )

    return normalized


def _output_name(source: Path, index: int, page_range: PageRange) -> str:
    start, end = page_range
    pages = f"page-{start}" if start == end else f"pages-{start}-{end}"
    return f"{source.stem}_part-{index:03d}_{pages}.pdf"


def split_pdf(
    input_file: Path,
    output_dir: Path,
    ranges: Sequence[PageRange] | None = None,
    progress_callback: ProgressCallback | None = None,
    cancel_callback: CancelCallback | None = None,
) -> OperationResult:
    """Split one PDF into page ranges using staged outputs.

    Page ranges are one-based and inclusive. When ranges is omitted, every
    page becomes its own PDF. Existing target files are never overwritten.
    All parts are staged before publication; cancellation or failure removes
    this operation's temporary files and any newly published parts.
    """
    source = Path(input_file)
    destination = Path(output_dir)
    temporary_files: list[Path] = []
    published_files: list[Path] = []
    pages_processed = 0

    try:
        if not source.exists() or not source.is_file():
            raise ValueError(f"Input file does not exist: {source}")

        reader = PdfReader(source)
        page_ranges = _normalize_ranges(len(reader.pages), ranges)
        destination.mkdir(parents=True, exist_ok=True)

        outputs = tuple(
            destination / _output_name(source, index, page_range)
            for index, page_range in enumerate(page_ranges, start=1)
        )

        conflicts = [path for path in outputs if path.exists()]
        if conflicts:
            raise FileExistsError(f"Output already exists: {conflicts[0]}")

        total_parts = len(page_ranges)

        for index, ((start, end), output) in enumerate(
            zip(page_ranges, outputs),
            start=1,
        ):
            if cancel_callback and cancel_callback():
                return OperationResult(
                    state=OperationState.CANCELLED,
                    pages_processed=pages_processed,
                    current_file=source,
                )

            writer = PdfWriter()
            try:
                for page_number in range(start - 1, end):
                    writer.add_page(reader.pages[page_number])
                    pages_processed += 1

                with NamedTemporaryFile(
                    dir=destination,
                    prefix=f".{output.name}.",
                    suffix=".tmp.pdf",
                    delete=False,
                ) as temporary:
                    temporary_path = Path(temporary.name)

                temporary_files.append(temporary_path)
                writer.write(temporary_path)
            finally:
                writer.close()

            if progress_callback:
                progress_callback(index, total_parts, output)

        if cancel_callback and cancel_callback():
            return OperationResult(
                state=OperationState.CANCELLED,
                pages_processed=pages_processed,
                current_file=source,
            )

        for temporary_path, output in zip(temporary_files, outputs):
            temporary_path.replace(output)
            published_files.append(output)

        return OperationResult(
            state=OperationState.SUCCESS,
            outputs=outputs,
            pages_processed=pages_processed,
        )

    except Exception as error:
        for published in published_files:
            if published.exists():
                published.unlink()

        return OperationResult(
            state=OperationState.FAILED,
            pages_processed=pages_processed,
            error=str(error),
            current_file=source,
        )

    finally:
        for temporary_path in temporary_files:
            if temporary_path.exists():
                temporary_path.unlink()
