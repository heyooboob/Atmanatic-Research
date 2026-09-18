"""Bounded validity contract for human promotion packets."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .error_codes import ContractError, EXPIRED_OR_REVOKED, MISSING_OR_INVALID_FIELD

DEFENSIVE_LANGUAGE_PATTERNS = [
    r"further research is needed",
    r"we do not address",
    r"it should be noted that we didn't",
    r"while not optimal",
    r"though limited in scope",
]


@dataclass(frozen=True)
class ValidityReview:
    valid: bool
    reasons: tuple[str, ...]


class ValidityStandardError(ContractError):
    """Raised when a validity packet fails the truth-validity standard."""


_EXPIRY_REASONS = (
    "validity expiry is missing",
    "validity packet is expired",
    "validity expiry is invalid",
)


def validate_validity_packet(packet: dict[str, Any], *, now: datetime | None = None) -> ValidityReview:
    """Validate bounded operational validity without claiming universal truth."""
    reasons: list[str] = []
    required_text = {
        "scope": "validity scope is missing",
        "observations": "observations are missing",
        "limitations": "limitations are missing",
        "revalidation": "revalidation policy is missing",
    }
    for field, reason in required_text.items():
        value = packet.get(field)
        if not isinstance(value, str) or not value.strip():
            reasons.append(reason)

    obs = str(packet.get("observations", ""))
    for pat in DEFENSIVE_LANGUAGE_PATTERNS:
        if re.search(pat, obs, re.IGNORECASE):
            reasons.append("observations contain prohibited defensive language; isolate constraints to limitations")
            break

    evidence = packet.get("evidence_refs")
    if not isinstance(evidence, list) or not evidence or not all(isinstance(item, str) and item.strip() for item in evidence):
        reasons.append("validity evidence references are missing")
    expires_at = packet.get("expires_at")
    if not isinstance(expires_at, str) or not expires_at.strip():
        reasons.append("validity expiry is missing")
    else:
        try:
            expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            if expiry <= (now or datetime.now(timezone.utc)):
                reasons.append("validity packet is expired")
        except ValueError:
            reasons.append("validity expiry is invalid")
    return ValidityReview(not reasons, tuple(dict.fromkeys(reasons)))


def require_validity_packet(packet: dict[str, Any]) -> dict[str, Any]:
    result = validate_validity_packet(packet)
    if not result.valid:
        code = EXPIRED_OR_REVOKED if any(reason in _EXPIRY_REASONS for reason in result.reasons) else MISSING_OR_INVALID_FIELD
        raise ValidityStandardError("Validity packet blocked: " + "; ".join(result.reasons), code=code)
    return packet