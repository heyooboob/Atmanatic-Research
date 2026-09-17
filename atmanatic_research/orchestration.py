"""Provider-neutral proposal and referee orchestration primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

_FINDING_SEVERITIES = {"blocker", "warning", "info"}
_FINDING_DISPOSITIONS = {"open", "resolved"}
_REVIEW_PURPOSES = {
    "falsifier",
    "assumption_auditor",
    "provenance_auditor",
    "boundary_tester",
    "implementation_contract_reviewer",
}


class OrchestrationError(ValueError):
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
class ReviewRound:
    attempt: int
    proposal: dict[str, Any]
    findings: tuple[RefereeFinding, ...]


@dataclass(frozen=True)
class OrchestrationResult:
    accepted: bool
    proposal: dict[str, Any]
    rounds: tuple[ReviewRound, ...]
    reasons: tuple[str, ...]


def _finding(value: Any, index: int) -> RefereeFinding:
    if not isinstance(value, dict):
        raise OrchestrationError(f"referee finding {index} must be an object")
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
            f"referee finding {index} is missing non-empty fields: {', '.join(missing)}"
        )
    if value["severity"] not in _FINDING_SEVERITIES:
        raise OrchestrationError(f"referee finding {index} has an invalid severity")
    if value["disposition"] not in _FINDING_DISPOSITIONS:
        raise OrchestrationError(f"referee finding {index} has an invalid disposition")
    if value["review_purpose"] not in _REVIEW_PURPOSES:
        raise OrchestrationError(f"referee finding {index} has an invalid review purpose")
    evidence_refs = value.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs or not all(
        isinstance(reference, str) and reference.strip() for reference in evidence_refs
    ):
        raise OrchestrationError(
            f"referee finding {index} evidence_refs must be a non-empty list of strings"
        )
    if len(evidence_refs) != len(set(evidence_refs)):
        raise OrchestrationError(f"referee finding {index} evidence_refs must be unique")
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
        raise OrchestrationError("referee finding IDs must be unique within a round")
    return values


def run_referee_loop(
    proposal: dict[str, Any],
    reviewers: Iterable[Callable[[dict[str, Any]], Iterable[dict[str, Any]]]],
    reviser: Callable[[dict[str, Any], tuple[RefereeFinding, ...]], dict[str, Any]],
    *,
    max_revisions: int = 3,
) -> OrchestrationResult:
    """Review and revise a proposal with bounded, fail-closed retries.

    Reviewers and the reviser are injected callables so model providers,
    deterministic test doubles, or external services remain outside this
    package. Any malformed reviewer output, unresolved finding, or missing
    revision rejects the loop rather than being treated as approval.
    """
    if not isinstance(proposal, dict):
        raise OrchestrationError("proposal must be an object")
    if not isinstance(max_revisions, int) or max_revisions < 0:
        raise OrchestrationError("max_revisions must be a non-negative integer")
    reviewer_list = tuple(reviewers)
    if not reviewer_list:
        raise OrchestrationError("at least one reviewer is required")
    if not callable(reviser):
        raise OrchestrationError("reviser must be callable")

    current = proposal
    rounds: list[ReviewRound] = []
    for attempt in range(max_revisions + 1):
        findings: list[RefereeFinding] = []
        for reviewer in reviewer_list:
            if not callable(reviewer):
                raise OrchestrationError("every reviewer must be callable")
            reviewer_findings = reviewer(current)
            if isinstance(reviewer_findings, (str, bytes)):
                raise OrchestrationError("reviewer output must be an iterable of finding objects")
            findings.extend(_review(reviewer_findings))
        reviewed = tuple(findings)
        finding_ids = [finding.finding_id for finding in reviewed]
        if len(finding_ids) != len(set(finding_ids)):
            raise OrchestrationError("referee finding IDs must be unique within a round")
        round_record = ReviewRound(attempt=attempt, proposal=dict(current), findings=reviewed)
        rounds.append(round_record)
        unresolved = tuple(finding for finding in reviewed if finding.disposition != "resolved")
        if not unresolved:
            return OrchestrationResult(
                accepted=True,
                proposal=dict(current),
                rounds=tuple(rounds),
                reasons=(),
            )
        if attempt == max_revisions:
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
        revised = reviser(dict(current), reviewed)
        if not isinstance(revised, dict):
            raise OrchestrationError("reviser must return a proposal object")
        if revised == current:
            return OrchestrationResult(
                accepted=False,
                proposal=dict(current),
                rounds=tuple(rounds),
                reasons=("reviser made no progress",),
            )
        current = revised

    raise AssertionError("bounded referee loop did not terminate")
