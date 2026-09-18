# Atmanatic Master Implementation Roadmap

**Status:** Working roadmap, synthesized from current repository state
**Date:** 2026-09-18
**Purpose:** Translate the existing strategy documents into one ordered,
falsifiable execution sequence. This document does not replace
[ATMANATIC_VERIFIABLE_AGENTIC_RESEARCH_IMPLEMENTATION_PLAN.md](ATMANATIC_VERIFIABLE_AGENTIC_RESEARCH_IMPLEMENTATION_PLAN.md),
[ATMANATIC_PROTOCOL_0.1_DRAFT.md](ATMANATIC_PROTOCOL_0.1_DRAFT.md), or the
[docs/architecture/](docs/architecture/) appendix. It states what is actually
built today, what is only specified, and the exact next actions in priority
order.

## 1. The ultimate goal, stated plainly

Atmanatic becomes a **vendor-neutral protocol and reference implementation**
for exchanging bounded, falsifiable, evidence-linked claims — with formal
separation between optimization, memory, verification, and authority — that:

- is independently installable with zero runtime dependencies;
- has at least one other independent implementation that interoperates with it;
- fails closed on every malformed, stale, unresolved, or self-reviewed artifact;
- never grants execution authority by implication, at any layer;
- is trusted enough that external consumers adopt it without adopting Atmanatic.

Everything below is the path from "well-specified library with passing tests"
to that end state.

## 2. Ground truth: what exists right now

Verified directly against the repository, not against the plan documents:

| Area | State |
| --- | --- |
| Package | `atmanatic-research` 0.1.0, zero runtime deps, `requires-python >= 3.11`, wheel builds clean |
| Tests | 97 tests across 12 files, all passing |
| Contracts implemented | proposal, artifact, evidence, promotion-record, benchmark, review, source-policy, validity governance, orchestration + audit events |
| Orchestration | proposer/referee loop, typed findings/responses, non-progress detection, time budgets, escalation requests, deterministic audit events — all implemented (Phase 3 substantially complete) |
| Repository boundary | shims removed, packaging clean, separation audit passes with zero violations — but **no second repository has ever actually been split off and proven** |
| Protocol 0.1 draft | written, but self-declares several **Proposed** (not implemented) sections: strict RFC 3339 timestamp profile, canonical JSON + content-hash projection, extensions mechanism, machine-readable error codes/conformance results |
| Graph analysis (optimization/memory layer) | fully specified in [docs/architecture/eigenvector_graph_analysis.md](docs/architecture/eigenvector_graph_analysis.md) — **`atmanatic_research/graph_analysis.py` does not exist yet** |
| Benchmark harness (Phase 4) | validator (`validate_benchmark`) exists; no fixtures, no harness, no CI gate |
| Formal verification adapters (Phase 5) | not started — no sandbox, no verifier-result runner |
| Lifecycle event log / promotion workflow (Phase 6) | `validate_promotion_record` exists as a static contract; no transition-event log wiring it to `validity_governance.py` |
| Release hardening (Phase 8) | no signing, no wheel-inspection CI, no rollback runbook |
| Working tree | uncommitted changes: `docs/architecture/*`, `docs/foundations/*`, two new root docs, and edits to the implementation plan + README referencing them |

**Read of the situation:** Phases 0–3 of the implementation plan are real and
tested. Phases 4–8 are specified in prose but have zero code. The Protocol 0.1
draft is honest about its own gaps. This is a good position — the foundation
is solid — but "ultimate goal" work from here is concrete engineering, not
more strategy documents.

## 3. Immediate housekeeping (do this first, low risk)

1. Commit the current working tree (`docs/architecture/*`, `docs/foundations/*`,
   the two new root docs, and the plan/README edits). Uncommitted architecture
   docs are not reviewable or citable as "current state" until they're in history.
2. Add a one-line status table to [docs/architecture/README.md](docs/architecture/README.md)
   marking each phase `implemented`, `partial`, or `not started`, cross-linked
   to this roadmap, so the phase status never drifts from reality again.

