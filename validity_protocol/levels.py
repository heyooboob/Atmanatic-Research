"""The six-stage validity ladder from TRUTH_VALIDITY_STANDARD.md, as an enforceable enum."""

from __future__ import annotations

from enum import Enum


class ValidityLevel(str, Enum):
    OBSERVED = "observed"
    TESTED = "tested"
    VALIDATED_IN_SCOPE = "validated_in_scope"
    INDEPENDENTLY_VERIFIED = "independently_verified"
    AWAITING_HUMAN_PROMOTION = "awaiting_human_promotion"
    PROMOTED = "promoted"


_ORDER = [
    ValidityLevel.OBSERVED,
    ValidityLevel.TESTED,
    ValidityLevel.VALIDATED_IN_SCOPE,
    ValidityLevel.INDEPENDENTLY_VERIFIED,
    ValidityLevel.AWAITING_HUMAN_PROMOTION,
    ValidityLevel.PROMOTED,
]

_RANK = {level: index for index, level in enumerate(_ORDER)}


def rank(level: ValidityLevel) -> int:
    return _RANK[level]


def can_advance(current: ValidityLevel, target: ValidityLevel) -> bool:
    """Levels advance one step at a time; expiry/revalidation may always drop a packet back to OBSERVED."""
    if target == ValidityLevel.OBSERVED:
        return True
    return rank(target) == rank(current) + 1
