import unittest
from datetime import datetime, timedelta, timezone

from atmanatic_research import (
    ArtifactContractError,
    is_expired,
    validate_artifact_lineage,
    validate_promotion_record,
    validate_review_outcome,
    validate_verification_result,
)


CONTENT_HASH = "a" * 64


def _lineage(**overrides):
    record = {
        "schema_version": 1,
        "artifact_id": "artifact-1",
        "parent_artifact_ids": [],
        "producer": "research-agent",
        "created_at": "2026-09-17T00:00:00+00:00",
        "content_hash": CONTENT_HASH,
        "execution_authorized": False,
        "processor_version": "1.0",
        "revalidation_policy": "revalidate on source or environment change",
    }
    record.update(overrides)
    return record


class ArtifactLineageTests(unittest.TestCase):
    def test_complete_lineage_passes(self):
        record = validate_artifact_lineage(_lineage())
        self.assertEqual(record["artifact_id"], "artifact-1")

    def test_lineage_requires_read_only_authority_and_hash(self):
        for overrides, message in (
            ({"execution_authorized": True}, "execution_authorized"),
            ({"content_hash": "not-a-hash"}, "content_hash"),
            ({"schema_version": 2}, "schema_version"),
        ):
            with self.subTest(message=message):
                with self.assertRaisesRegex(ArtifactContractError, message):
                    validate_artifact_lineage(_lineage(**overrides))

    def test_expiry_is_deterministic(self):
        record = _lineage(expires_at="2026-09-16T00:00:00+00:00")
        now = datetime(2026, 9, 17, tzinfo=timezone.utc)
        self.assertTrue(is_expired(record, now=now))


class VerificationResultTests(unittest.TestCase):
    def test_verified_result_passes(self):
        result = validate_verification_result(_lineage(
            verifier_name="deterministic-checker",
            verifier_version="2.0",
            input_artifact_hash=CONTENT_HASH,
            specification_ids=["spec:bounded-output"],
            status="verified",
            diagnostics=[],
            resource_usage={"wall_time_ms": 12},
            environment_id="ci-python-312",
        ))
        self.assertEqual(result["status"], "verified")

    def test_unknown_status_fails(self):
        with self.assertRaisesRegex(ArtifactContractError, "status"):
            validate_verification_result(_lineage(
                verifier_name="checker",
                verifier_version="1",
                input_artifact_hash=CONTENT_HASH,
                specification_ids=["spec-1"],
                status="approved",
                environment_id="ci",
            ))


class PromotionRecordTests(unittest.TestCase):
    def test_promotion_record_is_explicit_but_non_authorizing(self):
        record = validate_promotion_record(_lineage(
            approver="human-reviewer",
            approved_artifact_hash=CONTENT_HASH,
            approved_scope="bounded evaluation environment",
            approved_at="2026-09-17T01:00:00+00:00",
            rollback_target="artifact-previous",
            status="approved",
        ))
        self.assertFalse(record["execution_authorized"])


class ReviewOutcomeTests(unittest.TestCase):
    def test_resolved_independent_review_passes(self):
        record = validate_review_outcome(_lineage(
            reviewer="independent-reviewer",
            subject_artifact_hash=CONTENT_HASH,
            challenge_findings=["tested the declared boundary"],
            outcome="challenged_and_resolved",
            resolution="boundary held under the stated fixture",
        ))
        self.assertEqual(record["outcome"], "challenged_and_resolved")

    def test_review_cannot_be_self_authored_or_unresolved(self):
        with self.assertRaisesRegex(ArtifactContractError, "distinct"):
            validate_review_outcome(_lineage(
                reviewer="research-agent",
                subject_artifact_hash=CONTENT_HASH,
                challenge_findings=["checked"],
                outcome="challenged_and_resolved",
                resolution="resolved",
            ))
        with self.assertRaisesRegex(ArtifactContractError, "resolution"):
            validate_review_outcome(_lineage(
                reviewer="independent-reviewer",
                subject_artifact_hash=CONTENT_HASH,
                challenge_findings=["checked"],
                outcome="challenged_and_resolved",
            ))


if __name__ == "__main__":
    unittest.main()
