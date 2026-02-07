"""Top level moderation orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from .config import DEFAULT_CONFIG, FilterConfig
from .lexicon import LexiconChecker
from .model import LinearModel
from .normalizer import TextNormalizer
from .rules import RuleEngine


class ModerationStatus(str, Enum):
    ACCEPT = "kabul"
    REJECT = "red"
    ADMIN_REVIEW_SPAM = "yeniden_admin_kontrolu_spam"
    ADMIN_REVIEW_POLITICS = "yeniden_admin_kontrolu_politics"


@dataclass
class ModerationResult:
    status: ModerationStatus
    reason: list[str]
    scores: Dict[str, float]
    metadata: Dict[str, object]


class ContentModerator:
    """Encapsulates the entire moderation pipeline."""

    def __init__(self, config: FilterConfig) -> None:
        self.config = config
        self.normalizer = TextNormalizer(config.normalizer)
        self.lexicon = LexiconChecker(config.lexicon_dir)
        self.rules = RuleEngine(config.rule_weights)
        self.spam_model = LinearModel.load(config.model_dir / "spam_model.json")
        self.politics_model = LinearModel.load(config.model_dir / "politics_model.json")

    def moderate(self, text: str) -> ModerationResult:
        normalized = self.normalizer.normalize(text or "")
        lexicon_match = self.lexicon.scan_tokens(normalized.tokens)

        extra_features = {
            "spam_keyword_hits": float(len(lexicon_match.spam)),
            "politics_keyword_hits": float(len(lexicon_match.politics)),
        }

        rule_scores = self.rules.evaluate(normalized, extra_features=extra_features)
        spam_prob = self.spam_model.predict_proba(rule_scores.features)
        politics_prob = self.politics_model.predict_proba(rule_scores.features)

        scores = {
            "spam_rule": round(rule_scores.spam_score, 3),
            "spam_model": round(spam_prob, 3),
            "politics_rule": round(rule_scores.politics_score, 3),
            "politics_model": round(politics_prob, 3),
        }

        reasons: list[str] = []

        # Flag'ler
        forbidden_flag = bool(lexicon_match.has_forbidden)
        spam_flag = self._should_flag_spam(scores)
        politics_flag = self._should_flag_politics(scores)

        # Reasons'ları biriktir (REJECT olsa bile)
        if forbidden_flag:
            reasons.append("yasakli_kelime_kullanimi")
        if spam_flag:
            reasons.append("spam_supheli")
        if politics_flag:
            reasons.append("politics_supheli")

        # Status önceliği (yasaklı kelime en üst)
        if forbidden_flag:
            status = ModerationStatus.REJECT
        elif politics_flag:
            status = ModerationStatus.ADMIN_REVIEW_POLITICS
        elif spam_flag:
            status = ModerationStatus.ADMIN_REVIEW_SPAM
        else:
            status = ModerationStatus.ACCEPT
            reasons = ["temiz"]

        return ModerationResult(
            status=status,
            reason=reasons,
            scores=scores,
            metadata={
                "forbidden_words": sorted(lexicon_match.forbidden),
                "spam_keywords": sorted(lexicon_match.spam),
                "politics_keywords": sorted(lexicon_match.politics),
            },
        )



    def _should_flag_spam(self, scores: Dict[str, float]) -> bool:
            thresholds = self.config.thresholds
            return scores["spam_rule"] >= thresholds.spam_rule or scores["spam_model"] >= thresholds.spam_model

    def _should_flag_politics(self, scores: Dict[str, float]) -> bool:
        thresholds = self.config.thresholds
        return scores["politics_rule"] >= thresholds.politics_rule or scores["politics_model"] >= thresholds.politics_model
    @classmethod
    def load_default(cls, config: Optional[FilterConfig] = None) -> "ContentModerator":
        return cls(config or DEFAULT_CONFIG)

