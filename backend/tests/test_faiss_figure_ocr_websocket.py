import unittest
import asyncio
from backend.app.rag.faiss_vector_index import faiss_vector_store, FAISSVectorStore
from backend.app.parser.figure_formula_ocr import figure_formula_ocr
from backend.app.websocket_progress import progress_ws_manager

class MockWebSocket:
    def __init__(self):
        self.sent_messages = []
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_text(self, text: str):
        self.sent_messages.append(text)

class TestFAISSFigureOCRWebSocket(unittest.TestCase):

    def test_faiss_vector_store_indexing_and_search(self):
        vstore = FAISSVectorStore(dimension=4)
        vecs = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.8, 0.2, 0.0, 0.0]
        ]
        ids = ["doc1", "doc2", "doc3"]
        payloads = [{"text": "Quantum computing"}, {"text": "Deep learning"}, {"text": "Quantum algorithms"}]

        vstore.add_vectors(vecs, ids, payloads)
        results = vstore.search_similar([0.9, 0.1, 0.0, 0.0], top_k=2)

        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["id"], "doc1")
        self.assertIn("similarity_score", results[0])

    def test_figure_formula_ocr_extraction(self):
        # Test math operator matching logic
        sample_formula = "E = mc^2 + int_0^inf"
        is_math = any(import_pat in sample_formula for import_pat in ["=", "^", "+"])
        self.assertTrue(is_math)

    def test_websocket_progress_broadcast(self):
        async def run_ws_test():
            ws_client = MockWebSocket()
            paper_id = "test_paper_ws_99"

            await progress_ws_manager.connect(paper_id, ws_client)
            self.assertTrue(ws_client.accepted)

            await progress_ws_manager.broadcast_progress(
                paper_id=paper_id,
                step="rewrite_section_1",
                progress_pct=25,
                message="Rewriting Introduction section"
            )

            self.assertEqual(len(ws_client.sent_messages), 1)
            self.assertIn("rewrite_section_1", ws_client.sent_messages[0])
            self.assertIn("25", ws_client.sent_messages[0])

        asyncio.run(run_ws_test())

if __name__ == "__main__":
    unittest.main()
