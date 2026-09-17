import unittest

from atmanatic_research import EvidenceContractError, validate_evidence_card


class EvidenceContractTests(unittest.TestCase):
    def test_complete_card_is_accepted(self):
        card = {
            "evidence_id": "evidence-1",
            "claim": "The observed value is bounded.",
            "source_ids": ["source-1"],
            "agent": "research-agent",
            "observed_at": "2026-09-16T00:00:00+00:00",
            "confidence": 0.8,
            "content_hash": "hash-1",
            "status": "provisional",
            "details": {},
        }
        self.assertIs(validate_evidence_card(card), card)

    def test_malformed_card_fails_closed(self):
        with self.assertRaises(EvidenceContractError):
            validate_evidence_card({"evidence_id": "evidence-1"})

    def test_confidence_and_timestamp_are_bounded(self):
        card = {
            "evidence_id": "evidence-1",
            "claim": "Observed",
            "source_ids": ["source-1"],
            "agent": "research-agent",
            "observed_at": "not-a-time",
            "confidence": 1.1,
            "content_hash": "hash-1",
            "status": "provisional",
            "details": {},
        }
        with self.assertRaises(EvidenceContractError):
            validate_evidence_card(card)


if __name__ == "__main__":
    unittest.main()