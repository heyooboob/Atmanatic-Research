import hashlib
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from atmanatic_research import text_processing  # noqa: E402


class TextProcessingTests(unittest.TestCase):
    def test_normalization_canonicalizes_aliases_and_whitespace(self):
        variants = ["research record", "Research-Record", " research_record\u00a0"]
        self.assertEqual({text_processing.normalize_text(value) for value in variants}, {"research_record"})

    def test_tokenization_preserves_domain_terms_ids_and_tickers(self):
        tokens = text_processing.tokenize("evidence_id review_status proposal_123 uncertainty statement")
        self.assertEqual(tokens, ["evidence_id", "review_status", "proposal_123", "uncertainty", "statement"])

    def test_ngrams_extract_phrases(self):
        ngrams = text_processing.extract_ngrams("Evidence has uncertainty and a rollback plan")
        self.assertIn("uncertainty and", ngrams)
        self.assertIn("rollback plan", ngrams)

    def test_process_text_contains_replay_metadata_and_hashes(self):
        source = "  Evidence   Benchmark  "
        result = text_processing.process_text(source)
        self.assertEqual(result["input_text_hash"], hashlib.sha256(source.encode()).hexdigest())
        self.assertEqual(result["normalized_text"], "evidence benchmark")
        self.assertEqual(len(result["normalized_text_hash"]), 64)
        self.assertTrue(result["created_at"])
        self.assertEqual(result["processor_version"], text_processing.PROCESSOR_VERSION)


if __name__ == "__main__":
    unittest.main()