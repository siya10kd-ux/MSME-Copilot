"""OCR and text extraction for PDF/image documents."""

from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None


def extract_text_from_pdf(file_path: str | Path) -> str:
    """Extract text from a PDF using PyMuPDF and pdfplumber."""
    file_path = Path(file_path)
    text_parts: list[str] = []

    # PyMuPDF extraction
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text_parts.append(page.get_text())
    except Exception:
        pass

    # pdfplumber fallback for tables
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        text_parts.append(" | ".join(str(c) for c in row if c))
    except Exception:
        pass

    return "\n".join(text_parts).strip()


def extract_text_from_image(file_path: str | Path) -> str:
    """Extract text from an image using OCR."""
    if pytesseract is None:
        return ""
    file_path = Path(file_path)
    image = Image.open(file_path)
    return pytesseract.image_to_string(image).strip()


def extract_text(file_path: str | Path) -> str:
    """Extract text from a document based on file extension."""
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    if suffix in (".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
        return extract_text_from_image(file_path)
    if suffix in (".txt", ".csv"):
        return file_path.read_text(encoding="utf-8", errors="replace")
    return ""
