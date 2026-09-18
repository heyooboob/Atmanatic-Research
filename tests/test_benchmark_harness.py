import unittest

from atmanatic_research import (
    BenchmarkCase,
    BenchmarkHarnessError,
    run_benchmark,
    validate_artifact_lineage,
    validate_evidence_card,
    validate_promotion_record,
    validate_proposal_envelope,
    validate_review_outcome,
    validate_source_definition,
    validate_benchmark,
)


def _valid_lineage():
    return {
        "schema_version": 1,
        "artifact_id": "artifact-1",
        "parent_artifact_ids": [],
        "producer": "research-agent",
        "created_at": "2026-09-17T00:00:00+00:00",
        "content_hash": "a" * 64,
        "execution_authorized": False,
    }


def _invalid_lineage():
    record = _valid_lineage()
    record["execution_authorized"] = True
    return record


def _valid_proposal():
    return {
        "schema_version": 1,
        "proposal_id": "p-1",
        "parent_proposal_id": None,
        "producer": "agent",
        "created_at": "2026-09-17T12:00:00Z",
        "content_hash": "a" * 64,
        "evidence_refs": ["e-1"],
        "tool_versions": {"agent": "1.0"},
        "payload": {"claim": "x"},
        "execution_authorized": False,
    }


def _valid_promotion():
    record = _valid_lineage()
    record.update(
        {
            "approver": "human-reviewer",
            "approved_artifact_hash": "a" * 64,
            "approved_scope": "bounded evaluation environment",
            "approved_at": "2026-09-17T01:00:00+00:00",
            "rollback_target": "artifact-previous",
            "status": "approved",
        }
    )
    return record


def _valid_review():
    record = _valid_lineage()
    record.update(
        {
            "reviewer": "independent-reviewer",
            "subject_artifact_hash": "a" * 64,
            "challenge_findings": ["tested the declared boundary"],
            "outcome": "challenged_and_resolved",
            "resolution": "the boundary held for the declared fixture",
        }
    )
    return record


VALIDATORS = {
    "artifact_lineage": validate_artifact_lineage,
    "evidence_card": validate_evidence_card,
    "proposal_envelope": validate_proposal_envelope,
    "source_definition": validate_source_definition,
    "promotion_record": validate_promotion_record,
    "review_outcome": validate_review_outcome,
}

CASES = [
    BenchmarkCase("artifact-valid", "artifact_lineage", _valid_lineage(), "accept"),
    BenchmarkCase("artifact-invalid-authority", "artifact_lineage", _invalid_lineage(), "reject"),
    BenchmarkCase(
        "evidence-missing-fields", "evidence_card", {}, "reject"
    ),
    BenchmarkCase(
        "evidence-valid",
        "evidence_card",
        {
            "evidence_id": "e-1",
            "claim": "a claim",
            "source_ids": ["s-1"],
            "agent": "agent",
            "observed_at": "2026-09-17T00:00:00+00:00",
            "confidence": 0.5,
            "content_hash": "hash",
            "status": "fresh",
            "details": {},
        },
        "accept",
    ),
    BenchmarkCase("proposal-valid", "proposal_envelope", _valid_proposal(), "accept"),
    BenchmarkCase(
        "proposal-invalid-authority",
        "proposal_envelope",
        {**_valid_proposal(), "execution_authorized": True},
        "reject",
    ),
    BenchmarkCase("source-valid", "source_definition", {"source_id": "s-1"}, "accept"),
    BenchmarkCase("source-missing-id", "source_definition", {"source_id": ""}, "reject"),
    BenchmarkCase("promotion-valid", "promotion_record", _valid_promotion(), "accept"),
    BenchmarkCase(
        "promotion-invalid-status",
        "promotion_record",
        {**_valid_promotion(), "status": "not-a-real-status"},
        "reject",
    ),
    BenchmarkCase("review-valid", "review_outcome", _valid_review(), "accept"),
    BenchmarkCase(
        "review-self-authored",
        "review_outcome",
        {**_valid_review(), "reviewer": "research-agent"},
        "reject",
    ),
]


class BenchmarkHarnessTests(unittest.TestCase):
    def test_run_benchmark_produces_conformant_record(self):
        record = run_benchmark(CASES, VALIDATORS, benchmark_id="core-contracts", processor_version="1.0.0")
        validated = validate_benchmark(record)
        self.assertEqual(validated["metrics"]["false_accept_rate"], 0.0)
        self.assertEqual(validated["metrics"]["false_reject_rate"], 0.0)
        self.assertTrue(all(case["passed"] for case in validated["cases"]))

    def test_deliberately_broken_validator_fails_the_gate(self):
        broken_validators = dict(VALIDATORS)
        broken_validators["artifact_lineage"] = lambda record: record  # accepts everything
        record = run_benchmark(CASES, broken_validators, benchmark_id="core-contracts", processor_version="1.0.0")
        failing = [case for case in record["cases"] if not case["passed"]]
        self.assertTrue(failing)
        self.assertEqual(failing[0]["case_id"], "artifact-invalid-authority")

    def test_unknown_validator_reference_raises(self):
        bad_case = BenchmarkCase("bad", "does-not-exist", {}, "accept")
        with self.assertRaises(BenchmarkHarnessError):
            run_benchmark([bad_case], VALIDATORS, benchmark_id="x", processor_version="1.0.0")

    def test_empty_cases_rejected(self):
        with self.assertRaises(BenchmarkHarnessError):
            run_benchmark([], VALIDATORS, benchmark_id="x", processor_version="1.0.0")

    def test_expected_code_is_checked_when_declared(self):
        case = BenchmarkCase(
            "artifact-invalid-authority-code",
            "artifact_lineage",
            _invalid_lineage(),
            "reject",
            expected_code="prohibited_authority_claim",
        )
        record = run_benchmark([case], VALIDATORS, benchmark_id="x", processor_version="1.0.0")
        self.assertTrue(record["cases"][0]["passed"])

    def test_fixture_hash_is_stable_for_identical_cases(self):
        first = run_benchmark(CASES, VALIDATORS, benchmark_id="x", processor_version="1.0.0")
        second = run_benchmark(CASES, VALIDATORS, benchmark_id="x", processor_version="1.0.0")
        self.assertEqual(first["fixture_hash"], second["fixture_hash"])


if __name__ == "__main__":
    unittest.main()
