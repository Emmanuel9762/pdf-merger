from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from pathlib import Path
from tempfile import NamedTemporaryFile

from pypdf import PdfReader, PdfWriter

from .operations import OperationResult, OperationState
from .page_ranges import PageRange

ProgressCallback = Callable[[int, int, Path], None]
CancelCallback = Callable[[], bool]


def _validate_ranges(
    page_count: int,
    ranges: Sequence[PageRange] | None,
) -> tuple[PageRange, ...]:
    if page_count < 1:
        raise ValueError("PDF contains no pages.")

    if ranges is None:
        raise ValueError("At least one page range is required.")

    normalized = tuple(ranges)
    if not normalized:
        raise ValueError("At least one page range is required.")

    for start, end in normalized:
        if start < 1 or end < start or end > page_count:
            raise ValueError(
                f"Invalid page range {start}-{end}; PDF has {page_count} pages."
            )

    return normalized


def extract_pages(
    input_file: Path,
    output_file: Path,
    ranges: Sequence[PageRange],
    progress_callback: ProgressCallback | None = None,
    cancel_callback: CancelCallback | None = None,
) -> OperationResult:
    """Extract selected page ranges into one PDF.

    Page ranges are one-based and inclusive. Ranges are processed in the
    supplied order, and overlapping ranges intentionally duplicate pages.
    The output is staged and then published without overwriting an existing
    target.
    """
    source = Path(input_file)
    output = Path(output_file)
    temporary_path: Path | None = None
    pages_processed = 0

    try:
        if not source.exists() or not source.is_file():
            raise ValueError(f"Input file does not exist: {source}")

        reader = PdfReader(source)
        page_ranges = _validate_ranges(len(reader.pages), ranges)

        output.parent.mkdir(parents=True, exist_ok=True)

        if output.exists():
            raise FileExistsError(f"Output already exists: {output}")

        selected_pages = [
            page_number
            for start, end in page_ranges
            for page_number in range(start - 1, end)
        ]
        total_pages = len(selected_pages)

        writer = PdfWriter()

        try:
            for page_number in selected_pages:
                if cancel_callback and cancel_callback():
                    return OperationResult(
                        state=OperationState.CANCELLED,
                        pages_processed=pages_processed,
                        current_file=source,
                    )

                writer.add_page(reader.pages[page_number])
                pages_processed += 1

                if progress_callback:
                    progress_callback(
                        pages_processed,
                        total_pages,
                        source,
                    )

            if cancel_callback and cancel_callback():
                return OperationResult(
                    state=OperationState.CANCELLED,
                    pages_processed=pages_processed,
                    current_file=source,
                )

            with NamedTemporaryFile(
                dir=output.parent,
                prefix=f".{output.name}.",
                suffix=".tmp.pdf",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)

            writer.write(temporary_path)
        finally:
            writer.close()

        if cancel_callback and cancel_callback():
            return OperationResult(
                state=OperationState.CANCELLED,
                pages_processed=pages_processed,
                current_file=source,
            )

        os.link(temporary_path, output)
        temporary_path.unlink()
        temporary_path = None

        return OperationResult(
            state=OperationState.SUCCESS,
            outputs=(output,),
            pages_processed=pages_processed,
        )

    except Exception as error:
        return OperationResult(
            state=OperationState.FAILED,
            pages_processed=pages_processed,
            error=str(error),
            current_file=source,
        )

    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
