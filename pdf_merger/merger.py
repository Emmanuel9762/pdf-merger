from pathlib import Path

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


def merge_pdfs(pdf_files, output_file, progress_callback=None):
    writer = PdfWriter()
    temp_file = output_file.with_suffix(".tmp.pdf")
    current_file = None
    total_files = len(pdf_files)

    try:
        for index, pdf_file in enumerate(pdf_files, start=1):
            current_file = pdf_file
            print(f"Processing: {pdf_file.name}")

            writer.append(pdf_file)

            if progress_callback:
                progress_callback(
                    index,
                    total_files,
                    pdf_file
                )

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


def merge_files(pdf_files, output_file, progress_callback=None):
    if not pdf_files:
        return None

    return merge_pdfs(
        pdf_files,
        output_file,
        progress_callback=progress_callback
    )