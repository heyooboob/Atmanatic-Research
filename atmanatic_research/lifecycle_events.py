"""Append-only lifecycle transition-event log wrapping validity advancement.

Implements ATMANATIC_PROTOCOL_0.1_DRAFT.md section 7.1: every attempted
transition is recorded as an immutable event, independent of whether the
in-memory packet mutated. The event log is the audit history; the packet
object itself is not.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Collection

from validity_protocol import ValidationResult, ValidityLevel
from validity_protocol.jsonl import JsonLinesLog

from .error_codes import (
    ContractError,
    INVALID_STATE_TRANSITION,
    MALFORMED_SYNTAX,
    MISSING_OR_INVALID_FIELD,
    UNSUPPORTED_VERSION,
)
from .timestamps import TimestampError, parse_rfc3339

LIFECYCLE_EVENT_SCHEMA_VERSION = 1
_VALID_LEVELS = {level.value for level in ValidityLevel}
_RESULTS = {"accepted", "rejected"}


class LifecycleEventError(ContractError):
    """Raised when a lifecycle transition event is malformed."""


def validate_lifecycle_event(record: dict[str, Any]) -> dict[str, Any]:
    """Validate the immutable transition-event envelope."""
    if not isinstance(record, dict):
        raise LifecycleEventError("lifecycle event must be an object", code=MALFORMED_SYNTAX)
    if record.get("schema_version") != LIFECYCLE_EVENT_SCHEMA_VERSION:
        raise LifecycleEventError(
            f"schema_version must be {LIFECYCLE_EVENT_SCHEMA_VERSION}", code=UNSUPPORTED_VERSION
        )
    for field_name in ("event_id", "prior_level", "requested_level", "actor"):
        value = record.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise LifecycleEventError(f"{field_name} must be a non-empty string", code=MISSING_OR_INVALID_FIELD)
    if record["prior_level"] not in _VALID_LEVELS or record["requested_level"] not in _VALID_LEVELS:
        raise LifecycleEventError(
            "prior_level and requested_level must be known validity levels", code=MISSING_OR_INVALID_FIELD
        )
    try:
        parse_rfc3339(record.get("created_at"), "created_at")
    except TimestampError as error:
        raise LifecycleEventError(str(error), code=MISSING_OR_INVALID_FIELD) from error
    if not isinstance(record.get("packet_content_hash"), str) or not record["packet_content_hash"].strip():
        raise LifecycleEventError("packet_content_hash must be a non-empty string", code=MISSING_OR_INVALID_FIELD)
    supporting = record.get("supporting_artifact_hashes", [])
    if not isinstance(supporting, list) or not all(isinstance(item, str) for item in supporting):
        raise LifecycleEventError(
            "supporting_artifact_hashes must be a list of strings", code=MISSING_OR_INVALID_FIELD
        )
    if record.get("result") not in _RESULTS:
        raise LifecycleEventError("result must be 'accepted' or 'rejected'", code=MISSING_OR_INVALID_FIELD)
    violations = record.get("violations", [])
    if not isinstance(violations, list) or not all(isinstance(item, str) for item in violations):
        raise LifecycleEventError("violations must be a list of strings", code=MISSING_OR_INVALID_FIELD)
    violation_codes = record.get("violation_codes", [])
    if not isinstance(violation_codes, list) or not all(isinstance(item, str) for item in violation_codes):
        raise LifecycleEventError("violation_codes must be a list of strings", code=MISSING_OR_INVALID_FIELD)
    if violation_codes and len(violation_codes) != len(violations):
        raise LifecycleEventError(
            "violation_codes must pair one-to-one with violations when present",
            code=MISSING_OR_INVALID_FIELD,
        )
    if record["result"] == "rejected" and not violations:
        raise LifecycleEventError(
            "rejected transitions must record at least one violation", code=INVALID_STATE_TRANSITION
        )
    if record["result"] == "accepted" and violations:
        raise LifecycleEventError(
            "accepted transitions must not carry violations", code=INVALID_STATE_TRANSITION
        )
    if record["result"] == "accepted" and violation_codes:
        raise LifecycleEventError(
            "accepted transitions must not carry violation_codes", code=INVALID_STATE_TRANSITION
        )
    return record


def record_transition(
    packet: Any,
    *,
    actor: str,
    event_id: str,
    transition: Callable[[], ValidationResult],
    requested_level: ValidityLevel,
    supporting_artifact_hashes: Collection[str] = (),
    now: datetime | None = None,
) -> tuple[ValidationResult, dict[str, Any]]:
    """Run `transition`, then record the attempt as an immutable, validated event.

    The event is recorded regardless of whether the transition passed or
    failed, and regardless of whether the packet mutated.
    """
    prior_level = packet.level.value
    packet_hash = packet.metadata.get("content_hash", "")
    result = transition()
    event = {
        "schema_version": LIFECYCLE_EVENT_SCHEMA_VERSION,
        "event_id": event_id,
        "packet_content_hash": packet_hash,
        "prior_level": prior_level,
        "requested_level": requested_level.value,
        "actor": actor,
        "created_at": (now or datetime.now(timezone.utc)).isoformat(),
        "supporting_artifact_hashes": list(supporting_artifact_hashes),
        "result": "accepted" if result.passed else "rejected",
        "violations": list(result.violations),
        "violation_codes": list(result.violation_codes),
    }
    return result, validate_lifecycle_event(event)


class LifecycleEventLog:
    """Append-only JSON-lines log of validated lifecycle transition events."""

    def __init__(self, path: Path):
        self._log = JsonLinesLog(path)

    @property
    def path(self) -> Path:
        return self._log.path

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        validated = validate_lifecycle_event(event)
        self._log.append_record(validated, sort_keys=True)
        return validated

    def read_all(self) -> list[dict[str, Any]]:
        return self._log.read_all()

    def latest_status(self) -> dict[str, dict[str, Any]]:
        """Return the most recent event per packet, keyed by `packet_content_hash`.

        Recency is resolved by `created_at`, not by arrival/write order, per
        the protocol's revocation and revalidation requirements.
        """
        latest: dict[str, dict[str, Any]] = {}
        for event in self.read_all():
            key = event["packet_content_hash"]
            current = latest.get(key)
            if current is None or event["created_at"] >= current["created_at"]:
                latest[key] = event
        return latest
