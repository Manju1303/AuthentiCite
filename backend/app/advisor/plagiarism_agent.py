import re
import math
import logging
from typing import List, Dict, Any, Set, Optional

logger = logging.getLogger(__name__)

# Lazy model loader for SentenceTransformer to optimize startup time
_SBERT_MODEL = None
_SBERT_INITIALIZED = False

def get_sbert_model():
    """
    Lazy loads the SentenceTransformer trained model ('all-MiniLM-L6-v2').
    Returns None if sentence_transformers is not installed or fails to initialize.
    """
    global _SBERT_MODEL, _SBERT_INITIALIZED
    if not _SBERT_INITIALIZED:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading pre-trained SentenceTransformer model 'all-MiniLM-L6-v2'...")
            _SBERT_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ('all-MiniLM-L6-v2'): {e}. Falling back to lexical/TF-IDF similarity.")
            _SBERT_MODEL = None
        _SBERT_INITIALIZED = True
    return _SBERT_MODEL


class PlagiarismDetectionAgent:
    """
    Multi-Stage Plagiarism & Paraphrase Detection Agent.
    Combines:
    1. Lexical N-Gram Fingerprinting (Sherlock/Moss Jaccard algorithm for verbatim matches)
    2. Sparse TF-IDF Keyword Cosine Similarity
    3. Dense Neural Transformer Embeddings (SBERT 'all-MiniLM-L6-v2' for paraphrased plagiarism)
    """

    def __init__(self, use_neural: bool = True):
        self.use_neural = use_neural
        self.model = get_sbert_model() if use_neural else None

    # --- 1. Lexical N-Gram Fingerprinting & Winnowing ---
    @staticmethod
    def _normalize_text(text: str) -> str:
        """Removes punctuation and normalizes whitespace for clean fingerprinting."""
        cleaned = re.sub(r'[^\w\s]', '', text.lower())
        return re.sub(r'\s+', ' ', cleaned).strip()

    def generate_word_ngrams(self, text: str, n: int = 4) -> Set[str]:
        """Generates word n-grams for text matching."""
        words = self._normalize_text(text).split()
        if len(words) < n:
            return {' '.join(words)} if words else set()
        return {' '.join(words[i:i+n]) for i in range(len(words) - n + 1)}

    def generate_char_ngrams(self, text: str, n: int = 5) -> Set[str]:
        """Generates character n-gram rolling hash fingerprints."""
        clean = self._normalize_text(text)
        if len(clean) < n:
            return {clean} if clean else set()
        return {clean[i:i+n] for i in range(len(clean) - n + 1)}

    def compute_ngram_jaccard(self, text1: str, text2: str) -> Dict[str, float]:
        """
        Computes Jaccard Similarity on word 4-grams and character 5-grams.
        """
        word_set1 = self.generate_word_ngrams(text1, n=4)
        word_set2 = self.generate_word_ngrams(text2, n=4)
        
        char_set1 = self.generate_char_ngrams(text1, n=5)
        char_set2 = self.generate_char_ngrams(text2, n=5)

        def jaccard(s1: Set[str], s2: Set[str]) -> float:
            if not s1 or not s2:
                return 0.0
            union = s1 | s2
            intersection = s1 & s2
            return len(intersection) / len(union) if union else 0.0

        w_jaccard = jaccard(word_set1, word_set2)
        c_jaccard = jaccard(char_set1, char_set2)

        # Weighted lexical similarity
        lexical_score = 0.6 * w_jaccard + 0.4 * c_jaccard
        return {
            "lexical_score": round(lexical_score, 4),
            "word_ngram_jaccard": round(w_jaccard, 4),
            "char_ngram_jaccard": round(c_jaccard, 4)
        }

    # --- 2. Sparse TF-IDF Keyword Matcher ---
    def compute_tfidf_similarity(self, text1: str, text2: str) -> float:
        """Computes Cosine Similarity based on Term Frequencies."""
        words1 = [w for w in re.findall(r'\b\w+\b', text1.lower()) if len(w) > 1]
        words2 = [w for w in re.findall(r'\b\w+\b', text2.lower()) if len(w) > 1]

        if not words1 or not words2:
            return 0.0

        freq1, freq2 = {}, {}
        for w in words1:
            freq1[w] = freq1.get(w, 0) + 1
        for w in words2:
            freq2[w] = freq2.get(w, 0) + 1

        all_words = set(freq1.keys()) | set(freq2.keys())
        dot_product = sum(freq1.get(w, 0) * freq2.get(w, 0) for w in all_words)
        mag1 = math.sqrt(sum(v ** 2 for v in freq1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in freq2.values()))

        if not mag1 or not mag2:
            return 0.0

        return round(dot_product / (mag1 * mag2), 4)

    # --- 3. Dense Neural Embedding Matcher (SBERT) ---
    def encode_dense_vector(self, text: str) -> Optional[List[float]]:
        """Encodes text into a dense semantic embedding vector using SBERT model."""
        if not self.model:
            return None
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"SBERT encoding failed: {e}")
            return None

    def compute_cosine_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """Computes cosine similarity between two dense vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if not norm1 or not norm2:
            return 0.0
        return round(dot / (norm1 * norm2), 4)

    def compute_neural_similarity(self, text1: str, text2: str) -> float:
        """Calculates dense semantic embedding similarity between two texts."""
        if not self.model:
            return self.compute_tfidf_similarity(text1, text2)

        v1 = self.encode_dense_vector(text1)
        v2 = self.encode_dense_vector(text2)
        if not v1 or not v2:
            return self.compute_tfidf_similarity(text1, text2)
        return self.compute_cosine_distance(v1, v2)

    # --- 4. Matching Span Extractor ---
    def extract_matching_spans(self, text1: str, text2: str, min_words: int = 3) -> List[str]:
        """Extracts verbatim matching word sequences present in both texts."""
        words1 = self._normalize_text(text1).split()
        words2_set = self.generate_word_ngrams(text2, n=min_words)
        
        matches = []
        i = 0
        while i <= len(words1) - min_words:
            gram = ' '.join(words1[i:i+min_words])
            if gram in words2_set:
                phrase = words1[i:i+min_words]
                j = i + min_words
                while j < len(words1):
                    ext_gram = ' '.join(words1[i:j+1])
                    if ext_gram in text2.lower():
                        phrase.append(words1[j])
                        j += 1
                    else:
                        break
                matches.append(' '.join(phrase))
                i = j
            else:
                i += 1
        return list(set(matches))[:5]

    # --- 5. Multi-Stage Ensemble Analyzer ---
    def analyze_pair(
        self,
        query_text: str,
        target_text: str,
        query_vector: Optional[List[float]] = None,
        target_vector: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Runs full multi-stage agent analysis comparing query text against target text.
        Calculates Lexical, Keyword, and Dense Neural Scores into an Ensemble Score.
        """
        # Stage 1: Lexical N-Gram Fingerprint Jaccard
        lex_data = self.compute_ngram_jaccard(query_text, target_text)
        lexical_score = lex_data["lexical_score"]

        # Stage 2: Sparse TF-IDF Keyword Matcher
        tfidf_score = self.compute_tfidf_similarity(query_text, target_text)

        # Stage 3: Dense Neural Semantic Matcher
        if query_vector and target_vector:
            semantic_score = self.compute_cosine_distance(query_vector, target_vector)
        else:
            semantic_score = self.compute_neural_similarity(query_text, target_text)

        # Stage 4: Weighted Ensemble Scoring
        # 40% Dense Semantic + 35% Lexical N-Gram + 25% TF-IDF Keyword
        composite_score = round(
            0.40 * semantic_score + 0.35 * lexical_score + 0.25 * tfidf_score, 4
        )

        # Stage 5: Classification & Risk Assessment
        if lexical_score >= 0.70 or composite_score >= 0.75:
            risk_category = "Exact Copy / Direct Plagiarism"
            risk_level = "HIGH"
        elif semantic_score >= 0.65 and lexical_score < 0.35:
            risk_category = "Paraphrased Plagiarism (Synonym/Structural Re-ordering)"
            risk_level = "HIGH"
        elif composite_score >= 0.25:
            risk_category = "Moderate Overlap / Shared Terminology"
            risk_level = "MEDIUM"
        else:
            risk_category = "Original Content / Low Overlap"
            risk_level = "LOW"

        matched_spans = self.extract_matching_spans(query_text, target_text)

        return {
            "composite_score": composite_score,
            "semantic_score": semantic_score,
            "lexical_score": lexical_score,
            "tfidf_score": tfidf_score,
            "risk_category": risk_category,
            "risk_level": risk_level,
            "word_jaccard": lex_data["word_ngram_jaccard"],
            "char_jaccard": lex_data["char_ngram_jaccard"],
            "matched_spans": matched_spans,
            "has_neural_model": self.model is not None
        }


# Global agent singleton
plagiarism_agent = PlagiarismDetectionAgent(use_neural=True)
