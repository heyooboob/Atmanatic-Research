# Implementation Checklist by File

This checklist is the implementation baseline for the repository. Each module
should satisfy the listed invariants, validation rules, and rejection
conditions before it is considered hardened.

## Sequencing note

Sections are ordered by dependency, not alphabetically or by creation date:
foundational primitives first, then the contracts built on them, then
governance, then the validity-protocol package, then lifecycle/promotion,
then orchestration, then the non-authoritative optimization/memory layer,
then verification, then cross-cutting quality assurance. This mirrors the
build order that actually gets the repository to its stated objective in
[ATMANATIC_MASTER_IMPLEMENTATION_ROADMAP.md](../../ATMANATIC_MASTER_IMPLEMENTATION_ROADMAP.md)
section 1 — a vendor-neutral protocol with at least one independent,
interoperating implementation — because every later tier depends on the
tiers before it, and nothing here is ordered by convenience.

1. **Foundational primitives** (§1–3): shared by every other module; changing
   these changes everything downstream.
2. **Core artifact contracts** (§4–7): the wire-level artifact shapes the
   protocol actually exchanges.
3. **Governance and admission** (§8–11): policy that decides what evidence and
   claims may be used, independent of whether they are structurally valid.
4. **Validity protocol package** (§12–16): the standalone, dependency-free
   validity ladder and its persistence.
5. **Lifecycle, promotion, and audit ties** (§17–18): binds validity
   transitions to an immutable event history and an explicit human-promotion
   boundary.
6. **Orchestration** (§19–20): the proposer/referee loop and its audit
   projection; the only place model-facing loops live.
7. **Optimization / memory (non-authoritative)** (§21–22): may never influence
   governance outcomes; exists purely for throughput and context.
8. **Verification** (§23): narrow, formal/deterministic checks external to the
   contract layer.
9. **Cross-cutting quality assurance** (§24): regression protection over
   everything above; deliberately last because it has nothing to test until
   the rest exists.

---

## 1. atmanatic_research/error_codes.py

### Exact invariants to enforce
- `ERROR_CODES` is the single frozen registry referenced by every validator
- `ContractError` cannot be constructed with a code outside the registry
- codes are protocol API: additive changes only, no repurposing an existing code

### Exact validation rules
- validate the supplied code against `ERROR_CODES` at construction time
- reject unknown codes before the exception is raised

### Exact rejection conditions
- unknown or misspelled error code
- missing code on a `ContractError` subclass raise

### Recommended tests
- constructing with a known code succeeds
- constructing with an unknown code raises `ValueError`
- every module-specific error subclass exposes `.code`

---

## 2. atmanatic_research/timestamps.py

### Exact invariants to enforce
- every accepted timestamp includes an explicit UTC offset
- `Z` is accepted as shorthand for `+00:00`
- naive timestamps fail closed, never silently assumed UTC

### Exact validation rules
- reject non-string, empty, or malformed timestamp values
- reject timestamps missing `tzinfo` after parsing

### Exact rejection conditions
- naive timestamp
- non-string input
- malformed ISO/RFC 3339 text

### Recommended tests
- `Z`-suffixed timestamp accepted
- explicit-offset timestamp accepted
- naive timestamp rejected
- malformed and non-string input rejected

---

## 3. atmanatic_research/canonical.py

### Exact invariants to enforce
- canonical JSON uses sorted keys and compact separators
- `content_hash` and `signature` are excluded from the hashed projection
- non-finite floats (`NaN`, `Infinity`) are rejected, never silently serialized

### Exact validation rules
- reject non-object input to `project_for_hash`
- recompute and compare hashes byte-for-byte in `verify_content_hash`

### Exact rejection conditions
- non-finite float anywhere in the value, including nested
- non-object passed to `project_for_hash`

### Recommended tests
- key order does not affect canonical bytes or hash
- `NaN`/`Infinity` rejected, including nested
- tampering with a hashed field is detected by `verify_content_hash`
- cross-language parity: `interop/reference-ts` reproduces the same SHA-256
  for the same record (see `interop/fixtures/canonical_hash_parity.json`)

---

