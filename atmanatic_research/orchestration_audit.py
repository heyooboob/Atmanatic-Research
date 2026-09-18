"""Deterministic audit-event projection for completed orchestration runs."""

from __future__ import annotations

from dataclasses import dataclass

from .error_codes import MALFORMED_SYNTAX, MISSING_OR_INVALID_FIELD
from .orchestration import OrchestrationError, OrchestrationResult


@dataclass(frozen=True)
class OrchestrationAuditEvent:
    event_id: str
    run_id: str
    sequence: int
    event_type: str
    attempt: int | None
    proposal_id: str | None
    finding_ids: tuple[str, ...]
    reviewer_ids: tuple[str, ...]
    reasons: tuple[str, ...]
    execution_authorized: bool = False


def _proposal_id(proposal: dict[str, object]) -> str | None:
    value = proposal.get("proposal_id")
    return value if isinstance(value, str) and value.strip() else None


def build_orchestration_audit_events(
    result: OrchestrationResult, *, run_id: str
) -> tuple[OrchestrationAuditEvent, ...]:
    """Project a completed result into an ordered, replay-stable audit event stream."""
    if not isinstance(result, OrchestrationResult):
        raise OrchestrationError("result must be an OrchestrationResult", code=MALFORMED_SYNTAX)
    if not isinstance(run_id, str) or not run_id.strip():
        raise OrchestrationError("run_id must be a non-empty string", code=MISSING_OR_INVALID_FIELD)

    events: list[OrchestrationAuditEvent] = []

    def append(
        event_type: str,
        *,
        attempt: int | None,
        proposal_id: str | None,
        finding_ids: tuple[str, ...] = (),
        reviewer_ids: tuple[str, ...] = (),
        reasons: tuple[str, ...] = (),
    ) -> None:
        sequence = len(events)
        events.append(
            OrchestrationAuditEvent(
                event_id=f"{run_id}:{sequence}",
                run_id=run_id,
                sequence=sequence,
                event_type=event_type,
                attempt=attempt,
                proposal_id=proposal_id,
                finding_ids=finding_ids,
                reviewer_ids=reviewer_ids,
                reasons=reasons,
            )
        )

    for round_record in result.rounds:
        proposal_id = _proposal_id(round_record.proposal)
        finding_ids = tuple(finding.finding_id for finding in round_record.findings)
        reviewer_ids = tuple(
            sorted({finding.reviewer for finding in round_record.findings})
        )
        append(
            "review_completed",
            attempt=round_record.attempt,
            proposal_id=proposal_id,
            finding_ids=finding_ids,
            reviewer_ids=reviewer_ids,
        )
        if round_record.responses:
            append(
                "finding_responses_recorded",
                attempt=round_record.attempt,
                proposal_id=proposal_id,
                finding_ids=tuple(
                    response.finding_id for response in round_record.responses
                ),
                reviewer_ids=reviewer_ids,
            )

    terminal_type = "orchestration_accepted" if result.accepted else "orchestration_rejected"
    finding_ids: tuple[str, ...] = ()
    reviewer_ids: tuple[str, ...] = ()
    reasons = result.reasons
    if result.escalation is not None:
        terminal_type = "human_escalation_requested"
        finding_ids = result.escalation.finding_ids
        reviewer_ids = result.escalation.reviewers
        reasons = result.escalation.reasons
    append(
        terminal_type,
        attempt=result.rounds[-1].attempt if result.rounds else None,
        proposal_id=_proposal_id(result.proposal),
        finding_ids=finding_ids,
        reviewer_ids=reviewer_ids,
        reasons=reasons,
    )
    return tuple(events)