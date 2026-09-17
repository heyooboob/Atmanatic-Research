"""Strict provider-neutral proposal envelopes for external orchestrators."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping

PROPOSAL_SCHEMA_VERSION = 1
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


class ProposalContractError(ValueError):
    """Raised when proposer output violates the versioned envelope contract."""


@dataclass(frozen=True)
class ProposalEnvelope:
    schema_version: int
    proposal_id: str
    parent_proposal_id: str | None
    producer: str
    created_at: str
    content_hash: str
    evidence_refs: tuple[str, ...]
    tool_versions: Mapping[str, str]
    payload: Mapping[str, Any]
    execution_authorized: bool


def _non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProposalContractError(f"{field} must be a non-empty string")
    return value


def validate_proposal_envelope(value: dict[str, Any]) -> ProposalEnvelope:
    """Validate untrusted proposer output and return an immutable typed envelope."""
    if not isinstance(value, dict):
        raise ProposalContractError("proposal envelope must be an object")
    if value.get("schema_version") != PROPOSAL_SCHEMA_VERSION:
        raise ProposalContractError(
            f"schema_version must be {PROPOSAL_SCHEMA_VERSION}"
        )
    proposal_id = _non_empty_string(value.get("proposal_id"), "proposal_id")
    parent_proposal_id = value.get("parent_proposal_id")
    if parent_proposal_id is not None:
        parent_proposal_id = _non_empty_string(
            parent_proposal_id, "parent_proposal_id"
        )
        if parent_proposal_id == proposal_id:
            raise ProposalContractError("parent_proposal_id must differ from proposal_id")
    producer = _non_empty_string(value.get("producer"), "producer")
    created_at = _non_empty_string(value.get("created_at"), "created_at")
    try:
        parsed_created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise ProposalContractError("created_at must be a valid ISO timestamp") from error
    if parsed_created_at.tzinfo is None:
        raise ProposalContractError("created_at must include a timezone")
    content_hash = _non_empty_string(value.get("content_hash"), "content_hash")
    if not _SHA256.fullmatch(content_hash):
        raise ProposalContractError("content_hash must be a SHA-256 hex digest")

    evidence_refs = value.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs or not all(
        isinstance(reference, str) and reference.strip() for reference in evidence_refs
    ):
        raise ProposalContractError("evidence_refs must be a non-empty list of strings")
    if len(evidence_refs) != len(set(evidence_refs)):
        raise ProposalContractError("evidence_refs must be unique")
    tool_versions = value.get("tool_versions")
    if not isinstance(tool_versions, dict) or not tool_versions or not all(
        isinstance(name, str)
        and name.strip()
        and isinstance(version, str)
        and version.strip()
        for name, version in tool_versions.items()
    ):
        raise ProposalContractError(
            "tool_versions must be a non-empty mapping of names to versions"
        )
    payload = value.get("payload")
    if not isinstance(payload, dict) or not payload:
        raise ProposalContractError("payload must be a non-empty object")
    if value.get("execution_authorized") is not False:
        raise ProposalContractError("execution_authorized must be false")

    return ProposalEnvelope(
        schema_version=PROPOSAL_SCHEMA_VERSION,
        proposal_id=proposal_id,
        parent_proposal_id=parent_proposal_id,
        producer=producer,
        created_at=created_at,
        content_hash=content_hash.lower(),
        evidence_refs=tuple(evidence_refs),
        tool_versions=MappingProxyType(dict(tool_versions)),
        payload=MappingProxyType(dict(payload)),
        execution_authorized=False,
    )