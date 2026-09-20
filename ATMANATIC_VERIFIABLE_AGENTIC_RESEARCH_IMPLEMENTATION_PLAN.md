# Atmanatic Verifiable Agentic Research Implementation Plan

**Status:** Proposed implementation plan  
**Effective:** 2026-09-17  
**Owner:** Atmanatic Research Institution  
**Primary consumers:** independent research consumers  
**Baseline package:** `atmanatic-research` 0.1.3
**Immediate milestone:** [Atmanatic Protocol 0.1](ATMANATIC_PROTOCOL_0.1_DRAFT.md)

## 1. Purpose

This plan defines how to extend Atmanatic from a standalone research-contract
library into a durable evidence-governance and verification boundary for
agentic systems.

The target architecture is a controlled loop:

```text
untrusted inputs and sources
        |
        v
agent proposal or research output
        |
        v
structured evidence and claim contracts
        |
        v
adversarial challenge and independent review
        |
        v
deterministic validation and domain-specific verification
        |
        v
bounded artifact awaiting authorization
        |
        v
separate human or operational authority
```

The objective is not to make an AI or a research artifact universally true.
The objective is to make consequential outputs:

- explicit about scope and assumptions;
- linked to evidence and provenance;
- falsifiable and challengeable;
- testable by deterministic tools;
- time-bounded and revalidatable;
- reversible when they are wrong or stale;
- unable to grant execution authority by implication.

Formal verification, including Lean, may establish that a formal proposition
follows from its formal premises. It does not establish that the premises model
external reality, that source data is honest, or that a financial strategy is
profitable. Those questions require separate evidence, simulation, policy, and
human controls.

## 2. Baseline and non-negotiable boundaries

The current package already provides:

- versioned intelligence envelopes;
- evidence-card structure validation;
- evidence admission checks;
- adversarial claim review;
- source-policy evaluation;
- deterministic text normalization and replay metadata;
- a dictionary-based validity check;
- a typed validity-packet protocol;
- one-step validity advancement;
- caller-supplied append-only JSON-lines persistence.

The baseline package is dependency-free and requires Python `>=3.11`. It must
remain installable, testable, and releasable without any external consumer.

### Ownership boundary

Atmanatic may own:

- domain-neutral schemas and contracts;
- provenance and evidence semantics;
- falsification and review rules;
- validity state transitions;
- deterministic research transformations;
- verification-result envelopes;
- package release and compatibility policy.

Atmanatic must not own or require:

- wallets, treasury, capital, or trading;
- live execution or transaction signing;
- external-consumer filesystem paths, databases, or runtime processes;
- LLM provider credentials or deployment secrets;
- autonomous promotion authority.

An external consumer may own:

- source acquisition and operational registries;
- retrieval, orchestration, and agent runtime;
- domain-specific simulators and risk policy;
- execution systems and operational circuit breakers;
- human approval workflows;
- production state and action logs.

The integration boundary remains versioned JSON-compatible artifacts. Every
artifact that can influence a downstream decision must make its producer,
schema version, creation time, content hash, expiry or revalidation rules, and
execution authority explicit.

## 3. Design principles

### 3.1 Separate proposing from judging

An agent may propose a claim, configuration, proof obligation, or code change.
It must not be the sole judge of its own proposal. Review and verification
components must be independently represented in the artifact history.

### 3.2 Evidence is not truth

A valid evidence card proves that the record has the required shape and
provenance fields. It does not prove that the source is correct. Admission
means that the evidence passes declared freshness and decision-use rules; it
does not mean the underlying claim is true.

### 3.3 Deterministic failures are authoritative

A failed schema check, test, invariant, or formal verification step must remain
a failure in the state machine. Natural-language explanations must not convert
failure into success.

### 3.4 Narrow invariants are better than grand claims

Formal tools should verify narrow properties such as bounds, permissions,
state transitions, conservation rules, or serialization invariants. Broader
claims about the external world require empirical evidence and declared
limitations.

### 3.5 No authority by implication

A research artifact must not authorize signing, submission, deployment, trading,
or other irreversible action. Promotion must be an explicit external decision.

### 3.6 Reproducibility before optimization

