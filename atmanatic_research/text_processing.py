"""Deterministic, dependency-free text processing for research artifacts."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

PROCESSOR_VERSION = "1.0"
TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:_[a-z0-9]+)*")
WHITESPACE_PATTERN = re.compile(r"\s+")
KNOWN_ENTITIES = {
    "evidence": "evidence",
    "provenance": "provenance",
    "benchmark": "benchmark",
    "falsifier": "falsifier",
    "rollback": "rollback",
    "schema": "schema",
    "review": "review",
    "impermanent loss": "impermanent loss",
    "kill switch": "kill switch",
}

CANONICAL_ALIASES = (
    (re.compile(r"\bresearch[\s_-]+record\b", re.IGNORECASE), "research_record"),
)


def normalize_text(text: str) -> str:
    """Return stable lowercase text with canonical aliases and whitespace."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    normalized = unicodedata.normalize("NFKC", text).replace("\u00a0", " ")
    for pattern, replacement in CANONICAL_ALIASES:
        normalized = pattern.sub(replacement, normalized)
    normalized = normalized.lower().replace("-", " ")
    normalized = WHITESPACE_PATTERN.sub(" ", normalized)
    return normalized.strip()


def tokenize(text: str) -> list[str]:
    """Tokenize normalized domain text while preserving IDs, tickers, and underscores."""
    return TOKEN_PATTERN.findall(normalize_text(text))


def extract_ngrams(text: str, min_n: int = 2, max_n: int = 3) -> list[str]:
    """Return unique ordered word n-grams, including domain phrases."""
    if min_n < 1 or max_n < min_n:
        raise ValueError("require 1 <= min_n <= max_n")
    tokens = tokenize(text)
    seen: set[str] = set()
    ngrams: list[str] = []
    for size in range(min_n, max_n + 1):
        for start in range(len(tokens) - size + 1):
            phrase = " ".join(tokens[start:start + size])
            if phrase not in seen:
                seen.add(phrase)
                ngrams.append(phrase)
    return ngrams


def explain_match(query: str, document: str) -> dict[str, list[str]]:
    """Explain lexical, phrase, and known-domain-entity overlap."""
    normalized_document = normalize_text(document)
    document_tokens = set(tokenize(normalized_document))
    query_tokens = list(dict.fromkeys(tokenize(query)))
    matched_terms = [term for term in query_tokens if term in document_tokens]
    matched_phrases = [phrase for phrase in extract_ngrams(query) if phrase in normalized_document]
    normalized_query = normalize_text(query)
    matched_entities = [
        label for value, label in KNOWN_ENTITIES.items()
        if value in normalized_query and ((" " in value and value in normalized_document) or (" " not in value and value in document_tokens))
    ]
    return {
        "matched_terms": matched_terms,
        "matched_phrases": matched_phrases,
        "matched_entities": matched_entities,
    }


def process_text(text: str) -> dict[str, Any]:
    """Process text and return replayable lexical and provenance metadata."""
    normalized = normalize_text(text)
    return {
        "processor_version": PROCESSOR_VERSION,
        "input_text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "normalized_text_hash": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "normalized_text": normalized,
        "tokens": tokenize(normalized),
        "ngrams": extract_ngrams(normalized),
    }