import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from atmanatic_research import KeyRegistry, build_key_record, generate_signing_key
from sign_release import SignReleaseError, build_release_manifest, sign_release  # noqa: E402
from verify_release_manifest import ReleaseManifestVerificationError, verify_release_manifest  # noqa: E402

_WHEEL_SUMMARY = {"wheel_name": "atmanatic_research-0.1.0-py3-none-any.whl", "sha256": "a" * 64}


class BuildReleaseManifestTests(unittest.TestCase):
    def test_manifest_never_authorizes_execution(self):
        manifest = build_release_manifest(tag="v0.1.0", wheel_summary=_WHEEL_SUMMARY, producer="ci")
        self.assertFalse(manifest["execution_authorized"])
        self.assertEqual(manifest["release_tag"], "v0.1.0")
        self.assertEqual(manifest["wheel_sha256"], _WHEEL_SUMMARY["sha256"])

    def test_two_manifests_for_the_same_tag_have_distinct_artifact_ids(self):
        first = build_release_manifest(tag="v0.1.0", wheel_summary=_WHEEL_SUMMARY, producer="ci")
        second = build_release_manifest(tag="v0.1.0", wheel_summary=_WHEEL_SUMMARY, producer="ci")
        self.assertNotEqual(first["artifact_id"], second["artifact_id"])


class SignReleaseTests(unittest.TestCase):
    def test_sign_release_with_registered_active_key_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "keys.jsonl"
            registry = KeyRegistry(registry_path)
            private_bytes, public_bytes = generate_signing_key()
            registry.register(build_key_record(public_key_bytes=public_bytes, producer="release-authority"))

            signed = sign_release(
                tag="v0.1.0",
                producer="ci",
                private_key_hex=private_bytes.hex(),
                registry_path=registry_path,
                wheel_summary=_WHEEL_SUMMARY,
            )
            verify_release_manifest(signed, registry_path=registry_path)

    def test_sign_release_with_unregistered_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "keys.jsonl"
            private_bytes, _ = generate_signing_key()
            with self.assertRaises(SignReleaseError):
                sign_release(
                    tag="v0.1.0",
                    producer="ci",
                    private_key_hex=private_bytes.hex(),
                    registry_path=registry_path,
                    wheel_summary=_WHEEL_SUMMARY,
                )

    def test_sign_release_with_revoked_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "keys.jsonl"
            registry = KeyRegistry(registry_path)
            private_bytes, public_bytes = generate_signing_key()
            record = registry.register(build_key_record(public_key_bytes=public_bytes, producer="release-authority"))
            registry.revoke(record["key_id"], reason="compromised")

            with self.assertRaises(SignReleaseError):
                sign_release(
                    tag="v0.1.0",
                    producer="ci",
                    private_key_hex=private_bytes.hex(),
                    registry_path=registry_path,
                    wheel_summary=_WHEEL_SUMMARY,
                )


class VerifyReleaseManifestTests(unittest.TestCase):
    def _signed_manifest(self, registry_path: Path):
        registry = KeyRegistry(registry_path)
        private_bytes, public_bytes = generate_signing_key()
        registry.register(build_key_record(public_key_bytes=public_bytes, producer="release-authority"))
        return sign_release(
            tag="v0.1.0",
            producer="ci",
            private_key_hex=private_bytes.hex(),
            registry_path=registry_path,
            wheel_summary=_WHEEL_SUMMARY,
        )

    def test_tampered_manifest_fails_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "keys.jsonl"
            signed = self._signed_manifest(registry_path)
            signed["wheel_sha256"] = "b" * 64
            with self.assertRaises(ReleaseManifestVerificationError):
                verify_release_manifest(signed, registry_path=registry_path)

    def test_revoked_key_fails_verification_even_for_a_previously_valid_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "keys.jsonl"
            signed = self._signed_manifest(registry_path)
            registry = KeyRegistry(registry_path)
            registry.revoke(signed["signature"]["key_id"], reason="compromised")
            with self.assertRaises(ReleaseManifestVerificationError):
                verify_release_manifest(signed, registry_path=registry_path)

    def test_wheel_hash_mismatch_fails_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry_path = Path(tmp) / "keys.jsonl"
            signed = self._signed_manifest(registry_path)
            wheel_path = Path(tmp) / "wheel.whl"
            wheel_path.write_bytes(b"not the bytes the manifest hash describes")
            with self.assertRaises(ReleaseManifestVerificationError):
                verify_release_manifest(signed, registry_path=registry_path, wheel_path=wheel_path)


if __name__ == "__main__":
    unittest.main()
