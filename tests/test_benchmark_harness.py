import unittest

from atmanatic_research import (
    ArtifactContractError,
    BenchmarkCase,
    BenchmarkHarnessError,
    EvidenceContractError,
    ProposalContractError,
    run_benchmark,
    validate_artifact_lineage,
    validate_evidence_card,
    validate_proposal_envelope,
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


VALIDATORS = {
    "artifact_lineage": validate_artifact_lineage,
    "evidence_card": validate_evidence_card,
    "proposal_envelope": validate_proposal_envelope,
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
