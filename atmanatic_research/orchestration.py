"""Provider-neutral proposal and referee orchestration primitives."""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Any, Callable, Iterable

from .error_codes import (
    ContractError,
    INVALID_STATE_TRANSITION,
    MALFORMED_SYNTAX,
    MISSING_OR_INVALID_FIELD,
    UNRESOLVED_REFERENCE,
)
from .proposal_contracts import ProposalContractError, ProposalEnvelope, validate_proposal_envelope

_FINDING_SEVERITIES = {"blocker", "warning", "info"}
_FINDING_DISPOSITIONS = {"open", "resolved"}
_RESPONSE_DISPOSITIONS = {"addressed", "disputed"}
_REVIEW_PURPOSES = {
    "falsifier",
    "assumption_auditor",
    "provenance_auditor",
    "boundary_tester",
    "implementation_contract_reviewer",
}


class OrchestrationError(ContractError):
    """Raised when a proposer or referee returns an invalid result."""


@dataclass(frozen=True)
class RefereeFinding:
    finding_id: str
    reviewer: str
    review_purpose: str
    evidence_refs: tuple[str, ...]
    severity: str
    disposition: str
    message: str


@dataclass(frozen=True)
class FindingResponse:
    finding_id: str
    disposition: str
    response: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class ReviewRound:
    attempt: int
    proposal: dict[str, Any]
    findings: tuple[RefereeFinding, ...]
    responses: tuple[FindingResponse, ...] = ()


@dataclass(frozen=True)
class EscalationRequest:
    status: str
    reasons: tuple[str, ...]
    finding_ids: tuple[str, ...]
    reviewers: tuple[str, ...]
    proposal: dict[str, Any]
    execution_authorized: bool = False


@dataclass(frozen=True)
class OrchestrationResult:
    accepted: bool
    proposal: dict[str, Any]
    rounds: tuple[ReviewRound, ...]
    reasons: tuple[str, ...]
    escalation: EscalationRequest | None = None


def _finding(value: Any, index: int) -> RefereeFinding:
    if not isinstance(value, dict):
        raise OrchestrationError(f"referee finding {index} must be an object", code=MALFORMED_SYNTAX)
    required = (
        "finding_id",
        "reviewer",
        "review_purpose",
        "severity",
        "disposition",
        "message",
    )
    missing = [key for key in required if not isinstance(value.get(key), str) or not value[key].strip()]
    if missing:
        raise OrchestrationError(
            f"referee finding {index} is missing non-empty fields: {', '.join(missing)}",
            code=MISSING_OR_INVALID_FIELD,
        )
    if value["severity"] not in _FINDING_SEVERITIES:
        raise OrchestrationError(f"referee finding {index} has an invalid severity", code=MISSING_OR_INVALID_FIELD)
    if value["disposition"] not in _FINDING_DISPOSITIONS:
        raise OrchestrationError(f"referee finding {index} has an invalid disposition", code=MISSING_OR_INVALID_FIELD)
    if value["review_purpose"] not in _REVIEW_PURPOSES:
        raise OrchestrationError(f"referee finding {index} has an invalid review purpose", code=MISSING_OR_INVALID_FIELD)
    evidence_refs = value.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs or not all(
        isinstance(reference, str) and reference.strip() for reference in evidence_refs
    ):
        raise OrchestrationError(
            f"referee finding {index} evidence_refs must be a non-empty list of strings",
            code=MISSING_OR_INVALID_FIELD,
        )
    if len(evidence_refs) != len(set(evidence_refs)):
        raise OrchestrationError(f"referee finding {index} evidence_refs must be unique", code=MISSING_OR_INVALID_FIELD)
    return RefereeFinding(
        finding_id=value["finding_id"],
        reviewer=value["reviewer"],
        review_purpose=value["review_purpose"],
        evidence_refs=tuple(evidence_refs),
        severity=value["severity"],
        disposition=value["disposition"],
        message=value["message"],
    )


def _review(findings: Iterable[Any]) -> tuple[RefereeFinding, ...]:
    values = tuple(_finding(value, index) for index, value in enumerate(findings))
    finding_ids = [finding.finding_id for finding in values]
    if len(finding_ids) != len(set(finding_ids)):
        raise OrchestrationError("referee finding IDs must be unique within a round", code=MISSING_OR_INVALID_FIELD)
    return values


