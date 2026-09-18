"""First formal/deterministic verification adapter: validity-ladder invariants.

Pilots Phase 5 of ATMANATIC_VERIFIABLE_AGENTIC_RESEARCH_IMPLEMENTATION_PLAN.md
with a narrow, finite, mathematically well-specified property: the validity
ladder's transition rule admits no unreachable level and no non-forward
(non-monotonic) transition other than the explicit reset-to-`observed` escape
hatch. This is a claim about the declared transition table, not about
external reality, source honesty, or operational safety.

This adapter has no untrusted input and requires no sandbox: it checks a
fixed, reviewed specification against the fixed `validity_protocol.levels`
rule. A future adapter that accepts untrusted specifications or code (for
example, a Lean proof) MUST run in a network-isolated, resource-limited
sandbox per the implementation plan's Phase 5 guidance; that sandbox remains
unbuilt and is explicitly out of scope here.
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from typing import Any, Callable

from validity_protocol.levels import ValidityLevel, can_advance

from .artifact_contracts import validate_verification_result
from .canonical import canonical_json_bytes, compute_content_hash

VERIFIER_NAME = "validity-transition-table-checker"
VERIFIER_VERSION = "1.0.0"
SPECIFICATION_ID = "spec:validity-ladder-monotonic-reachability"


def check_validity_transition_table(
    levels: list[ValidityLevel] | None = None,
    can_advance_fn: Callable[[ValidityLevel, ValidityLevel], bool] | None = None,
) -> tuple[bool, list[str]]:
    """Check a validity ladder for unreachable levels and non-monotonic edges.

    `levels` and `can_advance_fn` default to the real ladder and rule; they are
    overridable so this narrow invariant checker itself can be tested against
    a deliberately broken specification.
    """
    levels = list(levels) if levels is not None else list(ValidityLevel)
    can_advance_fn = can_advance_fn or can_advance
    diagnostics: list[str] = []

    for index, level in enumerate(levels):
        if index == 0:
            continue
        predecessor = levels[index - 1]
        if not can_advance_fn(predecessor, level):
            diagnostics.append(
                f"{level.value} is not reachable by one forward step from {predecessor.value}"
            )

    for source in levels:
        for target in levels:
            if source == target or target == ValidityLevel.OBSERVED:
                continue
            if can_advance_fn(source, target) and levels.index(target) <= levels.index(source):
                diagnostics.append(f"{source.value} can advance to non-forward level {target.value}")

    return (not diagnostics, diagnostics)


def _ladder_specification_hash() -> str:
    """Hash of the declared ladder order; the exact input this pilot verifies."""
    return hashlib.sha256(canonical_json_bytes([level.value for level in ValidityLevel])).hexdigest()


def run_validity_transition_pilot(
    *, environment_id: str, now: datetime | None = None
) -> dict[str, Any]:
    """Run the narrow invariant check and return a `validate_verification_result`-conformant record.

    The result is reproducible from the recorded input alone: `input_artifact_hash`
    is the hash of the declared ladder order this run checked, not an
    ambient or caller-supplied value.
    """
    started = time.perf_counter()
    ok, diagnostics = check_validity_transition_table()
    elapsed_ms = (time.perf_counter() - started) * 1000

    record: dict[str, Any] = {
        "schema_version": 1,
        "artifact_id": f"verification-{SPECIFICATION_ID}",
        "parent_artifact_ids": [],
        "producer": VERIFIER_NAME,
        "created_at": (now or datetime.now(timezone.utc)).isoformat(),
        "content_hash": "0" * 64,
        "execution_authorized": False,
        "verifier_name": VERIFIER_NAME,
        "verifier_version": VERIFIER_VERSION,
        "input_artifact_hash": _ladder_specification_hash(),
        "specification_ids": [SPECIFICATION_ID],
        "status": "verified" if ok else "failed",
        "diagnostics": diagnostics,
        "resource_usage": {"wall_time_ms": round(elapsed_ms, 3)},
        "environment_id": environment_id,
    }
    record["content_hash"] = compute_content_hash(record)
    return validate_verification_result(record)
