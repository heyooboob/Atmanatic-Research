"""Pure admission checks for decision-grade evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .evidence_contracts import validate_evidence_card
from .source_policy import (
    TIER_RANK,
    SourcePolicyError,
    assert_source_allowed,
    evidence_requirement,
    validate_acquisition_receipt,
)

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


def validate_and_admit_governed_evidence(
    cards: list[dict[str, Any]],
    registry: dict[str, Any],
    *,
    minimum_tier: str | None = None,
    request_contexts: dict[str, dict[str, Any]] | None = None,
    acquisition_receipts: list[dict[str, Any]] | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Apply source policy and acquisition provenance before evidence admission."""
    if request_contexts is not None and not isinstance(request_contexts, dict):
        raise ValueError("Governed evidence blocked: request_contexts must be an object")
    if acquisition_receipts is not None and not isinstance(acquisition_receipts, list):
        raise ValueError("Governed evidence blocked: acquisition_receipts must be a list")
    contexts = request_contexts or {}
    receipts = acquisition_receipts or []
    policies = registry.get("minimum_evidence", {})
    if not isinstance(policies, dict):
        raise SourcePolicyError("minimum_evidence must be an object")
    sources_by_agent: dict[str, dict[str, dict[str, Any]]] = {}
    for card in cards:
        agent = card.get("agent") if isinstance(card, dict) else None
        source_ids = card.get("source_ids") if isinstance(card, dict) else None
        if not isinstance(agent, str) or not agent.strip():
            raise ValueError("Governed evidence blocked: card has no valid agent")
        if not isinstance(source_ids, list) or not source_ids or not all(
            isinstance(source_id, str) and source_id.strip() for source_id in source_ids
        ):
            raise ValueError("Governed evidence blocked: card has no valid source references")

        for source_id in source_ids:
            requirement = None
            if agent in policies:
                requirement = evidence_requirement(registry, agent)
            required_tier = (requirement or {}).get("minimum_tier")
            if minimum_tier:
                caller_tier = minimum_tier.upper()
                if caller_tier not in TIER_RANK:
                    raise SourcePolicyError(f"Unknown source tier: {minimum_tier}")
                if required_tier is None or TIER_RANK[caller_tier] > TIER_RANK[required_tier.upper()]:
                    required_tier = caller_tier
            source = assert_source_allowed(
                registry,
                source_id,
                agent,
                minimum_tier=required_tier,
                request_context=contexts.get(source_id),
            )
            sources_by_agent.setdefault(agent, {})[source_id] = source
            access = source.get("access") or {}
            if access.get("mode") != "public_identified":
                continue
            matching_receipts = [
                receipt
                for receipt in receipts
                if isinstance(receipt, dict)
                and receipt.get("source_id") == source_id
                and receipt.get("response_content_hash") == card.get("content_hash")
            ]
            if not matching_receipts:
                raise ValueError(
                    f"Governed evidence blocked: source '{source_id}' requires an acquisition receipt matching the card content hash"
                )
            for receipt in matching_receipts:
                validate_acquisition_receipt(receipt, source=source)

    for agent, sources in sources_by_agent.items():
        if agent not in policies:
            continue
        requirement = evidence_requirement(registry, agent)
        minimum_sources = requirement.get("minimum_sources", 1)
        if len(sources) < minimum_sources:
            raise ValueError(
                f"Governed evidence blocked: agent '{agent}' requires at least {minimum_sources} distinct sources"
            )
        minimum_independent = requirement.get("minimum_independent_sources", 1)
        missing_groups = [
            source_id
            for source_id, source in sources.items()
            if not isinstance(source.get("independence_group"), str)
            or not source["independence_group"].strip()
        ]
        if minimum_independent > 1 and missing_groups:
            raise ValueError(
                "Governed evidence blocked: sources are missing independence_group: "
                + ", ".join(sorted(missing_groups))
            )
        groups = {
            source.get("independence_group")
            for source in sources.values()
            if isinstance(source.get("independence_group"), str)
            and source["independence_group"].strip()
        }
        if minimum_independent > 1 and len(groups) < minimum_independent:
            raise ValueError(
                f"Governed evidence blocked: agent '{agent}' requires at least {minimum_independent} independent source groups"
            )

    return validate_and_admit_evidence(cards, now=now)


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