from pathlib import Path
from pypdf import PdfWriter


def find_pdfs(input_folder):
    return [
        file for file in input_folder.iterdir()
        if file.is_file() and file.suffix.lower() == ".pdf"
    ]


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


def get_output_file(output_folder):
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
                print("Merge cancelled.")
                continue

        return output_file


def merge_pdfs(pdf_files, output_file):
    writer = PdfWriter()

    for pdf_file in pdf_files:
        writer.append(pdf_file)

    writer.write(output_file)


def main():
    input_folder = Path("input")
    output_folder = Path("output")

    if not input_folder.exists():
        print("Input folder not found.")
        return

    output_folder.mkdir(exist_ok=True)

    pdf_files = find_pdfs(input_folder)

    if not pdf_files:
        print("No PDF files found in the input folder.")
        return

    selected_files = get_merge_order(pdf_files)

    print("\nMerge order:")

    for index, pdf_file in enumerate(selected_files, start=1):
        print(f"{index}. {pdf_file.name}")

    output_file = get_output_file(output_folder)

    merge_pdfs(selected_files, output_file)

    print("\nPDFs merged successfully!")
    print(f"Output: {output_file}")


if __name__ == "__main__":
    main()