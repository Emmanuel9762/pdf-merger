from pathlib import Path
from pypdf import PdfWriter


# Set directories
input_folder = Path("input")
output_folder = Path("output")

pdf_files = list(input_folder.glob("*.pdf"))


# Filter for PDF files specifically
pdf_files = [
    file for file in input_folder.iterdir()
    if file.is_file() and file.suffix.lower() == ".pdf"
]

print("PDFs found:")

writer = PdfWriter()

# Combine all PDFs 
for pdf_file in pdf_files: 
    writer.append(pdf_file)

output_file = output_folder / "merged.pdf"

print(pdf_files)

# Save the final merged file
writer.write(output_file)

print(f"\nPDFs merged successfully!")

print(f"Output: {output_file}")