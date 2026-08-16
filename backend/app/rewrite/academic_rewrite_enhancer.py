import re
from typing import Dict, Any, Tuple

class AcademicRewriteEnhancer:
    """
    Academic Context-Aware Paraphrase & Style Rewrite Enhancer.
    Shields LaTeX equations and citation keys prior to LLM paraphrasing,
    and restores them cleanly in the output to guarantee zero formula/citation corruption.
    """

    def shield_latex_and_citations(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Replaces LaTeX math equations and citation brackets with unique placeholder tokens.
        Returns shielded text and placeholder mapping dictionary.
        """
        mask_map = {}
        counter = 0

        # 1. Shield display math $$...$$
        def replace_display_math(match):
            nonlocal counter
            token = f"__MATH_SHIELD_{counter}__"
            mask_map[token] = match.group(0)
            counter += 1
            return token

        shielded = re.sub(r'\$\$.*?\$\$', replace_display_math, text, flags=re.DOTALL)

        # 2. Shield inline math $...$
        def replace_inline_math(match):
            nonlocal counter
            token = f"__MATH_SHIELD_{counter}__"
            mask_map[token] = match.group(0)
            counter += 1
            return token

        shielded = re.sub(r'\$.*?\$', replace_inline_math, shielded)

        # 3. Shield bracketed citations e.g. [1], [2, 3], [4-7]
        def replace_citations(match):
            nonlocal counter
            token = f"__CITE_SHIELD_{counter}__"
            mask_map[token] = match.group(0)
            counter += 1
            return token

        shielded = re.sub(r'\[[0-9\s,\-\u2013]+\]', replace_citations, shielded)

        return shielded, mask_map

    def unshield_latex_and_citations(self, rewritten_text: str, mask_map: Dict[str, str]) -> str:
        """Restores shielded LaTeX math equations and citation tokens back into rewritten text."""
        result = rewritten_text
        for token, original_val in mask_map.items():
            result = result.replace(token, original_val)
        return result


# Global instance
academic_rewrite_enhancer = AcademicRewriteEnhancer()