Performance or reliability claims require fixed fixtures, reproducible
configuration, recorded versions, and comparison with a baseline. A faster
implementation that silently weakens validation is a regression.

### 3.7 Grounded execution stack and operational boundaries

The implementation should be interpreted as a grounded execution stack with four
separate responsibilities. The optimization layer improves ordering, batching,
and locality without altering the truth of the underlying claims. The memory
layer preserves state continuity and replayable context. The verification layer
validates structure, evidence, provenance, review state, and formal invariants.
The authority layer remains separate from the research artifact itself and owns
any decision to promote, consume, or execute an artifact.

These responsibilities are distinct and intentionally separated. No lower layer
may infer execution authority, validity, or truth by implication. Optimization,
memory continuity, and retrieval analysis may improve context and throughput, but
they do not validate truth, substitute for evidence admission, or grant
execution authority.

The project maintains a grounded architecture appendix documenting this layered
model, file-by-file invariants, rejection conditions, and hardening standards.
The appendix should be read as a complement to the protocol and contract rules,
not as a replacement for them. See [docs/architecture/README.md](docs/architecture/README.md),
[docs/architecture/layered_stack.md](docs/architecture/layered_stack.md),
[docs/architecture/implementation_checklist.md](docs/architecture/implementation_checklist.md),
[docs/architecture/hardening_standards.md](docs/architecture/hardening_standards.md),
and [docs/architecture/test_strategy.md](docs/architecture/test_strategy.md).

## 4. Target architecture

The implementation is divided into four planes.

### Research plane

Produces source observations, evidence cards, claims, and candidate validity
packets. This plane may contain LLMs, retrieval, databases, or domain-specific
research tools, but these are external to the core Atmanatic package.

### Governance plane

Uses Atmanatic contracts to validate structure, provenance, falsifiability,
uncertainty, review state, expiry, and rollback information.

### Verification plane

Runs deterministic tests, simulators, static analyzers, theorem provers, or
other domain-specific validators. It returns signed or hash-linked result
artifacts; it does not directly authorize execution.

### Authority plane

A human or separately governed service decides whether a validated artifact
may be promoted or consumed by an operational system. This plane owns
credentials, deployment, execution, and emergency controls.

The four planes should be interpreted as a layered execution model with clear
boundaries. The optimization plane is responsible for batching, ordering, and
locality. The memory plane preserves structure and replayable context. The
verification plane enforces schema, evidence, review, and formal validation
rules. The authority plane remains external to the artifact model and decides
whether a validated artifact may be acted upon. A full implementation guide for
this grounded layer model is maintained in
[docs/architecture/layered_stack.md](docs/architecture/layered_stack.md).

## 5. Phase 0: Baseline, threat model, and contract freeze

### Objective

Define exactly what the system is allowed to claim and establish a stable
baseline before adding orchestration or formal tooling.

### Work

1. Freeze the public API and schema version for the 0.1.0 baseline.
2. Inventory every public import, validator, exception, dataclass, and
   serialized field.
3. Document the difference between:
   - structural validation;
   - evidence admission;
   - adversarial review;
   - deterministic testing;
   - formal verification;
   - human authorization.
4. Create a threat model covering:
   - sycophantic or leading prompts;
   - fabricated provenance;
   - stale evidence;
   - reviewer collusion;
   - replayed artifacts;
   - schema confusion;
   - malicious generated code;
   - verifier outages;
   - denial of service through expensive proofs;
   - unauthorized execution from a research artifact.
5. Define prohibited claims, including “universally true,” “guaranteed
   profitable,” and “safe because Lean compiled.”
6. Maintain a file-by-file implementation checklist covering invariants,
   validation rules, rejection conditions, and required tests for each public
   module. This checklist is maintained in
   [docs/architecture/implementation_checklist.md](docs/architecture/implementation_checklist.md).
7. Maintain a hardening standard for fail-closed validation, idempotence,
   determinism, explicit rejection reasons, no implicit authority, and
   replayable state transitions. This standard is maintained in
   [docs/architecture/hardening_standards.md](docs/architecture/hardening_standards.md).
8. Maintain a module-by-module validation strategy covering valid, invalid,
   replay, and authority-boundary conditions. This strategy is maintained in
   [docs/architecture/test_strategy.md](docs/architecture/test_strategy.md).

