from pathlib import Path
from pypdf import PdfWriter


# Set directories
input_folder = Path("input")
output_folder = Path("output")

output_folder.mkdir(exist_ok=True)

# Filter for PDF files specifically
pdf_files = [
    file for file in input_folder.iterdir()
    if file.is_file() and file.suffix.lower() == ".pdf"
]
if not pdf_files:
    print("No PDF files found.")
    exit()

print("\nPDFs found:")

for index, pdf_file in enumerate(pdf_files, start=1):
    print(f"{index}. {pdf_file.name}")

order = input("\nEnter the order you want (e.g 1 2 3): ")

order = [int(number) for number in order.split()]

selected_files = [pdf_files[index - 1] for index in order]

print("\nMerge Order:")

for index, pdf_file in enumerate (selected_files, start=1):
    print(f"{index}. {pdf_file.name}")

writer = PdfWriter()

for pdf_file in selected_files: 
    writer.append(pdf_file)

output_file = output_folder / "merged.pdf"

print(pdf_files)

# Save the final merged file
writer.write(output_file)

print(f"\nPDFs merged successfully!")

print(f"Output: {output_file}")