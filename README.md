# Atmanatic Research Institution

This is the standalone Atmanatic research project.

Atmanatic owns domain-neutral research contracts, evidence and provenance
structures, validity packets, falsification and review rules, source-policy
evaluation, and deterministic research transformations.

External consumers may use this project's published package or API, but they
are not included in this project and have no shared filesystem, database,
credential, treasury, or execution relationship here.

## Build

```powershell
python -m pip install build
python -m build
```

## Test

```powershell
python -m unittest discover -s tests -q
```

The project must build and test successfully with every external consumer
repository absent.

## Artifact contracts

The public package also validates common artifact lineage and verification
envelopes:

```python
from atmanatic_research import (
	validate_artifact_lineage,
	validate_verification_result,
	validate_review_outcome,
	validate_promotion_record,
)
```

These contracts require versioned identity, producer, timestamps, content
hashes, explicit non-authority, and lifecycle metadata. Verification results
record what a verifier checked; they do not establish universal truth or grant
execution authority. Promotion records are explicit, scoped decisions and
remain non-authorizing research artifacts.

`validate_review_outcome()` records the independent reviewer, the exact
artifact hash under review, concrete challenge findings, and the disposition.
A resolved outcome must include its resolution and cannot be authored by the
same producer as the reviewed artifact.

The provider-neutral `run_referee_loop()` accepts injected proposer/referee
callables without adding an LLM or workflow dependency. Referee findings must
be structured, unresolved findings block acceptance, revisions are bounded by
`max_revisions`, unchanged revisions are rejected as non-progress, and
malformed reviewer output fails closed.

For decision-grade evidence, use `validate_and_admit_evidence()` when the
caller wants one fail-closed entry point. It first applies the complete
evidence-card contract and then applies freshness, provenance, status, and
recall admission checks.

Use `require_claim_evidence()` when a claim must be tied to those admitted
cards. It rejects duplicate or conflicting evidence identifiers and rejects
claim source references that are not present in the admitted evidence set.

Use `validate_and_admit_governed_evidence()` when evidence must also pass the
institutional source registry before admission. It checks that every source is
enabled, permitted for the card's agent, and meets the requested authority
tier. Identified public sources additionally require a compliant request
context and an acquisition receipt whose source and response hash match the
evidence card:

```python
from atmanatic_research import validate_and_admit_governed_evidence

validate_and_admit_governed_evidence(
	[cards[0]],
	registry,
	minimum_tier="A",
	request_contexts={
		"sec-edgar": {
			"identity_profile_id": "institutional-contact",
			"headers_present": ["User-Agent"],
		},
	},
	acquisition_receipts=[receipt],
)
```

Request contexts are keyed by source ID. Receipts are a list so separate
retrievals from the same source can be linked by response content hash. The
function returns the original cards only after source governance, complete
card validation, and decision-grade admission all succeed.

## Identified public sources

Public sources that require request identification can declare that policy
without giving Atmanatic credentials, personal data, or responsibility for
HTTP acquisition:

```python
from atmanatic_research import assert_source_allowed, validate_acquisition_receipt

source = {
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
registry = {"sources": [source]}

assert_source_allowed(
	registry,
	"sec-edgar",
	"research-agent",
	request_context={
		"identity_profile_id": "institutional-contact",
		"headers_present": ["User-Agent"],
	},
)
```

The consumer resolves `institutional-contact`, performs the request, and may
then call `validate_acquisition_receipt()` with a non-secret receipt containing
the source ID, retrieval time, policy version, identity profile ID, compliance
attestation, and response content hash. The receipt records declared policy
compliance; it does not independently prove what headers were sent. Sources
without an `access` policy retain the 0.1.0 behavior for compatibility.

## Measurable falsifiers

Claims remain backward compatible and use qualitative falsifiers by default.
When a domain permits measurement, declare `falsifier_kind` as `measurable`
and provide the deterministic comparison condition:

```python
claim = {
	"claim": "Source refresh latency remains below the decision window.",
	"source_ids": ["source-1"],
	"falsifier": "The p95 refresh latency exceeds 300 seconds over 24 hours.",
	"falsifier_kind": "measurable",
	"falsifier_measurement": {
		"metric": "source_refresh_latency_p95",
		"operator": ">",
		"threshold": 300,
		"unit": "seconds",
		"observation_window": "24 hours",
	},
	"counterclaim": "Burst load may cause refresh latency to exceed the window.",
	"uncertainty": "The observation excludes upstream outages.",
	"author": "research-agent",
	"independent_reviewer": "review-agent",
	"review_outcome": "challenged_and_resolved",
}
```

`review_claim()` validates the condition's structure. A domain validator,
simulation, or human reviewer must still determine whether the named metric
actually tests the claim and whether the threshold is appropriate.
