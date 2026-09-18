"""Stable machine-readable error codes shared by protocol validators.

Codes are protocol API and follow the same compatibility rules as artifact
schemas: adding a code is additive, removing or repurposing one is breaking.
Human-readable exception messages may change without a protocol version
change.
"""

from __future__ import annotations

MALFORMED_SYNTAX = "malformed_syntax"
UNSUPPORTED_VERSION = "unsupported_version"
UNSUPPORTED_CRITICAL_EXTENSION = "unsupported_critical_extension"
MISSING_OR_INVALID_FIELD = "missing_or_invalid_field"
HASH_MISMATCH = "hash_mismatch"
EXPIRED_OR_REVOKED = "expired_or_revoked"
UNRESOLVED_REFERENCE = "unresolved_reference"
SOURCE_POLICY_REJECTED = "source_policy_rejected"
EVIDENCE_CONFLICT = "evidence_conflict"
SELF_REVIEW_OR_UNRESOLVED = "self_review_or_unresolved"
INVALID_STATE_TRANSITION = "invalid_state_transition"
PROHIBITED_AUTHORITY_CLAIM = "prohibited_authority_claim"

ERROR_CODES = frozenset(
    {
        MALFORMED_SYNTAX,
        UNSUPPORTED_VERSION,
        UNSUPPORTED_CRITICAL_EXTENSION,
        MISSING_OR_INVALID_FIELD,
        HASH_MISMATCH,
        EXPIRED_OR_REVOKED,
        UNRESOLVED_REFERENCE,
        SOURCE_POLICY_REJECTED,
        EVIDENCE_CONFLICT,
        SELF_REVIEW_OR_UNRESOLVED,
        INVALID_STATE_TRANSITION,
        PROHIBITED_AUTHORITY_CLAIM,
    }
)


class ContractError(ValueError):
    """Base contract violation carrying a stable machine-readable error code."""

    def __init__(self, message: str, *, code: str) -> None:
        if code not in ERROR_CODES:
            raise ValueError(f"unknown error code: {code}")
        super().__init__(message)
        self.code = code
