import unittest
from backend.app.database import init_db, create_paper, add_sections, get_db_connection
from backend.app.generator.paper_generator import generate_full_paper
from backend.app.advisor.plagiarism_advisor import generate_reduction_advice

class TestGeneratorAdvisor(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_paper_generation_service(self):
        res = generate_full_paper(topic="Blockchain Consensus Protocols in Edge Devices", journal_tier="q1_ieee")
        self.assertIn("paper_id", res)
        self.assertIn("title", res)
        self.assertGreater(res["sections_count"], 0)
        self.assertGreater(res["references_count"], 0)

    def test_plagiarism_advisor_service(self):
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
        self.assertEqual(advice["paper_id"], paper_id)
        self.assertEqual(advice["flagged_count"], 1)
        self.assertEqual(len(advice["recommendations"]), 1)
        self.assertEqual(advice["recommendations"][0]["similarity_score"], 45.0)

if __name__ == "__main__":
    unittest.main()
