from pathlib import Path
from pypdf import PdfWriter


# Set directories
input_folder = Path("input")
output_folder = Path("output")


output_folder.mkdir(exist_ok=True)


pdf_files = [
    file for file in input_folder.iterdir()
    if file.is_file() and file.suffix.lower() == ".pdf"
]

# Check for PDFs
if not pdf_files:
    print("No PDF files found.")
    exit()


# Display available PDFs
print("\nPDFs found:")

for index, pdf_file in enumerate(pdf_files, start=1):
    print(f"{index}. {pdf_file.name}")


# Get merge order
order = input("\nEnter the order you want (e.g. 1 2 3): ")

try:
    order = [int(number) for number in order.split()]
except ValueError:
    print("Invalid input. Please enter numbers only.")
    exit()


# Check that selected numbers are valid
if any(index < 1 or index > len(pdf_files) for index in order):
    print("Invalid file number.")
    exit()

if len(order) != len(pdf_files):
    print("Please select every PDF exactly once.")
    exit()

if len(set(order)) != len(order):
    print("Duplicate file numbers are not allowed.")
    exit()


# Select files in chosen order
selected_files = [pdf_files[index - 1] for index in order]


print("\nMerge Order:")

for index, pdf_file in enumerate (selected_files, start=1):
    print(f"{index}. {pdf_file.name}")


# Merge selected files
writer = PdfWriter()

for pdf_file in selected_files: 
    writer.append(pdf_file)


output_file = output_folder / "merged.pdf"

print(pdf_files)

# Save the final merged file
writer.write(output_file)

print(f"\nPDFs merged successfully!")

print(f"Output: {output_file}")