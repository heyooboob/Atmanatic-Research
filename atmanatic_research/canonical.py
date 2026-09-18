"""Canonical JSON serialization and content-hash projection for artifacts.

This freezes the Protocol 0.1 canonicalization scheme described in
ATMANATIC_PROTOCOL_0.1_DRAFT.md section 5.2: sorted object keys, compact
separators, UTF-8 bytes, and no non-finite numbers. `content_hash` and
`signature` fields are excluded from the hashed projection so a record can
declare its own hash without creating a circular dependency.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

EXCLUDED_HASH_FIELDS = frozenset({"content_hash", "signature"})


class CanonicalizationError(ValueError):
    """Raised when a value cannot be canonicalized deterministically."""


def _check_finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise CanonicalizationError("canonical JSON does not permit NaN or infinite numbers")
    if isinstance(value, dict):
        for item in value.values():
            _check_finite(item)
    elif isinstance(value, list):
        for item in value:
            _check_finite(item)


def canonical_json_bytes(value: Any) -> bytes:
    """Return the canonical UTF-8 JSON bytes for `value`.

    Object keys are sorted, separators are compact, and non-finite floats are
    rejected. Callers MUST pass only JSON-compatible values.
    """
    _check_finite(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def project_for_hash(record: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of `record` with hash and signature fields removed."""
    if not isinstance(record, dict):
        raise CanonicalizationError("record must be an object")
    return {key: value for key, value in record.items() if key not in EXCLUDED_HASH_FIELDS}


def compute_content_hash(record: dict[str, Any]) -> str:
    """Compute the SHA-256 content hash of `record` under the canonical projection."""
    projected = project_for_hash(record)
    return hashlib.sha256(canonical_json_bytes(projected)).hexdigest()


def verify_content_hash(record: dict[str, Any]) -> bool:
    """Return whether `record["content_hash"]` matches its recomputed canonical hash."""
    declared = record.get("content_hash") if isinstance(record, dict) else None
    if not isinstance(declared, str):
        return False
    return declared.lower() == compute_content_hash(record).lower()
