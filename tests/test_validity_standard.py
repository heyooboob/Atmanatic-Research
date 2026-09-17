import unittest
from datetime import datetime, timezone

from atmanatic_research.validity_standard import validate_validity_packet


class ValidityStandardTests(unittest.TestCase):
    def test_bounded_packet_is_valid_until_expiry(self):
        packet = {
            "scope": "Local paper-only validation.",
            "observations": "Tests passed.",
            "limitations": "Finite fixture set.",
            "revalidation": "Re-run after changes.",
            "evidence_refs": ["tests:1"],
            "expires_at": "2026-02-01T00:00:00+00:00",
        }
        result = validate_validity_packet(packet, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.assertTrue(result.valid)

    def test_missing_scope_and_expiry_fail_closed(self):
        result = validate_validity_packet({"observations": "Observed"})
        self.assertFalse(result.valid)
        self.assertIn("validity scope is missing", result.reasons)
        self.assertIn("validity expiry is missing", result.reasons)

    def test_expired_packet_is_not_valid(self):
        result = validate_validity_packet({
            "scope": "Local",
            "observations": "Observed",
            "limitations": "Finite",
            "revalidation": "On change",
            "evidence_refs": ["e1"],
            "expires_at": "2025-01-01T00:00:00+00:00",
        }, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.assertFalse(result.valid)
        self.assertIn("validity packet is expired", result.reasons)


if __name__ == "__main__":
    unittest.main()