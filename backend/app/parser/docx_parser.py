import os
import uuid
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from typing import List, Dict, Any

def parse_docx(file_path: str, media_dir: str = "uploads/media") -> Dict[str, Any]:
    doc = Document(file_path)
    os.makedirs(media_dir, exist_ok=True)
    
    sections_list = []
    references = []
    layout_map = {
        "margins": {
            "top": doc.sections[0].top_margin.inches if doc.sections else 1.0,
            "bottom": doc.sections[0].bottom_margin.inches if doc.sections else 1.0,
            "left": doc.sections[0].left_margin.inches if doc.sections else 1.0,
            "right": doc.sections[0].right_margin.inches if doc.sections else 1.0
        },
        "page_width": doc.sections[0].page_width.inches if doc.sections else 8.5,
        "page_height": doc.sections[0].page_height.inches if doc.sections else 11.0,
    }
    
    # Track document structure
    current_section = "Title/Abstract"
    is_references_section = False
    
    # 1. Helper to extract images from run XML element if any
    def extract_image_from_run(run, media_dir):
        # python-docx stores images in run._r.get_or_add_drawing() or similar
        # A simpler way to get all images is via doc.inline_shapes or doc.part.related_parts
        # Let's write a generic run-image finder by looking at run XML
        r_elem = run._r
        xml_str = r_elem.xml
        if "pic:pic" in xml_str or "drawing" in xml_str:
            # Found drawing, let's see if we can find relationship id
            import re
            embed_ids = re.findall(r'r:embed="([^"]+)"', xml_str)
            if embed_ids:
                rel_id = embed_ids[0]
                part = doc.part.related_parts[rel_id]
                image_bytes = part.image.blob
                image_ext = part.image.ext
                image_name = f"img_{uuid.uuid4().hex}.{image_ext}"
                dest_path = os.path.join(media_dir, image_name)
                with open(dest_path, "wb") as f:
                    f.write(image_bytes)
                return image_name
        return None

    # Helper to check if text is a section header
    def detect_section_header(text: str) -> str:
        t_clean = text.strip().lower()
        if not t_clean:
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
            # Match header starting with Roman numeral or just words (e.g. "I. Introduction" or "1. Introduction")
            import re
            pattern = rf"^([ixv0-9\.\-\s]+)?\b{keyword}s?\b"
            if re.search(pattern, t_clean):
                return section_name
        return None

    # Parse elements in order. 
    # Since python-docx doesn't preserve exact sequence of paragraphs vs tables out-of-the-box easily,
    # we can iterate over the body element's child XML tags: `<w:p>` (paragraph) and `<w:tbl>` (table)
    from docx.oxml.ns import qn
    body_element = doc.element.body
    
    element_index = 0
    for child in body_element.iterchildren():
        tag = child.tag.split("}")[-1]
        
        if tag == "p":
            # Reconstruct the paragraph object
            from docx.text.paragraph import Paragraph
            para = Paragraph(child, doc)
            text = para.text.strip()
            
            if not text:
                # Check if it has images
                has_image = False
                for r in para.runs:
                    img_name = extract_image_from_run(r, media_dir)
                    if img_name:
                        sections_list.append({
                            "id": f"block_{element_index}",
                            "section_name": current_section,
                            "original_text": f"[IMAGE: {img_name}]",
                            "rewritten_text": f"[IMAGE: {img_name}]",
                            "similarity_score": 0.0,
                            "is_flagged": False,
                            "layout_metadata": {
                                "type": "image",
                                "image_name": img_name,
                                "alignment": "CENTER"
                            }
                        })
                        element_index += 1
                        has_image = True
                if not has_image:
                    continue # Skip empty paragraph
                continue
                
            # Section header transition check
            new_sec = detect_section_header(text)
            if new_sec:
                current_section = new_sec
                if new_sec == "References":
                    is_references_section = True
            
            # Format metadata
            align_val = "LEFT"
            if para.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                align_val = "CENTER"
            elif para.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.RIGHT:
                align_val = "RIGHT"
            elif para.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY:
                align_val = "JUSTIFY"

            runs_data = []
            for r in para.runs:
                # Check for images in run
                img_name = extract_image_from_run(r, media_dir)
                if img_name:
                    runs_data.append({
                        "type": "image",
                        "image_name": img_name
                    })
                    continue
                
                runs_data.append({
                    "text": r.text,
                    "font_name": r.font.name or "Calibri",
                    "font_size": r.font.size.pt if r.font.size else 11.0,
                    "bold": r.bold or False,
                    "italic": r.italic or False,
                    "color": r.font.color.rgb.to_hex() if (r.font.color and r.font.color.rgb) else None
                })
            
            layout_meta = {
                "type": "paragraph",
                "alignment": align_val,
                "style": para.style.name,
                "runs": runs_data,
                "spacing_before": para.paragraph_format.space_before.pt if para.paragraph_format.space_before else 0,
                "spacing_after": para.paragraph_format.space_after.pt if para.paragraph_format.space_after else 6,
                "line_spacing": para.paragraph_format.line_spacing if para.paragraph_format.line_spacing else 1.15
            }
            
            if is_references_section and text.lower() != "references":
                # Save to references list
                import re
                cit_key_match = re.match(r"^\[([0-9]+)\]", text)
                citation_key = cit_key_match.group(1) if cit_key_match else None
                references.append({
                    "raw_reference": text,
                    "citation_key": citation_key
                })
            else:
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
                
        elif tag == "tbl":
            # Reconstruct the table object
            from docx.table import Table
            table = Table(child, doc)
            table_data = []
            
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    cell_paragraphs = []
                    for cp in cell.paragraphs:
                        if cp.text.strip():
                            cell_paragraphs.append(cp.text.strip())
                    row_data.append("\n".join(cell_paragraphs))
                table_data.append(row_data)
                
            layout_meta = {
                "type": "table",
                "alignment": "CENTER",
                "rows_count": len(table.rows),
                "cols_count": len(table.columns) if table.rows else 0
            }
            
            # Format table as Markdown or HTML representation to send to LLM
            table_str = " | ".join(table_data[0]) + "\n"
            table_str += " | ".join(["---"] * len(table_data[0])) + "\n"
            for row in table_data[1:]:
                table_str += " | ".join(row) + "\n"
                
            sections_list.append({
                "id": f"block_{element_index}",
                "section_name": current_section,
                "original_text": table_str.strip(),
                "rewritten_text": table_str.strip(),
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
