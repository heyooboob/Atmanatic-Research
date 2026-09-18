import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from inspect_release import (  # noqa: E402
    ReleaseInspectionError,
    hash_wheel,
    inspect_release,
    inspect_wheel_contents,
)


class WheelContentInspectionTests(unittest.TestCase):
    def test_allowed_packages_and_metadata_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            wheel_path = Path(tmp) / "fixture.whl"
            with zipfile.ZipFile(wheel_path, "w") as archive:
                archive.writestr("atmanatic_research/__init__.py", "")
                archive.writestr("validity_protocol/__init__.py", "")
                archive.writestr("atmanatic_research-0.1.0.dist-info/METADATA", "")
            names = inspect_wheel_contents(wheel_path)
            self.assertIn("atmanatic_research/__init__.py", names)

    def test_out_of_scope_top_level_package_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            wheel_path = Path(tmp) / "fixture.whl"
            with zipfile.ZipFile(wheel_path, "w") as archive:
                archive.writestr("atmanatic_research/__init__.py", "")
                archive.writestr("unexpected_consumer_module/__init__.py", "")
            with self.assertRaises(ReleaseInspectionError):
                inspect_wheel_contents(wheel_path)

    def test_path_escaping_member_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            wheel_path = Path(tmp) / "fixture.whl"
            with zipfile.ZipFile(wheel_path, "w") as archive:
                archive.writestr("../outside/evil.py", "")
            with self.assertRaises(ReleaseInspectionError):
                inspect_wheel_contents(wheel_path)


class HashWheelTests(unittest.TestCase):
    def test_hash_is_stable_for_identical_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            wheel_path = Path(tmp) / "fixture.whl"
            wheel_path.write_bytes(b"identical-bytes")
            self.assertEqual(hash_wheel(wheel_path), hash_wheel(wheel_path))

    def test_hash_changes_with_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "a.whl"
            second = Path(tmp) / "b.whl"
            first.write_bytes(b"content-a")
            second.write_bytes(b"content-b")
            self.assertNotEqual(hash_wheel(first), hash_wheel(second))


class InspectReleaseIntegrationTest(unittest.TestCase):
    def test_current_tree_builds_a_clean_wheel(self):
        summary = inspect_release()
        self.assertTrue(summary["wheel_name"].startswith("atmanatic_research-"))
        self.assertEqual(len(summary["sha256"]), 64)
        self.assertGreater(summary["member_count"], 0)


if __name__ == "__main__":
    unittest.main()
