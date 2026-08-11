import re
import httpx
from typing import Dict, Any, List, Optional

def clean_citation_string(raw_ref: str) -> str:
    """
    Cleans up citation strings by removing bracketed/numeric prefixes (e.g., [1], 1., etc.)
    """
    cleaned = raw_ref.strip()
    # Remove prefix like [12], [1], 1., 12.
    cleaned = re.sub(r"^\[\d+\]\s*", "", cleaned)
    cleaned = re.sub(r"^\d+\.\s*", "", cleaned)
    return cleaned.strip()

def format_author_name_numeric(name: str) -> str:
    """
    Formats "John Smith" or "Smith, John" to "J. Smith"
    """
    parts = [p.strip() for p in re.split(r"[\s,]+", name) if p.strip()]
    if not parts:
        return name
    if "," in name:
        # e.g., "Smith, John" -> parts = ["Smith", "John"]
        last = parts[0]
        first = parts[1] if len(parts) > 1 else ""
    else:
        # e.g., "John Smith" -> parts = ["John", "Smith"]
        first = parts[0]
        last = parts[-1] if len(parts) > 1 else parts[0]
        
    initial = f"{first[0]}." if first else ""
    return f"{initial} {last}".strip()

def format_author_name_author_year(name: str) -> str:
    """
    Formats "John Smith" or "Smith, John" to "Smith, J."
    """
    parts = [p.strip() for p in re.split(r"[\s,]+", name) if p.strip()]
    if not parts:
        return name
    if "," in name:
        last = parts[0]
        first = parts[1] if len(parts) > 1 else ""
    else:
        first = parts[0]
        last = parts[-1] if len(parts) > 1 else parts[0]
        
    initial = f"{first[0]}." if first else ""
    return f"{last}, {initial}".strip()

def format_citation(metadata: Dict[str, Any], style: str = "numeric", citation_idx: int = 1) -> str:
    """
    Formats parsed Semantic Scholar metadata into IEEE (numeric) or Harvard (author-year) style.
    """
    title = metadata.get("title", "").strip().rstrip(".")
    year = metadata.get("year") or "n.d."
    venue = metadata.get("venue", "").strip() or "Academic Press"
    doi = metadata.get("externalIds", {}).get("DOI", "")
    authors_raw = metadata.get("authors", [])
    
    author_names = [a.get("name", "") for a in authors_raw if a.get("name")]
    
    if style == "numeric":
        # IEEE Style: [1] J. Smith and A. Jones, "Title of paper," Venue, vol. x, pp. y-z, Year.
        if not author_names:
            authors_str = "Anon."
        elif len(author_names) > 3:
            authors_str = f"{format_author_name_numeric(author_names[0])} et al."
        elif len(author_names) == 1:
            authors_str = format_author_name_numeric(author_names[0])
        else:
            formatted = [format_author_name_numeric(name) for name in author_names]
            authors_str = ", ".join(formatted[:-1]) + " and " + formatted[-1]
            
        citation_text = f"[{citation_idx}] {authors_str}, \"{title},\" *{venue}*, {year}."
        if doi:
            citation_text += f" DOI: {doi}"
            
    else:
        # Harvard / Author-Year Style: Smith, J., & Jones, A. (Year). Title of paper. Venue.
        if not author_names:
            authors_str = "Anon"
        elif len(author_names) > 3:
            authors_str = f"{format_author_name_author_year(author_names[0])} et al."
        elif len(author_names) == 1:
            authors_str = format_author_name_author_year(author_names[0])
        else:
            formatted = [format_author_name_author_year(name) for name in author_names]
            authors_str = ", ".join(formatted[:-1]) + ", & " + formatted[-1]
            
        citation_text = f"{authors_str} ({year}). {title}. *{venue}*."
        if doi:
            citation_text += f" https://doi.org/{doi}"
            
    return citation_text

from backend.app.config import settings

async def resolve_and_format_citation(
    raw_reference: str, 
    style: str = "numeric", 
    citation_idx: int = 1
) -> Dict[str, Any]:
    """
    Cleans raw reference string, queries Semantic Scholar, extracts metadata,
    and returns a structured dict including the formatted citation text.
    """
    cleaned_query = clean_citation_string(raw_reference)
    
    # Return original if query is empty or too short to be useful
    if len(cleaned_query) < 5:
        return {
            "resolved": False,
            "formatted_reference": raw_reference,
            "doi": None,
            "title": None,
            "citation_count": 0,
            "abstract": None
        }
        
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": cleaned_query,
        "limit": 1,
        "fields": "title,authors,year,venue,externalIds,citationCount,abstract"
    }
    
    headers = {}
    if getattr(settings, "SEMANTIC_SCHOLAR_API_KEY", ""):
        headers["x-api-key"] = settings.SEMANTIC_SCHOLAR_API_KEY
        
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=12.0)
            if response.status_code == 200:
                data = response.json()
                results = data.get("data", [])
                if results:
                    match = results[0]
                    formatted_ref = format_citation(match, style=style, citation_idx=citation_idx)
                    return {
                        "resolved": True,
                        "formatted_reference": formatted_ref,
                        "doi": match.get("externalIds", {}).get("DOI"),
                        "title": match.get("title"),
                        "citation_count": match.get("citationCount", 0),
                        "abstract": match.get("abstract")
                    }
            elif response.status_code == 429:
                print("Semantic Scholar rate limit hit (429). Please configure SEMANTIC_SCHOLAR_API_KEY to increase limits.")
        except Exception as e:
            print(f"Failed to resolve citation online: {e}")
            
    # Fallback to the original raw reference
    return {
        "resolved": False,
        "formatted_reference": raw_reference,
        "doi": None,
        "title": None,
        "citation_count": 0,
        "abstract": None
    }
