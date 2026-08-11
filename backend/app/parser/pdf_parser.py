import os
import uuid
import re
import logging
from pypdf import PdfReader
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def parse_pdf(file_path: str, media_dir: str = "uploads/media") -> Dict[str, Any]:
    """
    Parses a PDF file using pypdf. Extracts text, reconstructs paragraph blocks,
    detects section transitions, and extracts images.
    """
    reader = PdfReader(file_path)
    os.makedirs(media_dir, exist_ok=True)
    
    sections_list = []
    references = []
    
    layout_map = {
        "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0},
        "page_width": 8.5,
        "page_height": 11.0,
    }
    
    current_section = "Title/Abstract"
    is_references_section = False
    element_index = 0
    
    def detect_section_header(text: str) -> str:
        t_clean = text.strip().lower()
        if not t_clean or len(t_clean) > 80:
            return None
            
        headers = {
            "abstract": "Abstract",
            "keyword": "Keywords",
            "introduction": "Introduction",
            "literature": "Literature Review",
            "method": "Methodology",
            "result": "Results",
            "discussion": "Discussion",
            "conclusion": "Conclusion",
            "reference": "References"
        }
        
        for keyword, section_name in headers.items():
            pattern = rf"^([ixv0-9\.\-\s]+)?\b{keyword}s?\b"
            if re.search(pattern, t_clean):
                return section_name
        return None

    # Parse page by page
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        
        # 1. Extract images in the page
        try:
            for image_file_object in page.images:
                image_ext = os.path.splitext(image_file_object.name)[1].strip(".") or "png"
                image_name = f"pdf_img_{page_num}_{uuid.uuid4().hex}.{image_ext}"
                dest_path = os.path.join(media_dir, image_name)
                with open(dest_path, "wb") as f:
                    f.write(image_file_object.data)
                    
                sections_list.append({
                    "id": f"block_{element_index}",
                    "section_name": current_section,
                    "original_text": f"[IMAGE: {image_name}]",
                    "rewritten_text": f"[IMAGE: {image_name}]",
                    "similarity_score": 0.0,
                    "is_flagged": False,
                    "layout_metadata": {
                        "type": "image",
                        "image_name": image_name,
                        "alignment": "CENTER"
                    }
                })
                element_index += 1
        except Exception as e:
            logger.error(f"Error extracting images from PDF: {e}", exc_info=True)

        # 2. Extract and segment text
        text = page.extract_text()
        if not text:
            continue
            
        # Split text into paragraphs based on double line breaks or line endings followed by capitals
        raw_paragraphs = text.split("\n\n")
        if len(raw_paragraphs) <= 1:
            # Fallback if split failed: split by lines and try to combine
            lines = text.split("\n")
            combined_paras = []
            curr_para = []
            for line in lines:
                curr_para.append(line.strip())
                if line.strip().endswith(".") or len(line.strip()) < 30:
                    combined_paras.append(" ".join(curr_para))
                    curr_para = []
            if curr_para:
                combined_paras.append(" ".join(curr_para))
            raw_paragraphs = combined_paras

        for para in raw_paragraphs:
            para_text = para.strip()
            # Clean hyphens at line endings and excessive spacing
            para_text = re.sub(r'\s+', ' ', para_text)
            para_text = re.sub(r'-\s+', '', para_text)
            
            if not para_text or len(para_text) < 5:
                continue
                
            # Check if this paragraph is a section header
            new_sec = detect_section_header(para_text)
            if new_sec:
                current_section = new_sec
                if new_sec == "References":
                    is_references_section = True
                    
            layout_meta = {
                "type": "paragraph",
                "alignment": "LEFT",
                "runs": [{"text": para_text, "font_name": "Times New Roman", "font_size": 10.0, "bold": False, "italic": False}]
            }
            
            if is_references_section and para_text.lower() != "references":
                # Extract citation key if it starts with [1] or similar
                cit_key_match = re.match(r"^\[([0-9]+)\]", para_text)
                citation_key = cit_key_match.group(1) if cit_key_match else None
                references.append({
                    "raw_reference": para_text,
                    "citation_key": citation_key
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
