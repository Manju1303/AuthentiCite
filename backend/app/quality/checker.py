import re
from typing import List, Dict, Any

def extract_citations(text: str) -> List[str]:
    """
    Extracts citation hooks from text.
    Handles numeric citations [1], [1, 2], [3-5] and author-year citations (Smith et al., 2020).
    """
    citations = []
    # 1. Bracketed citations: [1], [2, 3], [4-7]
    bracketed = re.findall(r'\[[0-9\s,\-\u2013]+\]', text)
    citations.extend(bracketed)
    
    # 2. Parenthetical author-year: (Smith, 2020), (Jones et al., 2019)
    # Match strings containing capital letter name followed by year
    author_year = re.findall(r'\([A-Z][a-zA-Z\s\.]+\bet\sal\.\,\s\d{4}\)|\([A-Z][a-zA-Z\s\.]+\,\s\d{4}\)', text)
    citations.extend(author_year)
    
    return list(set(citations))

def extract_equations(text: str) -> List[str]:
    """Extracts LaTeX math formulas ($...$ or $$...$$)."""
    # Double dollar $$...$$
    display_math = re.findall(r'\$\$.*?\$\$', text)
    # Single dollar $...$
    inline_math = re.findall(r'\$.*?\$', text)
    
    return list(set(display_math + inline_math))

from backend.app.quality.scholarly_metrics import scholarly_metrics

def check_academic_quality(original: str, rewritten: str) -> Dict[str, Any]:
    """
    Validates rewritten academic text against the original.
    Checks for missing citations, equations, numerical consistency, informal vocabulary,
    and calculates scholarly readability & tone metrics.
    """
    warnings = []
    
    # 1. Check citations
    orig_cits = extract_citations(original)
    rewr_cits = extract_citations(rewritten)
    
    missing_cits = [c for c in orig_cits if c not in rewritten]
    if missing_cits:
        warnings.append(f"Missing citation markers: {', '.join(missing_cits)}")
        
    # 2. Check equations
    orig_eqs = extract_equations(original)
    rewr_eqs = extract_equations(rewritten)
    
    missing_eqs = [e for e in orig_eqs if e not in rewritten]
    if missing_eqs:
        warnings.append(f"Missing or modified mathematical formula: {', '.join(missing_eqs)}")
        
    # 3. Numerical consistency check
    orig_nums = re.findall(r'\b\d+(?:\.\d+)?\b', original)
    rewr_nums = re.findall(r'\b\d+(?:\.\d+)?\b', rewritten)
    
    missing_nums = [n for n in orig_nums if n not in rewr_nums]
    if missing_nums:
        warnings.append(f"Potential numerical mismatch. Numbers from original missing in rewrite: {', '.join(set(missing_nums))}")
        
    # 4. Informal word detection
    informal_words = ['really', 'huge', 'awesome', 'nice', 'bad', 'good', 'kind of', 'sort of', 'massive', 'giant']
    found_informal = [w for w in informal_words if re.search(r'\b' + w + r'\b', rewritten.lower())]
    if found_informal:
        warnings.append(f"Avoid informal vocabulary: {', '.join(found_informal)}")

    # 5. Scholarly Readability & Tone Analysis
    scholarly_analysis = scholarly_metrics.analyze_readability_and_tone(rewritten)
        
    is_valid = len(warnings) == 0
    
    return {
        "is_valid": is_valid,
        "warnings": warnings,
        "original_citations_count": len(orig_cits),
        "rewritten_citations_count": len(rewr_cits),
        "original_equations_count": len(orig_eqs),
        "rewritten_equations_count": len(rewr_eqs),
        "scholarly_metrics": scholarly_analysis
    }

