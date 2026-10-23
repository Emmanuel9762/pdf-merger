import argparse
from pathlib import Path

from pdf_merger import (
    apply_merge_order,
    delete_pages,
    extract_pages,
    find_pdfs,
    get_cli_files,
    get_merge_order,
    merge_files,
    reorder_pages,
    resolve_output_path,
    rotate_pages,
    split_pdf,
)


def parse_page_range(value):
    from pdf_merger import parse_page_range as parse_core_page_range

    try:
        return parse_core_page_range(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def build_merge_parser():
    parser = argparse.ArgumentParser(description="Merge PDF files.")

    parser.add_argument(
        "files",
        nargs="*",
        help="PDF files to merge.",
    )

    parser.add_argument(
        "--input",
        default="input",
        help="Folder containing PDF files.",
    )

    parser.add_argument(
        "--output",
        help="Output PDF file.",
    )

    parser.add_argument(
        "--order",
        nargs="+",
        type=int,
        help="Order of input PDFs by number.",
    )

    parser.set_defaults(operation="merge")
    return parser


def build_split_parser():
    parser = argparse.ArgumentParser(
        prog="pdf-merger-cli split",
        description="Split a PDF into individual pages or page ranges.",
    )

    parser.add_argument(
        "file",
        help="PDF file to split.",
    )
    parser.add_argument(
        "--range",
        dest="ranges",
        action="append",
        type=parse_page_range,
        help=(
            "Page or inclusive page range to extract as one part. "
            "Repeat for multiple parts, for example --range 1-3 --range 4-6. "
            "If omitted, every page becomes its own PDF."
        ),
    )
    parser.add_argument(
        "--output",
        help=(
            "Directory for split PDFs. Defaults to "
            "output/<source-name>-parts."
        ),
    )

    parser.set_defaults(operation="split")
    return parser



def build_extract_parser():
    parser = argparse.ArgumentParser(
        prog="pdf-merger-cli extract",
        description="Extract selected pages into one PDF.",
    )
    parser.add_argument(
        "file",
        help="PDF file to extract pages from.",
    )
    parser.add_argument(
        "--range",
        dest="ranges",
        action="append",
        type=parse_page_range,
        required=True,
        help=(
            "Page or inclusive page range to include in the output. "
            "Repeat to preserve custom ordering, for example "
            "--range 4-5 --range 2."
        ),
    )
    parser.add_argument(
        "--output",
        help=(
            "Output PDF. Defaults to "
            "output/<source-name>-extracted.pdf."
        ),
    )
    parser.set_defaults(operation="extract")
    return parser


def build_rotate_parser():
    parser = argparse.ArgumentParser(
        prog="pdf-merger-cli rotate",
        description="Rotate selected PDF pages.",
    )
    parser.add_argument(
        "file",
        help="PDF file to rotate.",
    )
    parser.add_argument(
        "--degrees",
        type=int,
        choices=(90, 180, 270),
        required=True,
        help="Clockwise rotation in degrees.",
    )
    parser.add_argument(
        "--range",
        dest="ranges",
        action="append",
        type=parse_page_range,
        help=(
            "Page or inclusive page range to rotate. Repeat for multiple "
            "ranges. If omitted, every page is rotated."
        ),
    )
    parser.add_argument(
        "--output",
        help=(
            "Output PDF. Defaults to "
            "output/<source-name>-rotated.pdf."
        ),
    )
    parser.set_defaults(operation="rotate")
    return parser


def build_delete_parser():
    parser = argparse.ArgumentParser(
        prog="pdf-merger-cli delete",
        description="Delete selected pages from a PDF.",
    )
    parser.add_argument(
        "file",
        help="PDF file to remove pages from.",
    )
    parser.add_argument(
        "--range",
        dest="ranges",
        action="append",
        type=parse_page_range,
        required=True,
        help=(
            "Page or inclusive page range to delete. Repeat for multiple "
            "ranges, for example --range 2-3 --range 5."
        ),
    )
    parser.add_argument(
        "--output",
        help=(
            "Output PDF. Defaults to "
            "output/<source-name>-trimmed.pdf."
        ),
    )
    parser.set_defaults(operation="delete")
    return parser


def build_reorder_parser():
    parser = argparse.ArgumentParser(
        prog="pdf-merger-cli reorder",
        description="Reorder every page in a PDF.",
    )
    parser.add_argument(
        "file",
        help="PDF file to reorder.",
    )
    parser.add_argument(
        "--order",
        nargs="+",
        type=int,
        required=True,
        help=(
            "New page order using one-based page numbers. "
            "Every page must appear exactly once."
        ),
    )
    parser.add_argument(
        "--output",
        help=(
            "Output PDF. Defaults to "
            "output/<source-name>-reordered.pdf."
        ),
    )
    parser.set_defaults(operation="reorder")
    return parser

def parse_args(argv=None):
    arguments = list(argv) if argv is not None else None

    if arguments is None:
        import sys

        arguments = sys.argv[1:]

    if arguments and arguments[0] == "split":
        return build_split_parser().parse_args(arguments[1:])

    if arguments and arguments[0] == "extract":
        return build_extract_parser().parse_args(arguments[1:])

    if arguments and arguments[0] == "rotate":
        return build_rotate_parser().parse_args(arguments[1:])

    if arguments and arguments[0] == "delete":
        return build_delete_parser().parse_args(arguments[1:])

    if arguments and arguments[0] == "reorder":
        return build_reorder_parser().parse_args(arguments[1:])

    return build_merge_parser().parse_args(arguments)


def get_output_file(output_path=None, input_func=input):
    if output_path:
        output_file = resolve_output_path(output_path)

        if output_file.exists():
            choice = input_func(
                f"\nFile already exists: {output_file}\n"
                "Overwrite it? (y/n): "
            ).lower()

            if choice != "y":
                print("Merge cancelled.")
                return None

        return output_file

    while True:
        output_name = input_func("\nEnter output filename: ").strip()

        if not output_name:
            print("Filename cannot be empty.")
            continue

        output_file = resolve_output_path(output_name)

        if output_file.exists():
            choice = input_func(
                f"\nFile already exists: {output_file}\n"
                "Overwrite it? (y/n): "
            ).lower()

            if choice != "y":
                continue

        return output_file


def run_merge(args, input_func=input):
    input_folder = Path(args.input)

    if args.files:
        pdf_files = get_cli_files(args.files)

        if pdf_files is None:
            return 1
    else:
        if not input_folder.exists():
            print("Input folder not found.")
            return 1

        pdf_files = find_pdfs(input_folder)

        if not pdf_files:
            print("No PDF files found in the input folder.")
            return 1

        print("\nPDFs found:")

        for index, pdf_file in enumerate(pdf_files, start=1):
            print(f"{index}. {pdf_file.name}")

    if args.files:
        selected_files = pdf_files
    elif getattr(args, "order", None):
        selected_files = apply_merge_order(
            pdf_files,
            args.order,
        )

        if selected_files is None:
            print(
                f"Invalid order. Enter each number from 1 to "
                f"{len(pdf_files)} exactly once."
            )
            return 1
    else:
        selected_files = get_merge_order(
            pdf_files,
            input_func=input_func,
        )

    print("\nMerge order:")

    for index, pdf_file in enumerate(selected_files, start=1):
        print(f"{index}. {pdf_file.name}")

    output_file = get_output_file(args.output, input_func=input_func)

    if output_file is None:
        return 1

    merge_error = None

    def report_error(error_message, current_file):
        nonlocal merge_error
        merge_error = (error_message, current_file)

    total_pages = merge_files(
        selected_files,
        output_file,
        error_callback=report_error,
    )

    if total_pages is None:
        if merge_error is None:
            print("Merge failed.")
        else:
            error_message, current_file = merge_error

            if current_file is not None:
                print(f"Merge failed while processing: {Path(current_file).name}")
            else:
                print("Merge failed.")

            print(f"Reason: {error_message}")

        return 1

    print("\nPDFs merged successfully!")
    print(f"Files merged: {len(selected_files)}")
    print(f"Total pages: {total_pages}")
    print(f"Output: {output_file}")

    return 0


def run_split(args):
    source = Path(args.file)
    output_dir = (
        Path(args.output)
        if args.output
        else Path("output") / f"{source.stem}-parts"
    )

    def report_progress(current, total, output_file):
        print(f"Created part {current}/{total}: {output_file.name}")

    result = split_pdf(
        source,
        output_dir,
        ranges=args.ranges,
        progress_callback=report_progress,
    )

    if result.failed:
        print("Split failed.")
        print(f"Reason: {result.error}")
        return 1

    if result.cancelled:
        print("Split cancelled.")
        return 130

    print("\nPDF split successfully!")
    print(f"Parts created: {len(result.outputs)}")
    print(f"Pages processed: {result.pages_processed}")
    print(f"Output directory: {output_dir}")

    return 0



def run_extract(args):
    source = Path(args.file)
    output_file = (
        Path(args.output)
        if args.output
        else Path("output") / f"{source.stem}-extracted.pdf"
    )

    def report_progress(current, total, current_file):
        print(f"Extracting page {current}/{total} from {current_file.name}")

    result = extract_pages(
        source,
        output_file,
        ranges=args.ranges,
        progress_callback=report_progress,
    )

    if result.failed:
        print("Extract failed.")
        print(f"Reason: {result.error}")
        return 1

    if result.cancelled:
        print("Extract cancelled.")
        return 130

    print("\nPages extracted successfully!")
    print(f"Pages processed: {result.pages_processed}")
    print(f"Output: {output_file}")

    return 0



def run_rotate(args):
    source = Path(args.file)
    output_file = (
        Path(args.output)
        if args.output
        else Path("output") / f"{source.stem}-rotated.pdf"
    )

    def report_progress(current, total, current_file):
        print(f"Rotating page {current}/{total} in {current_file.name}")

    result = rotate_pages(
        source,
        output_file,
        degrees=args.degrees,
        ranges=args.ranges,
        progress_callback=report_progress,
    )

    if result.failed:
        print("Rotate failed.")
        print(f"Reason: {result.error}")
        return 1

    if result.cancelled:
        print("Rotate cancelled.")
        return 130

    print("\nPages rotated successfully!")
    print(f"Pages processed: {result.pages_processed}")
    print(f"Output: {output_file}")

    return 0



def run_delete(args):
    source = Path(args.file)
    output_file = (
        Path(args.output)
        if args.output
        else Path("output") / f"{source.stem}-trimmed.pdf"
    )

    def report_progress(current, total, current_file):
        print(f"Processing page {current}/{total} in {current_file.name}")

    result = delete_pages(
        source,
        output_file,
        ranges=args.ranges,
        progress_callback=report_progress,
    )

    if result.failed:
        print("Delete failed.")
        print(f"Reason: {result.error}")
        return 1

    if result.cancelled:
        print("Delete cancelled.")
        return 130

    print("\nPages deleted successfully!")
    print(f"Pages processed: {result.pages_processed}")
    print(f"Output: {output_file}")

    return 0



def run_reorder(args):
    source = Path(args.file)
    output_file = (
        Path(args.output)
        if args.output
        else Path("output") / f"{source.stem}-reordered.pdf"
    )

    def report_progress(current, total, current_file):
        print(f"Reordering page {current}/{total} in {current_file.name}")

    result = reorder_pages(
        source,
        output_file,
        order=args.order,
        progress_callback=report_progress,
    )

    if result.failed:
        print("Reorder failed.")
        print(f"Reason: {result.error}")
        return 1

    if result.cancelled:
        print("Reorder cancelled.")
        return 130

    print("\nPages reordered successfully!")
    print(f"Pages processed: {result.pages_processed}")
    print(f"Output: {output_file}")

    return 0


def run(args, input_func=input):
    operation = getattr(args, "operation", "merge")

    if operation == "split":
        return run_split(args)

    if operation == "extract":
        return run_extract(args)

    if operation == "rotate":
        return run_rotate(args)

    if operation == "delete":
        return run_delete(args)

    if operation == "reorder":
        return run_reorder(args)

    return run_merge(args, input_func=input_func)


def main():
    try:
        args = parse_args()
        return run(args)
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
