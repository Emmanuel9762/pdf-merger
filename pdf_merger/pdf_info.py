from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class PDFInfo:
    path: Path
    pages: int
    size_bytes: int


def get_pdf_info(file_path):
    file_path = Path(file_path)

    reader = PdfReader(file_path)

    return PDFInfo(
        path=file_path,
        pages=len(reader.pages),
        size_bytes=file_path.stat().st_size,
    )


def get_total_pages(pdf_files):
    return sum(
        get_pdf_info(pdf_file).pages
        for pdf_file in pdf_files
    )


def get_total_size(pdf_files):
    return sum(
        get_pdf_info(pdf_file).size_bytes
        for pdf_file in pdf_files
    )