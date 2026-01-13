"""Rule-based features and scores."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict

from .config import RuleWeights
from .normalizer import NormalizedText, extract_uppercase_ratio, sentence_count

URL_PATTERN = re.compile(r"https?://", re.IGNORECASE)
REPEAT_PATTERN = re.compile(r"(.)\1{3,}")


@dataclass
class RuleScores:
    spam_score: float
    politics_score: float
    features: Dict[str, float]


class RuleEngine:
    """Calculates heuristic scores based on hand tuned rules."""

    def __init__(self, weights: RuleWeights) -> None:
        self.weights = weights

    def evaluate(self, normalized: NormalizedText, extra_features: Dict[str, float] | None = None) -> RuleScores:
        features = self._extract_features(normalized)
        if extra_features:
            features.update(extra_features)
        spam_score = self._spam_score(features)
        politics_score = self._politics_score(features)
        return RuleScores(spam_score=spam_score, politics_score=politics_score, features=features)

    def _extract_features(self, normalized: NormalizedText) -> Dict[str, float]:
        text = normalized.original
        tokens = normalized.tokens
        token_count = len(tokens)
        unique_word_ratio = len(set(tokens)) / token_count if token_count else 1.0
        url_count = len(URL_PATTERN.findall(text))
        uppercase_ratio = extract_uppercase_ratio(text)
        long_repeat_ratio = self._long_repeat_ratio(text)
        sentence_cnt = sentence_count(text)
        question_mark_count = text.count("?")

        features = {
            "token_count": float(token_count),
            "unique_word_ratio": unique_word_ratio,
            "url_count": float(url_count),
            "uppercase_ratio": uppercase_ratio,
            "long_repeat_ratio": long_repeat_ratio,
            "sentence_count": float(sentence_cnt),
            "question_mark_count": float(question_mark_count),
        }
        return features

    def _spam_score(self, features: Dict[str, float]) -> float:
        score = 0.0
        score += min(features["url_count"], 3.0) * self.weights.url_weight
        score += features["long_repeat_ratio"] * self.weights.repeat_weight
        score += features["uppercase_ratio"] * self.weights.uppercase_weight
        score += features.get("spam_keyword_hits", 0.0) * self.weights.spam_keyword_weight
        low_diversity = max(0.0, 0.5 - features["unique_word_ratio"])
        score += low_diversity * self.weights.low_diversity_weight
        return min(score, 1.0)

    def _politics_score(self, features: Dict[str, float]) -> float:
        score = 0.0
        score += features.get("politics_keyword_hits", 0.0) * self.weights.politics_keyword_weight
        long_sentences = max(0.0, features["sentence_count"] - 3) / 5
        score += min(long_sentences, 1.0) * self.weights.long_sentence_weight
        return min(score, 1.0)

    @staticmethod
    def _long_repeat_ratio(text: str) -> float:
        matches = REPEAT_PATTERN.findall(text)
        if not text:
            return 0.0
        return min(len(matches) / max(len(text), 1), 1.0)

