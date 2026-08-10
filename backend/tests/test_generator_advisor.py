import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db, create_paper, add_sections, get_db_connection
from backend.app.generator.paper_generator import generate_full_paper
from backend.app.advisor.plagiarism_advisor import generate_reduction_advice

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_paper_generation_service():
    res = generate_full_paper(topic="Blockchain Consensus Protocols in Edge Devices", journal_tier="q1_ieee")
    assert "paper_id" in res
    assert "title" in res
    assert res["sections_count"] > 0
    assert res["references_count"] > 0

def test_plagiarism_advisor_service():
    paper_id = "test_advisor_paper_999"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sections WHERE paper_id = ?", (paper_id,))
    cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
    conn.commit()
    conn.close()

    create_paper(paper_id, "high_similarity_paper.pdf", "pdf")
    sections = [
        {
            "id": f"{paper_id}_sec1",
            "paper_id": paper_id,
            "section_name": "Background",
            "original_text": "Neural network optimization relies heavily on stochastic gradient descent and adaptive learning rates.",
            "similarity_score": 0.45,
            "is_flagged": True,
            "layout_metadata": {"type": "paragraph", "similarity_source": {"filename": "source1.pdf", "score": 0.45}}
        }
    ]
    add_sections(sections)

    advice = generate_reduction_advice(paper_id)
    assert advice["paper_id"] == paper_id
    assert advice["flagged_count"] == 1
    assert len(advice["recommendations"]) == 1
    assert advice["recommendations"][0]["similarity_score"] == 45.0

def test_paper_generator_api_endpoint():
    resp = client.post("/api/v1/generator/generate", json={
        "topic": "Quantum Computing Cryptographic Resilience",
        "journal_tier": "q1_ieee"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "paper_id" in data
    assert "Quantum" in data["title"]
