# Atmanatic Master Implementation Roadmap

**Status:** Canonical implementation path; synthesized from current repository state
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

## 2. Source of truth and current ground truth

This roadmap is the canonical execution sequence. Use the documents below for
the corresponding kind of decision:

| Question | Source of truth |
| --- | --- |
| What should be implemented next? | This roadmap, section 4 |
| What must each module enforce and test? | [docs/architecture/implementation_checklist.md](docs/architecture/implementation_checklist.md) |
| What is currently implemented per module? | [docs/architecture/README.md](docs/architecture/README.md) |
| What is the protocol contract and compatibility boundary? | [ATMANATIC_PROTOCOL_0.1_DRAFT.md](ATMANATIC_PROTOCOL_0.1_DRAFT.md) |
| Why does the architecture exist and what are its phases? | [ATMANATIC_VERIFIABLE_AGENTIC_RESEARCH_IMPLEMENTATION_PLAN.md](ATMANATIC_VERIFIABLE_AGENTIC_RESEARCH_IMPLEMENTATION_PLAN.md) |
| How should Spec Kit integrate without weakening the protocol boundary? | [ATMANATIC_SPECKIT_INTEGRATION_PLAN.md](ATMANATIC_SPECKIT_INTEGRATION_PLAN.md) |
| How should theoretical extensions be evaluated and rolled out? | [ATMANATIC_THEORETICAL_EXTENSIONS_ROLLOUT_PLAN.md](ATMANATIC_THEORETICAL_EXTENSIONS_ROLLOUT_PLAN.md) |

When these documents disagree about implementation status, repository code and
passing tests are authoritative; update this roadmap and the architecture
index in the same change. The protocol draft may intentionally describe future
requirements as **Proposed** even when the reference implementation already
contains a partial capability.

### Ground truth: what exists right now

Verified directly against the repository, not against the plan documents:

| Area | State |
| --- | --- |
| Package | `atmanatic-research` 0.1.3, zero required runtime deps (`cryptography` optional via the `signing` extra), `requires-python >= 3.11`, wheel builds clean |
| Tests | 227 Python tests and 26 TypeScript tests, all passing |
| Contracts implemented | proposal, artifact, evidence, promotion-record, benchmark, review, source-policy, validity governance, orchestration + audit events, graph analysis, verification-result envelopes, and key-record envelopes |
| Orchestration | proposer/referee loop, typed findings/responses, non-progress detection, time budgets, escalation requests, deterministic audit events — all implemented (Phase 3 substantially complete) |
| Repository boundary | shims removed, packaging clean, and the isolated wheel/consumer split acceptance test passes |
| Protocol 0.1 draft | canonical JSON, strict timestamp handling, extensions, error codes, six normative schemas, signing, and key lifecycle are implemented; a general artifact revocation-reason taxonomy and key rotation workflow remain open |
| Graph analysis (optimization/memory layer) | implemented in `atmanatic_research/graph_analysis.py` and deliberately isolated from governance |
| Benchmark harness (Phase 4) | implemented and covered by 24 benchmark entries, including deterministic adapters for primitive and stateful APIs |
| Formal verification adapters (Phase 5) | narrow fixed-code validity-ladder pilot implemented; `atmanatic_research/sandbox_runner.py` provides a resource-limited, timeout-enforcing subprocess sandbox with a strict output protocol, ready for a future untrusted-specification adapter, but nothing yet calls it with untrusted input |
| Lifecycle event log / promotion workflow (Phase 6) | implemented in `lifecycle_events.py` and `validity_governance.py`; a general artifact revocation-reason taxonomy remains open (key revocation reasons are implemented in `signing.py`) |
| Release hardening (Phase 8) | done: wheel inspection, CI gates, signing (`atmanatic_research/signing.py`), key lifecycle, tag-vs-version checks (`scripts/check_release_tag.py`), dependency scanning (`scripts/scan_dependencies.py`), and a signed-manifest CI release job are all implemented; see [RELEASE_RUNBOOK.md](RELEASE_RUNBOOK.md) |
| Working tree | clean at the time of this roadmap update |

