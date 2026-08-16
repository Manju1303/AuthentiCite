import re
import math
from typing import Dict, Any, List

class ScholarlyMetricsAnalyzer:
    """
    Computes academic readability, lexical diversity, passive voice ratio,
    and formal vocabulary metrics for manuscript quality evaluation.
    """

    PASSIVE_PATTERNS = [
        r'\b(?:is|are|was|were|be|been|being)\s+(?:\w+ed|\w+en)\b',
        r'\bhas\s+been\s+\w+ed\b',
        r'\bhave\s+been\s+\w+ed\b',
        r'\bwas\s+observed\b',
        r'\bwere\b\s+conducted\b'
    ]

    ACADEMIC_VOCAB = set([
        "demonstrate", "evaluates", "formulate", "empirical", "methodology",
        "hypothesize", "quantify", "synthesize", "validation", "benchmark",
        "paradigm", "optimization", "robustness", "statistically", "subsequent",
        "underlying", "systematic", "corroborate", "inherent", "convergence"
    ])

    @staticmethod
    def count_syllables(word: str) -> int:
        """Estimates syllable count in a word."""
        word = word.lower()
        if len(word) <= 3:
            return 1
        word = re.sub(r'(?:[^laeiouy]|ed|es|e)$', '', word)
        word = re.sub(r'^y', '', word)
        syllables = len(re.findall(r'[aeiouy]{1,2}', word))
        return max(1, syllables)

    def analyze_readability_and_tone(self, text: str) -> Dict[str, Any]:
        """Calculates Coleman-Liau Index, Flesch-Kincaid Grade, Lexical Diversity, and Passive Voice Ratio."""
        words = [w for w in re.findall(r'\b[a-zA-Z]+\b', text)]
        sentences = [s for s in re.split(r'(?<=[.!?])\s+', text.strip()) if len(s.strip()) > 0]

        if not words or not sentences:
            return {
                "coleman_liau_index": 12.0,
                "flesch_kincaid_grade": 12.0,
                "lexical_diversity_ttr": 0.5,
                "passive_voice_ratio": 20.0,
                "academic_vocabulary_score": 75.0,
                "readability_label": "Graduate Academic Level"
            }

        num_words = len(words)
        num_sentences = len(sentences)
        num_letters = sum(len(w) for w in words)
        num_syllables = sum(self.count_syllables(w) for w in words)

        # Coleman-Liau Index
        L = (num_letters / num_words) * 100
        S = (num_sentences / num_words) * 100
        coleman_liau = round(0.0588 * L - 0.296 * S - 15.8, 1)

        # Flesch-Kincaid Grade Level
        fk_grade = round(0.39 * (num_words / num_sentences) + 11.8 * (num_syllables / num_words) - 15.59, 1)

        # Lexical Diversity (Type-Token Ratio TTR)
        unique_words = set(w.lower() for w in words)
        ttr = round(len(unique_words) / num_words, 3)

        # Passive Voice Ratio
        passive_matches = 0
        for s in sentences:
            if any(re.search(pat, s, re.IGNORECASE) for pat in self.PASSIVE_PATTERNS):
                passive_matches += 1

        passive_ratio = round((passive_matches / num_sentences) * 100, 1)

        # Academic Vocabulary Ratio
        acad_words_found = [w.lower() for w in words if w.lower() in self.ACADEMIC_VOCAB]
        acad_score = round(min((len(acad_words_found) / num_words) * 1000, 100.0), 1)

        return {
            "coleman_liau_index": coleman_liau,
            "flesch_kincaid_grade": fk_grade,
            "lexical_diversity_ttr": ttr,
            "passive_voice_ratio": passive_ratio,
            "academic_vocabulary_score": acad_score,
            "readability_label": "Post-Graduate / Professional Journal Level" if coleman_liau >= 14 else "College Academic Level"
        }


# Global instance
scholarly_metrics = ScholarlyMetricsAnalyzer()
