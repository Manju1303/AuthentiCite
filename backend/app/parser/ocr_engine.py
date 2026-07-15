import os
import uuid
from PIL import Image
import io
from typing import Dict, Any

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# Try importing OCR engines
try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

def ocr_image(image_bytes: bytes) -> str:
    """Runs OCR on raw image bytes and returns the extracted text."""
    if PaddleOCR:
        try:
            # Initialize paddleocr (lazy load)
            ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            result = ocr.ocr(image_bytes, cls=True)
            text_lines = []
            for idx in range(len(result)):
                res = result[idx]
                if res:
                    for line in res:
                        text_lines.append(line[1][0])
            return "\n".join(text_lines)
        except Exception:
            pass # fall back to tesseract

    if pytesseract:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            return pytesseract.image_to_string(image)
        except Exception as e:
            return f"[OCR Failed: Tesseract error: {str(e)}]"
            
    return "[OCR Error: No OCR Engine (PaddleOCR or Tesseract) is installed. Please install Tesseract-OCR on your system.]"

def ocr_pdf(file_path: str, media_dir: str = "uploads/media") -> Dict[str, Any]:
    """Converts a scanned PDF into pages of images, runs OCR on them, and structures the text blocks."""
    if not fitz:
        raise ValueError("Scanned PDF OCR parsing requires PyMuPDF (fitz) library. Please install PyMuPDF or upload a digital text PDF.")
    doc = fitz.open(file_path)
    os.makedirs(media_dir, exist_ok=True)
    
    sections_list = []
    references = []
    
    layout_map = {
        "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0},
        "page_width": 8.5,
        "page_height": 11.0,
    }
    
    element_index = 0
    current_section = "Title/Abstract"
    is_references_section = False
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Render page to an image (resolution: 150 DPI)
        pix = page.get_pixmap(dpi=150)
        image_bytes = pix.tobytes("png")
        
        # Save page image for reference
        page_image_name = f"page_{page_num}_{uuid.uuid4().hex}.png"
        page_image_path = os.path.join(media_dir, page_image_name)
        with open(page_image_path, "wb") as f:
            f.write(image_bytes)
            
        page_text = ocr_image(image_bytes)
        
        # Split OCR text into paragraphs
        paragraphs = page_text.split("\n\n")
        for para in paragraphs:
            para_text = para.strip()
            if not para_text or len(para_text) < 5:
                continue
            
            # Simple header matching
            import re
            t_clean = para_text.lower()
            if "abstract" in t_clean and len(para_text) < 30:
                current_section = "Abstract"
            elif "introduction" in t_clean and len(para_text) < 35:
                current_section = "Introduction"
            elif "method" in t_clean and len(para_text) < 35:
                current_section = "Methodology"
            elif "result" in t_clean and len(para_text) < 35:
                current_section = "Results"
            elif "discussion" in t_clean and len(para_text) < 35:
                current_section = "Discussion"
            elif "conclusion" in t_clean and len(para_text) < 35:
                current_section = "Conclusion"
            elif "reference" in t_clean and len(para_text) < 30:
                current_section = "References"
                is_references_section = True
                
            layout_meta = {
                "type": "paragraph",
                "alignment": "LEFT",
                "runs": [{"text": para_text, "font_name": "Arial", "font_size": 11.0, "bold": False, "italic": False}]
            }
            
            if is_references_section and "reference" not in t_clean:
                # Add to bibliography references
                references.append({
                    "raw_reference": para_text,
                    "citation_key": None
                })
            else:
                sections_list.append({
                    "id": f"block_{element_index}",
                    "section_name": current_section,
                    "original_text": para_text,
                    "rewritten_text": para_text,
                    "similarity_score": 0.0,
                    "is_flagged": False,
                    "layout_metadata": layout_meta
                })
                element_index += 1
                
    return {
        "sections": sections_list,
        "references": references,
        "layout_map": layout_map
    }
