"""The validity packet: the required evidence bundle a claim must carry (TRUTH_VALIDITY_STANDARD.md)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .levels import ValidityLevel


@dataclass
class Observation:
    description: str
    observed_at: datetime


@dataclass
class ValidityPacket:
    claim: str
    scope: str
    author: str
    observations: list[Observation]
    evidence_refs: list[str]
    falsifier: str
    counterclaim: str
    uncertainty: str
    limitations: str
    rollback_path: str
    expiry: datetime
    revalidation_policy: str
    level: ValidityLevel = ValidityLevel.OBSERVED
    reviewer: str | None = None
    challenge_outcome: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self, *, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        return now >= self.expiry
