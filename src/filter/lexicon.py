"""Lexicon utilities for quick keyword-based detection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Set, Tuple
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

    def load_optional(self, name: str) -> Set[str]:
        """
        Like load(), but returns empty set if file doesn't exist.
        Useful for optional phrase lexicons.
        """
        path = self.directory / f"{name}.txt"
        if not path.exists():
            return set()
        return self.load(name)

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

        # Tek kelime lexicon setleri (tam eşleşme için normalize edilmiş)
        self._forbidden = (
                self.loader.load("argo")
                | self.loader.load("adult")
                | self.loader.load("yasakli_kelime")
        )
        self._spam = self.loader.load("spam")
        self._politics = self.loader.load("politics")

        # Opsiyonel: çok kelimeli phrase lexiconları (dosya yoksa boş)
        # Örn dosya içeriği: "bedava takipçi" / "oy ver" gibi satırlar
        self._forbidden_phrases = self._load_phrases_optional("forbidden_phrases")
        self._spam_phrases = self._load_phrases_optional("spam_phrases")
        self._politics_phrases = self._load_phrases_optional("politics_phrases")

    def scan_tokens(self, tokens: Iterable[str]) -> LexiconMatch:
        token_list = [t for t in tokens if t]

        forbidden_hits = self._match_category_exact(token_list, self._forbidden)
        spam_hits = self._match_category_exact(token_list, self._spam)
        politics_hits = self._match_category_exact(token_list, self._politics)

        # Opsiyonel phrase eşleşmeleri (substring yok, token dizisi içinde ardışık eşleşme)
        forbidden_hits |= self._match_phrases(token_list, self._forbidden_phrases)
        spam_hits |= self._match_phrases(token_list, self._spam_phrases)
        politics_hits |= self._match_phrases(token_list, self._politics_phrases)

        return LexiconMatch(
            forbidden=forbidden_hits,
            spam=spam_hits,
            politics=politics_hits,
        )

    def _match_category_exact(self, tokens: Iterable[str], lexicon: Set[str]) -> Set[str]:
        """
        SADECE tam token eşleşmesi.
        Substring/prefix arama YOK.
        """
        matches = {t for t in tokens if t in lexicon}
        # display_value ile orijinal yazımı döndür
        return {self.loader.display_value(item) for item in matches}

    def _load_phrases_optional(self, filename: str) -> Set[Tuple[str, ...]]:
        """
        Optional phrase file loader.
        Each line: "kelime1 kelime2 ..." -> tuple("kelime1","kelime2",...)
        """
        raw_lines = self.loader.load_optional(filename)
        # load_optional zaten normalize set döndürüyor; ama phrase için satır bazlı split gerek.
        # O yüzden dosyayı direkt okuyalım; yoksa boş set.
        path = self.loader.directory / f"{filename}.txt"
        if not path.exists():
            return set()

        phrases: Set[Tuple[str, ...]] = set()
        with path.open("r", encoding="utf-8") as handler:
            for line in handler:
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue
                normalized_line = self.loader._normalize_entry(raw)
                parts = tuple(p for p in normalized_line.split() if p)
                if len(parts) >= 2:
                    phrases.add(parts)
        return phrases

    def _match_phrases(self, tokens: list[str], phrases: Set[Tuple[str, ...]]) -> Set[str]:
        """
        Token listesi içinde ardışık n-gram eşleşmesi.
        """
        if not phrases or not tokens:
            return set()

        hits: Set[str] = set()
        for phrase in phrases:
            n = len(phrase)
            if n == 0 or n > len(tokens):
                continue
            for i in range(0, len(tokens) - n + 1):
                if tuple(tokens[i : i + n]) == phrase:
                    # display_value phrase tokenlarında olmayabilir; direkt phrase string olarak ekliyoruz
                    hits.add(" ".join(phrase))
                    break
        return hits