def _finding_response(value: Any, index: int) -> FindingResponse:
    if not isinstance(value, dict):
        raise OrchestrationError(f"finding response {index} must be an object", code=MALFORMED_SYNTAX)
    required = ("finding_id", "disposition", "response")
    missing = [
        key
        for key in required
        if not isinstance(value.get(key), str) or not value[key].strip()
    ]
    if missing:
        raise OrchestrationError(
            f"finding response {index} is missing non-empty fields: {', '.join(missing)}",
            code=MISSING_OR_INVALID_FIELD,
        )
    if value["disposition"] not in _RESPONSE_DISPOSITIONS:
        raise OrchestrationError(f"finding response {index} has an invalid disposition", code=MISSING_OR_INVALID_FIELD)
    evidence_refs = value.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs or not all(
        isinstance(reference, str) and reference.strip() for reference in evidence_refs
    ):
        raise OrchestrationError(
            f"finding response {index} evidence_refs must be a non-empty list of strings",
            code=MISSING_OR_INVALID_FIELD,
        )
    if len(evidence_refs) != len(set(evidence_refs)):
        raise OrchestrationError(f"finding response {index} evidence_refs must be unique", code=MISSING_OR_INVALID_FIELD)
    return FindingResponse(
        finding_id=value["finding_id"],
        disposition=value["disposition"],
        response=value["response"],
        evidence_refs=tuple(evidence_refs),
    )


def _responses(value: Any, findings: tuple[RefereeFinding, ...]) -> tuple[FindingResponse, ...]:
    if not isinstance(value, list):
        raise OrchestrationError("revised proposal must include a finding_responses list", code=MISSING_OR_INVALID_FIELD)
    responses = tuple(_finding_response(item, index) for index, item in enumerate(value))
    response_ids = [response.finding_id for response in responses]
    if len(response_ids) != len(set(response_ids)):
        raise OrchestrationError("finding response IDs must be unique within a revision", code=MISSING_OR_INVALID_FIELD)
    finding_ids = {finding.finding_id for finding in findings}
    missing = sorted(finding_ids - set(response_ids))
    extra = sorted(set(response_ids) - finding_ids)
    if missing:
        raise OrchestrationError(
            "revised proposal does not address findings: " + ", ".join(missing), code=UNRESOLVED_REFERENCE
        )
    if extra:
        raise OrchestrationError(
            "revised proposal addresses unknown findings: " + ", ".join(extra), code=UNRESOLVED_REFERENCE
        )
    return responses


def _proposal_body(proposal: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in proposal.items() if key != "finding_responses"}


def _escalation_reasons(
    policy: Callable[[dict[str, Any], tuple[RefereeFinding, ...]], Iterable[str] | None],
    proposal: dict[str, Any],
    findings: tuple[RefereeFinding, ...],
) -> tuple[str, ...]:
    try:
        value = policy(dict(proposal), findings)
        if value is None:
            return ()
        if isinstance(value, (str, bytes)):
            raise TypeError("must return an iterable of reasons")
        reasons = tuple(value)
    except Exception as error:
        raise OrchestrationError(f"escalation policy failed: {error}", code=MISSING_OR_INVALID_FIELD) from error
    if not all(isinstance(reason, str) and reason.strip() for reason in reasons):
        raise OrchestrationError("escalation policy returned an invalid reason", code=MISSING_OR_INVALID_FIELD)
    return reasons


def _time_budget_result(
    proposal: dict[str, Any], rounds: list[ReviewRound]
) -> OrchestrationResult:
    return OrchestrationResult(
        accepted=False,
        proposal=dict(proposal),
        rounds=tuple(rounds),
        reasons=("orchestration time budget exhausted",),
    )


