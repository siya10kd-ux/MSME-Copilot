"""OCR and text extraction for PDF/image documents."""

from pathlib import Path

import pymupdf as fitz
import pdfplumber
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None


def extract_text_from_pdf(file_path: str | Path) -> str:
    """Extract text from a PDF using PyMuPDF with pdfplumber as a fallback.

    Fix #6: The original code ran *both* extractors unconditionally and
    concatenated their output, duplicating every page's text (and tripling
    table rows).  Now PyMuPDF runs first; pdfplumber is only used page-by-page
    when PyMuPDF returned nothing for that page, so each page's text appears
    exactly once.
    """
    file_path = Path(file_path)

    # --- Primary extraction: PyMuPDF ---
    pymupdf_pages: list[str] = []
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                pymupdf_pages.append(page.get_text())
    except Exception:
        pymupdf_pages = []

    # --- Fallback: pdfplumber only for pages where PyMuPDF returned nothing ---
    final_parts: list[str] = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                pymupdf_text = pymupdf_pages[i] if i < len(pymupdf_pages) else ""
                if pymupdf_text.strip():
                    # PyMuPDF already got good text for this page — use it
                    final_parts.append(pymupdf_text)
                else:
                    # PyMuPDF got nothing; try pdfplumber (handles some scanned PDFs)
                    page_text = page.extract_text() or ""
                    if page_text:
                        final_parts.append(page_text)
                    # Also append any tables pdfplumber found
                    for table in page.extract_tables():
                        for row in table:
                            final_parts.append(" | ".join(str(c) for c in row if c))
    except Exception:
        # pdfplumber unavailable — fall back to whatever PyMuPDF gave us
        if pymupdf_pages:
            final_parts = pymupdf_pages

    return "\n".join(final_parts).strip()


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