### Expanded considerations

The current code validates many declared fields but does not independently
check external source content, content-hash correctness, reviewer identity, or
semantic support between evidence and claim. Those limitations must be part
of the contract rather than hidden behind stronger language.

The current `PacketStore` is append-only JSON Lines, not an audit database. It
is suitable for a caller-controlled local record but does not provide locking,
concurrency control, signatures, or tamper evidence. Those functions belong in
the surrounding system unless they are deliberately added as a new package
contract.

### Deliverables

- architecture decision record;
- threat model;
- public API and schema inventory;
- terminology and claims policy;
- baseline benchmark and correctness corpus;
- contract-compatibility test suite.

### Exit gate

The baseline package installs in isolation, all existing tests pass, the wheel
contains only intended packages, and reviewers can explain what each validator
does not prove.

## 6. Phase 1: Contract hardening and artifact lineage

### Objective

Make research artifacts sufficiently explicit for multi-stage processing,
replay, audit, and independent consumption.

### Work

1. Define stable JSON schemas for:
   - evidence cards;
   - claims;
   - validity packets;
   - provenance records;
   - review outcomes;
   - falsification records;
   - benchmark results;
   - verification results;
   - human promotion records.
2. Add common lineage fields where required:
   - `schema_version`;
   - `artifact_id`;
   - `parent_artifact_ids`;
   - `producer`;
   - `created_at`;
   - `content_hash`;
   - `processor_version`;
   - `expires_at` or revalidation policy;
   - `execution_authorized: false`.
3. Define canonical serialization and timestamp rules.
4. Define compatibility rules for additive, breaking, and deprecated fields.
5. Add explicit statuses for `draft`, `challenged`, `verified`, `expired`,
   `rejected`, `quarantined`, and `awaiting_human_promotion` where appropriate.
6. Add tests for malformed, replayed, stale, and cross-version artifacts.

### Expanded considerations

A schema version alone is not enough to prevent replay or confusion. Consumers
need stable artifact identifiers, producer identity, parent references, and
content hashes. If artifact signing is introduced, signatures should bind the
canonical serialized bytes and the declared producer, not an ambiguous Python
object representation.

The design should avoid putting model chain-of-thought into the contract.
Record concise conclusions, evidence references, critiques, tool telemetry,
and decisions. Private reasoning traces are not required to establish an
external, auditable result and create unnecessary privacy and security risk.

### Deliverables

- versioned JSON Schemas or equivalent normative definitions;
- canonical serialization specification;
- lineage and hash rules;
- compatibility matrix;
- fixtures and negative fixtures;
- migration notes for current 0.1.0 consumers.

### Exit gate

Two independent implementations can validate the same artifact and produce
compatible results. A consumer can determine the artifact's producer, parent,
version, expiry, and authority boundary without repository access.

## 7. Phase 2: Evidence, source, and claim governance

### Objective

Turn the existing validators into a complete gate for agent-generated research
artifacts.

### Work

1. Require source-policy checks before source identifiers enter evidence cards.
2. Validate evidence-card structure before admission checks.
3. Check freshness, blocked statuses, recall status, and future timestamps.
4. Link claims to admitted evidence rather than merely non-empty source IDs.
5. Require falsifiers that contain measurable conditions where the domain allows
   measurement.
6. Require counterclaims and uncertainty statements.
7. Record challenge outcomes and reviewer identities as separate artifacts.
8. Add explicit duplicate, conflict, and insufficient-independence handling.
9. Define domain-specific evidence requirements outside the generic package.
10. Represent public source access requirements declaratively, including
   request identification, policy version, and rate-limit metadata.
11. Validate non-secret acquisition receipts against the source and access
   policy used for retrieval.

### Expanded considerations

`review_claim()` distinguishes qualitative falsifiers from measurable ones. A
measurable falsifier must declare a metric, comparison operator, numeric
threshold, unit, and observation window. This establishes syntactic readiness;
it does not determine whether the metric is connected to the claim or whether
the threshold is scientifically adequate. Semantic adequacy may require a
domain plugin, simulation, or human review and must not be smuggled into a
generic validator.

