"""Versioned lineage, verification, and promotion contracts."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Collection

from .error_codes import (
    ContractError,
    MALFORMED_SYNTAX,
    MISSING_OR_INVALID_FIELD,
    PROHIBITED_AUTHORITY_CLAIM,
    SELF_REVIEW_OR_UNRESOLVED,
    UNSUPPORTED_CRITICAL_EXTENSION,
    UNSUPPORTED_VERSION,
)
from .timestamps import TimestampError, parse_rfc3339

ARTIFACT_SCHEMA_VERSION = 1
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_VERIFICATION_STATUSES = {"verified", "failed", "timed_out", "not_evaluated"}
_PROMOTION_STATUSES = {"approved", "rejected", "expired", "revoked"}
_REVIEW_OUTCOMES = {"challenged_and_resolved", "rejected", "insufficient_evidence"}


class ArtifactContractError(ContractError):
    """Raised when a versioned artifact violates its contract."""


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ArtifactContractError(f"{name} must be an object", code=MALFORMED_SYNTAX)
    return value


def _non_empty_string(record: dict[str, Any], key: str, name: str | None = None) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ArtifactContractError(
            f"{name or key} must be a non-empty string", code=MISSING_OR_INVALID_FIELD
        )
    return value


def _timestamp(value: Any, key: str) -> None:
    try:
        parse_rfc3339(value, key)
    except TimestampError as error:
        raise ArtifactContractError(str(error), code=MISSING_OR_INVALID_FIELD) from error


def _sha256(value: Any, key: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ArtifactContractError(f"{key} must be a SHA-256 hex digest", code=MALFORMED_SYNTAX)


def _string_list(record: dict[str, Any], key: str, *, required: bool = True) -> list[str]:
    value = record.get(key)
    if not isinstance(value, list) or (required and not value):
        raise ArtifactContractError(
            f"{key} must be a non-empty list of strings", code=MISSING_OR_INVALID_FIELD
        )
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ArtifactContractError(
            f"{key} must contain non-empty strings", code=MISSING_OR_INVALID_FIELD
        )
    return value


def _extensions(record: dict[str, Any], supported_extensions: Collection[str] | None) -> None:
    extensions = record.get("extensions")
    critical = record.get("critical_extensions", [])
    if extensions is None and not critical:
        return
    if extensions is not None and not isinstance(extensions, dict):
        raise ArtifactContractError("extensions must be an object", code=MALFORMED_SYNTAX)
    if not isinstance(critical, list) or not all(
        isinstance(item, str) and item.strip() for item in critical
    ):
        raise ArtifactContractError(
            "critical_extensions must be a list of strings", code=MISSING_OR_INVALID_FIELD
        )
    extensions = extensions or {}
    allowed = frozenset(supported_extensions or ())
    for key in critical:
        if key not in extensions:
            raise ArtifactContractError(
                f"critical extension '{key}' is not declared in extensions",
                code=MISSING_OR_INVALID_FIELD,
            )
        if key not in allowed:
            raise ArtifactContractError(
                f"critical extension '{key}' is not supported by this implementation",
                code=UNSUPPORTED_CRITICAL_EXTENSION,
            )


def _base_lineage(
    record: dict[str, Any], *, supported_extensions: Collection[str] | None = None
) -> dict[str, Any]:
    record = _object(record, "artifact")
    if record.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise ArtifactContractError(
            f"schema_version must be {ARTIFACT_SCHEMA_VERSION}", code=UNSUPPORTED_VERSION
        )
    _non_empty_string(record, "artifact_id")
    _string_list(record, "parent_artifact_ids", required=False)
    _non_empty_string(record, "producer")
    _timestamp(record.get("created_at"), "created_at")
    _sha256(record.get("content_hash"), "content_hash")
    if record.get("execution_authorized") is not False:
        raise ArtifactContractError(
            "execution_authorized must be false", code=PROHIBITED_AUTHORITY_CLAIM
        )
    if "processor_version" in record:
        _non_empty_string(record, "processor_version")
    if "expires_at" in record:
        _timestamp(record.get("expires_at"), "expires_at")
    if "revalidation_policy" in record:
        _non_empty_string(record, "revalidation_policy")
    _extensions(record, supported_extensions)
    return record


def validate_artifact_lineage(
    record: dict[str, Any], *, supported_extensions: Collection[str] | None = None
) -> dict[str, Any]:
    """Validate common identity, provenance, authority, and lifecycle fields.

    `supported_extensions` names the critical extension identifiers this
    caller understands. Any `critical_extensions` entry outside that set fails
    closed per the protocol's critical-extension rule.
    """
    return _base_lineage(record, supported_extensions=supported_extensions)


def validate_verification_result(
    record: dict[str, Any], *, supported_extensions: Collection[str] | None = None
) -> dict[str, Any]:
    """Validate a deterministic or formal verification result envelope."""
    record = _base_lineage(record, supported_extensions=supported_extensions)
    _non_empty_string(record, "verifier_name")
    _non_empty_string(record, "verifier_version")
    _sha256(record.get("input_artifact_hash"), "input_artifact_hash")
    _string_list(record, "specification_ids")
    status = record.get("status")
    if status not in _VERIFICATION_STATUSES:
        raise ArtifactContractError(
            f"status must be one of: {', '.join(sorted(_VERIFICATION_STATUSES))}",
            code=MISSING_OR_INVALID_FIELD,
        )
    diagnostics = record.get("diagnostics", [])
    if not isinstance(diagnostics, list) or not all(isinstance(item, str) for item in diagnostics):
        raise ArtifactContractError(
            "diagnostics must be a list of strings", code=MISSING_OR_INVALID_FIELD
        )
    if not isinstance(record.get("resource_usage", {}), dict):
        raise ArtifactContractError("resource_usage must be an object", code=MISSING_OR_INVALID_FIELD)
    _non_empty_string(record, "environment_id")
    return record


def validate_promotion_record(
    record: dict[str, Any], *, supported_extensions: Collection[str] | None = None
) -> dict[str, Any]:
    """Validate an explicit, scoped human or governance promotion decision."""
    record = _base_lineage(record, supported_extensions=supported_extensions)
    _non_empty_string(record, "approver")
    _sha256(record.get("approved_artifact_hash"), "approved_artifact_hash")
    _non_empty_string(record, "approved_scope")
    _timestamp(record.get("approved_at"), "approved_at")
    _non_empty_string(record, "rollback_target")
    status = record.get("status")
    if status not in _PROMOTION_STATUSES:
        raise ArtifactContractError(
            f"status must be one of: {', '.join(sorted(_PROMOTION_STATUSES))}",
            code=MISSING_OR_INVALID_FIELD,
        )
    if status == "approved" and record.get("execution_authorized") is not False:
        raise ArtifactContractError(
            "promotion records remain non-authorizing artifacts", code=PROHIBITED_AUTHORITY_CLAIM
        )
    return record


def validate_review_outcome(
    record: dict[str, Any], *, supported_extensions: Collection[str] | None = None
) -> dict[str, Any]:
    """Validate an explicit independent challenge and review outcome."""
    record = _base_lineage(record, supported_extensions=supported_extensions)
    reviewer = _non_empty_string(record, "reviewer")
    if reviewer.strip().lower() == record["producer"].strip().lower():
        raise ArtifactContractError(
            "reviewer must be distinct from producer", code=SELF_REVIEW_OR_UNRESOLVED
        )
    _sha256(record.get("subject_artifact_hash"), "subject_artifact_hash")
    _string_list(record, "challenge_findings")
    outcome = record.get("outcome")
    if outcome not in _REVIEW_OUTCOMES:
        raise ArtifactContractError(
            f"outcome must be one of: {', '.join(sorted(_REVIEW_OUTCOMES))}",
            code=MISSING_OR_INVALID_FIELD,
        )
    if outcome == "challenged_and_resolved" and not record.get("resolution"):
        raise ArtifactContractError(
            "resolution is required for a resolved challenge", code=SELF_REVIEW_OR_UNRESOLVED
        )
    if "resolution" in record:
        _non_empty_string(record, "resolution")
    return record


def is_expired(record: dict[str, Any], *, now: datetime | None = None) -> bool:
    """Return whether an artifact with an optional expiry has expired."""
    expires_at = record.get("expires_at")
    if not expires_at:
        return False
    try:
        expiry = parse_rfc3339(expires_at, "expires_at")
    except TimestampError as error:
        raise ArtifactContractError(str(error), code=MISSING_OR_INVALID_FIELD) from error
    return expiry <= (now or datetime.now(timezone.utc))
