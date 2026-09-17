"""Fail-closed adversarial review contract for decision-grade claims."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

WEAK_FALSIFIER_PATTERNS = [
    r"^n/?a$",
    r"^none$",
    r"^if it fails$",
    r"^if tests break$",
    r"^if metric is bad$",
    r"^unknown$",
    r"^tbd$",
]

DEFENSIVE_LANGUAGE_PATTERNS = [
    r"further research is needed",
    r"we do not address",
    r"it should be noted that we didn't",
    r"while not optimal",
    r"though limited in scope",
    r"as a preliminary attempt",
]

PLACEHOLDER_IDENTITIES = {"system", "self", "auto", "none", "unknown", "n/a", ""}
FALSIFIER_KINDS = {"qualitative", "measurable"}
MEASUREMENT_OPERATORS = {"<", "<=", "==", "!=", ">=", ">"}
MEASUREMENT_FIELDS = ("metric", "operator", "threshold", "unit", "observation_window")


@dataclass(frozen=True)
class TruthReview:
    admitted: bool
    reasons: tuple[str, ...]


def _review_falsifier_measurement(claim: dict[str, Any], reasons: list[str]) -> None:
    kind = claim.get("falsifier_kind", "qualitative")
    if not isinstance(kind, str) or kind not in FALSIFIER_KINDS:
        reasons.append("claim falsifier_kind must be qualitative or measurable")
        return
    if kind != "measurable":
        return

    measurement = claim.get("falsifier_measurement")
    if not isinstance(measurement, dict):
        reasons.append("measurable claim has no falsifier_measurement")
        return
    missing = [
        field
        for field in MEASUREMENT_FIELDS
        if field not in measurement
        or (isinstance(measurement[field], str) and not measurement[field].strip())
    ]
    if missing:
        reasons.append("falsifier_measurement is missing fields: " + ", ".join(missing))
        return
    if not isinstance(measurement["metric"], str):
        reasons.append("falsifier_measurement metric must be a non-empty string")
    if not isinstance(measurement["operator"], str) or measurement["operator"] not in MEASUREMENT_OPERATORS:
        reasons.append("falsifier_measurement operator is invalid")
    threshold = measurement["threshold"]
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
        reasons.append("falsifier_measurement threshold must be numeric")
    if not isinstance(measurement["unit"], str):
        reasons.append("falsifier_measurement unit must be a non-empty string")
    if not isinstance(measurement["observation_window"], str):
        reasons.append("falsifier_measurement observation_window must be a non-empty string")


def review_claim(claim: dict[str, Any]) -> TruthReview:
    """Require falsifiability, dissent, uncertainty, and independent review."""
    reasons: list[str] = []
    claim_text = str(claim.get("claim", "")).strip()
    if not claim_text:
        reasons.append("claim text is missing")
    else:
        for pat in DEFENSIVE_LANGUAGE_PATTERNS:
            if re.search(pat, claim_text, re.IGNORECASE):
                reasons.append("claim text contains prohibited defensive language")
                break

    if not claim.get("source_ids"):
        reasons.append("claim has no source references")

    falsifier = str(claim.get("falsifier", "")).strip()
    if not falsifier:
        reasons.append("claim has no falsification condition")
    else:
        for pat in WEAK_FALSIFIER_PATTERNS:
            if re.search(pat, falsifier, re.IGNORECASE):
                reasons.append("claim falsifier is too weak or unquantified")
                break
    _review_falsifier_measurement(claim, reasons)

    if not str(claim.get("counterclaim", "")).strip():
        reasons.append("claim has no counterclaim")
    if not str(claim.get("uncertainty", "")).strip():
        reasons.append("claim has no uncertainty statement")

    reviewer = str(claim.get("independent_reviewer", "")).strip()
    if not reviewer or reviewer.lower() in PLACEHOLDER_IDENTITIES:
        reasons.append("claim has no valid independent reviewer identity")

    author = str(claim.get("author", "")).strip() if claim.get("author") else None
    if author and author == reviewer:
        reasons.append("claim author cannot independently review the same claim")

    if claim.get("review_outcome") != "challenged_and_resolved":
        reasons.append("claim has not passed adversarial review")

    return TruthReview(not reasons, tuple(dict.fromkeys(reasons)))


def require_truth_review(claim: dict[str, Any]) -> dict[str, Any]:
    """Return the claim only after the adversarial review contract passes."""
    result = review_claim(claim)
    if not result.admitted:
        raise ValueError("Truth review blocked: " + "; ".join(result.reasons))
    return claim