`admit_evidence()` remains a low-level admission check, while
`validate_and_admit_evidence()` is the fail-closed public path that validates
complete evidence-card structure before admission.

`validate_and_admit_governed_evidence()` is the source-policy integration
adapter. It requires every card source to be enabled, permitted for the card's
agent, and compliant with the requested authority tier before final structural
validation and admission. For identified public sources, it also requires
declared request metadata and a policy-matching acquisition receipt linked to
the card's content hash. The receipt remains a caller attestation rather than
independent proof of the transmitted request.

Per-agent `minimum_evidence` policy now enforces distinct source counts,
independently controlled source groups, and minimum authority tiers. Sources
declare an `independence_group`; when multiple independent sources are
required, missing group metadata fails closed. Runtime callers may strengthen
the minimum tier but cannot weaken institutional policy.

Domain-specific evidence requirements are injected as named caller-owned
validators. They receive a structurally valid card and its resolved source
definitions after generic source governance, and run before decision-grade
admission. Rejection reasons, malformed output, and validator exceptions fail
closed with the validator name preserved. Atmanatic defines this extension
contract but does not own domain logic or dependencies.

`advance_with_review()` connects the separate review-outcome artifact to the
validity ladder. Review-gated advancement requires a structurally valid,
independent, `challenged_and_resolved` artifact whose subject hash matches the
packet's declared content hash. Reviewer fields are derived from that artifact,
and failed transitions do not partially mutate the packet.

### Deliverables

- evidence-to-claim linkage rules;
- source-policy integration adapter;
- identified-public-source policy and acquisition-receipt contracts;
- qualitative and measurable falsifier contracts;
- minimum source-count and source-independence policy;
- caller-owned domain evidence validator interface;
- review and challenge artifact schema;
- hash-linked review-gated validity advancement;
- adversarial test corpus;
- rejection taxonomy;
- examples for research, software engineering, and evaluation workflows.

### Exit gate

A deliberately incomplete, stale, conflicting, untrusted, or self-reviewed
artifact is rejected with an actionable reason and cannot advance to an
independently verified state.

## 8. Phase 3: External proposer and referee orchestration

### Objective

Implement the proposer-to-referee loop without making the core library depend
on a particular LLM framework or provider.

### Work

1. Build an external orchestrator using a state machine or workflow engine.
2. Give the proposer a strictly typed output envelope.
3. Route each proposal to purpose-specific reviewers:
   - falsifier;
   - assumption auditor;
   - provenance auditor;
   - boundary and edge-case tester;
   - implementation-contract reviewer.
4. Require each reviewer to return structured findings, evidence references,
   severity, and disposition.
5. Require the proposer to address every finding explicitly.
6. Limit retries and detect repetitive non-progress loops.
7. Preserve proposal, critique, revision, and verification identifiers.
8. Allow a human escalation path when reviewers disagree or evidence is
   insufficient.

### Expanded considerations

Multi-agent agreement is not independence. Agents sharing the same model,
prompt, data, or retrieval errors may produce correlated mistakes. Independence
should therefore be established through different roles, inputs, tools, or
review criteria, not by counting identical votes.

The orchestrator must not rely on a substring such as `FALLACY_DETECTED` as a
security boundary. It should parse a versioned result schema and treat unknown,
malformed, or missing statuses as failures. Retry limits and time budgets are
necessary to prevent an agent from endlessly rewriting a claim until a reviewer
happens to accept it.

`validate_proposal_envelope()` now parses untrusted proposer output into an
immutable `ProposalEnvelope`. The contract requires versioned proposal and
parent identities, producer and timestamp, a SHA-256 content digest, unique
evidence references, non-empty tool versions and payload, and explicit
non-authority. Provider invocation and independent hash recomputation remain
outside the package.

`RefereeFinding` now requires one of the five declared review purposes plus
unique, non-empty evidence references. Malformed purposes or unsupported
findings fail closed before acceptance, and the typed finding preserves its
review role and evidentiary basis for downstream audit.

Every revision now includes an evidence-backed `FindingResponse` for each
finding in the preceding round, including findings already marked resolved.
Missing, duplicate, or unknown finding responses fail closed. Responses are
preserved in the round history, and response-only edits do not satisfy the
loop's substantive progress requirement.

