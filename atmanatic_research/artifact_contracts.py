"""Versioned lineage, verification, and promotion contracts."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

ARTIFACT_SCHEMA_VERSION = 1
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_VERIFICATION_STATUSES = {"verified", "failed", "timed_out", "not_evaluated"}
_PROMOTION_STATUSES = {"approved", "rejected", "expired", "revoked"}
_REVIEW_OUTCOMES = {"challenged_and_resolved", "rejected", "insufficient_evidence"}


class ArtifactContractError(ValueError):
    """Raised when a versioned artifact violates its contract."""


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ArtifactContractError(f"{name} must be an object")
    return value


def _non_empty_string(record: dict[str, Any], key: str, name: str | None = None) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ArtifactContractError(f"{name or key} must be a non-empty string")
    return value


def _timestamp(value: Any, key: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ArtifactContractError(f"{key} must be an ISO timestamp string")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ArtifactContractError(f"{key} must be a valid ISO timestamp") from error


def _sha256(value: Any, key: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ArtifactContractError(f"{key} must be a SHA-256 hex digest")


def _string_list(record: dict[str, Any], key: str, *, required: bool = True) -> list[str]:
    value = record.get(key)
    if not isinstance(value, list) or (required and not value):
        raise ArtifactContractError(f"{key} must be a non-empty list of strings")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ArtifactContractError(f"{key} must contain non-empty strings")
    return value


def _base_lineage(record: dict[str, Any]) -> dict[str, Any]:
    record = _object(record, "artifact")
    if record.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise ArtifactContractError(f"schema_version must be {ARTIFACT_SCHEMA_VERSION}")
    _non_empty_string(record, "artifact_id")
    _string_list(record, "parent_artifact_ids", required=False)
    _non_empty_string(record, "producer")
    _timestamp(record.get("created_at"), "created_at")
    _sha256(record.get("content_hash"), "content_hash")
    if record.get("execution_authorized") is not False:
        raise ArtifactContractError("execution_authorized must be false")
    if "processor_version" in record:
        _non_empty_string(record, "processor_version")
    if "expires_at" in record:
        _timestamp(record.get("expires_at"), "expires_at")
    if "revalidation_policy" in record:
        _non_empty_string(record, "revalidation_policy")
    return record


def validate_artifact_lineage(record: dict[str, Any]) -> dict[str, Any]:
    """Validate common identity, provenance, authority, and lifecycle fields."""
    return _base_lineage(record)


def validate_verification_result(record: dict[str, Any]) -> dict[str, Any]:
    """Validate a deterministic or formal verification result envelope."""
    record = _base_lineage(record)
    _non_empty_string(record, "verifier_name")
    _non_empty_string(record, "verifier_version")
    _sha256(record.get("input_artifact_hash"), "input_artifact_hash")
    _string_list(record, "specification_ids")
    status = record.get("status")
    if status not in _VERIFICATION_STATUSES:
        raise ArtifactContractError(f"status must be one of: {', '.join(sorted(_VERIFICATION_STATUSES))}")
    diagnostics = record.get("diagnostics", [])
    if not isinstance(diagnostics, list) or not all(isinstance(item, str) for item in diagnostics):
        raise ArtifactContractError("diagnostics must be a list of strings")
    if not isinstance(record.get("resource_usage", {}), dict):
        raise ArtifactContractError("resource_usage must be an object")
    _non_empty_string(record, "environment_id")
    return record


def validate_promotion_record(record: dict[str, Any]) -> dict[str, Any]:
    """Validate an explicit, scoped human or governance promotion decision."""
    record = _base_lineage(record)
    _non_empty_string(record, "approver")
    _sha256(record.get("approved_artifact_hash"), "approved_artifact_hash")
    _non_empty_string(record, "approved_scope")
    _timestamp(record.get("approved_at"), "approved_at")
    _non_empty_string(record, "rollback_target")
    status = record.get("status")
    if status not in _PROMOTION_STATUSES:
        raise ArtifactContractError(f"status must be one of: {', '.join(sorted(_PROMOTION_STATUSES))}")
    if status == "approved" and record.get("execution_authorized") is not False:
        raise ArtifactContractError("promotion records remain non-authorizing artifacts")
    return record


def validate_review_outcome(record: dict[str, Any]) -> dict[str, Any]:
    """Validate an explicit independent challenge and review outcome."""
    record = _base_lineage(record)
    reviewer = _non_empty_string(record, "reviewer")
    if reviewer.strip().lower() == record["producer"].strip().lower():
        raise ArtifactContractError("reviewer must be distinct from producer")
    _sha256(record.get("subject_artifact_hash"), "subject_artifact_hash")
    _string_list(record, "challenge_findings")
    outcome = record.get("outcome")
    if outcome not in _REVIEW_OUTCOMES:
        raise ArtifactContractError(f"outcome must be one of: {', '.join(sorted(_REVIEW_OUTCOMES))}")
    if outcome == "challenged_and_resolved" and not record.get("resolution"):
        raise ArtifactContractError("resolution is required for a resolved challenge")
    if "resolution" in record:
        _non_empty_string(record, "resolution")
    return record


def is_expired(record: dict[str, Any], *, now: datetime | None = None) -> bool:
    """Return whether an artifact with an optional expiry has expired."""
    expires_at = record.get("expires_at")
    if not expires_at:
        return False
    try:
        expiry = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
    except ValueError as error:
        raise ArtifactContractError("expires_at must be a valid ISO timestamp") from error
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    return expiry <= (now or datetime.now(timezone.utc))
