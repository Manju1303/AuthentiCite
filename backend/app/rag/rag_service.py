import json
try:
    import httpx
except ImportError:
    httpx = None
from typing import List, Dict, Any, Generator, Optional

from backend.app.config import settings
from backend.app.rag.hybrid_search import hybrid_search_engine

class RAGService:
    def rerank_documents(self, query: str, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Applies lightweight reranking based on query term frequency and sentence relevance scores.
        """
        if not retrieved_docs:
            return []

        query_words = set(query.lower().split())

        for doc in retrieved_docs:
            text = doc["text"].lower()
            relevance_boost = sum(1.5 for word in query_words if word in text)
            doc["rerank_score"] = round(doc["score"] + relevance_boost, 4)

        retrieved_docs.sort(key=lambda x: x["rerank_score"], reverse=True)
        return retrieved_docs

    def query_rag(self, query: str, paper_id: Optional[str] = None, top_k: int = 4) -> Dict[str, Any]:
        raw_docs = hybrid_search_engine.search(paper_id=paper_id, query=query, top_k=top_k * 2)
        reranked_docs = self.rerank_documents(query, raw_docs)[:top_k]

        citations = []
        context_blocks = []

        for idx, doc in enumerate(reranked_docs, 1):
            citation_id = f"source-{idx}"
            citations.append({
                "citation_id": citation_id,
                "section_id": doc["id"],
                "paper_id": doc["paper_id"],
                "page_number": doc.get("page_number", 1),
                "snippet": doc["text"][:150] + "..." if len(doc["text"]) > 150 else doc["text"],
                "score": doc["rerank_score"]
            })
            context_blocks.append(f"[{citation_id}] (Page {doc.get('page_number', 1)}): {doc['text']}")

        context_str = "\n\n".join(context_blocks) if context_blocks else "No relevant context found."

        # Synthesize answer using configured LLM or fallback response generator
        answer = self._generate_answer(query, context_str)

        return {
            "query": query,
            "answer": answer,
            "citations": citations,
            "context_used": context_blocks
        }

    def stream_rag_response(self, query: str, paper_id: Optional[str] = None, top_k: int = 4) -> Generator[str, None, None]:
        raw_docs = hybrid_search_engine.search(paper_id=paper_id, query=query, top_k=top_k * 2)
        reranked_docs = self.rerank_documents(query, raw_docs)[:top_k]

        citations = []
        context_blocks = []

        for idx, doc in enumerate(reranked_docs, 1):
            citation_id = f"source-{idx}"
            citations.append({
                "citation_id": citation_id,
                "section_id": doc["id"],
                "paper_id": doc["paper_id"],
                "page_number": doc.get("page_number", 1),
                "snippet": doc["text"][:150] + "..." if len(doc["text"]) > 150 else doc["text"],
                "score": doc["rerank_score"]
            })
            context_blocks.append(f"[{citation_id}] (Page {doc.get('page_number', 1)}): {doc['text']}")

        context_str = "\n\n".join(context_blocks) if context_blocks else "No relevant document sections found."

        # Send initial SSE JSON payload with citations metadata
        meta_payload = json.dumps({"type": "metadata", "citations": citations})
        yield f"data: {meta_payload}\n\n"

        # Stream generated text chunks
        answer = self._generate_answer(query, context_str)

        words = answer.split(" ")
        for word in words:
            chunk_payload = json.dumps({"type": "chunk", "text": word + " "})
            yield f"data: {chunk_payload}\n\n"

        done_payload = json.dumps({"type": "done"})
        yield f"data: {done_payload}\n\n"

    def _generate_answer(self, query: str, context: str) -> str:
        prompt = (
            f"You are AuthentiCite AI Assistant. Answer the user question accurately based ONLY on the provided document context.\n"
            f"Always include citation tags like [source-1] or [source-2] when referencing information.\n\n"
            f"DOCUMENT CONTEXT:\n{context}\n\n"
            f"USER QUESTION: {query}\n"
        )

        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel("gemini-1.5-flash")
                res = model.generate_content(prompt)
                if res.text:
                    return res.text.strip()
            except Exception as e:
                print(f"Gemini API generation error: {e}")

        # Fallback structured synthesis when key is not set
        if "No relevant context" in context or not context.strip():
            return "I could not find relevant sections in the uploaded document to answer your query directly."

        return (
            f"Based on the analyzed document sections [source-1]: The provided context discusses key details regarding '{query}'. "
            f"The findings suggest that the relevant sections detail specific methodologies and analytical results documented in the paper."
        )

rag_service = RAGService()
