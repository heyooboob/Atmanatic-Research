import json
import unittest

from atmanatic_research import compute_content_hash

from interop.verify_fixtures import FIXTURES_DIR, verify


class InteropFixtureDriftTests(unittest.TestCase):
    def test_committed_fixtures_match_current_validator_behavior(self):
        checked = verify()
        self.assertGreater(checked, 0)

    def test_canonical_hash_parity_fixture_matches_python(self):
        parity = json.loads((FIXTURES_DIR / "canonical_hash_parity.json").read_text(encoding="utf-8"))
        self.assertEqual(compute_content_hash(parity["record"]), parity["expected_sha256"])


if __name__ == "__main__":
    unittest.main()
