import unittest

from atmanatic_research import OrchestrationError, run_referee_loop


class OrchestrationTests(unittest.TestCase):
    def test_resolved_review_is_accepted(self):
        def reviewer(proposal):
            return [{
                "finding_id": "f-1",
                "reviewer": "boundary-reviewer",
                "review_purpose": "boundary_tester",
                "evidence_refs": ["fixture:scope-boundary"],
                "severity": "info",
                "disposition": "resolved",
                "message": "scope is explicit",
            }]

        result = run_referee_loop({"scope": "bounded"}, [reviewer], lambda proposal, findings: proposal)
        self.assertTrue(result.accepted)
        self.assertEqual(len(result.rounds), 1)
        self.assertEqual(result.reasons, ())
        finding = result.rounds[0].findings[0]
        self.assertEqual(finding.review_purpose, "boundary_tester")
        self.assertEqual(finding.evidence_refs, ("fixture:scope-boundary",))

    def test_unresolved_findings_are_bounded_and_blocking(self):
        calls = []

        def reviewer(proposal):
            calls.append(proposal.get("attempt", 0))
            return [{
                "finding_id": "f-1",
                "reviewer": "red-team",
                "review_purpose": "falsifier",
                "evidence_refs": ["counterexample:1"],
                "severity": "blocker",
                "disposition": "open",
                "message": "counterexample remains",
            }]

        def reviser(proposal, findings):
            revised = dict(proposal)
            revised["attempt"] = revised.get("attempt", 0) + 1
            return revised

        result = run_referee_loop({}, [reviewer], reviser, max_revisions=2)
        self.assertFalse(result.accepted)
        self.assertEqual(len(result.rounds), 3)
        self.assertEqual(calls, [0, 1, 2])
        self.assertIn("unresolved finding f-1", result.reasons[0])

    def test_malformed_referee_output_fails_closed(self):
        def reviewer(proposal):
            return [{"finding_id": "f-1", "reviewer": "red-team"}]

        with self.assertRaisesRegex(OrchestrationError, "missing non-empty fields"):
            run_referee_loop({}, [reviewer], lambda proposal, findings: proposal)

    def test_duplicate_finding_ids_fail_closed(self):
        def reviewer(proposal):
            finding = {
                "finding_id": "same",
                "reviewer": "reviewer",
                "review_purpose": "assumption_auditor",
                "evidence_refs": ["assumption-log:1"],
                "severity": "warning",
                "disposition": "resolved",
                "message": "checked",
            }
            return [finding, dict(finding)]

        with self.assertRaisesRegex(OrchestrationError, "unique"):
            run_referee_loop({}, [reviewer], lambda proposal, findings: proposal)

    def test_non_progressing_revision_is_rejected(self):
        def reviewer(proposal):
            return [{
                "finding_id": "f-1",
                "reviewer": "red-team",
                "review_purpose": "boundary_tester",
                "evidence_refs": ["fixture:missing"],
                "severity": "blocker",
                "disposition": "open",
                "message": "boundary remains untested",
            }]

        result = run_referee_loop({}, [reviewer], lambda proposal, findings: proposal)
        self.assertFalse(result.accepted)
        self.assertEqual(result.reasons, ("reviser made no progress",))
        self.assertEqual(len(result.rounds), 1)

    def test_finding_requires_recognized_review_purpose(self):
        def reviewer(proposal):
            return [{
                "finding_id": "f-1",
                "reviewer": "general-reviewer",
                "review_purpose": "general_review",
                "evidence_refs": ["evidence-1"],
                "severity": "warning",
                "disposition": "open",
                "message": "purpose is not independently defined",
            }]

        with self.assertRaisesRegex(OrchestrationError, "invalid review purpose"):
            run_referee_loop({}, [reviewer], lambda proposal, findings: proposal)

    def test_finding_requires_unique_evidence_references(self):
        def finding(evidence_refs):
            return {
                "finding_id": "f-1",
                "reviewer": "provenance-reviewer",
                "review_purpose": "provenance_auditor",
                "evidence_refs": evidence_refs,
                "severity": "blocker",
                "disposition": "open",
                "message": "provenance is incomplete",
            }

        with self.assertRaisesRegex(OrchestrationError, "non-empty list"):
            run_referee_loop(
                {}, [lambda proposal: [finding([])]], lambda proposal, findings: proposal
            )
        with self.assertRaisesRegex(OrchestrationError, "must be unique"):
            run_referee_loop(
                {},
                [lambda proposal: [finding(["evidence-1", "evidence-1"])]],
                lambda proposal, findings: proposal,
            )


if __name__ == "__main__":
    unittest.main()