## 4. atmanatic_research/artifact_contracts.py

### Exact invariants to enforce
- artifact record is a dictionary
- required metadata fields are present
- producer is explicit
- timestamp is explicit and valid
- content hash is explicit
- lifecycle state is explicit
- execution_authorized is False
- promotion or approval is explicit and separated from creation
- unsupported critical extensions fail closed; unknown non-critical extensions
  are preserved without effect

### Exact validation rules
- validate metadata required for artifact identity and lineage
- reject hidden authority implied by artifact state
- validate lifecycle transitions only through declared rules
- reject artifacts with operational authority embedded in research metadata
- validate `extensions`/`critical_extensions` against caller-supplied
  `supported_extensions`

### Exact rejection conditions
- missing required metadata
- invalid timestamp
- invalid hash
- execution_authorized not False
- lifecycle contradiction
- implicit operational authorization
- promotion record created without explicit approval semantics
- critical extension not declared in `extensions`, or declared but unsupported

### Recommended tests
- valid artifact passes
- invalid timestamp fails
- invalid hash fails
- execution_authorized=True fails
- lifecycle mismatch fails
- implicit authority promotion rejected
- replay of same artifact unchanged remains stable
- unsupported critical extension rejected; unknown non-critical extension preserved

---

## 5. atmanatic_research/evidence_contracts.py

### Exact invariants to enforce
- evidence card is a dict
- required fields exist
- evidence_id non-empty string
- claim non-empty string
- source_ids non-empty list of strings
- agent non-empty string
- observed_at valid ISO timestamp with an explicit UTC offset
- confidence numeric in [0,1]
- content_hash non-empty string
- status non-empty string
- details is dict

### Exact validation rules
- reject empty object or malformed structure
- reject empty field values
- validate timestamp parseability via the shared `timestamps.parse_rfc3339`
- validate confidence range
- ensure details is a dict

### Exact rejection conditions
- non-dict card
- missing field
- empty evidence_id or claim
- empty source_ids
- invalid or naive observed_at
- confidence outside [0,1]
- details not dict
- status empty

### Recommended tests
- valid evidence card passes
- invalid timestamp fails
- confidence out of range fails
- empty source_ids fails
- missing claim fails
- non-dict details fails
- repeated validation stable

---

## 6. atmanatic_research/proposal_contracts.py

### Exact invariants to enforce
- proposal must be a dictionary
- schema_version must equal 1
- proposal_id must be a non-empty string
- parent_proposal_id, if present, must differ from proposal_id
- producer must be non-empty
- created_at must be a valid RFC 3339 timestamp with an explicit UTC offset
- content_hash must be a valid SHA-256 hex digest
- evidence_refs must be a non-empty list of unique non-empty strings
- tool_versions must be a non-empty mapping of names to versions
- payload must be a non-empty object
- execution_authorized must be False

### Exact validation rules
- reject non-dict input
- reject empty or whitespace fields
- reject timezone-less timestamps
- reject invalid hash format
- reject duplicates in evidence_refs
- normalize content_hash to lower-case when storing
- enforce mapping semantics on tool_versions

### Exact rejection conditions
- invalid schema_version
- missing proposal_id
- parent_proposal_id equal to proposal_id
- invalid created_at or timezone missing
- invalid content_hash
- empty evidence_refs
- duplicate evidence_refs
- empty payload
- execution_authorized is not False

### Recommended tests
- valid envelope passes
- invalid schema_version fails
- missing proposal_id fails
- invalid content_hash fails
- duplicate evidence_refs fails
- empty payload fails
- execution_authorized=True fails
- timezone-less created_at fails
- valid parent_proposal_id passes
- cross-language parity: `interop/reference-ts` accepts/rejects the same
  fixtures with the same error codes

---

## 7. atmanatic_research/intelligence_contracts.py

### Exact invariants to enforce
- `schema_version` fixed at `CURRENT_SCHEMA_VERSION` (benchmark/soak/collection)
  or `API_V2_SCHEMA_VERSION` (paginated API responses)
- `execution_authorized` is always False where present
- benchmark and export records declare an explicit, non-authorizing
  `trust_boundary`