## 4. Execution sequence (priority order)

Ordered by: (a) what unblocks the most other work, (b) what is fully specified
already so risk is low, (c) what closes the biggest credibility gap first.

### Step 1 — Build `graph_analysis.py` exactly as specified

**Status: done.** `atmanatic_research/graph_analysis.py` implements the three
phases from the spec: `build_graph_snapshot()` (validated, canonically ordered,
hashed nodes/edges), `personalized_pagerank()` (dangling-mass redistribution to
seed, deterministic ordering, structured `not_converged` finding on timeout),
and `build_graph_analysis_artifact()` / `validate_graph_analysis_result()` for
the non-authorizing artifact. `tests/test_graph_analysis.py` covers order
independence, unknown node/edge types, duplicate IDs, unresolved references,
negative/non-finite weights, convergence and non-convergence, and artifact
rejection of `execution_authorized: true`. Nothing in `evidence_admission.py`,
`truth_review.py`, or `validity_governance.py` was touched.

This is the lowest-risk, highest-leverage next unit of work: the spec in
[eigenvector_graph_analysis.md](docs/architecture/eigenvector_graph_analysis.md)
is already complete (data model, algorithms, determinism rules, artifact
schema, required tests). Implement it in the three phases the doc already
defines (pure graph construction → personalized PageRank → audit findings),
add `tests/test_graph_analysis.py` per its "Required Tests" section, and wire
nothing into `evidence_admission.py`, `truth_review.py`, or
`validity_governance.py` — the doc is explicit that governing code must never
accept a graph score. This proves the optimization/memory layer can ship
without ever touching authority.

**Exit check:** identical canonical input always produces an identical hash
and rank order; disabling/ignoring graph analysis entirely does not change any
governance test outcome. Verified by `tests/test_graph_analysis.py`.

### Step 2 — Close the Protocol 0.1 "Proposed" gaps

These block any real interoperability claim and are the single biggest
credibility risk right now (a draft that admits its own hashing scheme isn't
frozen cannot be implemented twice).

**Status: done.** `atmanatic_research/canonical.py` freezes canonical JSON
(sorted keys, compact separators, non-finite rejection) and the `content_hash`
projection/verification functions; `atmanatic_research/timestamps.py` enforces
RFC 3339 with an explicit UTC offset across artifact, evidence, proposal, and
acquisition-receipt validators; `atmanatic_research/error_codes.py` gives every
contract exception (`ArtifactContractError`, `ProposalContractError`,
`EvidenceContractError`, `SourcePolicyError`) a stable `.code` from the
registry in the protocol draft's error model section; and
`validate_artifact_lineage()` now accepts `supported_extensions` and enforces
fail-closed rejection of unsupported critical extensions while preserving
unknown non-critical ones. Remaining open items: normative JSON Schemas,
signatures/key lifecycle, and structured codes on `ValidationResult` (the
validity-transition path still returns string violations, not codes).

1. ~~Freeze one canonical JSON representation...~~
2. ~~Enforce the RFC 3339 + explicit-UTC-offset timestamp rule...~~
3. ~~Add a machine-readable error-code enum...~~
4. ~~Add the `extensions` / `critical_extensions` mechanism...~~
5. Update the draft from "Proposed" to "Implemented" only after tests exist
   for each item above — done for sections 5.1, 5.2, 5.3, and 11.

**Exit check:** two people, given only the updated protocol doc, could
independently write a validator that agrees byte-for-byte on a content hash
for the same fixture artifact. Verified by `tests/test_canonical.py`.

### Step 3 — Phase 4: deterministic benchmark harness

**Status: done.** `atmanatic_research/benchmark_harness.py` provides
`BenchmarkCase` and `run_benchmark()`, which executes a fixed case corpus
against named validators twice (raising if the two runs disagree), reports
`false_accept_rate`, `false_reject_rate`, and `reproducible` as separate
metrics — no composite score — and returns a record that passes the existing
`validate_benchmark()` contract. `tests/test_benchmark_harness.py` proves a
deliberately broken validator (one that accepts everything) fails the
corresponding case rather than passing silently, which is the actual
regression-gate behavior; wiring this into CI is still open since no CI
configuration exists in this repository yet.

