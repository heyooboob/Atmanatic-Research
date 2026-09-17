"""Pure admission checks for decision-grade evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .evidence_contracts import validate_evidence_card

BLOCKED_STATUSES = {"stale_source", "conflict", "insufficient_independent_sources"}


@dataclass(frozen=True)
class EvidenceAdmission:
    admitted: bool
    reasons: tuple[str, ...]


def admit_evidence(cards: list[dict[str, Any]], *, now: datetime | None = None) -> EvidenceAdmission:
    """Admit only fresh, provenance-backed, decision-grade evidence cards."""
    reasons: list[str] = []
    if not cards:
        return EvidenceAdmission(False, ("no evidence cards supplied",))
    seen_hashes: dict[str, str] = {}
    for card in cards:
        evidence_id = card.get("evidence_id")
        if not evidence_id:
            reasons.append("evidence card is missing evidence_id")
        elif evidence_id in seen_hashes:
            if seen_hashes[evidence_id] != card.get("content_hash"):
                reasons.append(f"evidence id '{evidence_id}' has conflicting content hashes")
            else:
                reasons.append(f"duplicate evidence id '{evidence_id}'")
        else:
            seen_hashes[evidence_id] = card.get("content_hash", "")
        if not card.get("source_ids"):
            reasons.append("evidence card is missing source_ids")
        if not card.get("content_hash"):
            reasons.append("evidence card is missing content_hash")
        if card.get("status") in BLOCKED_STATUSES:
            reasons.append(f"evidence status is {card['status']}")
        if card.get("recall_status") in {"untrusted", "reference", "discovery_only"}:
            reasons.append("evidence source is not decision-grade")
        observed_at = card.get("observed_at")
        if not observed_at:
            reasons.append("evidence card is missing observed_at")
        else:
            try:
                parsed = datetime.fromisoformat(str(observed_at).replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                if parsed > (now or datetime.now(timezone.utc)):
                    reasons.append("evidence observed_at is in the future")
            except ValueError:
                reasons.append("evidence observed_at is invalid")
    return EvidenceAdmission(not reasons, tuple(dict.fromkeys(reasons)))


def require_decision_evidence(cards: list[dict[str, Any]], *, now: datetime | None = None) -> list[dict[str, Any]]:
    """Return evidence cards admitted for decision-grade use or raise with reasons."""
    admission = admit_evidence(cards, now=now)
    if not admission.admitted:
        raise ValueError("Decision evidence blocked: " + "; ".join(admission.reasons))
    return cards


def validate_and_admit_evidence(
    cards: list[dict[str, Any]], *, now: datetime | None = None
) -> list[dict[str, Any]]:
    """Validate card structure before admitting cards for decision use."""
    for card in cards:
        validate_evidence_card(card)
    return require_decision_evidence(cards, now=now)


def require_claim_evidence(
    claim: dict[str, Any], cards: list[dict[str, Any]], *, now: datetime | None = None
) -> dict[str, Any]:
    """Require a claim's source IDs to be present in admitted evidence cards."""
    admitted_cards = validate_and_admit_evidence(cards, now=now)
    source_ids = claim.get("source_ids") if isinstance(claim, dict) else None
    if not isinstance(source_ids, list) or not source_ids or not all(
        isinstance(source_id, str) and source_id.strip() for source_id in source_ids
    ):
        raise ValueError("Claim evidence blocked: claim has no valid source references")
    admitted_source_ids = {
        source_id
        for card in admitted_cards
        for source_id in card["source_ids"]
    }
    missing = [source_id for source_id in source_ids if source_id not in admitted_source_ids]
    if missing:
        raise ValueError("Claim evidence blocked: unsupported source references: " + ", ".join(missing))
    return claim