def run_referee_loop(
    proposal: dict[str, Any],
    reviewers: Iterable[Callable[[dict[str, Any]], Iterable[dict[str, Any]]]],
    reviser: Callable[[dict[str, Any], tuple[RefereeFinding, ...]], dict[str, Any]],
    *,
    max_revisions: int = 3,
    escalation_policy: Callable[
        [dict[str, Any], tuple[RefereeFinding, ...]], Iterable[str] | None
    ]
    | None = None,
    time_budget_seconds: float | None = None,
    clock: Callable[[], float] | None = None,
) -> OrchestrationResult:
    """Review and revise a proposal with bounded, fail-closed retries.

    Reviewers and the reviser are injected callables so model providers,
    deterministic test doubles, or external services remain outside this
    package. Any malformed reviewer output, unresolved finding, or missing
    revision rejects the loop rather than being treated as approval.
    """
    if not isinstance(proposal, dict):
        raise OrchestrationError("proposal must be an object", code=MALFORMED_SYNTAX)
    if not isinstance(max_revisions, int) or max_revisions < 0:
        raise OrchestrationError("max_revisions must be a non-negative integer", code=MISSING_OR_INVALID_FIELD)
    reviewer_list = tuple(reviewers)
    if not reviewer_list:
        raise OrchestrationError("at least one reviewer is required", code=MISSING_OR_INVALID_FIELD)
    if not callable(reviser):
        raise OrchestrationError("reviser must be callable", code=MALFORMED_SYNTAX)
    if escalation_policy is not None and not callable(escalation_policy):
        raise OrchestrationError("escalation_policy must be callable", code=MALFORMED_SYNTAX)
    if time_budget_seconds is not None and (
        not isinstance(time_budget_seconds, (int, float))
        or isinstance(time_budget_seconds, bool)
        or time_budget_seconds <= 0
    ):
        raise OrchestrationError("time_budget_seconds must be positive", code=MISSING_OR_INVALID_FIELD)
    if clock is not None and not callable(clock):
        raise OrchestrationError("clock must be callable", code=MALFORMED_SYNTAX)
    clock_fn = clock or monotonic
    started_at = clock_fn()

    def budget_exhausted() -> bool:
        return (
            time_budget_seconds is not None
            and clock_fn() - started_at >= time_budget_seconds
        )

    current = proposal
    rounds: list[ReviewRound] = []
    seen_proposal_bodies = [_proposal_body(current)]
    for attempt in range(max_revisions + 1):
        if budget_exhausted():
            return _time_budget_result(current, rounds)
        findings: list[RefereeFinding] = []
        for reviewer in reviewer_list:
            if budget_exhausted():
                return _time_budget_result(current, rounds)
            if not callable(reviewer):
                raise OrchestrationError("every reviewer must be callable", code=MALFORMED_SYNTAX)
            reviewer_findings = reviewer(current)
            if budget_exhausted():
                return _time_budget_result(current, rounds)
            if isinstance(reviewer_findings, (str, bytes)):
                raise OrchestrationError("reviewer output must be an iterable of finding objects", code=MALFORMED_SYNTAX)
            findings.extend(_review(reviewer_findings))
        reviewed = tuple(findings)
        finding_ids = [finding.finding_id for finding in reviewed]
        if len(finding_ids) != len(set(finding_ids)):
            raise OrchestrationError("referee finding IDs must be unique within a round", code=MISSING_OR_INVALID_FIELD)
        if escalation_policy is not None:
            escalation_reasons = _escalation_reasons(
                escalation_policy, current, reviewed
            )
            if escalation_reasons:
                rounds.append(
                    ReviewRound(attempt=attempt, proposal=dict(current), findings=reviewed)
                )
                escalation = EscalationRequest(
                    status="awaiting_human_review",
                    reasons=escalation_reasons,
                    finding_ids=tuple(finding_ids),
                    reviewers=tuple(sorted({finding.reviewer for finding in reviewed})),
                    proposal=dict(current),
                )
                return OrchestrationResult(
                    accepted=False,
                    proposal=dict(current),
                    rounds=tuple(rounds),
                    reasons=tuple(
                        f"human escalation required: {reason}"
                        for reason in escalation_reasons
                    ),
                    escalation=escalation,
                )
        unresolved = tuple(finding for finding in reviewed if finding.disposition != "resolved")
        if not unresolved:
            rounds.append(ReviewRound(attempt=attempt, proposal=dict(current), findings=reviewed))
            return OrchestrationResult(
                accepted=True,
                proposal=dict(current),
                rounds=tuple(rounds),
                reasons=(),
            )
        if attempt == max_revisions:
            rounds.append(ReviewRound(attempt=attempt, proposal=dict(current), findings=reviewed))
            reasons = tuple(
                f"unresolved finding {finding.finding_id}: {finding.message}"
                for finding in unresolved
            )
            return OrchestrationResult(
                accepted=False,
                proposal=dict(current),
                rounds=tuple(rounds),
                reasons=reasons,
            )
        if budget_exhausted():
            rounds.append(ReviewRound(attempt=attempt, proposal=dict(current), findings=reviewed))
            return _time_budget_result(current, rounds)
        revised = reviser(dict(current), reviewed)
        if budget_exhausted():
            rounds.append(ReviewRound(attempt=attempt, proposal=dict(current), findings=reviewed))
            return _time_budget_result(current, rounds)
        if not isinstance(revised, dict):
            raise OrchestrationError("reviser must return a proposal object", code=MALFORMED_SYNTAX)
        responses = _responses(revised.get("finding_responses"), reviewed)
        rounds.append(
            ReviewRound(
                attempt=attempt,
                proposal=dict(current),
                findings=reviewed,
                responses=responses,
            )
        )
        revised_body = _proposal_body(revised)
        if revised_body == _proposal_body(current):
            return OrchestrationResult(
                accepted=False,
                proposal=dict(current),
                rounds=tuple(rounds),
                reasons=("reviser made no progress",),
            )
        if any(revised_body == prior for prior in seen_proposal_bodies):
            return OrchestrationResult(
                accepted=False,
                proposal=dict(current),
                rounds=tuple(rounds),
                reasons=("reviser repeated a prior proposal state",),
            )
        seen_proposal_bodies.append(revised_body)
        current = revised

    raise AssertionError("bounded referee loop did not terminate")