- `fixture_hash` and `source_hashes` are SHA-256 hex digests
- soak `passed` must equal the conjunction of all individual `checks[].passed`
- pagination fields (`page`, `page_size`, `total`) are integers within bounds

### Exact validation rules
- validate object shape before any field-specific check
- validate trust-boundary flags before benchmark/export field checks
- recompute soak's aggregate `passed` rather than trusting the declared value

### Exact rejection conditions
- wrong schema_version
- invalid or missing trust boundary flags
- missing benchmark identifier or malformed fixture_hash
- malformed source_hashes
- declared soak `passed` inconsistent with its checks
- non-integer or out-of-range pagination fields

### Recommended tests
- valid benchmark/export/soak/collection/API-page records pass
- each invalid variant above is rejected with its specific error code
- soak `passed=True` with a failing check is rejected
  (`invalid_state_transition`)

---

## 8. atmanatic_research/source_policy.py

### Exact invariants to enforce
- source identity explicit
- source enabled in registry
- source permitted for specific agent
- source meets minimum authority tier
- public source has valid request context and acquisition receipt
- receipt source and response hash match actual evidence

### Exact validation rules
- source registry must be structured and keyed by source id
- validate agent-specific policy
- match receipt hashes to response content
- reject disabled or unknown sources

### Exact rejection conditions
- source missing
- source disabled
- source not permitted for this agent
- source below minimum tier
- request_context missing for public source
- receipt missing or mismatch

### Recommended tests
- enabled source passes
- disabled source fails
- wrong agent fails
- minimum tier not met fails
- public source without request_context fails
- receipt mismatch fails
- valid public source with receipt passes

---

## 9. atmanatic_research/evidence_admission.py

### Exact invariants to enforce
- evidence must satisfy contract validation
- evidence must be fresh for decision-grade use
- provenance must be present and valid
- claim references must exist in admitted set
- duplicate or conflicting evidence identifiers are rejected
- source-governed admission fails closed on unresolved policy configuration

### Exact validation rules
- validate all cards before admission
- reject stale evidence by time gate
- reject unsupported provenance
- reject duplicate evidence IDs
- reject claim references missing from admitted set
- `EvidenceAdmissionError` carries `evidence_conflict` for duplicate/conflicting/
  blocked-status/independence failures and `missing_or_invalid_field` for
  structural gaps

### Exact rejection conditions
- empty evidence list
- invalid evidence card
- stale evidence
- missing provenance
- duplicate evidence_id
- conflicting evidence records
- claim references absent from admitted set
- insufficient distinct or independent sources for the agent's policy

### Recommended tests
- valid evidence admitted
- stale evidence rejected
- invalid evidence card rejected
- duplicate evidence_id rejected
- conflicting evidence rejected
- claim reference absent from admitted set rejected
- repeated admission stable
- each raised error carries the expected `.code`

---

## 10. atmanatic_research/truth_review.py

### Exact invariants to enforce
- review outcome tied to subject artifact
- subject artifact hash explicit
- reviewer identity explicit
- challenge findings explicit
- resolution explicit
- review outcome does not grant execution authority

### Exact validation rules
- validate hash match between subject artifact and review record
- reject self-authored review
- validate challenge findings are present
- require resolution to be substantive and explicit
- `TruthReviewError` always raises with `self_review_or_unresolved`, since the
  whole module is that gate

### Exact rejection conditions
- subject hash mismatch
- reviewer equals artifact producer
- missing resolution
- empty findings
- execution_authorized not False
- invalid disposition

### Recommended tests
- valid review passes
- self-authored review fails
- hash mismatch fails
- missing reviewer fails
- empty resolution fails
- execution_authorized=True fails

---

## 11. atmanatic_research/validity_standard.py

### Exact invariants to enforce
- validity levels explicit and known
- level semantics not ambiguous
- transitions follow a defined valid graph
- uncertainty represented as an explicit state
- expiry classified separately from other structural gaps

### Exact validation rules
- validate state membership
- validate transition graph
- reject undocumented levels
- ensure uncertainty and failure are distinct from success
- `ValidityStandardError` raises `expired_or_revoked` when the failing reasons
  are expiry-related, `missing_or_invalid_field` otherwise