`run_enveloped_referee_loop()` applies the typed proposal contract throughout
the loop. Every revision receives a unique proposal ID, identifies its immediate
parent, changes both payload and declared content hash, and retains finding IDs
and responses in round history. This establishes the proposal, critique, and
revision identity chain; verification-result identifiers remain in their
separate artifact envelopes.

Both referee loops accept a caller-owned escalation policy. Reviewer
disagreement, insufficient evidence, or other caller-defined conditions can
stop automated revision and produce a typed `EscalationRequest` preserving the
proposal, findings, reviewers, and reasons. The request is explicitly
non-authorizing; human workflow and decisions remain external.

Non-progress detection now rejects any revision that repeats a proposal state
seen earlier in the run. The strict envelope loop applies the same rule to
payloads independently of changing proposal IDs, timestamps, or declared
hashes, preventing alternating-state retry cycles.

Both loops support a monotonic total time budget checked around reviewer and
reviser callbacks. Budget exhaustion rejects the run while preserving the last
accepted proposal state. The package cannot interrupt a blocked external call;
hard callback deadlines and cancellation remain responsibilities of the
provider runtime or workflow engine.

`build_orchestration_audit_events()` deterministically projects completed run
results into ordered review, response, terminal, and escalation events. Stable
event IDs derive from a caller-owned run ID and sequence number; no random ID or
clock affects replay. Events remain non-authorizing. Durable storage,
signatures, and transport ordering are external responsibilities.

### Deliverables

- provider-neutral orchestration interface;
- typed proposer envelope and referee result schemas;
- bounded retry and escalation policy;
- audit event model;
- integration tests using deterministic fake agents;
- one real-model pilot in a non-operational environment.

### Exit gate

The orchestration layer can demonstrate that a false premise is challenged,
that unresolved findings block advancement, and that the same run can be
replayed from recorded inputs and tool versions.

## 9. Phase 4: Deterministic evaluation and benchmark system

### Objective

Measure correctness, robustness, throughput, and resource use independently
from agent rhetoric.

### Work

1. Create a benchmark repository or dedicated benchmark package.
2. Maintain fixed fixtures with content hashes.
3. Measure baseline and candidate versions under the same environment.
4. Add:
   - unit and contract tests;
   - differential tests against the baseline;
   - property-based and fuzz tests;
   - soak tests;
   - memory and latency measurements;
   - adversarial prompt suites;
   - malformed-artifact suites.
5. Represent benchmark and soak outputs using the existing contracts.
6. Track false-accept and false-reject rates separately.
7. Report calibration and correction quality where confidence is exposed.
8. Publish limitations with every result.

### Expanded considerations

A single pass rate is inadequate. A system that rejects everything may have a
low false-accept rate but no utility. A system that accepts everything may have
high throughput but unacceptable safety. The key metrics should include:

- false-accept rate;
- false-reject rate;
- unsupported-claim rate;
- premise-rejection rate;
- correction quality;
- verification pass rate;
- p50 and p95 latency;
- peak memory;
- stale-artifact detection rate;
- reproducibility across runs.

Do not use a single Sycophancy Resistance Score until its denominator,
annotation process, domain scope, and statistical uncertainty are defined. A
composite score can hide serious failures. Publish component metrics first.

### Deliverables

- reproducible benchmark harness;
- baseline reports;
- adversarial corpus;
- performance and memory reports;
- benchmark artifact fixtures;
- CI gates for regressions.

### Exit gate

A candidate change cannot be called an improvement unless it preserves the
compatibility corpus, meets the declared correctness gates, and demonstrates a
measured improvement or a separately approved capability gain.

## 10. Phase 5: Formal and domain-specific verification adapters

### Objective

Add formal verification where it meaningfully checks narrow invariants while
keeping the verifier external to the dependency-free Atmanatic core.

### Work

1. Define a provider-neutral verification-result contract:
   - verifier name and version;
   - input artifact hash;
   - specification or invariant identifiers;
   - status;
   - diagnostics;
   - resource usage;
   - created time;
   - environment identity.
2. Implement an initial adapter for one deterministic verifier.
3. Keep specifications in a reviewed, versioned repository.
4. Permit agents to instantiate bounded parameters, not rewrite foundational
   invariants.
