import unittest
import asyncio
from backend.app.advisor.research_agent import AutonomousResearchAgent

class TestResearchAgent(unittest.TestCase):
    def setUp(self):
        self.agent = AutonomousResearchAgent()

    def test_format_citation_reference_numeric(self):
        paper = {
            "title": "Attention Is All You Need",
            "authors": ["A. Vaswani", "N. Shazeer", "N. Parmar"],
            "year": 2017,
            "venue": "NeurIPS",
            "doi": "10.5555/3295222.3295349"
        }
        ref = self.agent.format_citation_reference(paper, idx=1, style="numeric")
        self.assertIn("[1]", ref)
        self.assertIn("Vaswani et al.", ref)
        self.assertIn("2017", ref)

    def test_format_citation_reference_author_year(self):
        paper = {
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "authors": ["J. Devlin", "M. Chang"],
            "year": 2019,
            "venue": "NAACL",
            "doi": None
        }
        ref = self.agent.format_citation_reference(paper, idx=1, style="author_year")
        self.assertIn("Devlin", ref)
        self.assertIn("2019", ref)


    def test_literature_search_async(self):
        async def run_search():
            return await self.agent.search_literature("Deep Learning NLP", limit=3)
        
        results = asyncio.run(run_search())
        self.assertIsInstance(results, list)

    def test_synthesize_literature_review_async(self):
        async def run_synth():
            return await self.agent.synthesize_literature_review("Large Language Models")
        
        res = asyncio.run(run_synth())
        self.assertIn("literature_review_text", res)
        self.assertIn("references", res)
        self.assertGreater(len(res["references"]), 0)

if __name__ == "__main__":
    unittest.main()
