import argparse
from pathlib import Path

from pdf_merger import (
    find_pdfs,
    get_cli_files,
    get_merge_order,
    merge_pdfs,
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

    return parser.parse_args()



def get_output_file(output_path=None):
    if output_path:
        output_file = Path(output_path)

        if not output_file.suffix:
            output_file = output_file.with_suffix(".pdf")

        output_file.parent.mkdir(parents=True, exist_ok=True)

        if output_file.exists():
            choice = input(
                f"\nFile already exists: {output_file}\n"
                "Overwrite it? (y/n): "
            ).lower()

            if choice != "y":
                print("Merge cancelled.")
                return None

        return output_file

    output_folder = Path("output")

    while True:
        output_name = input("\nEnter output filename: ").strip()

        if not output_name:
            print("Filename cannot be empty.")
            continue

        if not output_name.lower().endswith(".pdf"):
            output_name += ".pdf"

        output_file = output_folder / output_name

        if output_file.exists():
            choice = input(
                f"\nFile already exists: {output_file}\n"
                "Overwrite it? (y/n): "
            ).lower()

            if choice != "y":
                continue

        return output_file


def main():
    args = parse_args()
    input_folder = Path(args.input)

    if args.files:
        pdf_files = get_cli_files(args.files)

        if pdf_files is None:
            return
    else:
        if not input_folder.exists():
            print("Input folder not found.")
            return

        pdf_files = find_pdfs(input_folder)

        if not pdf_files:
            print("No PDF files found in the input folder.")
            return

    if args.files:
        selected_files = pdf_files
    else:
        selected_files = get_merge_order(pdf_files)

    print("\nMerge order:")

    for index, pdf_file in enumerate(selected_files, start=1):
        print(f"{index}. {pdf_file.name}")

    output_file = get_output_file(args.output)

    if output_file is None:
        return

    total_pages = merge_pdfs(selected_files, output_file)

    if total_pages is None:
        return

    print("\nPDFs merged successfully!")
    print(f"Files merged: {len(selected_files)}")
    print(f"Total pages: {total_pages}")
    print(f"Output: {output_file}")


if __name__ == "__main__":
    main()