5. Run verification in a disposable, network-isolated sandbox.
6. Apply CPU, memory, disk, and wall-clock limits.
7. Store failed telemetry as evidence of an unresolved obligation.
8. Distinguish:
   - verified from formal premises;
   - empirically tested;
   - simulated;
   - not evaluated.

### Tool selection

Lean 4 is appropriate for formal mathematical or logical propositions. Other
systems may be better for other domains:

- static analyzers for source-code properties;
- SMT or contract provers for bounded arithmetic and state invariants;
- model checkers for finite transition systems;
- domain simulators for physical or market behavior;
- property-based tests for broad input exploration.

No verifier should be presented as the universal arbiter of external truth.

### Expanded considerations

Generated Lean or other verifier input is untrusted code. A subprocess call to
`lake build` must not run with production credentials, network access, broad
filesystem access, or unbounded resources. The verifier sandbox should be
separate from the agent runtime and should return only bounded telemetry.

A successful proof can still be irrelevant if the specification is too weak,
if the wrong variables are modeled, or if external data changes after the
proof. Every verification result must therefore reference the exact
specification and input artifact it checked.

### Deliverables

- verification-result schema;
- sandbox runner;
- reviewed invariant repository;
- first verifier adapter;
- timeout and resource-limit tests;
- examples showing both successful and deliberately failed verification.

### Exit gate

A verifier result is reproducible from the recorded input and specification,
malformed or timed-out runs fail closed, and no verification result can itself
authorize an operational action.

## 11. Phase 6: Validity lifecycle, revalidation, and human promotion

### Objective

Use the validity protocol as an explicit state machine for bounded claims and
software or configuration changes.

### Work

1. Define entry criteria for each level:
   - `observed`;
   - `tested`;
   - `validated_in_scope`;
   - `independently_verified`;
   - `awaiting_human_promotion`.
2. Add evidence requirements appropriate to each level.
3. Record reviewer challenge outcomes as immutable lineage events.
4. Define expiry behavior for source drift, model changes, policy changes,
   environment changes, and specification changes.
5. Define downgrade and revalidation behavior explicitly.
6. Create a separate promotion record containing:
   - human approver;
   - approval time;
   - approved scope;
   - artifact hash;
   - rollback target;
   - expiry;
   - excluded uses.
7. Keep `PROMOTED` outside the automatic validator's authority.

### Expanded considerations

The current `advance()` mutates the packet after a successful check, which is
appropriate for a local state object but is not by itself an audit trail. A
production workflow should record each transition as an event with the prior
state, target state, evidence set, actor, and timestamp.

Promotion must be specific. Approval of a research claim for a bounded paper
analysis must not become approval for live execution, financial action, or a
different environment. The authority field should remain false in the
research artifact even when an external system records a separate operational
decision.

### Deliverables

- lifecycle transition table;
- revalidation and expiry policy;
- promotion-record schema;
- transition-event log;
- reviewer and approver separation rules;
- human-review interface or integration contract.

### Exit gate

Every promoted operational decision can be traced to a specific artifact,
review outcome, verification result, approver, scope, expiry, and rollback path.

## 12. Phase 7: Consumer integration and repository separation

### Objective

Make external consumers depend on released Atmanatic artifacts rather
than repository internals.

### Work

1. Install the released wheel in the consumer repository.
2. Replace source-tree imports with public package imports.
3. Convert internal records at the documented JSON boundary.
4. Keep consumer-owned databases, source registries, and operational state in
   the consumer repository.
5. Add tests that run with the Atmanatic source checkout absent.
6. Add dependency and import-boundary audits.
7. Remove or isolate compatibility shims only after supported consumers migrate.
8. Version the integration contract independently from implementation details.

### Expanded considerations

The integration must not rely on the current working directory, editable
installs, shared state files, or private module imports. An import test run from
a temporary directory is necessary to prove that the consumer uses the
installed package.

The package boundary should remain one-way: external consumers may consume
Atmanatic, but Atmanatic must not import consumer internals or know about
wallets, capital, or execution. Operational circuit breakers remain in the execution system and
must continue to work if the LLM, verifier, or message broker is unavailable.

### Deliverables

