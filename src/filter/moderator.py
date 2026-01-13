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
    reason: str
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

        if lexicon_match.has_forbidden:
            return ModerationResult(
                status=ModerationStatus.REJECT,
                reason="yasakli_kelime_kullanimi",
                scores={},
                metadata={"matches": sorted(lexicon_match.forbidden)},
            )

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

        if self._should_flag_spam(scores):
            return ModerationResult(
                status=ModerationStatus.ADMIN_REVIEW_SPAM,
                reason="spam_rule_trigger",
                scores=scores,
                metadata={"spam_keywords": sorted(lexicon_match.spam)},
            )

        if self._should_flag_politics(scores):
            return ModerationResult(
                status=ModerationStatus.ADMIN_REVIEW_POLITICS,
                reason="politics_rule_trigger",
                scores=scores,
                metadata={"politics_keywords": sorted(lexicon_match.politics)},
            )

        return ModerationResult(status=ModerationStatus.ACCEPT, reason="Temiz", scores=scores, metadata={})

    def _should_flag_spam(self, scores: Dict[str, float]) -> bool:
        thresholds = self.config.thresholds
        return scores["spam_rule"] >= thresholds.spam_rule or scores["spam_model"] >= thresholds.spam_model

    def _should_flag_politics(self, scores: Dict[str, float]) -> bool:
        thresholds = self.config.thresholds
        return scores["politics_rule"] >= thresholds.politics_rule or scores["politics_model"] >= thresholds.politics_model

    @classmethod
    def load_default(cls, config: Optional[FilterConfig] = None) -> "ContentModerator":
        return cls(config or DEFAULT_CONFIG)

