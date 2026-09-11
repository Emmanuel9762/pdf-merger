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