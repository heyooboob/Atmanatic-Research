import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from validity_protocol import (
    Observation,
    PacketStore,
    ValidityLevel,
    ValidityPacket,
    advance,
    validate_packet,
)
from atmanatic_research import (
    ValidityLevel as AtmanaticValidityLevel,
    ValidityPacket as AtmanaticValidityPacket,
    validate_packet as atmanatic_validate_packet,
)


def _make_packet(**overrides) -> ValidityPacket:
    now = datetime.now(timezone.utc)
    defaults = dict(
        claim="The observed process completes within the stated bound",
        scope="local test environment only",
        author="agent_a",
        observations=[Observation(description="ran the process once", observed_at=now)],
        evidence_refs=["log:run_1"],
        falsifier="a run exceeding the bound would falsify this",
        counterclaim="the process could exceed the bound under load",
        uncertainty="single run, no load testing performed",
        limitations="not tested under concurrent load",
        rollback_path="revert to previous process version",
        expiry=now + timedelta(days=7),
        revalidation_policy="revalidate weekly or after code change",
    )
    defaults.update(overrides)
    return ValidityPacket(**defaults)


class ValidatePacketTests(unittest.TestCase):
    def test_atmanatic_is_canonical_validity_protocol_surface(self):
        self.assertIs(AtmanaticValidityLevel, ValidityLevel)
        self.assertIs(AtmanaticValidityPacket, ValidityPacket)
        self.assertIs(atmanatic_validate_packet, validate_packet)

    def test_complete_packet_passes_at_observed(self):
        packet = _make_packet()
        result = validate_packet(packet)
        self.assertTrue(result.passed, result.violations)

    def test_missing_evidence_refs_fails(self):
        packet = _make_packet(evidence_refs=[])
        result = validate_packet(packet)
        self.assertFalse(result.passed)
        self.assertIn("no evidence references / provenance recorded", result.violations)

    def test_expired_packet_fails(self):
        now = datetime.now(timezone.utc)
        packet = _make_packet(expiry=now - timedelta(days=1))
        result = validate_packet(packet, now=now)
        self.assertFalse(result.passed)
        self.assertIn("packet has expired and requires revalidation", result.violations)

    def test_independently_verified_requires_reviewer_distinct_from_author(self):
        packet = _make_packet(author="agent_a", reviewer="agent_a", challenge_outcome="survived")
        result = validate_packet(packet, level=ValidityLevel.INDEPENDENTLY_VERIFIED)
        self.assertFalse(result.passed)
        self.assertIn("claim author cannot be its own independent reviewer", result.violations)

    def test_independently_verified_passes_with_distinct_reviewer(self):
        packet = _make_packet(author="agent_a", reviewer="agent_b", challenge_outcome="survived falsification attempt")
        result = validate_packet(packet, level=ValidityLevel.INDEPENDENTLY_VERIFIED)
        self.assertTrue(result.passed, result.violations)

    def test_promoted_can_never_pass_this_validator(self):
        packet = _make_packet(author="agent_a", reviewer="agent_b", challenge_outcome="survived")
        result = validate_packet(packet, level=ValidityLevel.PROMOTED)
        self.assertFalse(result.passed)
        self.assertTrue(any("explicit human-approval" in violation for violation in result.violations))


class AdvanceTests(unittest.TestCase):
    def test_advance_moves_one_step_at_a_time(self):
        packet = _make_packet()
        result = advance(packet, ValidityLevel.TESTED)
        self.assertTrue(result.passed, result.violations)
        self.assertEqual(packet.level, ValidityLevel.TESTED)

    def test_advance_rejects_skipping_levels(self):
        packet = _make_packet()
        result = advance(packet, ValidityLevel.INDEPENDENTLY_VERIFIED)
        self.assertFalse(result.passed)
        self.assertEqual(packet.level, ValidityLevel.OBSERVED)

    def test_advance_never_grants_promoted(self):
        packet = _make_packet(reviewer="agent_b", challenge_outcome="survived")
        for level in (
            ValidityLevel.TESTED,
            ValidityLevel.VALIDATED_IN_SCOPE,
            ValidityLevel.INDEPENDENTLY_VERIFIED,
            ValidityLevel.AWAITING_HUMAN_PROMOTION,
        ):
            result = advance(packet, level)
            self.assertTrue(result.passed, result.violations)
        result = advance(packet, ValidityLevel.PROMOTED)
        self.assertFalse(result.passed)
        self.assertEqual(packet.level, ValidityLevel.AWAITING_HUMAN_PROMOTION)


class PacketStoreTests(unittest.TestCase):
    def test_append_and_read_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = PacketStore(Path(temporary) / "packets.jsonl")
            packet = _make_packet()
            store.append(packet)
            records = store.read_all()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["claim"], packet.claim)
        self.assertEqual(records[0]["level"], ValidityLevel.OBSERVED.value)


if __name__ == "__main__":
    unittest.main()
