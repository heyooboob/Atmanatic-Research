import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from atmanatic_research import (
    LifecycleEventError,
    LifecycleEventLog,
    Observation,
    ValidityLevel,
    ValidityPacket,
    advance,
    promote_packet,
    record_transition,
    validate_lifecycle_event,
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


def _promotion_record(**overrides):
    record = {
        "schema_version": 1,
        "artifact_id": "promotion-1",
        "parent_artifact_ids": [],
        "producer": "human-reviewer",
        "created_at": "2026-09-17T02:00:00+00:00",
        "content_hash": "b" * 64,
        "execution_authorized": False,
        "approver": "human-reviewer",
        "approved_artifact_hash": CONTENT_HASH,
        "approved_scope": "bounded evaluation environment",
        "approved_at": "2026-09-17T02:00:00+00:00",
        "rollback_target": "artifact-previous",
        "status": "approved",
    }
    record.update(overrides)
    return record


class RecordTransitionTests(unittest.TestCase):
    def test_accepted_transition_is_recorded(self):
        packet = _packet()
        now = datetime(2026, 9, 17, tzinfo=timezone.utc)
        result, event = record_transition(
            packet,
            actor="orchestrator",
            event_id="event-1",
            transition=lambda: advance(packet, ValidityLevel.TESTED, now=now),
            requested_level=ValidityLevel.TESTED,
            now=now,
        )
        self.assertTrue(result.passed)
        self.assertEqual(event["result"], "accepted")
        self.assertEqual(event["prior_level"], "observed")
        self.assertEqual(event["requested_level"], "tested")
        self.assertEqual(event["violations"], [])
        self.assertEqual(event["violation_codes"], [])

    def test_rejected_transition_is_recorded_with_violations(self):
        packet = _packet()
        result, event = record_transition(
            packet,
            actor="orchestrator",
            event_id="event-2",
            transition=lambda: advance(packet, ValidityLevel.INDEPENDENTLY_VERIFIED),
            requested_level=ValidityLevel.INDEPENDENTLY_VERIFIED,
        )
        self.assertFalse(result.passed)
        self.assertEqual(event["result"], "rejected")
        self.assertTrue(event["violations"])
        self.assertEqual(len(event["violation_codes"]), len(event["violations"]))
        self.assertEqual(event["violation_codes"], ["invalid_state_transition"])


class ValidateLifecycleEventTests(unittest.TestCase):
    def _valid_event(self, **overrides):
        event = {
            "schema_version": 1,
            "event_id": "event-1",
            "packet_content_hash": CONTENT_HASH,
            "prior_level": "observed",
            "requested_level": "tested",
            "actor": "orchestrator",
            "created_at": "2026-09-17T00:00:00+00:00",
            "supporting_artifact_hashes": [],
            "result": "accepted",
            "violations": [],
            "violation_codes": [],
        }
        event.update(overrides)
        return event

    def test_accepted_event_with_violations_is_rejected(self):
        with self.assertRaises(LifecycleEventError):
            validate_lifecycle_event(self._valid_event(violations=["should not be here"]))

    def test_rejected_event_without_violations_is_rejected(self):
        with self.assertRaises(LifecycleEventError):
            validate_lifecycle_event(self._valid_event(result="rejected"))

    def test_accepted_event_with_violation_codes_is_rejected(self):
        with self.assertRaises(LifecycleEventError):
            validate_lifecycle_event(self._valid_event(violation_codes=["missing_or_invalid_field"]))

    def test_mismatched_violation_codes_length_is_rejected(self):
        with self.assertRaises(LifecycleEventError):
            validate_lifecycle_event(
                self._valid_event(
                    result="rejected",
                    violations=["a", "b"],
                    violation_codes=["missing_or_invalid_field"],
                )
            )

    def test_rejected_event_without_violation_codes_is_accepted_for_backward_compatibility(self):
        event = self._valid_event(result="rejected", violations=["legacy violation"], violation_codes=[])
        self.assertEqual(validate_lifecycle_event(event), event)

    def test_unknown_level_is_rejected(self):
        with self.assertRaises(LifecycleEventError):
            validate_lifecycle_event(self._valid_event(requested_level="bogus"))

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(LifecycleEventError):
            validate_lifecycle_event(self._valid_event(created_at="2026-09-17T00:00:00"))


class LifecycleEventLogTests(unittest.TestCase):
    def test_append_and_read_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = LifecycleEventLog(Path(tmp) / "events.jsonl")
            event = {
                "schema_version": 1,
                "event_id": "event-1",
                "packet_content_hash": CONTENT_HASH,
                "prior_level": "observed",
                "requested_level": "tested",
                "actor": "orchestrator",
                "created_at": "2026-09-17T00:00:00+00:00",
                "supporting_artifact_hashes": [],
                "result": "accepted",
                "violations": [],
                "violation_codes": [],
            }
            log.append(event)
            self.assertEqual(log.read_all(), [event])

    def test_latest_status_resolves_by_created_at_not_arrival_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = LifecycleEventLog(Path(tmp) / "events.jsonl")
            later = {
                "schema_version": 1,
                "event_id": "event-2",
                "packet_content_hash": CONTENT_HASH,
                "prior_level": "tested",
                "requested_level": "validated_in_scope",
                "actor": "orchestrator",
                "created_at": "2026-09-18T00:00:00+00:00",
                "supporting_artifact_hashes": [],
                "result": "accepted",
                "violations": [],
                "violation_codes": [],
            }
            earlier = {**later, "event_id": "event-1", "created_at": "2026-09-17T00:00:00+00:00"}
            log.append(later)
            log.append(earlier)
            latest = log.latest_status()
            self.assertEqual(latest[CONTENT_HASH]["event_id"], "event-2")


class PromotePacketTests(unittest.TestCase):
    def test_promotion_requires_awaiting_human_promotion_state(self):
        packet = _packet()
        result = promote_packet(packet, _promotion_record())
        self.assertFalse(result.passed)
        self.assertIn("awaiting_human_promotion", result.violations[0])
        self.assertEqual(result.violation_codes, ["invalid_state_transition"])

    def test_promotion_requires_matching_artifact_hash(self):
        packet = _packet(level=ValidityLevel.AWAITING_HUMAN_PROMOTION)
        result = promote_packet(packet, _promotion_record(approved_artifact_hash="c" * 64))
        self.assertFalse(result.passed)
        self.assertEqual(result.violation_codes, ["hash_mismatch"])

    def test_successful_promotion_sets_level_and_retains_record(self):
        packet = _packet(level=ValidityLevel.AWAITING_HUMAN_PROMOTION)
        result = promote_packet(packet, _promotion_record())
        self.assertTrue(result.passed, result.violations)
        self.assertEqual(result.violation_codes, [])
        self.assertEqual(packet.level, ValidityLevel.PROMOTED)
        self.assertEqual(packet.metadata["promotion_record"]["approver"], "human-reviewer")

    def test_non_approved_status_is_rejected(self):
        packet = _packet(level=ValidityLevel.AWAITING_HUMAN_PROMOTION)
        result = promote_packet(packet, _promotion_record(status="rejected"))
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
