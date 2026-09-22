import argparse
from pathlib import Path

from pdf_merger import (
    apply_merge_order,
    find_pdfs,
    get_cli_files,
    get_merge_order,
    merge_files,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Merge PDF files.")

    parser.add_argument(
        "files",
        nargs="*",
        help="PDF files to merge."
    )

    parser.add_argument(
        "--input",
        default="input",
        help="Folder containing PDF files."
    )

    parser.add_argument(
        "--output",
        help="Output PDF file."
    )

    parser.add_argument(
        "--order",
        nargs="+",
        type=int,
        help="Order of input PDFs by number."
    )

    return parser.parse_args()


def get_output_file(output_path=None, input_func=input):
    if output_path:
        output_file = Path(output_path)

        if not output_file.suffix:
            output_file = output_file.with_suffix(".pdf")

        output_file.parent.mkdir(parents=True, exist_ok=True)

        if output_file.exists():
            choice = input_func(
                f"\nFile already exists: {output_file}\n"
                "Overwrite it? (y/n): "
            ).lower()

            if choice != "y":
                print("Merge cancelled.")
                return None

        return output_file

    output_folder = Path("output")

    while True:
        output_name = input_func("\nEnter output filename: ").strip()

        if not output_name:
            print("Filename cannot be empty.")
            continue

        if not output_name.lower().endswith(".pdf"):
            output_name += ".pdf"

        output_file = output_folder / output_name

        if output_file.exists():
            choice = input_func(
                f"\nFile already exists: {output_file}\n"
                "Overwrite it? (y/n): "
            ).lower()

            if choice != "y":
                continue

        return output_file


def run(args, input_func=input):
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
            args.order
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
            input_func=input_func
        )

    print("\nMerge order:")

    for index, pdf_file in enumerate(selected_files, start=1):
        print(f"{index}. {pdf_file.name}")

    output_file = get_output_file(args.output, input_func=input_func)

    if output_file is None:
        return 1

    total_pages = merge_files(
    selected_files,
    output_file
)

    if total_pages is None:
        return 1

    print("\nPDFs merged successfully!")
    print(f"Files merged: {len(selected_files)}")
    print(f"Total pages: {total_pages}")
    print(f"Output: {output_file}")

    return 0


def main():
    args = parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())