"""Enforces TRUTH_VALIDITY_STANDARD.md rules against a ValidityPacket.

Zero dependency on downstream products. This module only checks whether a
packet's own stated evidence is complete and internally consistent; it never
decides whether the underlying claim is true.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .codes import (
    EXPIRED_OR_REVOKED,
    INVALID_STATE_TRANSITION,
    MISSING_OR_INVALID_FIELD,
    PROHIBITED_AUTHORITY_CLAIM,
    SELF_REVIEW_OR_UNRESOLVED,
)
from .levels import ValidityLevel, can_advance
from .packet import ValidityPacket

_REQUIRES_REVIEW = {
    ValidityLevel.INDEPENDENTLY_VERIFIED,
    ValidityLevel.AWAITING_HUMAN_PROMOTION,
    ValidityLevel.PROMOTED,
}


@dataclass
class ValidationResult:
    passed: bool
    violations: list[str] = field(default_factory=list)
    violation_codes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.violation_codes) != len(self.violations):
            raise ValueError("violation_codes must pair one-to-one with violations")
        if self.passed and self.violations:
            raise ValueError("a passed result cannot carry violations")


def validate_packet(
    packet: ValidityPacket, *, level: ValidityLevel | None = None, now: datetime | None = None
) -> ValidationResult:
    """Check packet completeness and the anti-sycophancy rules for the given level.

    `level` defaults to the packet's current level; pass the target level when
    checking whether a packet is ready to advance to it.
    """
    now = now or datetime.now(timezone.utc)
    level = level or packet.level
    violations: list[str] = []
    codes: list[str] = []

    def _fail(message: str, code: str) -> None:
        violations.append(message)
        codes.append(code)

    if not packet.claim.strip():
        _fail("claim is empty", MISSING_OR_INVALID_FIELD)
    if not packet.scope.strip():
        _fail("scope is missing", MISSING_OR_INVALID_FIELD)
    if not packet.observations:
        _fail("no direct observations recorded", MISSING_OR_INVALID_FIELD)
    if not packet.evidence_refs:
        _fail("no evidence references / provenance recorded", MISSING_OR_INVALID_FIELD)
    if not packet.falsifier.strip():
        _fail("falsification condition is missing", MISSING_OR_INVALID_FIELD)
    if not packet.counterclaim.strip():
        _fail("counterclaim is missing", MISSING_OR_INVALID_FIELD)
    if not packet.uncertainty.strip():
        _fail("uncertainty statement is missing", MISSING_OR_INVALID_FIELD)
    if not packet.rollback_path.strip():
        _fail("rollback path is missing", MISSING_OR_INVALID_FIELD)
    if not packet.revalidation_policy.strip():
        _fail("revalidation policy is missing", MISSING_OR_INVALID_FIELD)
    if packet.is_expired(now=now):
        _fail("packet has expired and requires revalidation", EXPIRED_OR_REVOKED)

    if level in _REQUIRES_REVIEW:
        if not packet.reviewer:
            _fail("independent reviewer is required at this validity level", SELF_REVIEW_OR_UNRESOLVED)
        elif packet.reviewer.strip().lower() == packet.author.strip().lower():
            _fail("claim author cannot be its own independent reviewer", SELF_REVIEW_OR_UNRESOLVED)
        if not packet.challenge_outcome:
            _fail("resolved challenge outcome is required at this validity level", SELF_REVIEW_OR_UNRESOLVED)

    if level == ValidityLevel.PROMOTED:
        _fail(
            "PROMOTED cannot be granted by this validator; it requires a separate, "
            "explicit human-approval record outside this library",
            PROHIBITED_AUTHORITY_CLAIM,
        )

    return ValidationResult(passed=not violations, violations=violations, violation_codes=codes)


def advance(packet: ValidityPacket, target: ValidityLevel, *, now: datetime | None = None) -> ValidationResult:
    """Attempt to move a packet to the next validity level; never performs the PROMOTED transition."""
    if target == ValidityLevel.PROMOTED:
        return ValidationResult(
            passed=False,
            violations=[
                "PROMOTED cannot be granted by this validator; it requires a separate, "
                "explicit human-approval record outside this library"
            ],
            violation_codes=[PROHIBITED_AUTHORITY_CLAIM],
        )
    if not can_advance(packet.level, target):
        return ValidationResult(
            passed=False,
            violations=[f"cannot advance from {packet.level.value} to {target.value} out of order"],
            violation_codes=[INVALID_STATE_TRANSITION],
        )
    result = validate_packet(packet, level=target, now=now)
    if result.passed:
        packet.level = target
    return result
