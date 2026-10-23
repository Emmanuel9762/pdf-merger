from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from pathlib import Path
from tempfile import NamedTemporaryFile

from pypdf import PdfReader, PdfWriter

from .operations import OperationResult, OperationState

ProgressCallback = Callable[[int, int, Path], None]
CancelCallback = Callable[[], bool]


def _validate_order(page_count: int, order: Sequence[int]) -> tuple[int, ...]:
    if page_count < 1:
        raise ValueError("PDF contains no pages.")

    normalized = tuple(order)

    if len(normalized) != page_count:
        raise ValueError(
            f"Page order must contain exactly {page_count} entries."
        )

    expected = set(range(1, page_count + 1))
    actual = set(normalized)

    if actual != expected:
        raise ValueError(
            f"Page order must contain each page from 1 to {page_count} exactly once."
        )

    return normalized


def reorder_pages(
    input_file: Path,
    output_file: Path,
    order: Sequence[int],
    progress_callback: ProgressCallback | None = None,
    cancel_callback: CancelCallback | None = None,
) -> OperationResult:
    """Create a new PDF with pages arranged in the requested order."""
    source = Path(input_file)
    output = Path(output_file)
    temporary_path: Path | None = None
    pages_processed = 0

    try:
        if not source.exists() or not source.is_file():
            raise ValueError(f"Input file does not exist: {source}")

        reader = PdfReader(source)
        normalized_order = _validate_order(len(reader.pages), order)

        output.parent.mkdir(parents=True, exist_ok=True)

        if output.exists():
            raise FileExistsError(f"Output already exists: {output}")

        writer = PdfWriter()
        total_pages = len(normalized_order)

        try:
            for page_number in normalized_order:
                if cancel_callback and cancel_callback():
                    return OperationResult(
                        state=OperationState.CANCELLED,
                        pages_processed=pages_processed,
                        current_file=source,
                    )

                writer.add_page(reader.pages[page_number - 1])
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
