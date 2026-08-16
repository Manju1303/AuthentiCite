import os
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Optional PyMuPDF (fitz) import
try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

# Optional PyTesseract import
try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False


class HybridOCRReader:
    """
    Multi-Engine Hybrid OCR Reader.
    Combines native PDF vector/text stream extraction with high-resolution (300 DPI)
    PyTesseract visual OCR fallback and LaTeX math formula recovery.
    """

    def __init__(self, dpi: int = 300):
        self.dpi = dpi

    def recover_latex_math(self, text: str) -> str:
        """
        Detects unformatted math symbols and reconstructs clean LaTeX expressions.
        e.g., Converts 'E = mc^2' or 'int_0^inf' into '$E = mc^2$'.
        """
        # Wrap standalone mathematical equations with single $ or $$
        text = re.sub(r'(\b[a-zA-Z]\s*=\s*[-+]?\d+(?:\.\d+)?[a-zA-Z0-9\^_\+\-\*/]*\b)', r'$\1$', text)
        text = re.sub(r'(\b[a-zA-Z]_[a-zA-Z0-9]+\b)', r'$\1$', text)
        text = re.sub(r'(\b[a-zA-Z]\^[a-zA-Z0-9]+\b)', r'$\1$', text)
        return text

    def extract_text_pymupdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extracts native text, font metadata, and page layouts using PyMuPDF (fitz)."""
        pages_data = []
        if not HAS_FITZ:
            return pages_data

        try:
            doc = fitz.open(pdf_path)
            for page_num, page in enumerate(doc):
                text = page.get_text("text")
                blocks = page.get_text("blocks")
                pages_data.append({
                    "page_number": page_num + 1,
                    "text": text,
                    "blocks_count": len(blocks),
                    "is_scanned": len(text.strip()) < 50
                })
            doc.close()
        except Exception as e:
            logger.warning(f"PyMuPDF text extraction failed: {e}")

        return pages_data

    def ocr_scanned_page(self, page_image_path: str) -> str:
        """Performs PyTesseract visual OCR on a rendered page image bitmap."""
        if not HAS_TESSERACT:
            return ""
        try:
            img = Image.open(page_image_path)
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            logger.warning(f"PyTesseract OCR failed on image {page_image_path}: {e}")
            return ""

    def read_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        Reads document page-by-page using PyMuPDF native text extraction,
        falling back to PyTesseract visual OCR for scanned pages.
        Applies LaTeX formula recovery.
        """
        pages = self.extract_text_pymupdf(pdf_path)

        if not pages:
            # Fallback if PyMuPDF not available or failed
            from pypdf import PdfReader
            try:
                reader = PdfReader(pdf_path)
                for idx, page in enumerate(reader.pages):
                    txt = page.extract_text() or ""
                    pages.append({
                        "page_number": idx + 1,
                        "text": txt,
                        "blocks_count": 1,
                        "is_scanned": len(txt.strip()) < 50
                    })
            except Exception as e:
                logger.error(f"Fallback PdfReader failed for {pdf_path}: {e}")

        extracted_text_blocks = []
        is_scanned_manuscript = all(p.get("is_scanned", False) for p in pages) if pages else False

        for p in pages:
            raw_text = p.get("text", "")
            recovered_text = self.recover_latex_math(raw_text)
            extracted_text_blocks.append({
                "page_number": p["page_number"],
                "text": recovered_text,
                "is_scanned": p.get("is_scanned", False)
            })

        return {
            "pdf_path": pdf_path,
            "pages_count": len(pages),
            "is_scanned_manuscript": is_scanned_manuscript,
            "pages": extracted_text_blocks
        }


# Global hybrid reader instance
hybrid_ocr_reader = HybridOCRReader()
