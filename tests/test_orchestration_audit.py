import unittest

from atmanatic_research import (
    EscalationRequest,
    FindingResponse,
    OrchestrationError,
    OrchestrationResult,
    RefereeFinding,
    ReviewRound,
    build_orchestration_audit_events,
)


def _finding(disposition="open"):
    return RefereeFinding(
        finding_id="f-1",
        reviewer="boundary-reviewer",
        review_purpose="boundary_tester",
        evidence_refs=("fixture:boundary",),
        severity="blocker",
        disposition=disposition,
        message="boundary requires review",
    )


class OrchestrationAuditTests(unittest.TestCase):
    def test_event_projection_is_deterministic_and_ordered(self):
        result = OrchestrationResult(
            accepted=True,
            proposal={"proposal_id": "proposal-2"},
            rounds=(
                ReviewRound(
                    attempt=0,
                    proposal={"proposal_id": "proposal-1"},
                    findings=(_finding(),),
                    responses=(FindingResponse(
                        finding_id="f-1",
                        disposition="addressed",
                        response="added boundary coverage",
                        evidence_refs=("fixture:boundary-added",),
                    ),),
                ),
                ReviewRound(
                    attempt=1,
                    proposal={"proposal_id": "proposal-2"},
                    findings=(_finding(disposition="resolved"),),
                ),
            ),
            reasons=(),
        )

        first = build_orchestration_audit_events(result, run_id="run-1")
        second = build_orchestration_audit_events(result, run_id="run-1")

        self.assertEqual(first, second)
        self.assertEqual([event.sequence for event in first], [0, 1, 2, 3])
        self.assertEqual(
            [event.event_type for event in first],
            [
                "review_completed",
                "finding_responses_recorded",
                "review_completed",
                "orchestration_accepted",
            ],
        )
        self.assertEqual(first[0].event_id, "run-1:0")
        self.assertEqual(first[-1].proposal_id, "proposal-2")
        self.assertTrue(all(not event.execution_authorized for event in first))

    def test_escalation_event_preserves_handoff_context(self):
        escalation = EscalationRequest(
            status="awaiting_human_review",
            reasons=("reviewers disagree",),
            finding_ids=("f-1",),
            reviewers=("boundary-reviewer",),
            proposal={"proposal_id": "proposal-1"},
        )
        result = OrchestrationResult(
            accepted=False,
            proposal={"proposal_id": "proposal-1"},
            rounds=(ReviewRound(
                attempt=0,
                proposal={"proposal_id": "proposal-1"},
                findings=(_finding(),),
            ),),
            reasons=("human escalation required: reviewers disagree",),
            escalation=escalation,
        )

        events = build_orchestration_audit_events(result, run_id="run-escalated")
        terminal = events[-1]
        self.assertEqual(terminal.event_type, "human_escalation_requested")
        self.assertEqual(terminal.reasons, ("reviewers disagree",))
        self.assertEqual(terminal.finding_ids, ("f-1",))
        self.assertEqual(terminal.reviewer_ids, ("boundary-reviewer",))

    def test_rejected_event_preserves_reasons_without_rounds(self):
        result = OrchestrationResult(
            accepted=False,
            proposal={},
            rounds=(),
            reasons=("orchestration time budget exhausted",),
        )
        events = build_orchestration_audit_events(result, run_id="run-timeout")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "orchestration_rejected")
        self.assertIsNone(events[0].attempt)
        self.assertEqual(events[0].reasons, result.reasons)

    def test_audit_projection_requires_result_and_run_id(self):
        with self.assertRaisesRegex(OrchestrationError, "OrchestrationResult"):
            build_orchestration_audit_events({}, run_id="run-1")
        with self.assertRaisesRegex(OrchestrationError, "run_id"):
            build_orchestration_audit_events(
                OrchestrationResult(False, {}, (), ("rejected",)), run_id=""
            )


if __name__ == "__main__":
    unittest.main()