1. Create a `benchmarks/` (or `tests/fixtures/`) directory with fixed,
   content-hashed fixtures: valid, invalid, boundary, and adversarial cases per
   module in [implementation_checklist.md](docs/architecture/implementation_checklist.md).
2. Track false-accept rate, false-reject rate, and reproducibility across runs
   as separate numbers — no composite score (the plan explicitly forbids a
   single "Sycophancy Resistance Score" until its methodology is defined).
3. Wire it into CI as a regression gate: a change cannot be called an
   improvement unless the compatibility corpus still passes.

**Exit check:** a deliberately broken PR (e.g., a validator that silently
accepts a naive timestamp) fails the benchmark gate, not just unit tests.

### Step 4 — Phase 6: lifecycle event log + promotion workflow

**Status: done.** `atmanatic_research/lifecycle_events.py` adds
`validate_lifecycle_event()`, `record_transition()` (wraps any `ValidationResult`-returning
transition callable — `advance()`, `advance_with_review()`, or `promote_packet()`
— and always records the attempt, pass or fail), and `LifecycleEventLog`, an
append-only JSON-lines store with `latest_status()` resolved by `created_at`
rather than write order. `atmanatic_research/validity_governance.py` gained
`promote_packet()`, which requires `awaiting_human_promotion`, a structurally
valid `approved` promotion record, and a matching `approved_artifact_hash`
before setting `PROMOTED` and retaining the promotion record on
`packet.metadata`. `tests/test_lifecycle_events.py` proves rejected transitions
always carry violations, accepted ones never do, and promotion cannot silently
apply to the wrong artifact hash or the wrong packet state.

1. Add an append-only transition-event log (prior state, target state, evidence
   set, actor, timestamp) that wraps `validity_governance.py`'s `advance()` /
   `advance_with_review()` instead of only mutating the in-memory packet.
2. Wire `validate_promotion_record` into an explicit promotion function that
   requires: `awaiting_human_promotion` state, a named human approver, approved
   scope, artifact hash match, rollback target, and expiry — reusing the
   existing contract rather than adding a second one.
3. Add tests proving a promotion for one bounded scope cannot silently apply to
   a different scope or a different artifact hash.

**Exit check:** every promoted decision is traceable to artifact → review →
verification → approver → scope → expiry → rollback, per the plan's Phase 6
exit gate — reproduce that trace in a test, not just in prose. Reproduced by
`test_successful_promotion_sets_level_and_retains_record`.

### Step 5 — Phase 5: first formal verification adapter (narrow scope)

**Status: piloted, narrower than the original plan.**
`atmanatic_research/verification_adapters.py` implements
`check_validity_transition_table()` (checks the six-level ladder for
unreachable levels and non-monotonic edges) and `run_validity_transition_pilot()`,
which returns a `validate_verification_result()`-conformant record with
`input_artifact_hash` derived from the declared ladder itself, so the result is
reproducible from recorded input alone. `tests/test_verification_adapters.py`
proves the real ladder verifies clean, and that a deliberately broken
transition rule (injected via `can_advance_fn`) is flagged rather than silently
passing.

This pilot is intentionally narrower than the original Phase 5 scope: it has no
untrusted input (the ladder is fixed, reviewed Python, not caller-supplied
specifications or generated proofs), so it requires no sandbox, no resource
limits, and no Lean toolchain. A verifier that accepts untrusted specifications
or generated code still needs the sandboxed-subprocess work described below
before it can be trusted — that remains unbuilt.

1. Define the verification-result schema from the plan (verifier name/version,
   input hash, spec ID, status, diagnostics, resource usage, environment).
2. Pick **one** deterministic verifier for a genuinely narrow invariant (a good
   first target: prove a validity-state transition table has no unreachable
   or contradictory states — this is exactly the kind of narrow, finite,
   mathematically well-specified property Lean/SMT are good at).
