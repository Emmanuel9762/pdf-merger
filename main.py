from pathlib import Path
from pypdf import PdfWriter

input_folder = Path("input")
output_folder = Path("output")

pdf_files = list(input_folder.glob("*.pdf"))

print(pdf_files)