### Exact rejection conditions
- undefined level
- invalid transition
- untracked status
- uncertainty misrepresented as success
- expired or missing revalidation policy

### Recommended tests
- valid standard states pass
- undefined state fails
- invalid transition fails
- uncertainty state remains distinct
- repeated standard check stable
- expired packet raises with `expired_or_revoked`

---

## 12. validity_protocol/levels.py

### Exact invariants to enforce
- levels finite and explicit
- semantics stable and known
- transition graph valid
- ordering explicit

### Exact validation rules
- validate enumerated values
- ensure every level has a defined semantic meaning
- ensure transition graph is defined

### Exact rejection conditions
- unknown level
- undefined transition
- invalid graph semantics

### Recommended tests
- known levels pass
- unknown level fails
- valid transitions succeed
- invalid transitions fail

---

## 13. validity_protocol/packet.py

### Exact invariants to enforce
- packet identity deterministic
- payload and metadata explicit
- validity state and evidence references unambiguous
- serialization stable

### Exact validation rules
- canonical serialization ordering
- strict field validation
- validate content hashes and references
- reject ambiguous metadata

### Exact rejection conditions
- missing packet identity
- missing evidence refs
- hash mismatch
- ambiguous or invalid validity state
- serialization mismatch

### Recommended tests
- valid packet serializes and deserializes
- round trip stable
- malformed packet rejected
- hash mismatch rejected
- ambiguous metadata rejected

---

## 14. validity_protocol/validator.py

### Exact invariants to enforce
- packet structure valid
- packet fields consistent
- packet identity unique
- validity result deterministic
- invalid packet fails closed

### Exact validation rules
- validate packet fields and types
- validate packet level membership
- validate embedded references and hashes
- reject field cross inconsistencies

### Exact rejection conditions
- malformed packet
- unknown level
- hash mismatch
- duplicate packet identity
- cross-field contradiction

### Recommended tests
- valid packet accepted
- invalid level rejected
- packet hash mismatch rejected
- duplicate packet rejected
- cross-field contradictions rejected

---

## 15. validity_protocol/jsonl.py

### Exact invariants to enforce
- append-only: `append_record` never rewrites or truncates existing lines
- parent directory is created on construction, never assumed to exist
- one JSON object per line; `read_all` returns records in file order
- shared by both `validity_protocol.store.PacketStore` and
  `atmanatic_research.lifecycle_events.LifecycleEventLog` so file I/O is
  defined exactly once

### Exact validation rules
- `append_record` accepts an optional `default` serializer (for dataclasses/
  enums) and an optional `sort_keys` flag
- `read_all` returns `[]` for a path that does not yet exist, never raises

### Exact rejection conditions
- a malformed line on read propagates `json.JSONDecodeError` rather than being
  silently skipped (known limitation: no quarantine-and-continue behavior yet)

### Recommended tests
- append then read_all round-trips exactly
- constructing over a missing parent directory creates it
- `PacketStore` and `LifecycleEventLog` both produce files readable by this
  module without either owning file-format logic independently

---

## 16. validity_protocol/store.py

### Exact invariants to enforce
- append-only storage semantics
- no silent overwrite
- deterministic record ordering
- readback exact match
- append failures explicit

### Exact validation rules
- only append new records
- store deterministic serialization
- enforce uniqueness policy for identical packets where required
- preserve ordering semantics

### Exact rejection conditions
- overwrite attempt
- duplicate store of identical packet if duplicate disallowed
- serialization mismatch
- readback corruption
- nondeterministic ordering

### Recommended tests
- append valid packet works
- readback matches original
- overwrite attempt fails
- duplicate append fails when required
- corrupted file or record rejected

---

## 17. atmanatic_research/validity_governance.py

### Exact invariants to enforce
- validity transitions explicit
- independently verified transitions require proper review
- human promotion remains separate from automatic verification
- invalid transitions fail closed
- packet hash must match subject artifact hash
- `promote_packet` requires `awaiting_human_promotion` and an `approved`
  promotion record whose `approved_artifact_hash` matches the packet

