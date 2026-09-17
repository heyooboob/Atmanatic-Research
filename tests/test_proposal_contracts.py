import unittest

from atmanatic_research import (
    PROPOSAL_SCHEMA_VERSION,
    ProposalContractError,
    ProposalEnvelope,
    validate_proposal_envelope,
)


def _proposal(**overrides):
    proposal = {
        "schema_version": PROPOSAL_SCHEMA_VERSION,
        "proposal_id": "proposal-1",
        "parent_proposal_id": None,
        "producer": "research-agent",
        "created_at": "2026-09-17T12:00:00Z",
        "content_hash": "A" * 64,
        "evidence_refs": ["evidence-1"],
        "tool_versions": {"research-agent": "1.2.0"},
        "payload": {"claim": "The bounded fixture passed."},
        "execution_authorized": False,
    }
    proposal.update(overrides)
    return proposal


class ProposalContractTests(unittest.TestCase):
    def test_complete_proposal_returns_typed_immutable_envelope(self):
        envelope = validate_proposal_envelope(_proposal())
        self.assertIsInstance(envelope, ProposalEnvelope)
        self.assertEqual(envelope.content_hash, "a" * 64)
        self.assertEqual(envelope.evidence_refs, ("evidence-1",))
        with self.assertRaises(TypeError):
            envelope.payload["claim"] = "rewritten"
        with self.assertRaises(TypeError):
            envelope.tool_versions["research-agent"] = "other"

    def test_schema_lineage_and_timestamp_fail_closed(self):
        for overrides, message in (
            ({"schema_version": 2}, "schema_version"),
            ({"parent_proposal_id": "proposal-1"}, "must differ"),
            ({"created_at": "2026-09-17T12:00:00"}, "include a timezone"),
            ({"content_hash": "not-a-hash"}, "SHA-256"),
        ):
            with self.subTest(message=message):
                with self.assertRaisesRegex(ProposalContractError, message):
                    validate_proposal_envelope(_proposal(**overrides))

    def test_provenance_and_payload_are_required(self):
        for overrides, message in (
            ({"evidence_refs": []}, "non-empty list"),
            ({"evidence_refs": ["e1", "e1"]}, "unique"),
            ({"tool_versions": {}}, "non-empty mapping"),
            ({"payload": {}}, "non-empty object"),
        ):
            with self.subTest(message=message):
                with self.assertRaisesRegex(ProposalContractError, message):
                    validate_proposal_envelope(_proposal(**overrides))

    def test_proposal_cannot_grant_execution_authority(self):
        with self.assertRaisesRegex(ProposalContractError, "execution_authorized"):
            validate_proposal_envelope(_proposal(execution_authorized=True))


if __name__ == "__main__":
    unittest.main()