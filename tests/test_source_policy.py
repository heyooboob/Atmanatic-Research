import unittest

from atmanatic_research import (
    SourcePolicyError,
    assert_request_compliant,
    assert_source_allowed,
    evidence_requirement,
    validate_acquisition_receipt,
    validate_source_definition,
)


class SourcePolicyTests(unittest.TestCase):
    def _identified_source(self):
        return {
            "source_id": "sec-edgar",
            "authority_tier": "A",
            "enabled": True,
            "allowed_for": ["research-agent"],
            "access": {
                "policy_version": "1",
                "mode": "public_identified",
                "identity": {
                    "mechanism": "header",
                    "name": "User-Agent",
                    "required": True,
                    "profile_id": "institutional-contact",
                },
                "rate_limit": {"requests": 10, "period_seconds": 1},
            },
        }

    def test_identified_source_accepts_declared_profile_and_header(self):
        source = self._identified_source()
        registry = {"sources": [source]}
        context = {
            "identity_profile_id": "institutional-contact",
            "headers_present": ["user-agent"],
        }

        self.assertIs(
            assert_source_allowed(
                registry,
                "sec-edgar",
                "research-agent",
                request_context=context,
            ),
            source,
        )

    def test_identified_source_fails_closed_without_request_context(self):
        with self.assertRaisesRegex(SourcePolicyError, "requires request identification"):
            assert_request_compliant(self._identified_source())

    def test_identified_source_rejects_wrong_profile_or_missing_header(self):
        source = self._identified_source()
        with self.assertRaisesRegex(SourcePolicyError, "requires identity profile"):
            assert_request_compliant(source, {
                "identity_profile_id": "other-contact",
                "headers_present": ["User-Agent"],
            })
        with self.assertRaisesRegex(SourcePolicyError, "requires request header"):
            assert_request_compliant(source, {
                "identity_profile_id": "institutional-contact",
                "headers_present": ["Accept"],
            })

    def test_legacy_source_without_access_policy_remains_allowed(self):
        source = {
            "source_id": "legacy-source",
            "enabled": True,
            "allowed_for": ["research-agent"],
        }
        registry = {"sources": [source]}
        self.assertIs(
            assert_source_allowed(registry, "legacy-source", "research-agent"),
            source,
        )

    def test_malformed_identity_and_rate_limit_are_rejected(self):
        source = self._identified_source()
        source["access"]["identity"]["required"] = False
        with self.assertRaisesRegex(SourcePolicyError, "must be required"):
            validate_source_definition(source)

        source = self._identified_source()
        source["access"]["rate_limit"]["requests"] = 0
        with self.assertRaisesRegex(SourcePolicyError, "positive integer"):
            validate_source_definition(source)

    def test_acquisition_receipt_matches_source_without_identity_values(self):
        receipt = {
            "receipt_id": "receipt-123",
            "source_id": "sec-edgar",
            "retrieved_at": "2026-09-17T12:00:00Z",
            "request_policy_version": "1",
            "identity_profile_id": "institutional-contact",
            "identity_requirement_satisfied": True,
            "response_content_hash": "sha256:abc",
        }
        self.assertIs(
            validate_acquisition_receipt(receipt, source=self._identified_source()),
            receipt,
        )

        receipt["identity_profile_id"] = "other-contact"
        with self.assertRaisesRegex(SourcePolicyError, "does not match source policy"):
            validate_acquisition_receipt(receipt, source=self._identified_source())

        receipt["identity_profile_id"] = "institutional-contact"
        receipt["request_policy_version"] = "2"
        with self.assertRaisesRegex(SourcePolicyError, "request_policy_version"):
            validate_acquisition_receipt(receipt, source=self._identified_source())

    def test_acquisition_receipt_requires_timezone_and_compliance(self):
        receipt = {
            "receipt_id": "receipt-123",
            "source_id": "sec-edgar",
            "retrieved_at": "2026-09-17T12:00:00",
            "request_policy_version": "1",
            "identity_requirement_satisfied": False,
            "response_content_hash": "sha256:abc",
        }
        with self.assertRaisesRegex(SourcePolicyError, "explicit UTC offset"):
            validate_acquisition_receipt(receipt)

        receipt["retrieved_at"] = "2026-09-17T12:00:00Z"
        with self.assertRaisesRegex(SourcePolicyError, "requirements were satisfied"):
            validate_acquisition_receipt(receipt)

    def test_evidence_requirement_validates_independence_policy(self):
        registry = {
            "minimum_evidence": {
                "research-agent": {
                    "minimum_sources": 2,
                    "minimum_independent_sources": 2,
                    "minimum_tier": "B",
                },
            },
        }
        self.assertEqual(
            evidence_requirement(registry, "research-agent")["minimum_tier"], "B"
        )

        registry["minimum_evidence"]["research-agent"]["minimum_sources"] = 0
        with self.assertRaisesRegex(SourcePolicyError, "positive integer"):
            evidence_requirement(registry, "research-agent")

        with self.assertRaisesRegex(SourcePolicyError, "minimum_evidence must be an object"):
            evidence_requirement({"minimum_evidence": []}, "research-agent")


if __name__ == "__main__":
    unittest.main()