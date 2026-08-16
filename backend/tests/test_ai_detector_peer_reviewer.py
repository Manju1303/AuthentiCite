import unittest
from backend.app.advisor.ai_detector_agent import ai_detector
from backend.app.advisor.peer_reviewer import peer_reviewer
from backend.app.quality.scholarly_metrics import scholarly_metrics
from backend.app.database import init_db, create_paper, add_sections, get_db_connection

class TestAIDetectorAndPeerReviewer(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_ai_detector_perplexity_burstiness(self):
        sample_text = (
            "Furthermore, it is important to note that neural network architectures play a pivotal role in modern NLP. "
            "Recent advancements demonstrate a paradigm shift in transformer optimization algorithms. "
            "However, human writers frequently vary sentence lengths dramatically for rhetorical emphasis and cognitive flow."
        )
        res = ai_detector.analyze_text(sample_text)
        self.assertIn("ai_probability", res)
        self.assertIn("perplexity_score", res)
        self.assertIn("burstiness_score", res)
        self.assertIn("classification", res)

    def test_scholarly_metrics_readability(self):
        sample_text = (
            "The empirical evaluation demonstrates statistical convergence across baseline benchmark datasets. "
            "The hypothesis was validated using non-parametric Wilcoxon signed-rank tests."
        )
        metrics = scholarly_metrics.analyze_readability_and_tone(sample_text)
        self.assertIn("coleman_liau_index", metrics)
        self.assertIn("flesch_kincaid_grade", metrics)
        self.assertIn("lexical_diversity_ttr", metrics)
        self.assertIn("passive_voice_ratio", metrics)

    def test_peer_reviewer_evaluation(self):
        paper_id = "test_peer_review_paper_88"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sections WHERE paper_id = ?", (paper_id,))
        cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
        conn.commit()
        conn.close()

        create_paper(paper_id, "quantum_edge_computing.pdf", "pdf")
        sections = [
            {
                "id": f"{paper_id}_abstract",
                "paper_id": paper_id,
                "section_name": "Abstract",
                "original_text": "This paper proposes a quantum consensus algorithm achieving 99.4% accuracy across distributed edge nodes.",
                "layout_metadata": {"type": "paragraph"}
            },
            {
                "id": f"{paper_id}_method",
                "paper_id": paper_id,
                "section_name": "Methodology",
                "original_text": "The quantum state vector is defined as $|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$ where $|\\alpha|^2 + |\\beta|^2 = 1$.",
                "layout_metadata": {"type": "paragraph"}
            }
        ]
        add_sections(sections)

        review = peer_reviewer.evaluate_paper(paper_id)
        self.assertEqual(review["paper_id"], paper_id)
        self.assertIn("q1_acceptability_score", review)
        self.assertIn("peer_review_decision", review)
        self.assertGreaterEqual(review["q1_acceptability_score"], 0.0)

if __name__ == "__main__":
    unittest.main()
