"""Configuration helpers for the moderation pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
LEXICON_DIR = DATA_DIR / "lexicons"
MODEL_DIR = PROJECT_ROOT / "models"


@dataclass(frozen=True)
class Thresholds:
    """Decision thresholds for rules and models."""

    spam_rule: float = 0.55
    spam_model: float = 0.6
    politics_rule: float = 0.5
    politics_model: float = 0.55


@dataclass(frozen=True)
class NormalizerSettings:
    """Parameters for the text normalization pipeline."""

    collapse_repeated_chars: bool = True
    strip_diacritics: bool = True
    keep_emojis: bool = False


@dataclass(frozen=True)
class RuleWeights:
    """Weights used by rule-based scorers."""

    url_weight: float = 0.18
    repeat_weight: float = 0.2
    uppercase_weight: float = 0.15
    spam_keyword_weight: float = 0.25
    low_diversity_weight: float = 0.2
    politics_keyword_weight: float = 0.35
    long_sentence_weight: float = 0.1


@dataclass(frozen=True)
class FilterConfig:
    """Top level configuration object."""

    thresholds: Thresholds = Thresholds()
    normalizer: NormalizerSettings = NormalizerSettings()
    rule_weights: RuleWeights = RuleWeights()
    lexicon_dir: Path = LEXICON_DIR
    model_dir: Path = MODEL_DIR


DEFAULT_CONFIG = FilterConfig()