### Exact validation rules
- validate state machine transitions
- require review-backed transition when needed
- ensure human promotion remains external to artifact package
- reject advancement without review or valid packet state
- retain the promotion record on `packet.metadata` after a successful promotion

### Exact rejection conditions
- invalid transition
- review unresolved when required
- hash mismatch
- promotion without human authority
- duplicate advancement
- promotion attempted from a level other than `awaiting_human_promotion`
- promotion record status other than `approved`

### Recommended tests
- valid transition passes
- invalid jump fails
- unresolved review fails advancement
- content hash mismatch fails
- duplicate same transition rejected
- human promotion separate from auto verification
- promotion rejected from the wrong packet state or hash

---

## 18. atmanatic_research/lifecycle_events.py

### Exact invariants to enforce
- every transition attempt is recorded, whether accepted or rejected
- rejected events always carry at least one violation; accepted events carry none
- `latest_status` resolves recency by `created_at`, not append/arrival order

### Exact validation rules
- validate `prior_level`/`requested_level` against the known validity levels
- validate `created_at` as an explicit-offset timestamp
- reject accepted events with violations and rejected events without any

### Exact rejection conditions
- unknown validity level
- naive timestamp
- accepted/rejected result inconsistent with the violations list

### Recommended tests
- accepted and rejected transitions both produce a validated event
- accepted-with-violations and rejected-without-violations both rejected
- append/read round-trip is stable; latest_status ignores write order

---

## 19. atmanatic_research/orchestration.py

### Exact invariants to enforce
- at least one reviewer required
- reviser callable
- escalation_policy callable if present
- max_revisions non-negative integer
- time_budget_seconds positive if provided
- referee finding IDs unique within a round
- finding responses cover every finding exactly once
- repeated proposal states rejected
- unresolved findings block acceptance

### Exact validation rules
- validate reviewer output type and schema
- validate each finding object
- validate each response object
- validate evidence_refs arrays as non-empty, unique strings
- enforce non-progress detection across the full run
- enforce time-budget checks before and after callbacks
- escalate when policy returns non-empty reasons

### Exact rejection conditions
- no reviewers
- invalid reviewer callable
- duplicate finding IDs
- invalid severity or disposition
- empty evidence_refs
- reviser returns non-dict
- no progress revision
- repeated proposal state
- missing or extra responses
- time budget exhausted
- malformed escalation policy output

### Recommended tests
- single accepted review loop passes
- missing reviewer fails
- malformed reviewer output fails
- duplicate finding_id fails
- unresolved findings rejected
- no-progress revision rejected
- repeated state rejected
- time budget exhaustion rejected
- escalation raises EscalationRequest
- extra unknown response fails
- missing response fails

---

## 20. atmanatic_research/orchestration_audit.py

### Exact invariants to enforce
- input must be an `OrchestrationResult`; `run_id` must be a non-empty string
- event IDs are stable and derived only from `run_id` and sequence number — no
  random ID and no clock affects replay
- every event carries `execution_authorized: false`
- the terminal event reflects the run's real outcome: `orchestration_accepted`,
  `orchestration_rejected`, or `human_escalation_requested`

### Exact validation rules
- project each review round in order, then the terminal event, deterministically
- derive `event_id` as `f"{run_id}:{sequence}"`

### Exact rejection conditions
- non-`OrchestrationResult` input
- empty or non-string `run_id`

### Recommended tests
- accepted, rejected, and escalated runs each produce the correct terminal event
- replaying the same result and run_id twice produces identical event IDs
- every event's `execution_authorized` is `False`

---

## 21. atmanatic_research/text_processing.py

### Exact invariants to enforce
- text normalization deterministic
- normalization idempotent
- semantics not lost silently
- original content retained when needed

### Exact validation rules
- canonicalize whitespace and encoding consistently
- use deterministic ordering for comparison
- preserve original content alongside normalized representation if required

### Exact rejection conditions
- non-text input
- nondeterministic normalization
- silent semantic collapse during normalization
- collision without explicit declaration

