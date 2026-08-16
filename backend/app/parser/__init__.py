import os
from typing import Dict, Any

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

from backend.app.parser.docx_parser import parse_docx
from backend.app.parser.pdf_parser import parse_pdf
from backend.app.parser.ocr_engine import ocr_pdf


def parse_document(file_path: str, media_dir: str = "uploads/media") -> Dict[str, Any]:
    """
    Parses a document (DOCX or PDF), extracts sections, layout structures, and references.
    If a PDF is scanned (contains no text), it runs OCR on it.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".docx":
        return parse_docx(file_path, media_dir)
        
    elif ext == ".pdf":
        from backend.app.config import settings
        if getattr(settings, "USE_MARKER", False):
            from backend.app.parser.marker_parser import parse_pdf_with_marker
            return parse_pdf_with_marker(file_path, media_dir)
            
        # Check if PDF contains text, or if it is scanned
        if PdfReader is not None:
            try:
                reader = PdfReader(file_path)
                total_chars = 0
                for page in reader.pages:
                    total_chars += len(page.extract_text() or "")
                
                if total_chars < 50:
                    # Scanned PDF, run OCR
                    return ocr_pdf(file_path, media_dir)
                else:
                    return parse_pdf(file_path, media_dir)
            except Exception as e:
                print(f"PdfReader extraction failed, falling back to parse_pdf: {e}")
                return parse_pdf(file_path, media_dir)
        else:
            return parse_pdf(file_path, media_dir)
            
    else:
        raise ValueError(f"Unsupported file format: {ext}")
