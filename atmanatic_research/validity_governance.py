"""Governed validity transitions backed by separate review artifacts."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from validity_protocol import ValidationResult, ValidityLevel, ValidityPacket, advance

from .artifact_contracts import ArtifactContractError, validate_review_outcome

_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_REVIEW_GATED_LEVELS = {
    ValidityLevel.INDEPENDENTLY_VERIFIED,
    ValidityLevel.AWAITING_HUMAN_PROMOTION,
}


def advance_with_review(
    packet: ValidityPacket,
    target: ValidityLevel,
    review_record: dict[str, Any],
    *,
    now: datetime | None = None,
) -> ValidationResult:
    """Advance a review-gated packet only with a resolved, hash-linked review artifact."""
    if target not in _REVIEW_GATED_LEVELS:
        return ValidationResult(
            passed=False,
            violations=[f"{target.value} is not a review-gated validity transition"],
        )

    packet_hash = packet.metadata.get("content_hash")
    if not isinstance(packet_hash, str) or not _SHA256.fullmatch(packet_hash):
        return ValidationResult(
            passed=False,
            violations=["packet metadata content_hash must be a SHA-256 hex digest"],
        )

    try:
        review = validate_review_outcome(review_record)
    except ArtifactContractError as error:
        return ValidationResult(
            passed=False,
            violations=[f"review artifact is invalid: {error}"],
        )
    if review["subject_artifact_hash"].lower() != packet_hash.lower():
        return ValidationResult(
            passed=False,
            violations=["review artifact subject hash does not match packet content hash"],
        )
    if review["outcome"] != "challenged_and_resolved":
        return ValidationResult(
            passed=False,
            violations=["review artifact must have outcome challenged_and_resolved"],
        )

    previous_reviewer = packet.reviewer
    previous_outcome = packet.challenge_outcome
    packet.reviewer = review["reviewer"]
    packet.challenge_outcome = review["outcome"]
    result = advance(packet, target, now=now)
    if not result.passed:
        packet.reviewer = previous_reviewer
        packet.challenge_outcome = previous_outcome
    return result