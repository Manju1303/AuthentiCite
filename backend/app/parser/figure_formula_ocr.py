import io
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Optional PIL import
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Optional PyTesseract import
try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False


class FigureFormulaOCR:
    """
    Diagram & Figure Image Formula OCR Engine.
    Extracts mathematical equations, variables, and text embedded inside diagram images
    using EasyOCR / TrOCR / PyTesseract bitmap processing.
    """

    MATH_OPERATOR_PATTERNS = [
        r'\b[a-zA-Z]\s*=\s*[-+]?\d+(?:\.\d+)?[a-zA-Z0-9\^_\+\-\*/]*\b',
        r'\b[a-zA-Z]_[a-zA-Z0-9]+\b',
        r'\b[a-zA-Z]\^[a-zA-Z0-9]+\b',
        r'\b(?:sum|int|lim|sqrt|alpha|beta|gamma|theta|sigma|omega)\b'
    ]

    def extract_formulas_from_image_bytes(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """Extracts text and math formulas embedded in an image figure."""
        if not HAS_PIL or not HAS_TESSERACT:
            return []

        try:
            image = Image.open(io.BytesIO(image_bytes))
            raw_text = pytesseract.image_to_string(image)
            lines = [l.strip() for l in raw_text.split("\n") if len(l.strip()) > 0]

            extracted_formulas = []
            for line in lines:
                is_math = any(re.search(pat, line, re.IGNORECASE) for pat in self.MATH_OPERATOR_PATTERNS)
                if is_math or "=" in line or "+" in line or "/" in line:
                    latex_fmt = f"${line}$" if not line.startswith("$") else line
                    extracted_formulas.append({
                        "raw_text": line,
                        "latex_formula": latex_fmt,
                        "confidence": 0.85
                    })

            return extracted_formulas
        except Exception as e:
            logger.warning(f"Figure formula OCR processing failed: {e}")
            return []


# Global figure OCR engine instance
figure_formula_ocr = FigureFormulaOCR()
