"""
RAG Engine module for AuthentiCite.
Handles document OCR, Qdrant / SQLite hybrid vector search, cross-encoder reranking, and citation-backed streaming generation.
"""

from backend.app.rag.rag_service import rag_service
from backend.app.rag.ocr_parser import parse_document_ocr
from backend.app.rag.hybrid_search import hybrid_search_engine

__all__ = ["rag_service", "parse_document_ocr", "hybrid_search_engine"]
