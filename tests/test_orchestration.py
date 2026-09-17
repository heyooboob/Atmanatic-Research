import unittest

from atmanatic_research import OrchestrationError, run_referee_loop


class OrchestrationTests(unittest.TestCase):
    def test_resolved_review_is_accepted(self):
        def reviewer(proposal):
            return [{
                "finding_id": "f-1",
                "reviewer": "boundary-reviewer",
                "severity": "info",
                "disposition": "resolved",
                "message": "scope is explicit",
            }]

        result = run_referee_loop({"scope": "bounded"}, [reviewer], lambda proposal, findings: proposal)
        self.assertTrue(result.accepted)
        self.assertEqual(len(result.rounds), 1)
        self.assertEqual(result.reasons, ())

    def test_unresolved_findings_are_bounded_and_blocking(self):
        calls = []

        def reviewer(proposal):
            calls.append(proposal.get("attempt", 0))
            return [{
                "finding_id": "f-1",
                "reviewer": "red-team",
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
                "severity": "blocker",
                "disposition": "open",
                "message": "boundary remains untested",
            }]

        result = run_referee_loop({}, [reviewer], lambda proposal, findings: proposal)
        self.assertFalse(result.accepted)
        self.assertEqual(result.reasons, ("reviser made no progress",))
        self.assertEqual(len(result.rounds), 1)


if __name__ == "__main__":
    unittest.main()