**Read of the situation:** the core contract, orchestration, optimization,
lifecycle, verification-pilot, interoperability, signing/key-lifecycle, and
repository-boundary work is implemented and tested, and release operations
(Phase 8) are now complete end to end. Remaining work is concentrated in
deeper benchmark coverage, wiring the sandbox runner to a real
untrusted-specification adapter, protocol registries, key rotation tooling,
and a general artifact revocation taxonomy.

## 3. Completed housekeeping

The architecture index contains the per-module status table and cross-links
back to this roadmap. Repository commits remain an ordinary release/workflow
operation and are intentionally not part of implementation status.

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
unknown non-critical ones. `ValidationResult` (`validity_protocol.validator`)
now carries a `violation_codes` field paired one-to-one with `violations`,
backed by the finite registry in `validity_protocol/codes.py`; every
`ValidationResult`-returning transition (`validate_packet()`, `advance()`,
`advance_with_review()`, `promote_packet()`) and the persisted lifecycle
event record populate it. Remaining open items: normative JSON Schemas and
signatures/key lifecycle.

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
regression-gate behavior. The repository CI runs the full test suite, including
this benchmark gate.

1. Maintain the fixed, content-hashed corpus in
   `tests/test_benchmark_harness.py` with valid, invalid, boundary, and
   adversarial cases for every checklist module. Primitive and stateful APIs
   use deterministic adapters; storage and registry behavior remains covered
   by dedicated unit tests.
2. Track false-accept rate, false-reject rate, and reproducibility across runs
   as separate numbers — no composite score (the plan explicitly forbids a
   single "Sycophancy Resistance Score" until its methodology is defined).
3. Keep the benchmark tests wired into CI as a regression gate: a change cannot
   be called an improvement unless the compatibility corpus still passes.

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

**Status: done.** `scripts/inspect_release.py` builds the wheel, computes its
SHA-256 over the exact archive bytes, and fails closed if any member falls
outside `atmanatic_research`/`validity_protocol` or escapes the archive root
(path traversal); `tests/test_release_inspection.py` proves a synthetic wheel
containing an unexpected top-level package is rejected, and that the current
tree builds a clean one.

Signing, key lifecycle, dependency scanning, tag checks, and a rollback
runbook are now implemented on top of that:

- `atmanatic_research/signing.py` (ed25519, requires the optional
  `cryptography` extra) plus `scripts/generate_release_key.py`,
  `scripts/sign_release.py`, and `scripts/verify_release_manifest.py` build,
  sign, and independently re-verify a non-authorizing release manifest
  (`execution_authorized: false`) binding a tag to the wheel's exact SHA-256,
  against a registered, active key in `release/keys.jsonl`.
- `scripts/check_release_tag.py` fails closed unless a `vMAJOR.MINOR.PATCH`
  git tag matches `[project].version` in `pyproject.toml` exactly.
- `scripts/scan_dependencies.py` runs `pip-audit --strict` and fails closed
  if the scanner itself is missing rather than reporting a false-clean scan.
- `.github/workflows/ci.yml`'s `python` job now runs the dependency scan on
  every push/PR, and a new tag-gated `release` job (`refs/tags/v*`) runs the
  tag check, signs the release manifest from a CI secret key, re-verifies it,
  and uploads it as a build artifact.
- [RELEASE_RUNBOOK.md](RELEASE_RUNBOOK.md) documents the end-to-end
  procedure: key bootstrap, cutting a release, verifying one later, rollback
  (restore the retained artifact, never rebuild at rollback time), and key
  compromise/rotation (revoke via the finite `KEY_REVOCATION_REASONS`
  taxonomy; past signatures remain valid historical attestations).