def run_enveloped_referee_loop(
    proposal: dict[str, Any],
    reviewers: Iterable[Callable[[ProposalEnvelope], Iterable[dict[str, Any]]]],
    reviser: Callable[
        [ProposalEnvelope, tuple[RefereeFinding, ...]], dict[str, Any]
    ],
    *,
    max_revisions: int = 3,
    escalation_policy: Callable[
        [dict[str, Any], tuple[RefereeFinding, ...]], Iterable[str] | None
    ]
    | None = None,
    time_budget_seconds: float | None = None,
    clock: Callable[[], float] | None = None,
) -> OrchestrationResult:
    """Run the referee loop with strict proposal identity and revision lineage."""
    try:
        initial = validate_proposal_envelope(proposal)
    except ProposalContractError as error:
        raise OrchestrationError(f"initial proposal envelope is invalid: {error}", code=MISSING_OR_INVALID_FIELD) from error
    reviewer_list = tuple(reviewers)
    if not reviewer_list:
        raise OrchestrationError("at least one reviewer is required", code=MISSING_OR_INVALID_FIELD)
    if not all(callable(reviewer) for reviewer in reviewer_list):
        raise OrchestrationError("every reviewer must be callable", code=MALFORMED_SYNTAX)
    if not callable(reviser):
        raise OrchestrationError("reviser must be callable", code=MALFORMED_SYNTAX)
    seen_proposal_ids = {initial.proposal_id}
    seen_payloads = [dict(initial.payload)]

    def wrap_reviewer(
        reviewer: Callable[[ProposalEnvelope], Iterable[dict[str, Any]]],
    ) -> Callable[[dict[str, Any]], Iterable[dict[str, Any]]]:
        def reviewed(current: dict[str, Any]) -> Iterable[dict[str, Any]]:
            try:
                envelope = validate_proposal_envelope(current)
            except ProposalContractError as error:
                raise OrchestrationError(
                    f"proposal envelope is invalid during review: {error}", code=MISSING_OR_INVALID_FIELD
                ) from error
            return reviewer(envelope)

        return reviewed

    def revise(
        current: dict[str, Any], findings: tuple[RefereeFinding, ...]
    ) -> dict[str, Any]:
        current_envelope = validate_proposal_envelope(current)
        revised = reviser(current_envelope, findings)
        try:
            revised_envelope = validate_proposal_envelope(revised)
        except ProposalContractError as error:
            raise OrchestrationError(f"revised proposal envelope is invalid: {error}", code=MISSING_OR_INVALID_FIELD) from error
        if revised_envelope.parent_proposal_id != current_envelope.proposal_id:
            raise OrchestrationError(
                "revised proposal parent_proposal_id must match the preceding proposal_id",
                code=INVALID_STATE_TRANSITION,
            )
        if revised_envelope.proposal_id in seen_proposal_ids:
            raise OrchestrationError("revised proposal_id must be unique within the run", code=INVALID_STATE_TRANSITION)
        revised_payload = dict(revised_envelope.payload)
        if revised_payload == dict(current_envelope.payload):
            raise OrchestrationError("revised proposal payload made no substantive progress", code=INVALID_STATE_TRANSITION)
        if any(revised_payload == prior for prior in seen_payloads):
            raise OrchestrationError("revised proposal payload repeats a prior state", code=INVALID_STATE_TRANSITION)
        if revised_envelope.content_hash == current_envelope.content_hash:
            raise OrchestrationError("revised proposal content_hash must change with its payload", code=INVALID_STATE_TRANSITION)
        seen_proposal_ids.add(revised_envelope.proposal_id)
        seen_payloads.append(revised_payload)
        return revised

    return run_referee_loop(
        proposal,
        tuple(wrap_reviewer(reviewer) for reviewer in reviewer_list),
        revise,
        max_revisions=max_revisions,
        escalation_policy=escalation_policy,
        time_budget_seconds=time_budget_seconds,
        clock=clock,
    )
