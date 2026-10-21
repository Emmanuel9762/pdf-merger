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


def _pages_to_delete(
    page_count: int,
    ranges: Sequence[PageRange] | None,
) -> set[int]:
    if page_count < 1:
        raise ValueError("PDF contains no pages.")

    if ranges is None:
        raise ValueError("At least one page range is required.")

    normalized = tuple(ranges)
    if not normalized:
        raise ValueError("At least one page range is required.")

    selected: set[int] = set()

    for start, end in normalized:
        if start < 1 or end < start or end > page_count:
            raise ValueError(
                f"Invalid page range {start}-{end}; PDF has {page_count} pages."
            )

        selected.update(range(start - 1, end))

    if len(selected) == page_count:
        raise ValueError("Cannot delete every page from a PDF.")

    return selected


def delete_pages(
    input_file: Path,
    output_file: Path,
    ranges: Sequence[PageRange],
    progress_callback: ProgressCallback | None = None,
    cancel_callback: CancelCallback | None = None,
) -> OperationResult:
    """Create a new PDF with selected pages removed.

    Page ranges are one-based and inclusive. Overlapping ranges are
    deduplicated. The output is staged and published without overwriting an
    existing target.
    """
    source = Path(input_file)
    output = Path(output_file)
    temporary_path: Path | None = None
    pages_processed = 0

    try:
        if not source.exists() or not source.is_file():
            raise ValueError(f"Input file does not exist: {source}")

        reader = PdfReader(source)
        selected = _pages_to_delete(len(reader.pages), ranges)

        output.parent.mkdir(parents=True, exist_ok=True)

        if output.exists():
            raise FileExistsError(f"Output already exists: {output}")

        writer = PdfWriter()
        total_pages = len(reader.pages)

        try:
            for index, source_page in enumerate(reader.pages):
                if cancel_callback and cancel_callback():
                    return OperationResult(
                        state=OperationState.CANCELLED,
                        pages_processed=pages_processed,
                        current_file=source,
                    )

                if index not in selected:
                    writer.add_page(source_page)

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
