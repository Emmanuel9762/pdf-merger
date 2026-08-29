from pathlib import Path
from pypdf import PdfWriter

input_folder = Path("input")
output_folder = Path("output")

pdf_files = list(input_folder.glob("*.pdf"))

pdf_files = [
    file for file in input_folder.iterdir()
    if file.is_file() and file.suffix.lower() == ".pdf"
]

print("pdf_files:", pdf_files)