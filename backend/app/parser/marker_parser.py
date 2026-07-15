# backend/app/parser/marker_parser.py

import os
import re
import uuid
from typing import Dict, Any, List
from backend.app.parser.pdf_parser import parse_pdf

def parse_pdf_with_marker(file_path: str, media_dir: str = "uploads/media") -> Dict[str, Any]:
    """
    Parses a PDF using the open-source Marker library.
    It translates formatting, columns, tables, and equations into clean Markdown,
    then segments them into database section objects.
    
    If Marker is not installed or lacks GPU resources, it falls back to the native pypdf parser.
    """
    os.makedirs(media_dir, exist_ok=True)
    
    # Heuristic fallback indicator
    marker_available = False
    full_markdown = ""
    
    # 1. Attempt programmatic import and conversion
    try:
        from marker.convert import convert_single_pdf
        from marker.models import load_all_models
        
        print("Marker-pdf package detected. Loading neural models...")
        model_lst = load_all_models()
        full_markdown, out_meta, images = convert_single_pdf(file_path, model_lst)
        marker_available = True
        print("Marker successfully parsed PDF into Markdown.")
        
        # Save images extracted by Marker
        for img_name, img_data in images.items():
            dest_path = os.path.join(media_dir, img_name)
            with open(dest_path, "wb") as f:
                f.write(img_data)
                
    except ImportError:
        # 2. Try Command Line execution if package is globally installed
        import subprocess
        temp_out = os.path.join(os.path.dirname(file_path), f"marker_out_{uuid.uuid4().hex}")
        os.makedirs(temp_out, exist_ok=True)
        
        try:
            print("Attempting to run marker_single via subprocess...")
            cmd = ["marker_single", file_path, temp_out, "--langs", "English"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=90.0)
            
            if res.returncode == 0:
                # Find output markdown file
                for f_name in os.listdir(temp_out):
                    if f_name.endswith(".md"):
                        with open(os.path.join(temp_out, f_name), "r", encoding="utf-8") as f:
                            full_markdown = f.read()
                        marker_available = True
                        print("Marker CLI successfully parsed PDF.")
                        break
            else:
                print(f"Marker CLI execution returned code {res.returncode}. Falling back.")
        except Exception as e:
            print(f"Marker CLI not available or failed: {e}. Defaulting to pypdf parser.")
            
    # Fallback to pypdf parser if Marker didn't run
    if not marker_available or not full_markdown.strip():
        print("Falling back to standard pypdf parsing pipeline.")
        return parse_pdf(file_path, media_dir)

    # 3. Process Marker Markdown output into sections
    sections_list = []
    references = []
    
    layout_map = {
        "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0},
        "page_width": 8.5,
        "page_height": 11.0,
        "source": "Marker Markdown Parser"
    }
    
    current_section = "Title/Abstract"
    is_references_section = False
    element_index = 0
    
    # Split text into markdown blocks/paragraphs
    blocks = full_markdown.split("\n\n")
    
    for block in blocks:
        text = block.strip()
        if not text:
            continue
            
        # Detect headers
        if text.startswith("#"):
            # Markdown header (e.g. "# 1. Introduction" or "## A. Methodology")
            header_match = re.match(r"^#+\s+(.+)$", text)
            if header_match:
                header_title = header_match.group(1)
                current_section = header_title
                if "reference" in header_title.lower():
                    is_references_section = True
                
                # Treat headers as a paragraph of style Heading
                level = len(text) - len(text.lstrip("#"))
                layout_meta = {
                    "type": "paragraph",
                    "alignment": "LEFT",
                    "style": f"Heading {level}",
                    "runs": [{"text": header_title, "bold": True, "font_name": "Times New Roman", "font_size": 12.0}]
                }
                sections_list.append({
                    "id": f"block_{element_index}",
                    "section_name": current_section,
                    "original_text": header_title,
                    "rewritten_text": header_title,
                    "similarity_score": 0.0,
                    "is_flagged": False,
                    "layout_metadata": layout_meta
                })
                element_index += 1
                continue
        
        # Detect references lists
        if is_references_section:
            # Marker usually formats lists cleanly
            lines = text.split("\n")
            for line in lines:
                line_clean = line.strip().lstrip("-*•").strip()
                if not line_clean:
                    continue
                cit_key_match = re.match(r"^\[?([0-9]+)\]?", line_clean)
                cit_key = cit_key_match.group(1) if cit_key_match else None
                references.append({
                    "raw_reference": line_clean,
                    "citation_key": cit_key
                })
            continue
            
        # Detect Tables
        if "|" in text and ("---" in text or "-|-" in text):
            layout_meta = {
                "type": "table",
                "alignment": "CENTER"
            }
            sections_list.append({
                "id": f"block_{element_index}",
                "section_name": current_section,
                "original_text": text,
                "rewritten_text": text,
                "similarity_score": 0.0,
                "is_flagged": False,
                "layout_metadata": layout_meta
            })
            element_index += 1
            continue
            
        # Detect Images
        img_match = re.search(r"!\[(.*?)\]\((.*?)\)", text)
        if img_match:
            img_name = os.path.basename(img_match.group(2))
            layout_meta = {
                "type": "image",
                "image_name": img_name,
                "alignment": "CENTER"
            }
            sections_list.append({
                "id": f"block_{element_index}",
                "section_name": current_section,
                "original_text": f"[IMAGE: {img_name}]",
                "rewritten_text": f"[IMAGE: {img_name}]",
                "similarity_score": 0.0,
                "is_flagged": False,
                "layout_metadata": layout_meta
            })
            element_index += 1
            continue
            
        # Normal paragraphs
        layout_meta = {
            "type": "paragraph",
            "alignment": "LEFT",
            "runs": [{"text": text, "font_name": "Times New Roman", "font_size": 10.0, "bold": False, "italic": False}]
        }
        sections_list.append({
            "id": f"block_{element_index}",
            "section_name": current_section,
            "original_text": text,
            "rewritten_text": text,
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
