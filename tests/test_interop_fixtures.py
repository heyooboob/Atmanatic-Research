import unittest

from interop.verify_fixtures import verify


class InteropFixtureDriftTests(unittest.TestCase):
    def test_committed_fixtures_match_current_validator_behavior(self):
        checked = verify()
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
