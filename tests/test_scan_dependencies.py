import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scan_dependencies import DependencyScanError, scan_dependencies  # noqa: E402


class ScanDependenciesTests(unittest.TestCase):
    def test_missing_pip_audit_fails_closed(self):
        with mock.patch("scan_dependencies.importlib.util.find_spec", return_value=None):
            with self.assertRaises(DependencyScanError):
                scan_dependencies()

    def test_clean_scan_returns_output(self):
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="no known vulnerabilities found", stderr="")
        with mock.patch("scan_dependencies.importlib.util.find_spec", return_value=object()):
            with mock.patch("scan_dependencies.subprocess.run", return_value=completed):
                output = scan_dependencies()
        self.assertIn("no known vulnerabilities found", output)

    def test_finding_raises_dependency_scan_error(self):
        completed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="found a vulnerability")
        with mock.patch("scan_dependencies.importlib.util.find_spec", return_value=object()):
            with mock.patch("scan_dependencies.subprocess.run", return_value=completed):
                with self.assertRaises(DependencyScanError):
                    scan_dependencies()


if __name__ == "__main__":
    unittest.main()