- `release/keys.jsonl` itself is intentionally not committed by this change:
  minting the actual production key is a maintainer action
  (`scripts/generate_release_key.py`, run locally, never in CI), not
  something this repository should assert on a maintainer's behalf.

### Step 8 — Standards-track activity (longer horizon)

Only after Steps 1–7: seek a second, independently-written implementation
(ideally a different language) and run bidirectional interoperability tests.
This is the step that actually validates "protocol" versus "library."

**Status: groundwork done (8.2/8.4); second implementation not started (8.3/8.5).**
`interop/` is a new, non-packaged top-level directory (not shipped in the
wheel — verified by `scripts/inspect_release.py`'s scope check) containing:

- `interop/schemas/*.schema.json` — six normative JSON Schemas (draft 2020-12)
  for the common envelope, evidence cards, proposal envelopes, review
  outcomes, verification results, and promotion records — the Step 8.2 schema
  freeze, expressed as literal schema files instead of prose.
- `interop/generate_fixtures.py` — generates fixtures **from the live
  validators** and refuses to write a fixture whose declared expectation
  doesn't match what the validator actually returns (verdict and, for
  rejections, the exact error code). This is the Step 8.4 fixture corpus;
  19 fixtures across the 6 core types were generated and self-verified.
- `interop/verify_fixtures.py` + `tests/test_interop_fixtures.py` — re-checks
  every committed fixture against current validator behavior, catching drift
  if a validator changes without regenerating fixtures. This is the Python
  half of the Step 8.5 bidirectional harness.

What remains, and is explicitly not attempted here: a second implementation in
an independent codebase (TypeScript is the pragmatic first choice — see
scoping discussion) that loads `interop/fixtures/manifest.json` and reproduces
the same verdicts/codes; the interoperability report that comparison would
produce; and the governance/IP/standards-body activity in the draft's section
17, which is an organizational process, not an engineering task, and is not
simulated here.

**Future language expansion (noted, not scheduled):** once one second
implementation has full fixture parity, a deliberately different runtime
(strictly typed, e.g. Rust or Go) would add real evidence-matrix value by
stressing canonicalization/timestamp assumptions a dynamically-typed second
implementation wouldn't. This is intentionally not started now — sequencing
is: prove the pattern once, then add more only if warranted by a real
consumer or standards-body review, not for its own sake.

**Exit check (partial):** `interop/generate_fixtures.py` and
`interop/verify_fixtures.py` both exit 0 with zero drift against the current
tree. Full Step 8 exit (a real second implementation passing the same
fixtures) remains open.

**Update — second implementation started and passing.**
`interop/reference-ts/` is a real, independent TypeScript/Node
implementation (zero dependency on `atmanatic_research` or
`validity_protocol` source) covering: error codes, RFC 3339 timestamps,
canonical JSON + content-hash projection, and the six core validators
(artifact lineage, evidence card, proposal envelope, review outcome,
verification result, promotion record). Running `npm test` in that directory
type-checks the implementation and runs it against the shared
`interop/fixtures/manifest.json` corpus: **all 19 fixtures pass with identical
verdicts and error codes to Python.** A dedicated cross-language canonical-hash
parity fixture (`interop/fixtures/canonical_hash_parity.json`) was also added
and independently verified: both implementations compute
`b93d00dc2a8e78c892cd6a71457e14b6c88f37947d2932f9ecceeac1935d7c5b` for the same
input record, checked by a test on each side
(`tests/test_interop_fixtures.py::test_canonical_hash_parity_fixture_matches_python`
and `interop/reference-ts/test/canonical.test.ts`). This is the first real
piece of cross-language interoperability evidence for Draft 0.1, not an
assertion.

Not yet covered by the TypeScript side: source policy, evidence admission,
orchestration/referee loops, lifecycle events, and graph analysis — all
correctly out of scope for a first interoperability slice (source
policy/evidence admission/orchestration are more implementation-specific
and less "wire protocol"; graph analysis is explicitly non-core per
section 18 of the draft). Per the earlier scoping discussion, a third
implementation in a strictly-typed language (Rust/Go) remains noted as a
future option if warranted by a real consumer or standards-body review, not
scheduled now.

