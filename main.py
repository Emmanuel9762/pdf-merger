from pypdf import PdfWriter

writer = PdfWriter()

writer.append("first.pdf")
writer.append("second.pdf")

writer.write("merged.pdf")

print("PDFs merged successfully!")