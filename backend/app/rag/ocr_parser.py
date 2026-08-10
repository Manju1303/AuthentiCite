import os
import re
from typing import Dict, Any, List
import httpx
from backend.app.config import settings

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

def parse_document_ocr(file_path: str) -> Dict[str, Any]:
    """
    Parses a PDF or Image file using PyMuPDF / PyTesseract OCR,
    or external Gemma 3 / Nemotron OCR services if configured.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    # Check for Gemma 3 OCR endpoint or Nemotron API key if configured
    if settings.GEMMA_OCR_ENDPOINT:
        try:
            return _call_gemma_ocr_endpoint(file_path)
        except Exception as e:
            print(f"Gemma 3 OCR failed, falling back to local PyMuPDF parser: {e}")

    if ext == ".pdf":
        return _parse_pdf_with_ocr(file_path)
    else:
        return _parse_image_ocr(file_path)

def _parse_pdf_with_ocr(pdf_path: str) -> Dict[str, Any]:
    if fitz is None:
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            pages_data = []
            full_text_list = []
            for page_num, page in enumerate(reader.pages):
                text = (page.extract_text() or "").strip()
                pages_data.append({"page_number": page_num + 1, "text": text, "char_count": len(text)})
                full_text_list.append(f"--- Page {page_num + 1} ---\n{text}")
            full_text = "\n\n".join(full_text_list)
            sections = _create_sections_from_pages(pages_data)
            return {
                "text": full_text,
                "page_count": len(pages_data),
                "pages": pages_data,
                "sections": sections,
                "parser_used": "PyPDF Fallback Parser"
            }
        except Exception as e:
            print(f"PyPDF fallback error: {e}")
            return {"text": "", "page_count": 0, "pages": [], "sections": [], "parser_used": "Failed"}

    doc = fitz.open(pdf_path)
    pages_data = []
    full_text_list = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()
        
        # If extracted text is sparse, attempt OCR image fallback
        if len(text) < 50:
            ocr_text = _extract_page_ocr_tesseract(page)
            if len(ocr_text) > len(text):
                text = ocr_text

        pages_data.append({
            "page_number": page_num + 1,
            "text": text,
            "char_count": len(text)
        })
        full_text_list.append(f"--- Page {page_num + 1} ---\n{text}")

    doc.close()

    full_text = "\n\n".join(full_text_list)
    sections = _create_sections_from_pages(pages_data)

    return {
        "text": full_text,
        "page_count": len(pages_data),
        "pages": pages_data,
        "sections": sections,
        "parser_used": "PyMuPDF + Tesseract OCR"
    }

def _extract_page_ocr_tesseract(page: fitz.Page) -> str:
    try:
        import pytesseract
        from PIL import Image
        import io

        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes()))
        return pytesseract.image_to_string(img)
    except Exception as e:
        print(f"Tesseract page OCR error: {e}")
        return page.get_text("text")

def _parse_image_ocr(image_path: str) -> Dict[str, Any]:
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(image_path)
        extracted = pytesseract.image_to_string(img)
    except Exception as e:
        extracted = f"[Error running pytesseract on image: {e}]"

    return {
        "text": extracted,
        "page_count": 1,
        "pages": [{"page_number": 1, "text": extracted, "char_count": len(extracted)}],
        "sections": [{"title": "Image OCR Content", "text": extracted, "page_number": 1}],
        "parser_used": "PyTesseract Image OCR"
    }

def _create_sections_from_pages(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sections = []
    sec_index = 1
    
    for p in pages:
        paragraphs = re.split(r'\n\s*\n', p["text"])
        for idx, para in enumerate(paragraphs):
            cleaned = para.strip()
            if len(cleaned) > 20:
                sections.append({
                    "id": f"sec_p{p['page_number']}_{idx+1}",
                    "title": f"Page {p['page_number']} Section {idx+1}",
                    "text": cleaned,
                    "page_number": p["page_number"],
                    "section_index": sec_index
                })
                sec_index += 1
    return sections

def _call_gemma_ocr_endpoint(file_path: str) -> Dict[str, Any]:
    # Placeholder for Gemma 3 Vision / OCR API call
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    
    response = httpx.post(
        settings.GEMMA_OCR_ENDPOINT,
        files={"file": (os.path.basename(file_path), file_bytes)},
        timeout=30.0
    )
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        raise RuntimeError(f"Gemma OCR server returned status {response.status_code}")
