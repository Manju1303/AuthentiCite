import re
import math
from typing import List, Dict, Any

class AIDetectionAgent:
    """
    AI Content & Perplexity/Burstiness Detector Agent.
    Analyzes text readability entropy, vocabulary predictability (Perplexity),
    and sentence length variance (Burstiness) to estimate AI vs Human probability.
    """

    # Academic & common AI marker transition phrases
    AI_TRANSITION_MARKERS = [
        "furthermore", "moreover", "in conclusion", "it is important to note",
        "delve into", "tapestry", "testament to", "pivotal role", "game-changer",
        "beacon of", "underscores the", "interplay", "synergy", "holistic approach",
        "seamless integration", "paradigm shift", "rapidly evolving", "cutting-edge"
    ]

    @staticmethod
    def _clean_sentences(text: str) -> List[str]:
        """Splits text into clean non-empty sentences."""
        raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in raw_sentences if len(s.strip().split()) >= 3]

    def compute_perplexity_proxy(self, text: str) -> float:
        """
        Computes a statistical proxy for Perplexity based on vocabulary entropy,
        unique word ratio, and word length variance.
        Human text has higher entropy; AI text tends to have smoother, lower entropy distributions.
        """
        words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{2,}\b', text)]
        if not words:
            return 50.0

        total_words = len(words)
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1

        # Calculate Shannon entropy over word distribution
        entropy = 0.0
        for count in freq.values():
            p = count / total_words
            entropy -= p * math.log2(p)

        # Scale entropy to a perplexity proxy score (range 10 to 100)
        max_possible_entropy = math.log2(total_words) if total_words > 1 else 1.0
        normalized_entropy = entropy / max_possible_entropy if max_possible_entropy > 0 else 0.5

        perplexity_score = round(normalized_entropy * 100, 2)
        return min(max(perplexity_score, 10.0), 100.0)

    def compute_burstiness(self, text: str) -> float:
        """
        Computes Burstiness (variance of sentence lengths).
        Human writing exhibits high burstiness (mixing short punchy sentences with complex long ones).
        AI text exhibits low burstiness (uniform sentence lengths around 15-25 words).
        """
        sentences = self._clean_sentences(text)
        if len(sentences) < 2:
            return 50.0

        lengths = [len(s.split()) for s in sentences]
        mean_len = sum(lengths) / len(lengths)

        if mean_len == 0:
            return 50.0

        variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
        std_dev = math.sqrt(variance)

        # Coefficient of variation (Burstiness metric)
        burstiness_ratio = (std_dev / mean_len) if mean_len > 0 else 0.0
        # Convert ratio to a 0-100 score (higher burstiness = more human-like)
        burstiness_score = round(min(burstiness_ratio * 100, 100.0), 2)
        return burstiness_score

    def detect_ai_markers(self, text: str) -> List[str]:
        """Detects presence of frequent AI-generated transition cliches."""
        lowered = text.lower()
        found = [marker for marker in self.AI_TRANSITION_MARKERS if marker in lowered]
        return found

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Executes full AI content detection audit on text.
        Returns AI probability score, Perplexity, Burstiness, and risk sentence highlights.
        """
        sentences = self._clean_sentences(text)
        if not sentences or len(text.split()) < 15:
            return {
                "ai_probability": 0.0,
                "classification": "Human-Written / Insufficient Sample",
                "risk_level": "LOW",
                "perplexity_score": 80.0,
                "burstiness_score": 80.0,
                "ai_markers_found": [],
                "flagged_sentences": []
            }

        perplexity = self.compute_perplexity_proxy(text)
        burstiness = self.compute_burstiness(text)
        markers = self.detect_ai_markers(text)

        # AI Probability Composite Formula:
        # Low Perplexity (<55) + Low Burstiness (<35) + AI Markers increases AI probability
        ai_prob = 50.0

        # Adjust based on perplexity (lower perplexity = higher AI probability)
        if perplexity < 45.0:
            ai_prob += 25.0
        elif perplexity < 60.0:
            ai_prob += 10.0
        else:
            ai_prob -= 15.0

        # Adjust based on burstiness (lower burstiness = higher AI probability)
        if burstiness < 30.0:
            ai_prob += 25.0
        elif burstiness < 45.0:
            ai_prob += 10.0
        else:
            ai_prob -= 15.0

        # Adjust for AI marker phrase frequency
        ai_prob += len(markers) * 8.0

        ai_probability = round(min(max(ai_prob, 5.0), 95.0), 1)

        if ai_probability >= 70.0:
            classification = "Likely AI-Generated Content"
            risk_level = "HIGH"
        elif ai_probability >= 45.0:
            classification = "Hybrid / AI-Assisted Text"
            risk_level = "MEDIUM"
        else:
            classification = "Human-Written Content"
            risk_level = "LOW"

        # Flag sentences with uniform length and AI markers
        flagged = []
        for s in sentences:
            s_len = len(s.split())
            contains_marker = any(m in s.lower() for m in markers)
            if (18 <= s_len <= 24 and burstiness < 40.0) or contains_marker:
                flagged.append({
                    "sentence": s[:120] + "..." if len(s) > 120 else s,
                    "reason": "Uniform sentence length / AI cliché phrase detected" if contains_marker else "Low variance length pattern"
                })

        return {
            "ai_probability": ai_probability,
            "classification": classification,
            "risk_level": risk_level,
            "perplexity_score": perplexity,
            "burstiness_score": burstiness,
            "ai_markers_found": markers,
            "flagged_sentences_count": len(flagged),
            "flagged_sentences": flagged[:5]
        }


# Global detector singleton
ai_detector = AIDetectionAgent()
