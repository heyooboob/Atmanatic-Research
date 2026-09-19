import unittest
from datetime import datetime, timedelta, timezone

from atmanatic_research import (
    Observation,
    ValidityLevel,
    ValidityPacket,
    advance,
    advance_with_review,
)


CONTENT_HASH = "a" * 64


def _packet(**overrides):
    now = datetime(2026, 9, 17, tzinfo=timezone.utc)
    values = {
        "claim": "The bounded process completed.",
        "scope": "local fixture",
        "author": "research-agent",
        "observations": [Observation("completed", now)],
        "evidence_refs": ["evidence-1"],
        "falsifier": "A failed fixture falsifies the claim.",
        "counterclaim": "A broader fixture may fail.",
        "uncertainty": "Only the local fixture was observed.",
        "limitations": "No production execution.",
        "rollback_path": "Restore the prior artifact.",
        "expiry": now + timedelta(days=7),
        "revalidation_policy": "Revalidate after changes.",
        "metadata": {"content_hash": CONTENT_HASH},
    }
    values.update(overrides)
    return ValidityPacket(**values)


def _review(**overrides):
    record = {
        "schema_version": 1,
        "artifact_id": "review-1",
        "parent_artifact_ids": ["packet-1"],
        "producer": "research-agent",
        "created_at": "2026-09-17T01:00:00+00:00",
        "content_hash": "b" * 64,
        "execution_authorized": False,
        "reviewer": "independent-reviewer",
        "subject_artifact_hash": CONTENT_HASH,
        "challenge_findings": ["tested the declared boundary"],
        "outcome": "challenged_and_resolved",
        "resolution": "the boundary held for the declared fixture",
    }
    record.update(overrides)
    return record


class GovernedValidityTests(unittest.TestCase):
    def test_hash_linked_independent_review_advances_packet(self):
        now = datetime(2026, 9, 17, tzinfo=timezone.utc)
        packet = _packet()
        self.assertTrue(advance(packet, ValidityLevel.TESTED, now=now).passed)
        self.assertTrue(advance(packet, ValidityLevel.VALIDATED_IN_SCOPE, now=now).passed)

        result = advance_with_review(
            packet, ValidityLevel.INDEPENDENTLY_VERIFIED, _review(), now=now
        )

        self.assertTrue(result.passed, result.violations)
        self.assertEqual(result.violation_codes, [])
        self.assertEqual(packet.level, ValidityLevel.INDEPENDENTLY_VERIFIED)
        self.assertEqual(packet.reviewer, "independent-reviewer")
        self.assertEqual(packet.challenge_outcome, "challenged_and_resolved")

    def test_review_subject_hash_must_match_packet(self):
        packet = _packet()
        result = advance_with_review(
            packet,
            ValidityLevel.INDEPENDENTLY_VERIFIED,
            _review(subject_artifact_hash="c" * 64),
        )
        self.assertFalse(result.passed)
        self.assertIn("subject hash does not match", result.violations[0])
        self.assertEqual(result.violation_codes, ["hash_mismatch"])

    def test_review_must_be_resolved_and_independent(self):
        packet = _packet()
        unresolved_review = _review(outcome="insufficient_evidence")
        del unresolved_review["resolution"]
        unresolved = advance_with_review(
            packet,
            ValidityLevel.INDEPENDENTLY_VERIFIED,
            unresolved_review,
        )
        self.assertFalse(unresolved.passed)
        self.assertIn(
            "review artifact must have outcome challenged_and_resolved",
            unresolved.violations,
        )
        self.assertEqual(unresolved.violation_codes, ["self_review_or_unresolved"])

        self_review = advance_with_review(
            packet,
            ValidityLevel.INDEPENDENTLY_VERIFIED,
            _review(reviewer="research-agent"),
        )
        self.assertFalse(self_review.passed)
        self.assertIn("reviewer must be distinct", self_review.violations[0])

    def test_packet_requires_content_hash(self):
        packet = _packet(metadata={})
        result = advance_with_review(
            packet, ValidityLevel.INDEPENDENTLY_VERIFIED, _review()
        )
        self.assertFalse(result.passed)
        self.assertIn("packet metadata content_hash", result.violations[0])
        self.assertEqual(result.violation_codes, ["missing_or_invalid_field"])

    def test_failed_ordered_advance_does_not_mutate_review_fields(self):
        packet = _packet(reviewer="prior-reviewer", challenge_outcome="prior-outcome")
        result = advance_with_review(
            packet, ValidityLevel.INDEPENDENTLY_VERIFIED, _review()
        )
        self.assertFalse(result.passed)
        self.assertEqual(packet.level, ValidityLevel.OBSERVED)
        self.assertEqual(packet.reviewer, "prior-reviewer")
        self.assertEqual(packet.challenge_outcome, "prior-outcome")


if __name__ == "__main__":
    unittest.main()