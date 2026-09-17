"""Storage-neutral contracts for evidence cards."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class EvidenceContractError(ValueError):
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
        raise EvidenceContractError("evidence card must be an object")
    missing = [field for field in REQUIRED_FIELDS if field not in card]
    if missing:
        raise EvidenceContractError(f"evidence card is missing fields: {', '.join(missing)}")
    if not isinstance(card["evidence_id"], str) or not card["evidence_id"].strip():
        raise EvidenceContractError("evidence_id must be a non-empty string")
    if not isinstance(card["claim"], str) or not card["claim"].strip():
        raise EvidenceContractError("claim must be a non-empty string")
    if not isinstance(card["source_ids"], list) or not card["source_ids"] or not all(isinstance(item, str) and item.strip() for item in card["source_ids"]):
        raise EvidenceContractError("source_ids must be a non-empty list of strings")
    if not isinstance(card["agent"], str) or not card["agent"].strip():
        raise EvidenceContractError("agent must be a non-empty string")
    if not isinstance(card["observed_at"], str) or not card["observed_at"].strip():
        raise EvidenceContractError("observed_at must be an ISO timestamp string")
    try:
        datetime.fromisoformat(card["observed_at"].replace("Z", "+00:00"))
    except ValueError as error:
        raise EvidenceContractError("observed_at must be a valid ISO timestamp") from error
    if not isinstance(card["confidence"], (int, float)) or not 0 <= card["confidence"] <= 1:
        raise EvidenceContractError("confidence must be between 0 and 1")
    if not isinstance(card["content_hash"], str) or not card["content_hash"].strip():
        raise EvidenceContractError("content_hash must be a non-empty string")
    if not isinstance(card["status"], str) or not card["status"].strip():
        raise EvidenceContractError("status must be a non-empty string")
    if not isinstance(card["details"], dict):
        raise EvidenceContractError("details must be an object")
    return card