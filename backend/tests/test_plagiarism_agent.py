import unittest
from backend.app.advisor.plagiarism_agent import PlagiarismDetectionAgent

class TestPlagiarismAgent(unittest.TestCase):
    def setUp(self):
        self.agent = PlagiarismDetectionAgent(use_neural=False)

    def test_exact_match_detection(self):
        text1 = "Deep neural networks have revolutionized natural language processing and computer vision applications."
        text2 = "Deep neural networks have revolutionized natural language processing and computer vision applications."
        
        res = self.agent.analyze_pair(text1, text2)
        self.assertGreaterEqual(res["composite_score"], 0.70)
        self.assertEqual(res["risk_level"], "HIGH")
        self.assertIn("Exact Copy", res["risk_category"])

    def test_paraphrase_detection(self):
        text1 = "The quick brown fox jumps over the lazy dog."
        text2 = "A fast brown fox leaps over a sleepy canine."
        
        res = self.agent.analyze_pair(text1, text2)
        self.assertGreaterEqual(res["composite_score"], 0.20)
        self.assertTrue("matched_spans" in res)

    def test_distinct_content_detection(self):
        text1 = "Quantum computing relies on qubits and superposition."
        text2 = "Organic farming avoids synthetic pesticides and chemical fertilizers."
        
        res = self.agent.analyze_pair(text1, text2)
        self.assertLess(res["composite_score"], 0.25)
        self.assertEqual(res["risk_level"], "LOW")

    def test_ngram_fingerprinting(self):
        text1 = "Machine learning models require clean datasets for optimal performance."
        text2 = "Clean datasets are essential for training machine learning models."
        
        lex = self.agent.compute_ngram_jaccard(text1, text2)
        self.assertIn("lexical_score", lex)
        self.assertGreaterEqual(lex["word_ngram_jaccard"], 0.0)

if __name__ == "__main__":
    unittest.main()
