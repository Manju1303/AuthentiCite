import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.rag.hybrid_search import hybrid_search_engine
from backend.app.rag.rag_service import rag_service
from backend.app.database import init_db, create_paper, add_sections, get_db_connection

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_data():
    init_db()
    paper_id = "test_rag_paper_123"
    
    # Cleanup previous test data if present
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sections WHERE paper_id = ?", (paper_id,))
    cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
    conn.commit()
    conn.close()

    create_paper(paper_id, "sample_research_paper.pdf", "pdf")
    sections = [
        {
            "id": f"{paper_id}_sec1",
            "paper_id": paper_id,
            "section_name": "Abstract",
            "original_text": "This paper presents an advanced AI retrieval augmented generation model utilizing vector search and reranking.",
            "layout_metadata": {"type": "paragraph", "page_number": 1}
        },
        {
            "id": f"{paper_id}_sec2",
            "paper_id": paper_id,
            "section_name": "Methodology",
            "original_text": "We evaluate Qdrant hybrid search performance against classical BM25 text retrieval benchmarks.",
            "layout_metadata": {"type": "paragraph", "page_number": 2}
        }
    ]
    add_sections(sections)
    return paper_id

def test_hybrid_search_query():
    results = hybrid_search_engine.search(paper_id=None, query="Qdrant hybrid search vector", top_k=2)
    assert len(results) > 0
    assert "Qdrant" in results[0]["text"]

def test_rag_service_query(setup_test_data):
    res = rag_service.query_rag(query="What is the retrieval method used?", paper_id=setup_test_data)
    assert "query" in res
    assert "answer" in res
    assert "citations" in res
    assert len(res["citations"]) > 0

def test_rag_api_endpoint(setup_test_data):
    response = client.post("/api/v1/rag/query", json={
        "query": "vector search and reranking",
        "paper_id": setup_test_data
    })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["citations"]) > 0
