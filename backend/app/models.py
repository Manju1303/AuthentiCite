from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class PaperBase(BaseModel):
    filename: str
    original_format: str

class PaperCreate(PaperBase):
    pass

class PaperResponse(PaperBase):
    id: str
    status: str
    overall_similarity: float
    created_at: str

    model_config = ConfigDict(from_attributes=True)

class SectionResponse(BaseModel):
    id: str
    paper_id: str
    section_name: Optional[str] = None
    original_text: str
    rewritten_text: Optional[str] = None
    similarity_score: float
    is_flagged: bool
    layout_metadata: Dict[str, Any]

class ReferenceResponse(BaseModel):
    id: str
    paper_id: str
    raw_reference: str
    citation_key: Optional[str] = None

class SectionRewriteRequest(BaseModel):
    rewritten_text: str

class PaperRewriteRequest(BaseModel):
    target_similarity: Optional[float] = 0.15
    journal_format: Optional[str] = "original" # original, ieee, springer

class PaperAnalysisResponse(BaseModel):
    paper: PaperResponse
    sections: List[SectionResponse]
    references: List[ReferenceResponse]
