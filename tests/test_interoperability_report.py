import shutil
import unittest

from interop.generate_report import REFERENCE_TS_DIR, generate

_NPM_AVAILABLE = shutil.which("npm") is not None
_TS_DEPS_INSTALLED = (REFERENCE_TS_DIR / "node_modules").is_dir()


@unittest.skipUnless(
    _NPM_AVAILABLE and _TS_DEPS_INSTALLED,
    "requires npm and `npm install` run in interop/reference-ts",
)
class InteroperabilityReportTests(unittest.TestCase):
    def test_report_generates_and_shows_full_agreement(self):
        report = generate()
        self.assertIn("Fixtures checked: 19", report)
        self.assertIn("Implementations agreeing (verdict + error code): 19/19", report)
        self.assertNotIn("**NO**", report)
        self.assertIn("MATCH", report)


if __name__ == "__main__":
    unittest.main()
