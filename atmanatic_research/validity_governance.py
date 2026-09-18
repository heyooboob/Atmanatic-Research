"""Governed validity transitions backed by separate review artifacts."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from validity_protocol import ValidationResult, ValidityLevel, ValidityPacket, advance

from .artifact_contracts import ArtifactContractError, validate_promotion_record, validate_review_outcome

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


def promote_packet(packet: ValidityPacket, promotion_record: dict[str, Any]) -> ValidationResult:
    """Record an explicit, scoped human promotion; never inferred from a passing review.

    Requires the packet to be `awaiting_human_promotion` and a structurally
    valid, `approved` promotion record whose `approved_artifact_hash` matches
    the packet's declared content hash. The promotion record is retained on
    the packet's metadata for downstream traceability.
    """
    if packet.level != ValidityLevel.AWAITING_HUMAN_PROMOTION:
        return ValidationResult(
            passed=False,
            violations=[f"packet must be awaiting_human_promotion, was {packet.level.value}"],
        )

    packet_hash = packet.metadata.get("content_hash")
    if not isinstance(packet_hash, str) or not _SHA256.fullmatch(packet_hash):
        return ValidationResult(
            passed=False,
            violations=["packet metadata content_hash must be a SHA-256 hex digest"],
        )

    try:
        promotion = validate_promotion_record(promotion_record)
    except ArtifactContractError as error:
        return ValidationResult(passed=False, violations=[f"promotion record is invalid: {error}"])

    if promotion["approved_artifact_hash"].lower() != packet_hash.lower():
        return ValidationResult(
            passed=False,
            violations=["promotion record approved_artifact_hash does not match packet content hash"],
        )
    if promotion["status"] != "approved":
        return ValidationResult(
            passed=False,
            violations=["promotion record status must be 'approved' to promote a packet"],
        )

    packet.level = ValidityLevel.PROMOTED
    packet.metadata["promotion_record"] = promotion
    return ValidationResult(passed=True, violations=[])