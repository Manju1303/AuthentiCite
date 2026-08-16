import unittest
import asyncio
from backend.app.parser.hybrid_ocr_reader import hybrid_ocr_reader
from backend.app.parser.structure_recovery_agent import structure_recovery_agent
from backend.app.rewrite.academic_rewrite_enhancer import academic_rewrite_enhancer
from backend.app.rewrite.rewrite_engine import rewrite_text

class TestHybridOCRStructureRewrite(unittest.TestCase):
    def test_latex_math_recovery(self):
        raw_text = "The system state equation is x_1 = 4.2 + y_2"
        recovered = hybrid_ocr_reader.recover_latex_math(raw_text)
        self.assertIn("$", recovered)

    def test_structure_recovery_hyphenation_and_sections(self):
        hyphenated_text = "Modern artificial intelli-\ngence models require massive compute."
        unwrapped = structure_recovery_agent.unwrap_hyphenation_and_lines(hyphenated_text)
        self.assertIn("intelligence", unwrapped)
        self.assertNotIn("intelli-", unwrapped)

    def test_structure_recovery_reference_segmentation(self):
        ref_block = "[1] J. Smith, 'Neural Networks,' IEEE, 2021.\n[2] A. Jones, 'Deep Learning,' Springer, 2022."
        refs = structure_recovery_agent.segment_references(ref_block)
        self.assertEqual(len(refs), 2)
        self.assertEqual(refs[0]["citation_key"], "[1]")
        self.assertEqual(refs[1]["citation_key"], "[2]")

    def test_academic_rewrite_enhancer_shielding(self):
        text_with_math_and_cites = "As demonstrated in [1] and (Smith, 2021), the energy relation $E = mc^2$ governs relativistic dynamics."
        shielded, mask_map = academic_rewrite_enhancer.shield_latex_and_citations(text_with_math_and_cites)
        
        self.assertIn("__MATH_SHIELD_", shielded)
        self.assertIn("__CITE_SHIELD_", shielded)
        self.assertNotIn("$E = mc^2$", shielded)
        self.assertNotIn("[1]", shielded)

        unshielded = academic_rewrite_enhancer.unshield_latex_and_citations(shielded, mask_map)
        self.assertEqual(unshielded, text_with_math_and_cites)

    def test_async_rewrite_with_shielding(self):
        async def run_shielded_rewrite():
            text = "Equation $y = mx + b$ is cited in [1]."
            return await rewrite_text(text)

        result = asyncio.run(run_shielded_rewrite())
        self.assertIn("$y = mx + b$", result)
        self.assertIn("[1]", result)

if __name__ == "__main__":
    unittest.main()
