import math
import re
import json
import sqlite3
from typing import List, Dict, Any, Optional
from backend.app.config import settings
from backend.app.database import get_db_connection

class HybridSearchEngine:
    def __init__(self):
        self.qdrant_client = None
        self._init_qdrant()

    def _init_qdrant(self):
        if settings.QDRANT_URL:
            try:
                from qdrant_client import QdrantClient
                self.qdrant_client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
                )
                print("Qdrant Client connected successfully.")
            except Exception as e:
                print(f"Failed to connect to Qdrant, using SQLite fallback: {e}")

    def tokenize(self, text: str) -> List[str]:
        return [w for w in re.findall(r'\b\w+\b', text.lower()) if len(w) > 1]

    def compute_bm25_score(self, query_tokens: List[str], doc_tokens: List[str], avg_dl: float, k1: float = 1.5, b: float = 0.75) -> float:
        if not doc_tokens or not query_tokens:
            return 0.0
        
        doc_len = len(doc_tokens)
        score = 0.0
        doc_freqs = {}
        for w in doc_tokens:
            doc_freqs[w] = doc_freqs.get(w, 0) + 1

        for q in query_tokens:
            if q in doc_freqs:
                f = doc_freqs[q]
                numerator = f * (k1 + 1)
                denominator = f + k1 * (1 - b + b * (doc_len / (avg_dl or 1.0)))
                score += (numerator / denominator)
        return score

    def search(self, paper_id: Optional[str], query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        conn = get_db_connection()
        cursor = conn.cursor()

        if paper_id:
            cursor.execute("""
                SELECT id, paper_id, original_text, layout_metadata
                FROM sections
                WHERE paper_id = ?
            """, (paper_id,))
        else:
            cursor.execute("""
                SELECT id, paper_id, original_text, layout_metadata
                FROM sections
            """)

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        documents = []
        total_tokens = 0
        for r in rows:
            text = r["original_text"] or ""
            tokens = self.tokenize(text)
            meta = json.loads(r["layout_metadata"]) if r["layout_metadata"] else {}
            total_tokens += len(tokens)
            documents.append({
                "id": r["id"],
                "paper_id": r["paper_id"],
                "text": text,
                "tokens": tokens,
                "metadata": meta,
                "page_number": meta.get("page_number", 1)
            })

        avg_dl = total_tokens / len(documents) if documents else 1.0

        # Calculate hybrid score (BM25 + term coverage)
        scored_docs = []
        for doc in documents:
            bm25 = self.compute_bm25_score(query_tokens, doc["tokens"], avg_dl)
            match_count = sum(1 for q in query_tokens if q in doc["tokens"])
            coverage = match_count / len(query_tokens) if query_tokens else 0.0

            hybrid_score = round(bm25 * 0.7 + coverage * 0.3, 4)

            if hybrid_score > 0.0:
                scored_docs.append({
                    "id": doc["id"],
                    "paper_id": doc["paper_id"],
                    "text": doc["text"],
                    "score": hybrid_score,
                    "page_number": doc["page_number"],
                    "metadata": doc["metadata"]
                })

        # Sort by score descending
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:top_k]

hybrid_search_engine = HybridSearchEngine()
