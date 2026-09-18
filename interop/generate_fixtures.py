"""Generates the Atmanatic interoperability fixture corpus from the reference implementation.

Each fixture pairs a canonical input artifact with its actual, verified verdict
(accept, or reject with its error code) as produced by the Python reference
validators in `atmanatic_research`. An independent implementation is expected
to reproduce the same verdict and error code for every fixture; this is the
basis for the Draft 0.1 interoperability report described in
ATMANATIC_PROTOCOL_0.1_DRAFT.md section 14.

Fixtures are generated, not hand-written, so they cannot silently drift from
what the reference implementation actually does: this script fails closed if
a case's declared expectation does not match the validator's real behavior.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from atmanatic_research import (  # noqa: E402
    ContractError,
    validate_artifact_lineage,
    validate_evidence_card,
    validate_promotion_record,
    validate_proposal_envelope,
    validate_review_outcome,
    validate_verification_result,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
HASH_A = "a" * 64

SCHEMA_BY_TYPE = {
    "artifact_lineage": "common_envelope.schema.json",
    "evidence_card": "evidence_card.schema.json",
    "proposal_envelope": "proposal_envelope.schema.json",
    "review_outcome": "review_outcome.schema.json",
    "verification_result": "verification_result.schema.json",
    "promotion_record": "promotion_record.schema.json",
}


def _case(
    case_id: str,
    description: str,
    input_value: dict[str, Any],
    verdict: str,
    error_code: str | None = None,
) -> dict[str, Any]:
    expected = {"verdict": "accept"} if verdict == "accept" else {"verdict": "reject", "error_code": error_code}
    return {"case_id": case_id, "description": description, "input": input_value, "expected": expected}


def _lineage(**overrides: Any) -> dict[str, Any]:
    record = {
        "schema_version": 1,
        "artifact_id": "artifact-1",
        "parent_artifact_ids": [],
        "producer": "research-agent",
        "created_at": "2026-09-18T00:00:00+00:00",
        "content_hash": HASH_A,
        "execution_authorized": False,
    }
    record.update(overrides)
    return record


def _evidence_card(**overrides: Any) -> dict[str, Any]:
    record = {
        "evidence_id": "e-1",
        "claim": "a claim",
        "source_ids": ["s-1"],
        "agent": "agent",
        "observed_at": "2026-09-18T00:00:00+00:00",
        "confidence": 0.5,
        "content_hash": "hash",
        "status": "fresh",
        "details": {},
    }
    record.update(overrides)
    return record


def _proposal(**overrides: Any) -> dict[str, Any]:
    record = {
        "schema_version": 1,
        "proposal_id": "p-1",
        "parent_proposal_id": None,
        "producer": "agent",
        "created_at": "2026-09-18T00:00:00Z",
        "content_hash": HASH_A,
        "evidence_refs": ["e-1"],
        "tool_versions": {"agent": "1.0"},
        "payload": {"claim": "x"},
        "execution_authorized": False,
    }
    record.update(overrides)
    return record


CASE_SUITES: dict[str, tuple[Callable[[dict[str, Any]], Any], list[dict[str, Any]]]] = {
    "artifact_lineage": (
        validate_artifact_lineage,
        [
            _case("artifact_lineage-positive-001", "minimal valid lineage envelope", _lineage(), "accept"),
            _case(
                "artifact_lineage-negative-authority",
                "execution_authorized true must fail closed",
                _lineage(execution_authorized=True),
                "reject",
                "prohibited_authority_claim",
            ),
            _case(
                "artifact_lineage-negative-version",
                "unsupported schema_version must fail closed",
                _lineage(schema_version=99),
                "reject",
                "unsupported_version",
            ),
            _case(
                "artifact_lineage-negative-hash-format",
                "malformed content_hash must fail closed",
                _lineage(content_hash="not-a-hash"),
                "reject",
                "malformed_syntax",
            ),
            _case(
                "artifact_lineage-boundary-naive-timestamp",
                "naive created_at (no UTC offset) must fail closed",
                _lineage(created_at="2026-09-18T00:00:00"),
                "reject",
                "missing_or_invalid_field",
            ),
        ],
    ),
    "evidence_card": (
        validate_evidence_card,
        [
            _case("evidence_card-positive-001", "minimal valid evidence card", _evidence_card(), "accept"),
            _case("evidence_card-negative-empty", "empty object must fail closed", {}, "reject", "missing_or_invalid_field"),
            _case(
                "evidence_card-negative-confidence-range",
                "confidence outside [0,1] must fail closed",
                _evidence_card(confidence=1.5),
                "reject",
                "missing_or_invalid_field",
            ),
            _case(
                "evidence_card-boundary-naive-timestamp",
                "naive observed_at must fail closed",
                _evidence_card(observed_at="2026-09-18T00:00:00"),
                "reject",
                "missing_or_invalid_field",
            ),
        ],
    ),
    "proposal_envelope": (
        validate_proposal_envelope,
        [
            _case("proposal_envelope-positive-001", "minimal valid proposal envelope", _proposal(), "accept"),
            _case(
                "proposal_envelope-negative-authority",
                "execution_authorized true must fail closed",
                _proposal(execution_authorized=True),
                "reject",
                "prohibited_authority_claim",
            ),
            _case(
                "proposal_envelope-negative-duplicate-evidence-refs",
                "duplicate evidence_refs must fail closed",
                _proposal(evidence_refs=["e-1", "e-1"]),
                "reject",
                "missing_or_invalid_field",
            ),
        ],
    ),
    "review_outcome": (
        validate_review_outcome,
        [
            _case(
                "review_outcome-positive-001",
                "resolved, independent review",
                _lineage(
                    reviewer="independent-reviewer",
                    subject_artifact_hash=HASH_A,
                    challenge_findings=["tested the declared boundary"],
                    outcome="challenged_and_resolved",
                    resolution="the boundary held for the declared fixture",
                ),
                "accept",
            ),
            _case(
                "review_outcome-negative-self-review",
                "reviewer equal to producer must fail closed",
                _lineage(
                    reviewer="research-agent",
                    subject_artifact_hash=HASH_A,
                    challenge_findings=["tested"],
                    outcome="challenged_and_resolved",
                    resolution="resolved",
                ),
                "reject",
                "self_review_or_unresolved",
            ),
            _case(
                "review_outcome-negative-unresolved",
                "resolved outcome without a resolution must fail closed",
                _lineage(
                    reviewer="independent-reviewer",
                    subject_artifact_hash=HASH_A,
                    challenge_findings=["tested"],
                    outcome="challenged_and_resolved",
                ),
                "reject",
                "self_review_or_unresolved",
            ),
        ],
    ),
    "verification_result": (
        validate_verification_result,
        [
            _case(
                "verification_result-positive-001",
                "minimal valid verification result",
                _lineage(
                    verifier_name="deterministic-checker",
                    verifier_version="1.0",
                    input_artifact_hash=HASH_A,
                    specification_ids=["spec-1"],
                    status="verified",
                    diagnostics=[],
                    resource_usage={},
                    environment_id="ci",
                ),
                "accept",
            ),
            _case(
                "verification_result-negative-status",
                "unknown status must fail closed",
                _lineage(
                    verifier_name="deterministic-checker",
                    verifier_version="1.0",
                    input_artifact_hash=HASH_A,
                    specification_ids=["spec-1"],
                    status="approved",
                    diagnostics=[],
                    resource_usage={},
                    environment_id="ci",
                ),
                "reject",
                "missing_or_invalid_field",
            ),
        ],
    ),
    "promotion_record": (
        validate_promotion_record,
        [
            _case(
                "promotion_record-positive-001",
                "explicit, scoped, non-authorizing promotion",
                _lineage(
                    approver="human-reviewer",
                    approved_artifact_hash=HASH_A,
                    approved_scope="bounded evaluation environment",
                    approved_at="2026-09-18T01:00:00+00:00",
                    rollback_target="artifact-previous",
                    status="approved",
                ),
                "accept",
            ),
            _case(
                "promotion_record-negative-status",
                "unknown status must fail closed",
                _lineage(
                    approver="human-reviewer",
                    approved_artifact_hash=HASH_A,
                    approved_scope="bounded evaluation environment",
                    approved_at="2026-09-18T01:00:00+00:00",
                    rollback_target="artifact-previous",
                    status="not-a-real-status",
                ),
                "reject",
                "missing_or_invalid_field",
            ),
        ],
    ),
}


def _actual_verdict(validator: Callable[[dict[str, Any]], Any], input_value: dict[str, Any]) -> tuple[str, str | None]:
    try:
        validator(input_value)
        return "accept", None
    except ContractError as error:
        return "reject", error.code
    except ValueError:
        return "reject", None


def generate() -> list[dict[str, str]]:
    """Regenerate every fixture file, failing closed on any expectation mismatch."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, str]] = []
    for artifact_type, (validator, cases) in CASE_SUITES.items():
        type_dir = FIXTURES_DIR / artifact_type
        type_dir.mkdir(parents=True, exist_ok=True)
        for case in cases:
            actual_verdict, actual_code = _actual_verdict(validator, case["input"])
            expected = case["expected"]
            if actual_verdict != expected["verdict"]:
                raise SystemExit(
                    f"fixture generation refused: case '{case['case_id']}' expected verdict "
                    f"'{expected['verdict']}' but the validator actually returned '{actual_verdict}'"
                )
            if expected["verdict"] == "reject" and expected.get("error_code") is not None:
                if actual_code != expected["error_code"]:
                    raise SystemExit(
                        f"fixture generation refused: case '{case['case_id']}' expected error_code "
                        f"'{expected['error_code']}' but the validator actually raised '{actual_code}'"
                    )

            fixture_record = {
                "case_id": case["case_id"],
                "artifact_type": artifact_type,
                "schema": SCHEMA_BY_TYPE[artifact_type],
                "description": case["description"],
                "input": case["input"],
                "expected": expected,
            }
            fixture_path = type_dir / f"{case['case_id']}.json"
            fixture_path.write_text(json.dumps(fixture_record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            manifest.append(
                {
                    "artifact_type": artifact_type,
                    "case_id": case["case_id"],
                    "path": str(fixture_path.relative_to(FIXTURES_DIR)).replace("\\", "/"),
                }
            )

    manifest = sorted(manifest, key=lambda entry: (entry["artifact_type"], entry["case_id"]))
    manifest_path = FIXTURES_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    manifest = generate()
    print(f"generated {len(manifest)} fixtures across {len(CASE_SUITES)} artifact types")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
