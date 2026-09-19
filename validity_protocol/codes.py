"""Stable machine-readable violation codes for validity-packet transitions.

Values intentionally mirror the corresponding entries in
`atmanatic_research/error_codes.py` so the two registries agree, but this
module defines its own constants rather than importing that package: this
package has zero dependency on downstream products (see the package
docstring in `__init__.py`), and `atmanatic_research` depends on
`validity_protocol`, not the reverse. `tests/test_validity_protocol.py`
guards the two registries against drift.

Codes are protocol API: adding one is additive, removing or repurposing one
is breaking. Human-readable violation text may change freely.
"""

from __future__ import annotations

MISSING_OR_INVALID_FIELD = "missing_or_invalid_field"
EXPIRED_OR_REVOKED = "expired_or_revoked"
SELF_REVIEW_OR_UNRESOLVED = "self_review_or_unresolved"
INVALID_STATE_TRANSITION = "invalid_state_transition"
PROHIBITED_AUTHORITY_CLAIM = "prohibited_authority_claim"

VIOLATION_CODES = frozenset(
    {
        MISSING_OR_INVALID_FIELD,
        EXPIRED_OR_REVOKED,
        SELF_REVIEW_OR_UNRESOLVED,
        INVALID_STATE_TRANSITION,
        PROHIBITED_AUTHORITY_CLAIM,
    }
)
