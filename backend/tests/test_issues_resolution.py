import unittest
import asyncio
from backend.app.database import with_db_retry, get_db_connection
from backend.app.rewrite.rewrite_engine import rewrite_text
from backend.app.similarity.analyzer import analyze_paper_similarity

class TestIssuesResolution(unittest.TestCase):
    def test_database_retry_decorator(self):
        call_count = 0
        @with_db_retry(max_retries=3, delay=0.01)
        def mock_db_func():
            nonlocal call_count
            call_count += 1
            return "SUCCESS"

        result = mock_db_func()
        self.assertEqual(result, "SUCCESS")
        self.assertEqual(call_count, 1)

    def test_async_rewrite_engine_fallback(self):
        async def run_rewrite():
            return await rewrite_text("Test paragraph for academic editing.")
        
        result = asyncio.run(run_rewrite())
        self.assertIsInstance(result, str)

    def test_heading_filter_similarity(self):
        header_section = [{
            "id": "sec_header",
            "original_text": "II. LITERATURE REVIEW",
            "layout_metadata": {"type": "paragraph"}
        }]
        res = analyze_paper_similarity("dummy_paper", header_section)
        self.assertFalse(res["sections"][0]["is_flagged"])

if __name__ == "__main__":
    unittest.main()
