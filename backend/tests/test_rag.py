import unittest
from backend.app.rag.hybrid_search import hybrid_search_engine
from backend.app.rag.rag_service import rag_service
from backend.app.database import init_db, create_paper, add_sections, get_db_connection

class TestRAG(unittest.TestCase):
    def setUp(self):
        init_db()
        self.paper_id = "test_rag_paper_123"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sections WHERE paper_id = ?", (self.paper_id,))
        cursor.execute("DELETE FROM papers WHERE id = ?", (self.paper_id,))
        conn.commit()
        conn.close()

        create_paper(self.paper_id, "sample_research_paper.pdf", "pdf")
        sections = [
            {
                "id": f"{self.paper_id}_sec1",
                "paper_id": self.paper_id,
                "section_name": "Abstract",
                "original_text": "This paper presents an advanced AI retrieval augmented generation model utilizing vector search and reranking.",
                "layout_metadata": {"type": "paragraph", "page_number": 1}
            },
            {
                "id": f"{self.paper_id}_sec2",
                "paper_id": self.paper_id,
                "section_name": "Methodology",
                "original_text": "We evaluate Qdrant hybrid search performance against classical BM25 text retrieval benchmarks.",
                "layout_metadata": {"type": "paragraph", "page_number": 2}
            }
        ]
        add_sections(sections)

    def test_hybrid_search_query(self):
        results = hybrid_search_engine.search(paper_id=None, query="Qdrant hybrid search vector", top_k=2)
        self.assertGreater(len(results), 0)
        self.assertIn("Qdrant", results[0]["text"])

    def test_rag_service_query(self):
        res = rag_service.query_rag(query="What is the retrieval method used?", paper_id=self.paper_id)
        self.assertIn("query", res)
        self.assertIn("answer", res)
        self.assertIn("citations", res)
        self.assertGreater(len(res["citations"]), 0)

if __name__ == "__main__":
    unittest.main()
