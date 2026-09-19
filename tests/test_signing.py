import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from atmanatic_research import (
    KEY_REVOCATION_REASONS,
    KeyRegistry,
    SigningError,
    build_key_record,
    generate_signing_key,
    key_id_for_public_key,
    sign_record,
    validate_key_record,
    verify_record_signature,
    verify_signed_record_with_registry,
)


def _record(**overrides):
    record = {
        "schema_version": 1,
        "artifact_id": "artifact-1",
        "parent_artifact_ids": [],
        "producer": "research-agent",
        "created_at": "2026-09-18T00:00:00+00:00",
        "content_hash": "a" * 64,
        "execution_authorized": False,
    }
    record.update(overrides)
    return record


class KeyIdentityTests(unittest.TestCase):
    def test_key_id_is_derived_from_public_key_bytes(self):
        _, public_bytes = generate_signing_key()
        self.assertEqual(key_id_for_public_key(public_bytes), key_id_for_public_key(public_bytes))

    def test_different_keys_get_different_ids(self):
        _, first = generate_signing_key()
        _, second = generate_signing_key()
        self.assertNotEqual(key_id_for_public_key(first), key_id_for_public_key(second))


class SignAndVerifyTests(unittest.TestCase):
    def test_valid_signature_round_trips(self):
        private_bytes, public_bytes = generate_signing_key()
        key_id = key_id_for_public_key(public_bytes)
        record = _record()
        signed = sign_record(record, private_key_bytes=private_bytes, key_id=key_id)
        self.assertTrue(verify_record_signature(signed, public_key_bytes=public_bytes))

    def test_tampering_with_a_signed_field_invalidates_signature(self):
        private_bytes, public_bytes = generate_signing_key()
        key_id = key_id_for_public_key(public_bytes)
        signed = sign_record(_record(), private_key_bytes=private_bytes, key_id=key_id)
        signed["producer"] = "tampered-agent"
        self.assertFalse(verify_record_signature(signed, public_key_bytes=public_bytes))

    def test_wrong_public_key_fails_verification(self):
        private_bytes, _ = generate_signing_key()
        _, other_public_bytes = generate_signing_key()
        signed = sign_record(
            _record(), private_key_bytes=private_bytes, key_id=key_id_for_public_key(other_public_bytes)
        )
        self.assertFalse(verify_record_signature(signed, public_key_bytes=other_public_bytes))

    def test_missing_signature_fails_verification(self):
        _, public_bytes = generate_signing_key()
        self.assertFalse(verify_record_signature(_record(), public_key_bytes=public_bytes))

    def test_unsupported_algorithm_is_rejected(self):
        private_bytes, _ = generate_signing_key()
        with self.assertRaises(SigningError):
            sign_record(_record(), private_key_bytes=private_bytes, key_id="k-1", algorithm="rsa-4096")


class KeyRecordValidationTests(unittest.TestCase):
    def test_build_key_record_is_active_with_derived_id(self):
        _, public_bytes = generate_signing_key()
        record = build_key_record(public_key_bytes=public_bytes, producer="release-authority")
        self.assertEqual(record["status"], "active")
        self.assertEqual(record["key_id"], key_id_for_public_key(public_bytes))
        self.assertIsNone(record["revoked_at"])

    def test_key_id_mismatch_is_rejected(self):
        _, public_bytes = generate_signing_key()
        record = build_key_record(public_key_bytes=public_bytes, producer="release-authority")
        record["key_id"] = "0" * 64
        with self.assertRaises(SigningError):
            validate_key_record(record)

    def test_revoked_without_reason_is_rejected(self):
        _, public_bytes = generate_signing_key()
        record = build_key_record(public_key_bytes=public_bytes, producer="release-authority")
        record["status"] = "revoked"
        with self.assertRaises(SigningError):
            validate_key_record(record)

    def test_active_key_with_revocation_fields_is_rejected(self):
        _, public_bytes = generate_signing_key()
        record = build_key_record(public_key_bytes=public_bytes, producer="release-authority")
        record["revocation_reason"] = "compromised"
        with self.assertRaises(SigningError):
            validate_key_record(record)

    def test_every_taxonomy_reason_is_accepted(self):
        _, public_bytes = generate_signing_key()
        for reason in KEY_REVOCATION_REASONS:
            record = build_key_record(public_key_bytes=public_bytes, producer="release-authority")
            record["status"] = "revoked"
            record["revocation_reason"] = reason
            record["revoked_at"] = "2026-09-18T00:00:00+00:00"
            validate_key_record(record)


