import unittest
from datetime import datetime, timedelta, timezone

from validity_protocol import Observation, ValidityLevel, ValidityPacket, advance

from atmanatic_research import (
    BenchmarkCase,
    BenchmarkHarnessError,
    run_benchmark,
    validate_artifact_lineage,
    validate_api_v2_page,
    validate_export,
    validate_evidence_card,
    validate_intelligence_collection,
    validate_promotion_record,
    validate_proposal_envelope,
    validate_review_outcome,
    validate_lifecycle_event,
    validate_source_definition,
    validate_benchmark,
    validate_soak,
    require_validity_packet,
    validate_verification_result,
    build_graph_snapshot,
    build_orchestration_audit_events,
    canonical_json_bytes,
    parse_rfc3339,
    require_decision_evidence,
    require_truth_review,
    normalize_text,
    run_referee_loop,
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


def _valid_verification_result():
    record = _valid_lineage()
    record.update(
        {
            "verifier_name": "fixture-verifier",
            "verifier_version": "1.0.0",
            "input_artifact_hash": "b" * 64,
            "specification_ids": ["spec:fixture"],
            "status": "verified",
            "diagnostics": [],
            "resource_usage": {},
            "environment_id": "test",
        }
    )
    return record


def _validate_timestamp(value):
    parse_rfc3339(value, "timestamp")


def _validate_canonical(value):
    if isinstance(value, dict) and value.get("value") == "nan":
        value = {"value": float("nan")}
    canonical_json_bytes(value)


def _validate_truth_review(value):
    require_truth_review(value)


def _validate_evidence_admission(value):
    require_decision_evidence(value, now=datetime(2026, 9, 18, tzinfo=timezone.utc))


def _packet_from_record(record):
    now = datetime(2026, 9, 18, tzinfo=timezone.utc)
    return ValidityPacket(
        claim=record["claim"],
        scope=record["scope"],
        author=record["author"],
        observations=[Observation(record["observation"], now)],
        evidence_refs=record["evidence_refs"],
        falsifier=record["falsifier"],
        counterclaim=record["counterclaim"],
        uncertainty=record["uncertainty"],
        limitations=record["limitations"],
        rollback_path=record["rollback_path"],
        expiry=now + timedelta(days=30),
        revalidation_policy=record["revalidation_policy"],
    )


def _validate_validity_protocol(value):
    packet = _packet_from_record(value)
    result = __import__("validity_protocol", fromlist=["validate_packet"]).validate_packet(packet)
    if not result.passed:
        raise ValueError("; ".join(result.violations))


def _validate_text(value):
    if not isinstance(value, dict) or not isinstance(value.get("text"), str):
        raise ValueError("text input must be a string")
    if normalize_text(value["text"]) != value["expected"]:
        raise ValueError("normalized text does not match expected output")


def _validate_graph(value):
    build_graph_snapshot(value["nodes"], value["edges"])


def _validate_orchestration(value):
    if value.get("mode") == "invalid":
        run_referee_loop({}, [], lambda proposal, findings: {})
    result = run_referee_loop({}, [lambda proposal: []], lambda proposal, findings: {})
    if not result.accepted:
        raise ValueError("orchestration did not accept the empty review")


def _validate_audit(value):
    result = __import__("atmanatic_research", fromlist=["OrchestrationResult"]).OrchestrationResult(
        accepted=True, proposal={}, rounds=(), reasons=()
    )
    events = build_orchestration_audit_events(result, run_id=value)
    if events[-1].event_type != "orchestration_accepted":
        raise ValueError("audit projection did not produce terminal acceptance")


def _validate_governance(value):
    packet = _packet_from_record(value)
    target = ValidityLevel(value["target_level"])
    result = advance(packet, target)
    if not result.passed:
        raise ValueError("; ".join(result.violations))


def _valid_packet_record(**overrides):
    record = {
        "claim": "The bounded fixture completed.",
        "scope": "local fixture",
        "author": "research-agent",
        "observation": "fixture completed",
        "evidence_refs": ["fixture:1"],
        "falsifier": "A failed fixture falsifies this claim.",
        "counterclaim": "A broader fixture may fail.",
        "uncertainty": "Only the local fixture was observed.",
        "limitations": "No production execution.",
        "rollback_path": "Restore the prior artifact.",
        "revalidation_policy": "Revalidate after changes.",
        "target_level": "tested",
    }
    record.update(overrides)
    return record


VALIDATORS = {
    "artifact_lineage": validate_artifact_lineage,
    "evidence_card": validate_evidence_card,
    "proposal_envelope": validate_proposal_envelope,
    "source_definition": validate_source_definition,
    "promotion_record": validate_promotion_record,
    "review_outcome": validate_review_outcome,
    "benchmark": validate_benchmark,
    "export": validate_export,
    "soak": validate_soak,
    "intelligence_collection": validate_intelligence_collection,
    "api_v2_page": validate_api_v2_page,
    "validity_packet": require_validity_packet,
    "lifecycle_event": validate_lifecycle_event,
    "verification_result": validate_verification_result,
    "timestamp": _validate_timestamp,
    "canonical_json": _validate_canonical,
    "truth_review": _validate_truth_review,
    "evidence_admission": _validate_evidence_admission,
    "validity_protocol": _validate_validity_protocol,
    "text_processing": _validate_text,
    "graph_snapshot": _validate_graph,
    "orchestration": _validate_orchestration,
    "orchestration_audit": _validate_audit,
    "validity_governance": _validate_governance,
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
    BenchmarkCase(
        "benchmark-valid",
        "benchmark",
        {
            "schema_version": 1,
            "execution_authorized": False,
            "trust_boundary": {"untrusted_embedded": False, "execution_authorized": False},
            "benchmark": "fixture-benchmark",
            "fixture_hash": "b" * 64,
            "processor_version": "1.0.0",
            "metrics": {},
            "cases": [],
        },
        "accept",
    ),
    BenchmarkCase(
        "benchmark-invalid-boundary",
        "benchmark",
        {
            "schema_version": 1,
            "execution_authorized": False,
            "trust_boundary": {"untrusted_embedded": True, "execution_authorized": False},
            "benchmark": "fixture-benchmark",
            "fixture_hash": "b" * 64,
            "processor_version": "1.0.0",
            "metrics": {},
            "cases": [],
        },
        "reject",
    ),
    BenchmarkCase(
        "export-valid",
        "export",
        {
            "schema_version": 1,
            "execution_authorized": False,
            "trust_boundary": {"untrusted_excluded": True, "execution_authorized": False},
            "processor_version": "1.0.0",
            "source_hashes": ["c" * 64],
            "documents": [],
            "claims": [],
            "entities": [],
        },
        "accept",
    ),
    BenchmarkCase(
        "export-invalid-source-hash",
        "export",
        {
            "schema_version": 1,
            "execution_authorized": False,
            "trust_boundary": {"untrusted_excluded": True, "execution_authorized": False},
            "processor_version": "1.0.0",
            "source_hashes": ["not-a-hash"],
            "documents": [],
            "claims": [],
            "entities": [],
        },
        "reject",
    ),
    BenchmarkCase(
        "soak-valid",
        "soak",
        {"schema_version": 1, "execution_authorized": False, "checks": [{"passed": True}], "passed": True},
        "accept",
    ),
    BenchmarkCase(
        "soak-inconsistent-result",
        "soak",
        {"schema_version": 1, "execution_authorized": False, "checks": [{"passed": False}], "passed": True},
        "reject",
    ),
    BenchmarkCase(
        "intelligence-collection-valid",
        "intelligence_collection",
        {"execution_authorized": False, "recall": [], "evidence": [], "claims": []},
        "accept",
    ),
    BenchmarkCase(
        "intelligence-collection-invalid-authority",
        "intelligence_collection",
        {"execution_authorized": True, "recall": [], "evidence": [], "claims": []},
        "reject",
    ),
    BenchmarkCase(
        "api-v2-page-valid",
        "api_v2_page",
        {
            "schema_version": 1,
            "execution_authorized": False,
            "pagination": {"page": 1, "page_size": 10, "total": 0},
            "items": [],
        },
        "accept",
    ),
    BenchmarkCase(
        "api-v2-page-invalid-pagination",
        "api_v2_page",
        {
            "schema_version": 1,
            "execution_authorized": False,
            "pagination": {"page": 0, "page_size": 10, "total": 0},
            "items": [],
        },
        "reject",
    ),
    BenchmarkCase(
        "validity-packet-valid",
        "validity_packet",
        {
            "scope": "bounded fixture",
            "observations": "The fixture completed.",
            "limitations": "One fixed environment.",
            "revalidation": "Re-run after changes.",
            "evidence_refs": ["fixture:1"],
            "expires_at": "2027-01-01T00:00:00+00:00",
        },
        "accept",
    ),
    BenchmarkCase(
        "validity-packet-missing-evidence",
        "validity_packet",
        {
            "scope": "bounded fixture",
            "observations": "The fixture completed.",
            "limitations": "One fixed environment.",
            "revalidation": "Re-run after changes.",
            "expires_at": "2027-01-01T00:00:00+00:00",
        },
        "reject",
    ),
    BenchmarkCase(
        "lifecycle-event-valid",
        "lifecycle_event",
        {
            "schema_version": 1,
            "event_id": "event-1",
            "packet_content_hash": "d" * 64,
            "prior_level": "observed",
            "requested_level": "tested",
            "actor": "test-runner",
            "created_at": "2026-09-17T00:00:00+00:00",
            "supporting_artifact_hashes": [],
            "result": "accepted",
            "violations": [],
        },
        "accept",
    ),
    BenchmarkCase(
        "lifecycle-event-rejected-without-violation",
        "lifecycle_event",
        {
            "schema_version": 1,
            "event_id": "event-1",
            "packet_content_hash": "d" * 64,
            "prior_level": "observed",
            "requested_level": "tested",
            "actor": "test-runner",
            "created_at": "2026-09-17T00:00:00+00:00",
            "supporting_artifact_hashes": [],
            "result": "rejected",
            "violations": [],
        },
        "reject",
    ),
    BenchmarkCase("verification-result-valid", "verification_result", _valid_verification_result(), "accept"),
    BenchmarkCase(
        "verification-result-invalid-authority",
        "verification_result",
        {**_valid_verification_result(), "execution_authorized": True},
        "reject",
    ),
    BenchmarkCase("timestamp-valid", "timestamp", "2026-09-18T00:00:00Z", "accept"),
    BenchmarkCase("timestamp-naive", "timestamp", "2026-09-18T00:00:00", "reject"),
    BenchmarkCase("canonical-json-valid", "canonical_json", {"b": 2, "a": 1}, "accept"),
    BenchmarkCase("canonical-json-non-finite", "canonical_json", {"value": "nan"}, "reject"),
    BenchmarkCase(
        "truth-review-valid",
        "truth_review",
        {
            "claim": "The bounded fixture completed.",
            "source_ids": ["fixture:1"],
            "falsifier": "A failed fixture falsifies this claim.",
            "counterclaim": "A broader fixture may fail.",
            "uncertainty": "Only the local fixture was observed.",
            "independent_reviewer": "reviewer-b",
            "author": "research-agent",
            "review_outcome": "challenged_and_resolved",
        },
        "accept",
    ),
    BenchmarkCase(
        "truth-review-self-authored",
        "truth_review",
        {
            "claim": "The bounded fixture completed.",
            "source_ids": ["fixture:1"],
            "falsifier": "A failed fixture falsifies this claim.",
            "counterclaim": "A broader fixture may fail.",
            "uncertainty": "Only the local fixture was observed.",
            "independent_reviewer": "research-agent",
            "author": "research-agent",
            "review_outcome": "challenged_and_resolved",
        },
        "reject",
    ),
    BenchmarkCase(
        "evidence-admission-valid",
        "evidence_admission",
        [
            {
                "evidence_id": "e-1",
                "source_ids": ["s-1"],
                "content_hash": "a" * 64,
                "status": "fresh",
                "observed_at": "2026-09-17T00:00:00+00:00",
            }
        ],
        "accept",
    ),
    BenchmarkCase(
        "evidence-admission-blocked-status",
        "evidence_admission",
        [
            {
                "evidence_id": "e-1",
                "source_ids": ["s-1"],
                "content_hash": "a" * 64,
                "status": "stale_source",
                "observed_at": "2026-09-17T00:00:00+00:00",
            }
        ],
        "reject",
    ),
    BenchmarkCase("validity-protocol-valid", "validity_protocol", _valid_packet_record(), "accept"),
    BenchmarkCase(
        "validity-protocol-missing-evidence",
        "validity_protocol",
        _valid_packet_record(evidence_refs=[]),
        "reject",
    ),
    BenchmarkCase(
        "text-processing-valid",
        "text_processing",
        {"text": "Research-record  fixture", "expected": "research_record fixture"},
        "accept",
    ),
    BenchmarkCase(
        "text-processing-invalid-input",
        "text_processing",
        {"text": 42, "expected": "42"},
        "reject",
    ),
    BenchmarkCase(
        "graph-snapshot-valid",
        "graph_snapshot",
        {
            "nodes": [
                {"node_id": "claim-1", "node_type": "claim", "content_hash": "a" * 64},
                {"node_id": "evidence-1", "node_type": "evidence_card", "content_hash": "b" * 64},
            ],
            "edges": [
                {
                    "edge_id": "edge-1",
                    "relation_type": "supports",
                    "source_id": "evidence-1",
                    "target_id": "claim-1",
                }
            ],
        },
        "accept",
    ),
    BenchmarkCase(
        "graph-snapshot-unknown-node-type",
        "graph_snapshot",
        {"nodes": [{"node_id": "n-1", "node_type": "unknown", "content_hash": "a" * 64}], "edges": []},
        "reject",
    ),
    BenchmarkCase("orchestration-valid", "orchestration", {"mode": "valid"}, "accept"),
    BenchmarkCase("orchestration-no-reviewers", "orchestration", {"mode": "invalid"}, "reject"),
    BenchmarkCase("orchestration-audit-valid", "orchestration_audit", "run-1", "accept"),
    BenchmarkCase("orchestration-audit-empty-run-id", "orchestration_audit", "", "reject"),
    BenchmarkCase(
        "validity-governance-valid",
        "validity_governance",
        _valid_packet_record(target_level="tested"),
        "accept",
    ),
    BenchmarkCase(
        "validity-governance-invalid-skip",
        "validity_governance",
        _valid_packet_record(target_level="independently_verified"),
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
