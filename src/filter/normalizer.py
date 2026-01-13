"""Utilities for bringing user content into a canonical form."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, List

from .config import NormalizerSettings

_EMOJI_PATTERN = re.compile(r"[\U00010000-\U0010FFFF]", flags=re.UNICODE)
_URL_PATTERN = re.compile(r"https?://\S+")
_WHITESPACE = re.compile(r"\s+")
_TOKEN_SPLIT = re.compile(r"[^\w@#]+", flags=re.UNICODE)


@dataclass
class NormalizedText:
    """Container for frequently used normalization outputs."""

    original: str
    cleaned: str
    tokens: List[str]


class TextNormalizer:
    """Converts raw input into normalized strings and tokens."""

    def __init__(self, settings: NormalizerSettings) -> None:
        self.settings = settings

    def normalize(self, text: str) -> NormalizedText:
        """Return normalized, tokenized representation of text."""
        cleaned = self._basic_clean(text)
        tokens = [tok for tok in _TOKEN_SPLIT.split(cleaned) if tok]
        print(tokens)
        return NormalizedText(original=text, cleaned=cleaned, tokens=tokens)

    def _basic_clean(self, text: str) -> str:
        if not text:
            return ""

        normalized = unicodedata.normalize("NFKC", text)
        normalized = normalized.lower()

        if self.settings.strip_diacritics:
            normalized = "".join(
                ch for ch in unicodedata.normalize("NFD", normalized) if unicodedata.category(ch) != "Mn"
            )

        normalized = normalized.replace("’", "'")
        normalized = self._replace_leetspeak(normalized)

        if not self.settings.keep_emojis:
            normalized = _EMOJI_PATTERN.sub(" ", normalized)

        normalized = _URL_PATTERN.sub(" url ", normalized)

        if self.settings.collapse_repeated_chars:
            normalized = re.sub(r"(.)\1{2,}", r"\1\1", normalized)

        normalized = _WHITESPACE.sub(" ", normalized)
        return normalized.strip()

    @staticmethod
    def _replace_leetspeak(text: str) -> str:
        table = str.maketrans(
            {
                "0": "o",
                "1": "i",
                "3": "e",
                "4": "a",
                "5": "s",
                "7": "t",
                "@": "a",
                "$": "s",
            }
        )
        return text.translate(table)


def sentence_count(text: str) -> int:
    """Approximate sentence count."""
    return len([chunk for chunk in re.split(r"[.!?]+", text) if chunk.strip()])


def extract_uppercase_ratio(text: str) -> float:
    """Ratio of uppercase characters in original text."""
    if not text:
        return 0.0
    uppercase = sum(1 for ch in text if ch.isupper())
    letters = sum(1 for ch in text if ch.isalpha())
    return uppercase / letters if letters else 0.0

