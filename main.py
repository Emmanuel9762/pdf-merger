import argparse
from pathlib import Path
from pypdf import PdfWriter


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


def get_merge_order(pdf_files):
    print("\nPDFs found:")

    for index, pdf_file in enumerate(pdf_files, start=1):
        print(f"{index}. {pdf_file.name}")

    while True:
        order = input("\nEnter the order you want (e.g. 1 2 3): ")

        try:
            order = [int(number) for number in order.split()]
        except ValueError:
            print("Invalid input. Please enter numbers only.")
            continue

        if any(index < 1 or index > len(pdf_files) for index in order):
            print(f"Enter numbers between 1 and {len(pdf_files)}.")
            continue

        if len(order) != len(pdf_files):
            print(f"Please enter all {len(pdf_files)} PDF numbers.")
            continue

        if len(set(order)) != len(order):
            print("Duplicate file numbers are not allowed.")
            continue

        return [pdf_files[index - 1] for index in order]


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


def merge_pdfs(pdf_files, output_file):
    writer = PdfWriter()
    temp_file = output_file.with_suffix(".tmp.pdf")
    current_file = None

    try:
        for pdf_file in pdf_files:
            current_file = pdf_file
            print(f"Processing: {pdf_file.name}")
            writer.append(pdf_file)

        total_pages = len(writer.pages)
        writer.write(temp_file)
        temp_file.replace(output_file)

    except Exception as error:
        if current_file:
            print(f"\nFailed to process: {current_file.name}")
        else:
            print("\nMerge failed.")

        print(f"Reason: {error}")

        if temp_file.exists():
            temp_file.unlink()

        return None

    return total_pages


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