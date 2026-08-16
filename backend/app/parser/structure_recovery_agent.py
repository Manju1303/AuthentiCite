import re
from typing import List, Dict, Any, Optional

class StructureRecoveryAgent:
    """
    Smart Academic Structure Recovery Agent.
    Reconstructs section hierarchies, cleans line-ending hyphenations,
    repairs paragraph flows across page breaks, and segments references lists.
    """

    HEADER_PATTERNS = {
        "abstract": r"^\s*(?:abstract|keywords)\b",
        "introduction": r"^\s*(?:[ixv0-9]+\.|\d+\.)?\s*introduction\b",
        "literature_review": r"^\s*(?:[ixv0-9]+\.|\d+\.)?\s*(?:literature review|related work)\b",
        "methodology": r"^\s*(?:[ixv0-9]+\.|\d+\.)?\s*(?:methodology|proposed method|system architecture)\b",
        "results": r"^\s*(?:[ixv0-9]+\.|\d+\.)?\s*(?:experimental results|performance evaluation|results)\b",
        "discussion": r"^\s*(?:[ixv0-9]+\.|\d+\.)?\s*(?:discussion|comparative analysis)\b",
        "conclusion": r"^\s*(?:[ixv0-9]+\.|\d+\.)?\s*(?:conclusion|future work)\b",
        "references": r"^\s*(?:references|bibliography)\b"
    }

    def unwrap_hyphenation_and_lines(self, text: str) -> str:
        """
        Removes hyphenation at line breaks (e.g. 'develop-\nment' -> 'development')
        and cleans excessive spacing.
        """
        # Fix hyphenated words at line breaks
        cleaned = re.sub(r'(\b[a-zA-Z]+)-\s*\n\s*([a-zA-Z]+\b)', r'\1\2', text)
        # Replace remaining newlines with spaces within paragraphs
        cleaned = re.sub(r'(?<!\n)\n(?!\n)', ' ', cleaned)
        # Normalize double spaces
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        return cleaned.strip()

    def identify_section_header(self, line: str) -> Optional[str]:
        """Identifies if a text line matches an academic section heading."""
        l_clean = line.strip().lower()
        if not l_clean or len(l_clean) > 80:
            return None

        for sec_name, pattern in self.HEADER_PATTERNS.items():
            if re.search(pattern, l_clean):
                return sec_name.replace("_", " ").title()
        return None

    def segment_references(self, ref_text: str) -> List[Dict[str, Any]]:
        """Segments raw reference text into structured reference items."""
        lines = ref_text.split("\n")
        references = []
        curr_ref = []
        curr_key = None

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Match bracketed key e.g. [1], [12]
            key_m = re.match(r"^\[(\d+)\]", line_str)
            if key_m:
                if curr_ref:
                    references.append({
                        "raw_reference": " ".join(curr_ref),
                        "citation_key": f"[{curr_key}]" if curr_key else None
                    })
                curr_key = key_m.group(1)
                curr_ref = [line_str]
            else:
                if curr_ref:
                    curr_ref.append(line_str)
                else:
                    curr_ref = [line_str]

        if curr_ref:
            references.append({
                "raw_reference": " ".join(curr_ref),
                "citation_key": f"[{curr_key}]" if curr_key else None
            })

        return references

    def recover_document_structure(self, raw_pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Processes page text blocks, unwraps line hyphens, detects section transitions,
        and constructs structured sections and references lists.
        """
        sections = []
        references = []
        current_section = "Title/Abstract"
        is_in_references = False
        element_idx = 0

        for page in raw_pages:
            page_num = page.get("page_number", 1)
            text = page.get("text", "")
            cleaned_text = self.unwrap_hyphenation_and_lines(text)

            # Split into paragraph blocks
            paragraphs = [p.strip() for p in cleaned_text.split("\n\n") if p.strip()]

            for para in paragraphs:
                header = self.identify_section_header(para)
                if header:
                    current_section = header
                    if header.lower() == "references":
                        is_in_references = True

                if is_in_references and header != "References":
                    refs_segmented = self.segment_references(para)
                    references.extend(refs_segmented)
                else:
                    sections.append({
                        "id": f"rec_sec_{element_idx}",
                        "section_name": current_section,
                        "original_text": para,
                        "rewritten_text": para,
                        "similarity_score": 0.0,
                        "is_flagged": False,
                        "layout_metadata": {
                            "type": "paragraph",
                            "page_number": page_num,
                            "is_section_header": header is not None
                        }
                    })
                    element_idx += 1

        return {
            "sections": sections,
            "references": references,
            "sections_count": len(sections),
            "references_count": len(references)
        }


# Global structure recovery agent instance
structure_recovery_agent = StructureRecoveryAgent()
