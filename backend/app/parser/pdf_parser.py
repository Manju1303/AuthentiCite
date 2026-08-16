import os
import uuid
import re
import logging
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None
from typing import List, Dict, Any


logger = logging.getLogger(__name__)

from backend.app.parser.hybrid_ocr_reader import hybrid_ocr_reader
from backend.app.parser.structure_recovery_agent import structure_recovery_agent

def parse_pdf(file_path: str, media_dir: str = "uploads/media") -> Dict[str, Any]:
    """
    Parses a PDF file using HybridOCRReader and StructureRecoveryAgent.
    Applies dual-mode text extraction (native font stream + visual OCR), LaTeX math formula recovery,
    and automatic section hierarchy reconstruction.
    """
    os.makedirs(media_dir, exist_ok=True)
    
    # 1. Hybrid OCR & Math Recovery Reading
    doc_reading = hybrid_ocr_reader.read_document(file_path)

    # 2. Structure Recovery Agent (Section Hierarchy, Line Unwrapping & References Segmenter)
    recovered = structure_recovery_agent.recover_document_structure(doc_reading["pages"])

    layout_map = {
        "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0},
        "page_width": 8.5,
        "page_height": 11.0,
        "is_scanned_manuscript": doc_reading["is_scanned_manuscript"]
    }

    return {
        "sections": recovered["sections"],
        "references": recovered["references"],
        "layout_map": layout_map
    }

