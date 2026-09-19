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

    def test_scan_excludes_unpublished_local_project(self):
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="clean", stderr="")
        local = mock.Mock()
        local.metadata = {"Name": "atmanatic-research"}
        local.version = "0.1.0"
        external = mock.Mock()
        external.metadata = {"Name": "cryptography"}
        external.version = "42.0.0"
        with mock.patch("scan_dependencies.importlib.util.find_spec", return_value=object()):
            with mock.patch("scan_dependencies.importlib.metadata.distributions", return_value=[local, external]):
                with mock.patch("scan_dependencies.Path.write_text") as write_text:
                    with mock.patch("scan_dependencies.subprocess.run", return_value=completed):
                        scan_dependencies()
        requirements_text = write_text.call_args.args[0]
        self.assertEqual(requirements_text, "cryptography==42.0.0\n")

    def test_finding_raises_dependency_scan_error(self):
        completed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="found a vulnerability")
        with mock.patch("scan_dependencies.importlib.util.find_spec", return_value=object()):
            with mock.patch("scan_dependencies.subprocess.run", return_value=completed):
                with self.assertRaises(DependencyScanError):
                    scan_dependencies()


if __name__ == "__main__":
    unittest.main()
