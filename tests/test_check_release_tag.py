import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from check_release_tag import ReleaseTagError, check_release_tag, declared_version  # noqa: E402


class CheckReleaseTagTests(unittest.TestCase):
    def test_declared_version_matches_pyproject(self):
        self.assertEqual(declared_version(), "0.1.2")

    def test_tag_matching_declared_version_passes(self):
        self.assertEqual(check_release_tag("v0.1.2"), "0.1.2")

    def test_tag_with_mismatched_version_is_rejected(self):
        with self.assertRaises(ReleaseTagError):
            check_release_tag("v9.9.9")

    def test_malformed_tag_is_rejected(self):
        for bad_tag in ("0.1.0", "v0.1", "release-0.1.0", "v0.1.0-rc1", ""):
            with self.assertRaises(ReleaseTagError):
                check_release_tag(bad_tag)


if __name__ == "__main__":
    unittest.main()
