"""Lexicon utilities for quick keyword-based detection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set
import unicodedata


@dataclass(frozen=True)
class LexiconMatch:
    forbidden: Set[str]
    spam: Set[str]
    politics: Set[str]

    @property
    def has_forbidden(self) -> bool:
        return bool(self.forbidden)

    @property
    def has_spam(self) -> bool:
        return bool(self.spam)

    @property
    def has_politics(self) -> bool:
        return bool(self.politics)


class LexiconLoader:
    """Loads and caches words from text files."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self._cache: Dict[str, Set[str]] = {}
        self._display_lookup: Dict[str, str] = {}

    def load(self, name: str) -> Set[str]:
        if name in self._cache:
            return self._cache[name]

        path = self.directory / f"{name}.txt"
        if not path.exists():
            raise FileNotFoundError(f"Lexicon file not found: {path}")

        tokens: Set[str] = set()
        with path.open("r", encoding="utf-8") as handler:
            for line in handler:
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue
                normalized = self._normalize_entry(raw)
                tokens.add(normalized)
                self._display_lookup.setdefault(normalized, raw)

        self._cache[name] = tokens
        return tokens

    @staticmethod
    def _normalize_entry(value: str) -> str:
        normalized = unicodedata.normalize("NFKC", value.strip().lower())
        normalized = "".join(
            ch for ch in unicodedata.normalize("NFD", normalized) if unicodedata.category(ch) != "Mn"
        )
        return normalized

    def display_value(self, token: str) -> str:
        return self._display_lookup.get(token, token)


class LexiconChecker:
    """Checks normalized tokens against lexicon categories."""

    def __init__(self, directory: Path) -> None:
        self.loader = LexiconLoader(directory)
        self._forbidden = self.loader.load("argo") | self.loader.load("adult") |self.loader.load("yasakli_kelime")
        self._spam = self.loader.load("spam")
        self._politics = self.loader.load("politics")

    def scan_tokens(self, tokens: Iterable[str]) -> LexiconMatch:
        token_list = list(tokens)
        return LexiconMatch(
            forbidden=self._match_category(token_list, self._forbidden),
            spam=self._match_category(token_list, self._spam),
            politics=self._match_category(token_list, self._politics),
        )

    def _match_category(self, tokens: Iterable[str], lexicon: Set[str]) -> Set[str]:
        matches: Set[str] = set()
        for token in tokens:
            if token in lexicon:
                matches.add(token)
                continue
            for entry in lexicon:
                if token.startswith(entry) and len(token) - len(entry) <= 4:
                    matches.add(entry)
                elif entry in token and len(entry) > 3:
                    matches.add(entry)
        return {self.loader.display_value(item) for item in matches}