- consumer integration adapter;
- installed-wheel integration tests;
- separation audit;
- compatibility and deprecation policy;
- migration guide;
- release compatibility matrix.

### Exit gate

Atmanatic and each external consumer can be cloned, installed, tested, and run
with the other source tree absent. Neither imports the other's private modules
or uses the other's filesystem, database, environment variables, credentials,
or runtime processes.

## 13. Phase 8: Secure release and operational hardening

### Objective

Create a trustworthy path from reviewed source to immutable package and, where
applicable, to a controlled consumer deployment.

### Work

1. Build wheels from clean, tagged revisions.
2. Inspect wheel contents and dependency metadata.
3. Run tests against the installed artifact, not only the checkout.
4. Generate artifact hashes and provenance metadata.
5. Sign releases using an external release authority.
6. Publish release notes with changed contracts, benchmark results, known
   limitations, and rollback instructions.
7. Quarantine candidates until all gates pass.
8. Retain the prior known-good artifact.
9. Add vulnerability scanning and dependency policy checks.
10. Add operational monitoring for stale artifacts, verification failures,
    queue delays, and fallback activation.

### Expanded considerations

High availability does not require putting the LLM or formal verifier inside a
trading or execution loop. The mechanical consumer should use a bounded,
previously verified state and have an independent hardcoded emergency stop.
Kafka, Redis, Kubernetes, or similar infrastructure may be introduced by a
consumer, but they are not prerequisites for the core Atmanatic package and
must not become hidden dependencies.

A release pipeline must be able to reject an artifact. It must not repeatedly
modify production code until a benchmark happens to pass. Automated candidate
generation may be useful in a sandbox, but promotion remains governed by
review, evidence, and explicit release authority.

### Deliverables

- clean-build CI pipeline;
- artifact inspection and signing;
- installed-wheel verification;
- rollback procedure;
- security and dependency reports;
- operational runbook.

### Exit gate

A release is reproducible from a tagged revision, its artifact hash is known,
its tests and benchmark evidence are retained, and a previous version can be
restored without modifying the consumer's operational state.

## 14. Cross-phase acceptance criteria

The program is complete only when all of the following are true:

- Atmanatic remains independently installable and dependency-light.
- Public contracts are versioned and compatibility-tested.
- Evidence, claims, reviews, and verification results have traceable lineage.
- Invalid, stale, conflicting, or unresolved artifacts fail closed.
- Formal verification is scoped to declared propositions and specifications.
- Verification failures cannot be overridden by agent prose.
- No artifact grants execution authority by itself.
- Human promotion is explicit, scoped, recorded, and reversible.
- Consumer repositories operate without Atmanatic source code present.
- Operational systems retain independent circuit breakers.
- Performance claims are reproducible and do not weaken correctness gates.
- Release artifacts are inspectable, hashable, and rollback-capable.

## 15. Initial implementation sequence

The first delivery slice is the vendor-neutral Protocol 0.1 milestone:

1. Review the working draft against every public validator and test.
2. Resolve the typed validity packet's common-envelope migration.
3. Publish normative JSON Schemas and positive, negative, boundary, and
   adversarial fixtures.
4. Select a canonical JSON representation and define content-hash projection.
5. Add stable machine-readable error codes and conformance-result artifacts.
6. Add immutable transition, expiry, revalidation, and revocation events.
7. Build a second implementation in an independent codebase and preferably a
   different programming language.
8. Run bidirectional interoperability tests and publish their complete results.
9. Establish open contribution, intellectual-property, security disclosure,
   registry, and succession policies.
10. Seek multi-party deployment evidence and early standards-body review.

The deterministic proposer/referee harness, verifier adapters, benchmarks,
consumer integration, and signed package releases continue as reference
implementation work. They support protocol evidence but do not define the
protocol or make it an official standard by themselves.

## 16. Explicit non-goals

This plan does not propose that Atmanatic:

- prove universal truth;
- eliminate sycophancy mathematically;
- inspect or rewrite its own production source autonomously;
- execute trades or deploy contracts;
- manage wallets, capital, or credentials;
- replace domain experts or human authorization;
- treat model consensus as independent evidence;
- treat successful compilation as proof that a real-world strategy is safe or
  profitable.
