import unittest

from atmanatic_research import (
    ArtifactContractError,
    ERROR_CODES,
    EvidenceContractError,
    HASH_MISMATCH,
    MISSING_OR_INVALID_FIELD,
    ProposalContractError,
    PROHIBITED_AUTHORITY_CLAIM,
    SourcePolicyError,
    UNSUPPORTED_CRITICAL_EXTENSION,
    UNSUPPORTED_VERSION,
    validate_artifact_lineage,
    validate_evidence_card,
    validate_proposal_envelope,
)


def _lineage(**overrides):
    record = {
        "schema_version": 1,
        "artifact_id": "artifact-1",
        "parent_artifact_ids": [],
        "producer": "research-agent",
        "created_at": "2026-09-17T00:00:00+00:00",
        "content_hash": "a" * 64,
        "execution_authorized": False,
    }
    record.update(overrides)
    return record


class ErrorCodeTests(unittest.TestCase):
    def test_every_raised_error_carries_a_known_code(self):
        with self.assertRaises(ArtifactContractError) as ctx:
            validate_artifact_lineage(_lineage(execution_authorized=True))
        self.assertEqual(ctx.exception.code, PROHIBITED_AUTHORITY_CLAIM)
        self.assertIn(ctx.exception.code, ERROR_CODES)

    def test_unsupported_schema_version_code(self):
        with self.assertRaises(ArtifactContractError) as ctx:
            validate_artifact_lineage(_lineage(schema_version=99))
        self.assertEqual(ctx.exception.code, UNSUPPORTED_VERSION)

    def test_missing_field_code_on_evidence_card(self):
        with self.assertRaises(EvidenceContractError) as ctx:
            validate_evidence_card({})
        self.assertEqual(ctx.exception.code, MISSING_OR_INVALID_FIELD)

    def test_source_policy_error_defaults_to_source_policy_rejected_code(self):
        from atmanatic_research import SOURCE_POLICY_REJECTED

        with self.assertRaises(SourcePolicyError) as ctx:
            from atmanatic_research import get_source

            get_source({"sources": []}, "missing-source")
        self.assertEqual(ctx.exception.code, SOURCE_POLICY_REJECTED)

    def test_proposal_hash_format_code(self):
        proposal = {
            "schema_version": 1,
            "proposal_id": "p-1",
            "parent_proposal_id": None,
            "producer": "agent",
            "created_at": "2026-09-17T12:00:00Z",
            "content_hash": "not-a-hash",
            "evidence_refs": ["e-1"],
            "tool_versions": {"agent": "1.0"},
            "payload": {"claim": "x"},
            "execution_authorized": False,
        }
        with self.assertRaises(ProposalContractError):
            validate_proposal_envelope(proposal)


class CriticalExtensionTests(unittest.TestCase):
    def test_unsupported_critical_extension_fails_closed(self):
        record = _lineage(
            extensions={"urn:example:experimental": {"value": 1}},
            critical_extensions=["urn:example:experimental"],
        )
        with self.assertRaises(ArtifactContractError) as ctx:
            validate_artifact_lineage(record)
        self.assertEqual(ctx.exception.code, UNSUPPORTED_CRITICAL_EXTENSION)

    def test_declared_and_supported_critical_extension_passes(self):
        record = _lineage(
            extensions={"urn:example:experimental": {"value": 1}},
            critical_extensions=["urn:example:experimental"],
        )
        validated = validate_artifact_lineage(
            record, supported_extensions={"urn:example:experimental"}
        )
        self.assertIn("urn:example:experimental", validated["extensions"])

    def test_critical_extension_missing_from_extensions_fails_closed(self):
        record = _lineage(critical_extensions=["urn:example:experimental"])
        with self.assertRaises(ArtifactContractError):
            validate_artifact_lineage(record)

    def test_unknown_non_critical_extension_is_preserved_without_error(self):
        record = _lineage(extensions={"urn:example:cosmetic": {"note": "informational"}})
        validated = validate_artifact_lineage(record)
        self.assertEqual(validated["extensions"]["urn:example:cosmetic"]["note"], "informational")


if __name__ == "__main__":
    unittest.main()