## 4b. Interoperability report and CI (2026-09-18)

Two follow-on items closed after Step 8:

1. **Interoperability report.** `interop/generate_report.py` runs both
   reference implementations against the shared fixture corpus and the
   canonical-hash-parity check, then writes `interop/INTEROPERABILITY_REPORT.md`
   from the actual results — generated, not hand-maintained, so it cannot claim
   agreement that doesn't exist. Current result: **19/19 fixtures agree** on
   verdict and error code, and the canonical hash parity check matches.
   `interop/reference-ts/src/checkFixtures.ts` is the TypeScript-side CLI that
   emits machine-readable results for this report (kept separate from the test
   file so the generator doesn't have to parse a test-runner's output format).
   `tests/test_interoperability_report.py` re-generates and asserts full
   agreement, skipping cleanly if `npm`/TypeScript deps aren't present.
2. **CI wiring.** `.github/workflows/ci.yml` runs three jobs: `python` (matrix
   3.11/3.12 — test suite, the repository-split acceptance script, and release
   wheel inspection), `typescript` (`npm ci && npm test` against the fixture
   corpus), and `interoperability-report` (regenerates and uploads the report
   as a build artifact on every push/PR). This is the first CI configuration
   in the repository; previously every regression-catching script here had to
   be run manually.

## 4a. Review and remediation pass (2026-09-18)

A review after Steps 1–7 found six overlooked or inadequately-applied gaps.
All six are now closed:

1. **Error-code coverage was only 4 of ~10 validator modules.**
   `orchestration.py`, `orchestration_audit.py`, `evidence_admission.py`,
   `truth_review.py`, `validity_standard.py`, and `intelligence_contracts.py`
   raised bare `ValueError` with no `.code`. All six now derive from
   `ContractError` and raise with explicit codes from the shared registry
   (`OrchestrationError`, `IntelligenceContractError`, `TruthReviewError`,
   `ValidityStandardError`, `EvidenceAdmissionError` are the new/converted
   classes). `evidence_admission.py`'s mixed `ValueError`/`SourcePolicyError`
   usage is now consistently `EvidenceAdmissionError` with per-condition codes.
2. **`verification_adapters.run_validity_transition_pilot()` minted a constant
   `artifact_id`** across every run, violating the protocol's own rule that an
   identifier must not stand in for content identity. It now accepts an
   optional caller-supplied `artifact_id` and otherwise mints a `uuid4`-based
   one per run; a test proves two runs never collide.
3. **The benchmark corpus only exercised 2 of ~10 checklist modules** (4
   cases). It now covers `artifact_lineage`, `evidence_card`,
   `proposal_envelope`, `source_definition`, `promotion_record`, and
   `review_outcome` with paired accept/reject cases; the unused
   `proposal_envelope` mapping is now actually exercised.
4. **Documentation drift**: `docs/architecture/README.md`'s contents list
   didn't mention `eigenvector_graph_analysis.md` or
   `docs/foundations/mathematical_principles.md`, and
   `implementation_checklist.md` had no entries for `canonical.py`,
   `timestamps.py`, `error_codes.py`, `graph_analysis.py`,
   `benchmark_harness.py`, `lifecycle_events.py`, or
   `verification_adapters.py`. Both fixed; the checklist now has 20 module
   entries instead of 13.
5. **Two parallel append-only JSONL log implementations** (`PacketStore` and
   `LifecycleEventLog`) duplicated the same file I/O pattern. Both now share
   `validity_protocol/jsonl.py`'s `JsonLinesLog`; their public APIs
   (`.path`, `.append`, `.read_all`) are unchanged.
6. **Minor**: unused exception imports in `tests/test_benchmark_harness.py`
   removed as part of the corpus expansion.

All 168 tests pass after remediation (up from 166).

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