class KeyRegistryTests(unittest.TestCase):
    def _registry(self, tmp):
        return KeyRegistry(Path(tmp) / "keys.jsonl")

    def test_register_and_read_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = self._registry(tmp)
            _, public_bytes = generate_signing_key()
            record = build_key_record(public_key_bytes=public_bytes, producer="release-authority")
            registry.register(record)
            self.assertTrue(registry.is_active(record["key_id"]))
            self.assertEqual(len(registry.read_all()), 1)

    def test_cannot_register_the_same_key_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = self._registry(tmp)
            _, public_bytes = generate_signing_key()
            record = build_key_record(public_key_bytes=public_bytes, producer="release-authority")
            registry.register(record)
            with self.assertRaises(SigningError):
                registry.register(record)

    def test_revoke_moves_key_out_of_active_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = self._registry(tmp)
            _, public_bytes = generate_signing_key()
            record = build_key_record(public_key_bytes=public_bytes, producer="release-authority")
            registry.register(record)
            registry.revoke(record["key_id"], reason="compromised")
            self.assertFalse(registry.is_active(record["key_id"]))
            latest = registry.latest_status()[record["key_id"]]
            self.assertEqual(latest["status"], "revoked")
            self.assertEqual(latest["revocation_reason"], "compromised")

    def test_cannot_revoke_an_already_revoked_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = self._registry(tmp)
            _, public_bytes = generate_signing_key()
            record = build_key_record(public_key_bytes=public_bytes, producer="release-authority")
            registry.register(record)
            registry.revoke(record["key_id"], reason="compromised")
            with self.assertRaises(SigningError):
                registry.revoke(record["key_id"], reason="superseded")

    def test_revoke_unknown_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = self._registry(tmp)
            with self.assertRaises(SigningError):
                registry.revoke("nonexistent", reason="compromised")

    def test_revoke_rejects_unknown_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = self._registry(tmp)
            _, public_bytes = generate_signing_key()
            record = build_key_record(public_key_bytes=public_bytes, producer="release-authority")
            registry.register(record)
            with self.assertRaises(SigningError):
                registry.revoke(record["key_id"], reason="because")

    def test_latest_status_resolves_registration_then_revocation(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = self._registry(tmp)
            _, public_bytes = generate_signing_key()
            created_at = datetime(2026, 9, 17, tzinfo=timezone.utc)
            record = build_key_record(
                public_key_bytes=public_bytes, producer="release-authority", created_at=created_at
            )
            registry.register(record)
            registry.revoke(
                record["key_id"], reason="superseded", revoked_at=created_at + timedelta(days=1)
            )
            self.assertEqual(registry.latest_status()[record["key_id"]]["status"], "revoked")


class VerifySignedRecordWithRegistryTests(unittest.TestCase):
    def test_active_key_signature_verifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = KeyRegistry(Path(tmp) / "keys.jsonl")
            private_bytes, public_bytes = generate_signing_key()
            key_record = build_key_record(public_key_bytes=public_bytes, producer="release-authority")
            registry.register(key_record)

            signed = sign_record(_record(), private_key_bytes=private_bytes, key_id=key_record["key_id"])
            self.assertTrue(verify_signed_record_with_registry(signed, registry))

    def test_revoked_key_signature_no_longer_verifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = KeyRegistry(Path(tmp) / "keys.jsonl")
            private_bytes, public_bytes = generate_signing_key()
            key_record = build_key_record(public_key_bytes=public_bytes, producer="release-authority")
            registry.register(key_record)
            signed = sign_record(_record(), private_key_bytes=private_bytes, key_id=key_record["key_id"])

            registry.revoke(key_record["key_id"], reason="compromised")

            self.assertFalse(verify_signed_record_with_registry(signed, registry))

    def test_unknown_key_signature_does_not_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = KeyRegistry(Path(tmp) / "keys.jsonl")
            private_bytes, public_bytes = generate_signing_key()
            signed = sign_record(
                _record(), private_key_bytes=private_bytes, key_id=key_id_for_public_key(public_bytes)
            )
            self.assertFalse(verify_signed_record_with_registry(signed, registry))


if __name__ == "__main__":
    unittest.main()
