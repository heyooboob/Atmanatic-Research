# Atmanatic Research Institution

This is the standalone Atmanatic research project.

## Atmanatic Protocol 0.1

The project's immediate standards-track milestone is
[Atmanatic Protocol 0.1](ATMANATIC_PROTOCOL_0.1_DRAFT.md), a vendor-neutral
working draft for exchanging verifiable claims, evidence, and review outcomes
between humans, AI agents, and software systems.

The protocol is broader than this Python package and narrower than an AI
platform. It defines portable artifacts, validation semantics, review linkage,
and bounded validity transitions. It does not define model providers,
orchestration, storage, transport, or execution authority. The draft also
identifies the schemas, canonical serialization, security, conformance,
independent implementations, and open governance still required before the
work can credibly seek recognition as an official standard.

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

Use `advance_with_review()` for transitions to `independently_verified` or
`awaiting_human_promotion`. The packet must declare its SHA-256 content digest
as `metadata["content_hash"]`, and the validated review artifact's
`subject_artifact_hash` must match it:

```python
from atmanatic_research import ValidityLevel, advance_with_review

result = advance_with_review(
	packet,
	ValidityLevel.INDEPENDENTLY_VERIFIED,
	review_record,
)
```

Only a `challenged_and_resolved` review can advance the packet. Reviewer and
challenge fields are derived from the artifact, and a failed transition leaves
the packet unchanged. The standalone `advance()` remains the low-level validity
protocol primitive; consumers enforcing Phase 2 governance should use the
review-backed entry point for review-gated levels.

The provider-neutral `run_referee_loop()` accepts injected proposer/referee
callables without adding an LLM or workflow dependency. Referee findings must
be structured, unresolved findings block acceptance, revisions are bounded by
`max_revisions`, unchanged revisions are rejected as non-progress, and
malformed reviewer output fails closed.

Each referee finding declares `review_purpose` as one of `falsifier`,
`assumption_auditor`, `provenance_auditor`, `boundary_tester`, or
`implementation_contract_reviewer`. It must also include a non-empty, unique
list of `evidence_refs` supporting the finding or its resolution. The resulting
`RefereeFinding` preserves both fields as typed immutable values, so downstream
audit code can distinguish reviewer roles and trace each disposition to its
declared basis.

When findings require a revision, the reviser must return a proposal containing
`finding_responses`. Every finding ID from that round must appear exactly once;
each response declares `addressed` or `disputed`, a non-empty explanation, and
supporting evidence references. Unknown, duplicate, omitted, or malformed
responses fail closed. `ReviewRound.responses` preserves typed
`FindingResponse` records. Adding responses without changing the proposal body
still counts as non-progress and ends the loop without acceptance.

Untrusted proposer output can first pass through
`validate_proposal_envelope()`. It returns an immutable typed
`ProposalEnvelope` containing a schema version, proposal and parent identities,
producer, timestamp, SHA-256 content digest, evidence references, tool versions,
payload, and explicit non-authority:

```python
from atmanatic_research import validate_proposal_envelope

proposal = validate_proposal_envelope({
	"schema_version": 1,
	"proposal_id": "proposal-1",
	"parent_proposal_id": None,
	"producer": "research-agent",
	"created_at": "2026-09-17T12:00:00Z",
	"content_hash": "a" * 64,
	"evidence_refs": ["evidence-1"],
	"tool_versions": {"research-agent": "1.2.0"},
	"payload": {"claim": "The bounded fixture passed."},
	"execution_authorized": False,
})
```

The envelope validates declared lineage and replay metadata; it does not
recompute the payload hash or establish that cited evidence supports the
proposal. Those checks belong to deterministic tooling and governed evidence
admission.

Use `run_enveloped_referee_loop()` when every proposal and revision must satisfy
that envelope contract. Reviewers receive typed `ProposalEnvelope` values.
Each revision must use a new `proposal_id`, set `parent_proposal_id` to the
immediately preceding proposal, change its payload and declared content hash,
and include the required finding responses. Proposal IDs cannot be reused
within a run. The returned rounds retain each full proposal and its finding IDs,
providing a replayable proposal-to-critique-to-revision chain.

Both referee loops accept an optional caller-owned `escalation_policy`. It
receives the current proposal and typed findings after each review round and
returns escalation reasons when automated revision should stop. A non-empty
result produces an `EscalationRequest` with status `awaiting_human_review`, the
proposal snapshot, finding IDs, reviewer identities, and reasons. It always has
`execution_authorized=False`; the external human workflow owns any subsequent
decision. Malformed policy output and policy exceptions fail closed.

Non-progress detection covers the complete run, not only adjacent revisions.
The generic loop rejects a proposal body that equals any earlier state. The
envelope-aware loop separately rejects a payload that repeats under fresh
proposal IDs or hashes. This prevents bounded retries from oscillating between
previously rejected states while appearing to make progress.

Both loops also accept `time_budget_seconds`. They use a monotonic clock and
check the budget before and after each reviewer and reviser callback. Exhaustion
returns a rejected result with the last accepted proposal state. An optional
`clock` callable supports deterministic tests. This is a cooperative budget:
it detects an overrun after an external callback returns but cannot interrupt a
blocked model or service call. Consumers must enforce hard per-call timeouts in
their provider runtime.

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

Registries may also define per-agent evidence requirements:

```python
registry["minimum_evidence"] = {
	"research-agent": {
		"minimum_sources": 2,
		"minimum_independent_sources": 2,
		"minimum_tier": "B",
	},
}
registry["sources"][0]["independence_group"] = "publisher-a"
registry["sources"][1]["independence_group"] = "publisher-b"
```

`minimum_sources` counts distinct source IDs. `minimum_independent_sources`
counts distinct `independence_group` values, representing independently
controlled publishers, custodians, or collection systems rather than merely
different URLs. When more than one independent source is required, every
contributing source must declare its group. A caller may request a stricter
authority tier but cannot weaken the registry's `minimum_tier`.

Domain-specific evidence rules remain outside this package and can be injected
as named validators. Each validator receives a copy of the validated evidence
card and a tuple of its resolved source definitions. It returns no value or an
empty iterable to pass, and non-empty rejection reasons to block admission:

```python
def validate_sample_size(card, sources):
	if card["details"].get("sample_size", 0) < 30:
		return ["sample size is below 30"]
	return []

validate_and_admit_governed_evidence(
	cards,
	registry,
	domain_validators={"clinical-study": validate_sample_size},
)
```

Validator names appear in rejection messages for auditability. Malformed
outputs and validator exceptions fail closed. The consumer owns the domain
logic, versions, dependencies, and scientific adequacy of each validator.

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