3. Run it in a sandboxed subprocess with CPU/memory/wall-clock limits and no
   network access; treat timeout and malformed output as failure, never as
   partial success.

**Exit check:** a deliberately failing proof stays failed; result is
reproducible from the recorded input and spec alone. Reproduced by
`test_broken_reachability_is_flagged` / `test_broken_monotonicity_is_flagged`
and `test_pilot_is_reproducible_in_verdict_and_diagnostics`.

### Step 6 — Phase 7: prove the repository split for real

**Status: done.** `scripts/verify_repository_split.py` builds the wheel,
installs it into an isolated `--target` directory (no venv/`ensurepip`
bootstrap needed), and runs a consumer smoke test with `PYTHONPATH` limited to
that directory and `cwd` outside the repository. The smoke test asserts the
repository is not on `sys.path`, that `atmanatic_research.__file__` resolves
outside the repository tree, and that `validate_artifact_lineage` behaves
correctly (accepts a valid record, rejects `execution_authorized: true`) from
the installed package alone. After the consumer environment is deleted, the
script re-runs Atmanatic's own test suite from the repository to confirm it
never depended on the consumer. Executed run: wheel built
(`atmanatic_research-0.1.0-py3-none-any.whl`), consumer smoke test printed
`CONSUMER_SMOKE_TEST_OK` from the installed path, and all 160 repository tests
passed afterward — converting this from an asserted target into evidence.

1. Stand up a throwaway second directory/repo that imports only the built
   wheel (not the source tree) and runs a minimal consumer test suite against
   it.
2. Delete the Atmanatic source checkout in that environment and confirm the
   consumer still works.
3. Delete the consumer and confirm Atmanatic's own tests still pass with zero
   awareness of the consumer ever existing.

**Exit check:** this is the actual acceptance test already defined in
[ATMANATIC_REPOSITORY_BOUNDARY_PLAN.md](ATMANATIC_REPOSITORY_BOUNDARY_PLAN.md)
§"Final acceptance test" — it has never been executed, only asserted as a
target. Executing it once converts it from a claim into evidence.

### Step 7 — Phase 8: release hardening

Signed, hash-verified, rollback-capable releases with CI wheel inspection and
a dependency/vulnerability scan — mechanical once Steps 1–6 exist, and low
value to do earlier since there's nothing worth shipping externally yet.

### Step 8 — Standards-track activity (longer horizon)

Only after Steps 1–7: seek a second, independently-written implementation
(ideally a different language) and run bidirectional interoperability tests.
This is the step that actually validates "protocol" versus "library."

## 5. What not to do

- Do not add a composite trust/confidence score anywhere — the plan already
  forbids this explicitly and for good reason (hides component failures).
- Do not let graph analysis, benchmarks, or optimization telemetry influence
  `evidence_admission.py`, `truth_review.py`, or `validity_governance.py` pass/fail
  outcomes, even indirectly through prioritization that changes what gets reviewed
  first without changing what passes.
- Do not attempt Phase 7's repository split as a documentation exercise again —
  it has already been "declared" complete once (shim removal) without the
  actual split being executed; only running the real acceptance test counts.
- Do not chase Lean/formal verification breadth before Step 4 exists — an
  unresolved lifecycle/promotion gap is a bigger institutional-trust risk than
  missing formal proofs.

## 6. Definition of done for "best version of ourselves"

Per the existing cross-phase acceptance criteria in the implementation plan,
plus this roadmap's additions:

- [ ] Steps 1–7 above are complete and each has a passing, committed test.
- [ ] The Protocol 0.1 draft contains zero remaining "Proposed" markers.
- [ ] A second, independent implementation exists and interoperates.
- [ ] The repository split acceptance test has been executed at least once, not just asserted.
- [ ] Every promoted artifact is traceable end-to-end in a test, not just in the schema.
- [ ] No composite scores exist anywhere in the codebase.
