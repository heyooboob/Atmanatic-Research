import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from atmanatic_research import require_claim_evidence, validate_and_admit_evidence  # noqa: E402
from atmanatic_research.evidence_admission import admit_evidence  # noqa: E402


class EvidenceAdmissionTests(unittest.TestCase):
    def _complete_card(self, **overrides):
        card = {
            "evidence_id": "e1",
            "claim": "Observed",
            "source_ids": ["source-1"],
            "agent": "research-agent",
            "content_hash": "hash",
            "status": "provisional",
            "observed_at": "2026-01-01T00:00:00+00:00",
            "confidence": 0.8,
            "details": {},
        }
        card.update(overrides)
        return card

    def test_duplicate_and_conflicting_evidence_ids_block_admission(self):
        duplicate = admit_evidence([self._complete_card(), self._complete_card()])
        self.assertFalse(duplicate.admitted)
        self.assertIn("duplicate evidence id 'e1'", duplicate.reasons)

        conflict = admit_evidence([
            self._complete_card(),
            self._complete_card(content_hash="different"),
        ])
        self.assertFalse(conflict.admitted)
        self.assertIn("conflicting content hashes", conflict.reasons[0])

    def test_claim_must_reference_admitted_evidence_sources(self):
        card = self._complete_card()
        claim = {"source_ids": ["source-1"]}
        self.assertIs(require_claim_evidence(claim, [card]), claim)

        with self.assertRaisesRegex(ValueError, "unsupported source references"):
            require_claim_evidence({"source_ids": ["source-2"]}, [card])

    def test_validate_and_admit_requires_complete_card_contract(self):
        cards = [{
            "evidence_id": "e1",
            "claim": "Observed",
            "source_ids": ["source-1"],
            "agent": "research-agent",
            "content_hash": "hash",
            "status": "provisional",
            "observed_at": "2026-01-01T00:00:00+00:00",
            "confidence": 0.8,
            "details": {},
        }]
        self.assertIs(validate_and_admit_evidence(cards), cards)

    def test_validate_and_admit_rejects_structurally_incomplete_card(self):
        cards = [{
            "evidence_id": "e1",
            "source_ids": ["source-1"],
            "content_hash": "hash",
            "status": "provisional",
            "observed_at": "2026-01-01T00:00:00+00:00",
        }]
        with self.assertRaises(ValueError):
            validate_and_admit_evidence(cards)

    def test_admits_complete_provisional_card(self):
        result = admit_evidence([{
            "evidence_id": "e1",
            "source_ids": ["source-1"],
            "content_hash": "hash",
            "status": "provisional",
            "observed_at": "2026-01-01T00:00:00+00:00",
        }], now=datetime(2026, 1, 2, tzinfo=timezone.utc))
        self.assertTrue(result.admitted)
        self.assertEqual(result.reasons, ())

    def test_blocks_stale_and_missing_provenance(self):
        result = admit_evidence([{"status": "stale_source", "observed_at": "bad"}])
        self.assertFalse(result.admitted)
        self.assertTrue(any("stale_source" in reason for reason in result.reasons))
        self.assertTrue(any("content_hash" in reason for reason in result.reasons))

    def test_blocks_untrusted_and_empty_input(self):
        self.assertFalse(admit_evidence([]).admitted)
        result = admit_evidence([{
            "evidence_id": "e1", "source_ids": ["s"], "content_hash": "h",
            "status": "provisional", "recall_status": "untrusted",
            "observed_at": "2026-01-01T00:00:00+00:00",
        }])
        self.assertFalse(result.admitted)


if __name__ == "__main__":
    unittest.main()