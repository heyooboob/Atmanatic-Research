import unittest

from atmanatic_research import (
    CanonicalizationError,
    canonical_json_bytes,
    compute_content_hash,
    project_for_hash,
    verify_content_hash,
)


class CanonicalJsonTests(unittest.TestCase):
    def test_key_order_does_not_affect_bytes(self):
        first = canonical_json_bytes({"b": 1, "a": 2})
        second = canonical_json_bytes({"a": 2, "b": 1})
        self.assertEqual(first, second)

    def test_rejects_non_finite_floats(self):
        with self.assertRaises(CanonicalizationError):
            canonical_json_bytes({"value": float("nan")})
        with self.assertRaises(CanonicalizationError):
            canonical_json_bytes({"value": float("inf")})

    def test_nested_non_finite_floats_are_rejected(self):
        with self.assertRaises(CanonicalizationError):
            canonical_json_bytes({"outer": [{"inner": float("nan")}]})


class ContentHashProjectionTests(unittest.TestCase):
    def test_content_hash_and_signature_are_excluded_from_projection(self):
        record = {"a": 1, "content_hash": "stale", "signature": "stale-sig"}
        self.assertEqual(project_for_hash(record), {"a": 1})

    def test_identical_content_produces_identical_hash_regardless_of_field_order(self):
        first = {"artifact_id": "a-1", "producer": "agent", "content_hash": "irrelevant"}
        second = {"content_hash": "different", "producer": "agent", "artifact_id": "a-1"}
        self.assertEqual(compute_content_hash(first), compute_content_hash(second))

    def test_verify_content_hash_detects_tampering(self):
        record = {"artifact_id": "a-1", "producer": "agent"}
        record["content_hash"] = compute_content_hash(record)
        self.assertTrue(verify_content_hash(record))
        record["producer"] = "tampered-agent"
        self.assertFalse(verify_content_hash(record))

    def test_project_for_hash_rejects_non_object(self):
        with self.assertRaises(CanonicalizationError):
            project_for_hash([1, 2, 3])


if __name__ == "__main__":
    unittest.main()
