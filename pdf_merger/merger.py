import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from collections.abc import Callable, Sequence

from pypdf import PdfWriter


def find_pdfs(input_folder):
    return [
        file for file in input_folder.iterdir()
        if file.is_file() and file.suffix.lower() == ".pdf"
    ]


def is_valid_pdf(file_path):
    file = Path(file_path)

    if not file.exists():
        return False

    if not file.is_file():
        return False

    return file.suffix.lower() == ".pdf"


def get_cli_files(file_paths):
    pdf_files = []

    for file_path in file_paths:
        pdf_file = Path(file_path)

        if not is_valid_pdf(pdf_file):
            print(f"Invalid PDF file: {pdf_file}")
            return None

        pdf_files.append(pdf_file)

    return pdf_files


def validate_merge_request(pdf_files, output_file, error_callback=None):
    if not pdf_files:
        if error_callback:
            error_callback("No PDF files selected.", None)
        return False

    seen_paths = set()
    output_path = Path(output_file)

    for pdf_file in pdf_files:
        pdf_path = Path(pdf_file)

        if not pdf_path.exists():
            if error_callback:
                error_callback(
                    f"Input file does not exist: {pdf_path}",
                    pdf_path,
                )
            return False

        if not pdf_path.is_file():
            if error_callback:
                error_callback(
                    f"Input path is not a file: {pdf_path}",
                    pdf_path,
                )
            return False

        if not os.access(pdf_path, os.R_OK):
            if error_callback:
                error_callback(
                    f"Input file is not readable: {pdf_path}",
                    pdf_path,
                )
            return False

        normalized = pdf_path.resolve()

        if normalized in seen_paths:
            if error_callback:
                error_callback(
                    f"Duplicate input file: {pdf_path}",
                    pdf_path,
                )
            return False

        seen_paths.add(normalized)

    for pdf_file in pdf_files:
        pdf_path = Path(pdf_file)

        if output_path.resolve() == pdf_path.resolve():
            if error_callback:
                error_callback(
                    f"Output file cannot be the same as an input file: {output_path}",
                    pdf_path,
                )
            return False

    output_parent = output_path.parent

    if output_parent.exists() and not output_parent.is_dir():
        if error_callback:
            error_callback(
                f"Output parent is not a directory: {output_parent}",
                pdf_files[0],
            )
        return False

    try:
        output_parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        if error_callback:
            error_callback(
                f"Output parent cannot be created or accessed: {output_parent}",
                pdf_files[0],
            )
        return False

    if output_path.exists() and output_path.is_dir():
        if error_callback:
            error_callback(
                f"Output path is a directory: {output_path}",
                pdf_files[0],
            )
        return False

    return True


def merge_pdfs(
    pdf_files,
    output_file,
    progress_callback=None,
    error_callback=None,
    cancel_callback=None,
):
    writer = PdfWriter()
    temp_file = None
    current_file = None
    total_files = len(pdf_files)

    try:
        for index, pdf_file in enumerate(pdf_files, start=1):
            if cancel_callback and cancel_callback():
                return None

            current_file = pdf_file
            print(f"Processing: {pdf_file.name}")

            writer.append(pdf_file)

            if progress_callback:
                progress_callback(
                    index,
                    total_files,
                    pdf_file
                )

        if cancel_callback and cancel_callback():
            return None

        total_pages = len(writer.pages)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        # Own a unique sibling so replacement stays atomic and cleanup cannot
        # delete another request's temporary file (or an input with that name).
        with NamedTemporaryFile(
            dir=output_file.parent, prefix=f".{output_file.name}.",
            suffix=".tmp.pdf", delete=False,
        ) as temporary:
            temp_file = Path(temporary.name)
        writer.write(temp_file)
        if cancel_callback and cancel_callback():
            return None
        temp_file.replace(output_file)

    except Exception as error:
        if current_file:
            print(f"\nFailed to process: {current_file.name}")
        else:
            print("\nMerge failed.")

        print(f"Reason: {error}")

        if temp_file is not None and temp_file.exists():
            temp_file.unlink()

        if error_callback:
            error_callback(
                str(error),
                current_file
            )

        return None

    finally:
        try:
            if temp_file is not None and temp_file.exists():
                temp_file.unlink()
        finally:
            writer.close()

    return total_pages


def get_merge_order(pdf_files, input_func=input):
    while True:
        order = input_func(
            "\nEnter the order you want (e.g. 1 2 3): "
        )

        try:
            order = [int(number) for number in order.split()]
        except ValueError:
            print("Invalid input. Please enter numbers only.")
            continue

        if len(order) != len(pdf_files):
            print(f"Please enter all {len(pdf_files)} PDF numbers.")
            continue

        if any(index < 1 or index > len(pdf_files) for index in order):
            print(f"Enter numbers between 1 and {len(pdf_files)}.")
            continue

        if len(set(order)) != len(order):
            print("Duplicate file numbers are not allowed.")
            continue

        return [pdf_files[index - 1] for index in order]


def apply_merge_order(pdf_files, order):
    if len(order) != len(pdf_files):
        return None

    if any(index < 1 or index > len(pdf_files) for index in order):
        return None

    if len(set(order)) != len(order):
        return None

    return [pdf_files[index - 1] for index in order]


def merge_files(
    pdf_files: Sequence[Path],
    output_file: Path,
    progress_callback: Callable[[int, int, Path], None] | None = None,
    error_callback: Callable[[str, Path | None], None] | None = None,
    cancel_callback: Callable[[], bool] | None = None,
) -> int | None:
    """Merge inputs in order, returning page count only after atomic publication.

    Progress runs synchronously after each append with (1-based index, input
    count, input path); even the final progress event is not completion.
    Validation/I/O failure returns None and reports (message, current input)
    once when an error callback is supplied. Validation precedes cancellation.
    Cancellation returns None without an error; it is polled before each input,
    before writing, and immediately before publication. Publication is the
    commit point: requests arriving afterwards cannot undo a successful merge.
    Existing output is preserved on failure/cancellation and only this call's
    temporary file is removed. Callbacks should not raise; exceptions from the
    error callback or an unsuccessful filesystem cleanup propagate to callers.
    """
    if not validate_merge_request(
        pdf_files,
        output_file,
        error_callback=error_callback,
    ):
        return None

    return merge_pdfs(
        pdf_files,
        output_file,
        progress_callback=progress_callback,
        error_callback=error_callback,
        cancel_callback=cancel_callback,
    )
