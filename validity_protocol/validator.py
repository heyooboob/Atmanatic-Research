"""Enforces TRUTH_VALIDITY_STANDARD.md rules against a ValidityPacket.

Zero dependency on downstream products. This module only checks whether a
packet's own stated evidence is complete and internally consistent; it never
decides whether the underlying claim is true.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

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

    if not packet.claim.strip():
        violations.append("claim is empty")
    if not packet.scope.strip():
        violations.append("scope is missing")
    if not packet.observations:
        violations.append("no direct observations recorded")
    if not packet.evidence_refs:
        violations.append("no evidence references / provenance recorded")
    if not packet.falsifier.strip():
        violations.append("falsification condition is missing")
    if not packet.counterclaim.strip():
        violations.append("counterclaim is missing")
    if not packet.uncertainty.strip():
        violations.append("uncertainty statement is missing")
    if not packet.rollback_path.strip():
        violations.append("rollback path is missing")
    if not packet.revalidation_policy.strip():
        violations.append("revalidation policy is missing")
    if packet.is_expired(now=now):
        violations.append("packet has expired and requires revalidation")

    if level in _REQUIRES_REVIEW:
        if not packet.reviewer:
            violations.append("independent reviewer is required at this validity level")
        elif packet.reviewer.strip().lower() == packet.author.strip().lower():
            violations.append("claim author cannot be its own independent reviewer")
        if not packet.challenge_outcome:
            violations.append("resolved challenge outcome is required at this validity level")

    if level == ValidityLevel.PROMOTED:
        violations.append(
            "PROMOTED cannot be granted by this validator; it requires a separate, "
            "explicit human-approval record outside this library"
        )

    return ValidationResult(passed=not violations, violations=violations)


def advance(packet: ValidityPacket, target: ValidityLevel, *, now: datetime | None = None) -> ValidationResult:
    """Attempt to move a packet to the next validity level; never performs the PROMOTED transition."""
    if target == ValidityLevel.PROMOTED:
        return ValidationResult(
            passed=False,
            violations=[
                "PROMOTED cannot be granted by this validator; it requires a separate, "
                "explicit human-approval record outside this library"
            ],
        )
    if not can_advance(packet.level, target):
        return ValidationResult(
            passed=False,
            violations=[f"cannot advance from {packet.level.value} to {target.value} out of order"],
        )
    result = validate_packet(packet, level=target, now=now)
    if result.passed:
        packet.level = target
    return result
