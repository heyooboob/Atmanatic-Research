"""Storage-neutral contracts for evidence cards."""

from __future__ import annotations

from typing import Any

from .error_codes import ContractError, MALFORMED_SYNTAX, MISSING_OR_INVALID_FIELD
from .timestamps import TimestampError, parse_rfc3339


class EvidenceContractError(ContractError):
    """Raised when an evidence card is incomplete or malformed."""


REQUIRED_FIELDS = (
    "evidence_id",
    "claim",
    "source_ids",
    "agent",
    "observed_at",
    "confidence",
    "content_hash",
    "status",
    "details",
)


def validate_evidence_card(card: dict[str, Any]) -> dict[str, Any]:
    """Validate one persisted or proposed evidence card without assigning truth."""
    if not isinstance(card, dict):
        raise EvidenceContractError("evidence card must be an object", code=MALFORMED_SYNTAX)
    missing = [field for field in REQUIRED_FIELDS if field not in card]
    if missing:
        raise EvidenceContractError(
            f"evidence card is missing fields: {', '.join(missing)}",
            code=MISSING_OR_INVALID_FIELD,
        )
    if not isinstance(card["evidence_id"], str) or not card["evidence_id"].strip():
        raise EvidenceContractError("evidence_id must be a non-empty string", code=MISSING_OR_INVALID_FIELD)
    if not isinstance(card["claim"], str) or not card["claim"].strip():
        raise EvidenceContractError("claim must be a non-empty string", code=MISSING_OR_INVALID_FIELD)
    if not isinstance(card["source_ids"], list) or not card["source_ids"] or not all(
        isinstance(item, str) and item.strip() for item in card["source_ids"]
    ):
        raise EvidenceContractError(
            "source_ids must be a non-empty list of strings", code=MISSING_OR_INVALID_FIELD
        )
    if not isinstance(card["agent"], str) or not card["agent"].strip():
        raise EvidenceContractError("agent must be a non-empty string", code=MISSING_OR_INVALID_FIELD)
    try:
        parse_rfc3339(card["observed_at"], "observed_at")
    except TimestampError as error:
        raise EvidenceContractError(str(error), code=MISSING_OR_INVALID_FIELD) from error
    if not isinstance(card["confidence"], (int, float)) or not 0 <= card["confidence"] <= 1:
        raise EvidenceContractError("confidence must be between 0 and 1", code=MISSING_OR_INVALID_FIELD)
    if not isinstance(card["content_hash"], str) or not card["content_hash"].strip():
        raise EvidenceContractError("content_hash must be a non-empty string", code=MISSING_OR_INVALID_FIELD)
    if not isinstance(card["status"], str) or not card["status"].strip():
        raise EvidenceContractError("status must be a non-empty string", code=MISSING_OR_INVALID_FIELD)
    if not isinstance(card["details"], dict):
        raise EvidenceContractError("details must be an object", code=MISSING_OR_INVALID_FIELD)
    return card