### Recommended tests
- same text normalizes same way repeatedly
- whitespace normalization deterministic
- unicode normalization stable
- distinct text does not collapse accidentally
- original content retained when required

---

## 22. atmanatic_research/graph_analysis.py

### Exact invariants to enforce
- node/edge input order never affects snapshot hash or rank order
- unknown node/edge types, duplicate IDs, and unresolved references fail closed
- scores are finite and non-negative; failure to converge emits a structured
  finding, never a silent partial result
- the artifact never carries `execution_authorized: true`
- nothing in this module may influence evidence admission, truth review, or
  validity advancement — governing isolation is a design invariant, not a
  suggestion

### Exact validation rules
- validate node and edge records before snapshot construction
- reject negative or non-finite edge weights
- reject a duplicate edge_id whose content differs from the first occurrence
- require ranked_nodes ordered by descending score, then ascending node_id

### Exact rejection conditions
- unknown `node_type` or `relation_type`
- duplicate `node_id`
- edge referencing an unknown node
- empty or unknown `seed_node_ids`
- out-of-order `ranked_nodes` or missing `limitations`

### Recommended tests
- reversed input order produces an identical snapshot hash
- unknown types, duplicate IDs, and unresolved edges rejected
- convergence and forced non-convergence both produce correct, structured results
- artifact validator rejects `execution_authorized: true` and out-of-order ranks

---

## 23. atmanatic_research/verification_adapters.py

### Exact invariants to enforce
- the checked specification (the declared validity ladder) is fixed, reviewed
  code, not untrusted input
- `input_artifact_hash` is derived from the specification itself, so a result
  is reproducible from recorded input alone
- two runs never share an `artifact_id` unless the caller explicitly supplies one
- a broken transition rule is flagged, never silently treated as passing

### Exact validation rules
- `check_validity_transition_table` accepts injectable `levels`/`can_advance_fn`
  for testing against a deliberately broken specification
- the returned record must satisfy `validate_verification_result`

### Exact rejection conditions
- unreachable validity level
- non-monotonic (backward) transition
- malformed verification-result envelope

### Recommended tests
- the real ladder verifies clean
- injected broken reachability and monotonicity are both flagged
- default artifact_id is unique per run; caller-supplied artifact_id is honored

### Known limitation
This adapter has no untrusted input and needs no sandbox. An adapter that
accepts caller-supplied specifications or generated code (for example, Lean)
still needs the sandboxed-subprocess work described in the implementation
plan's Phase 5 before it can be trusted; that sandbox does not exist yet.

---

## 24. atmanatic_research/benchmark_harness.py

### Exact invariants to enforce
- identical case corpora run against the same validators twice must agree exactly
- false-accept rate, false-reject rate, and reproducibility are reported
  separately; no composite score
- unknown validator references fail closed rather than being skipped

### Exact validation rules
- require a non-empty case sequence
- raise if the two-pass run disagrees (non-reproducible)

### Exact rejection conditions
- empty case list
- case referencing an unregistered validator
- non-reproducible run

### Recommended tests
- conformant record passes `validate_benchmark`
- a deliberately broken validator produces a failing case, not a silent pass
- fixture hash is stable across repeated runs with identical cases

### Known limitation
The committed corpus in `tests/test_benchmark_harness.py` currently covers 6 of
the 24 modules in this checklist with paired accept/reject cases. Expanding
coverage to the remaining modules is tracked in the master roadmap, not
required for the harness mechanism itself to be considered hardened.

---

## Cross-cutting acceptance standard

Before a module is considered hardened, it must satisfy all of the following:

- deterministic behavior under identical inputs
- fail-closed behavior under invalid input
- idempotent behavior under repeated valid input
- explicit rejection reasons for every invalid path
- no hidden authority or implicit execution permission
- structured and replayable logs for state transitions
- test coverage for happy path, invalid path, and repeated path

This is the implementation baseline for making the repository genuinely
robust and trustworthy. As of 2026-09-18 all 24 modules listed above exist and
are covered by passing tests (171 Python tests, 26 TypeScript tests);
"hardened" here refers to depth of coverage per the standard above, not
existence.
