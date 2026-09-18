# Atmanatic Protocol 0.1

**Status:** Working Draft 0.1  
**Date:** 2026-09-17  
**Category:** Standards Track  
**Intended audience:** implementers, reviewers, standards bodies, and operators  
**Canonical repository:** to be assigned before public review

## Abstract

The Atmanatic Protocol defines a vendor-neutral method for exchanging bounded,
verifiable claims, evidence, and review outcomes between humans, AI agents, and
software systems.

The protocol standardizes artifact meaning, lineage, validation, review, and
validity transitions. It does not standardize model reasoning, require a model
provider, determine universal truth, or authorize an operational action. A
conforming implementation can produce, inspect, validate, challenge, and relay
protocol artifacts without sharing an application, programming language,
database, or orchestration framework.

This document derives the 0.1 core from the current Atmanatic implementation.
Sections explicitly marked **Proposed** are requirements for interoperability
and external standardization that are not yet implemented by the reference
library.

## 1. Status of this document

This document is a working draft, not an official national or international
standard. Publication by Atmanatic alone cannot make it one. Advancement
requires public review, multiple independent implementations, interoperable
test results, stable governance, intellectual-property commitments, and
adoption through an appropriate standards development organization.

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**,
**SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and
**OPTIONAL** in this document are to be interpreted as described by BCP 14 when,
and only when, they appear in capitals.

## 2. Design goals

The protocol is designed to provide:

1. portable evidence and claim artifacts;
2. explicit provenance and artifact lineage;
3. falsifiable claims with uncertainty and limitations;
4. independent, hash-linked review outcomes;
5. deterministic and formal verification result envelopes;
6. monotonic, bounded validity advancement;
7. expiry, revalidation, rejection, and revocation semantics;
8. an explicit boundary between validation and operational authority;
9. fail-closed processing of malformed or unknown critical data;
10. implementation independence across humans, agents, and software.

The protocol does not attempt to:

- prove that an external-world claim is universally true;
- expose or exchange private chain-of-thought;
- define an AI model, prompt format, agent framework, or transport protocol;
- rank every source or domain using one universal policy;
- replace scientific, legal, safety, or domain-specific review;
- grant signing, deployment, transaction, or execution authority.

## 3. Architectural boundary

The protocol core consists only of data contracts and deterministic processing
rules:

```text
producer                 protocol core                   consumer
--------                 -------------                   --------
human     ->         versioned artifacts          ->     human
AI agent  ->   lineage, validation, review, state ->     AI agent
software  ->       conformance and receipts       ->     software
                              |
                              v
                   no execution authority
```

HTTP, message queues, files, APIs, and content-addressed stores MAY carry
protocol artifacts. Transport authentication, storage, retrieval, model calls,
workflow orchestration, credentials, and operational execution are outside the
core. Profiles MAY standardize those bindings separately.

The protocol is intentionally layered: the optimization layer may improve
ordering, batching, and retrieval efficiency; the memory layer preserves
continuity and replayable state; the verification layer checks structure,
provenance, review state, and formal invariants; and the authority layer remains
separate and governs any decision to promote, consume, or execute an artifact.
These components may support one another, but no lower layer may infer
execution authority, validity, or truth by implication. Optimization,
memory continuity, and retrieval analysis do not validate claims, admit
evidence, or grant operational authority.

Product-specific names, services, paths, credentials, and policies MUST NOT be
required to parse or validate a core artifact.

## 4. Terminology

**Artifact**
: A versioned JSON-compatible record exchanged under this protocol.

**Claim**
: A bounded assertion with declared scope, evidence references, falsifier,
counterclaim, uncertainty, and limitations.

**Evidence card**
: A record describing an observation or source-derived item. Structural
validity does not establish factual correctness.

**Producer**
: The human, agent, organization, or software identity asserting an artifact.

**Reviewer**
: An identity that challenges an artifact and emits a review outcome. Protocol
independence means more than a different display name; stronger profiles SHOULD
define organizational, model, data, or tool independence.

**Verifier**
: A deterministic, empirical, simulated, or formal mechanism that evaluates a
declared specification against an identified input.

**Validity**
: Bounded readiness under declared conditions, not universal truth.

**Promotion**
: A separately governed acceptance decision for a declared scope. Promotion is
not execution authorization.

**Critical extension**
: An extension whose meaning a recipient must understand to process an
artifact safely.

## 5. Common artifact envelope

All 0.1 core artifacts other than the legacy typed validity packet MUST contain
the following fields:

| Field | Type | Requirement |
| --- | --- | --- |
| `schema_version` | integer | MUST equal `1` in the 0.1 core |
| `artifact_id` | non-empty string | Stable identifier within the producer namespace |
| `parent_artifact_ids` | array of strings | MAY be empty; each item identifies direct lineage |
| `producer` | non-empty string | Identity responsible for producing the artifact |
| `created_at` | timestamp string | Time the artifact was created |
| `content_hash` | string | SHA-256 digest encoded as 64 hexadecimal characters |
| `execution_authorized` | boolean | MUST be `false` |

The envelope MAY contain `processor_version`, `expires_at`, and
`revalidation_policy`. If present, each MUST satisfy its declared type and
`expires_at` MUST be a timestamp.

Artifact identifiers identify records; hashes identify content. Implementers
MUST NOT treat an identifier as proof that two records have identical content.
An artifact with an expired `expires_at` MUST NOT be used for a new
decision-grade determination until its declared revalidation process succeeds.

### 5.1 Timestamp profile

Interoperable 0.1 wire artifacts MUST encode timestamps using RFC 3339 with an
explicit UTC offset. Producers SHOULD emit UTC using `Z`. Naive timestamps
MUST be rejected. Leap-second handling MUST be documented by an implementation
profile.

The reference validators now share one `parse_rfc3339` implementation
(`atmanatic_research/timestamps.py`) used by artifact lineage, evidence cards,
proposal envelopes, and acquisition receipts. A timestamp without an explicit
offset fails closed with `TimestampError` in every one of those validators.

### 5.2 Canonical representation and content hashes

A conforming wire implementation MUST use a single published JSON
canonicalization scheme. The `content_hash` MUST be computed over canonical
artifact bytes with `content_hash` and `signature` omitted according to a
published projection algorithm.

The reference implementation freezes this scheme in
`atmanatic_research/canonical.py`: object keys are sorted, separators are
compact (`,`/`:`), encoding is UTF-8, and non-finite numbers (`NaN`,
`Infinity`) are rejected rather than silently serialized. `project_for_hash()`
removes `content_hash` and `signature` before hashing; `compute_content_hash()`
returns the SHA-256 hex digest of the resulting canonical bytes; and
`verify_content_hash()` recomputes and compares against a record's declared
hash. Media-type registration remains open work for Draft 0.2.

The current `PacketStore` writes ordinary JSON Lines and does not provide
canonical bytes, hash verification, locking, signatures, or tamper evidence.
Its output is a local persistence format, not the normative wire format.

### 5.3 Extensions

Artifacts MAY contain an `extensions` object. Each extension key MUST be a
collision-resistant URI or a name from the protocol registry. Critical
extensions MUST also be listed in `critical_extensions`. A recipient MUST
reject an artifact containing an unsupported critical extension. Unknown
non-critical extensions MUST be preserved when relaying an artifact and MUST
NOT alter core validation results.

`validate_artifact_lineage()` and the artifact validators built on it accept an
optional `supported_extensions` collection naming the critical extension
identifiers the caller understands. Any `critical_extensions` entry outside
that set, or missing from the accompanying `extensions` object, fails closed
with `UNSUPPORTED_CRITICAL_EXTENSION` or `MISSING_OR_INVALID_FIELD`. Unknown
non-critical extensions are preserved on the validated record without effect on
the result. A protocol-wide extension registry remains open work for Draft 0.2.

## 6. Core artifact types

### 6.1 Evidence card

An evidence card MUST contain:

- `evidence_id`: non-empty string;
- `claim`: non-empty description of what the evidence bears on;
- `source_ids`: non-empty array of source identifiers;
- `agent`: non-empty producer or collector identity;
- `observed_at`: timestamp string;
- `confidence`: number from 0 through 1 inclusive;
- `content_hash`: non-empty string;
- `status`: non-empty string;
- `details`: object.

Decision-grade admission MUST reject:

- an empty evidence set;
- duplicate evidence identifiers;
- one evidence identifier associated with conflicting hashes;
- missing source identifiers, hashes, or observation times;
- observations dated in the future;
- statuses `stale_source`, `conflict`, or
  `insufficient_independent_sources`;
- recall statuses `untrusted`, `reference`, or `discovery_only`.

Confidence is a producer assertion. Recipients MUST NOT interpret structural
validation or confidence as proof that a source is correct.

### 6.2 Claim artifact

A claim intended for adversarial review MUST contain:

- `claim`;
- non-empty `source_ids` linked to admitted evidence;
- `falsifier`;
- `counterclaim`;
- `uncertainty`;
- `author`.

The current Python compatibility profile also embeds `independent_reviewer`
and `review_outcome` in a claim. In that profile, the author MUST NOT be the
independent reviewer and the embedded outcome must be
`challenged_and_resolved`. A strict wire implementation MUST instead represent
review as the separate, hash-linked artifact defined in Section 6.3. Embedded
review fields are denormalized summaries and MUST NOT independently establish
review completion.

A claim MAY declare `falsifier_kind` as `qualitative` or `measurable`. A
measurable falsifier MUST include:

- `metric`;
- `operator`, one of `<`, `<=`, `==`, `!=`, `>=`, or `>`;
- numeric `threshold`;
- `unit`;
- `observation_window`.

These fields establish a testable shape. A domain profile or reviewer MUST
determine whether the metric, threshold, and observation window adequately test
the claim.

### 6.3 Review outcome

A review outcome uses the common envelope and MUST contain:

- `reviewer` distinct from `producer`;
- `subject_artifact_hash`, a SHA-256 digest of the reviewed artifact;
- non-empty `challenge_findings`;
- `outcome`, one of `challenged_and_resolved`, `rejected`, or
  `insufficient_evidence`;
- `resolution` when the outcome is `challenged_and_resolved`.

A recipient MUST validate the subject hash before associating a review with an
artifact. A review of one artifact version MUST NOT be transferred to another
version merely because their identifiers or claims are similar.

### 6.4 Verification result

A verification result uses the common envelope and MUST contain:

- `verifier_name` and `verifier_version`;
- `input_artifact_hash`;
- non-empty `specification_ids`;
- `status`, one of `verified`, `failed`, `timed_out`, or `not_evaluated`;
- `diagnostics`, an array of strings;
- `resource_usage`, an object;
- `environment_id`.

Only `verified` records a successful check against the named specifications.
It does not prove that the specifications are complete, that premises describe
external reality, or that operational use is safe. Unknown and malformed
statuses MUST fail closed.

### 6.5 Promotion record

A promotion record uses the common envelope and MUST contain:

- `approver`;
- `approved_artifact_hash`;
- `approved_scope`;
- `approved_at`;
- `rollback_target`;
- `status`, one of `approved`, `rejected`, `expired`, or `revoked`.

Promotion records MUST retain `execution_authorized: false`. Operational
authorization, where needed, belongs to a separate authority system with its
own policy and audit trail.

### 6.6 Validity packet

The 0.1 typed validity packet contains:

- `claim`, `scope`, and `author`;
- one or more observations, each with `description` and `observed_at`;
- one or more `evidence_refs`;
- `falsifier`, `counterclaim`, `uncertainty`, and `limitations`;
- `rollback_path`;
- `expiry` and `revalidation_policy`;
- `level`;
- optional `reviewer`, `challenge_outcome`, and `metadata`.

The current typed packet predates the common envelope. A 0.1 compatibility
implementation MAY exchange it as implemented. A strict wire implementation
MUST wrap or migrate it into a common artifact envelope once the canonical
schema and hashing rules are published.

## 7. Validity state machine

The validity ladder is ordered as follows:

1. `observed`;
2. `tested`;
3. `validated_in_scope`;
4. `independently_verified`;
5. `awaiting_human_promotion`;
6. `promoted`.

Automated advancement MUST move at most one level at a time. Validation failure
MUST leave the packet and its review fields unchanged. Reset to `observed` MAY
occur when expiry or revalidation requires it.

Advancement to `independently_verified` or `awaiting_human_promotion` MUST use a
valid, independent, `challenged_and_resolved` review whose
`subject_artifact_hash` matches the packet content hash.

The core validator MUST NOT perform the transition to `promoted`. An external
authority MAY record promotion only through a distinct promotion record that
identifies the exact artifact, approver, scope, time, rollback target, expiry,
and exclusions.

### 7.1 Transition events

**Proposed.** A production profile MUST represent every attempted transition as
an immutable event containing the prior level, requested level, actor, time,
input artifact hash, supporting artifact hashes, result, and violations. This
replaces mutable in-memory state as the authoritative audit history.

### 7.2 Revalidation and revocation

**Proposed.** Profiles MUST define events that invalidate prior readiness,
including evidence expiry, source withdrawal, policy change, model change,
environment drift, specification change, and discovered misconduct. Revocation
MUST preserve history and MUST NOT delete the superseded artifact. Consumers
MUST be able to determine the latest applicable status without trusting event
arrival order alone.

## 8. Processing requirements

A protocol processor MUST:

1. parse the artifact without executing embedded content;
2. identify the schema version and artifact type;
3. reject unsupported versions or critical extensions;
4. validate the common envelope where applicable;
5. verify canonical hashes and signatures when required by its profile;
6. validate type-specific structure and enumerations;
7. evaluate expiry and applicable source policy;
8. resolve referenced artifacts by both identifier and hash;
9. apply domain policy without weakening core requirements;
10. emit a deterministic result with machine-readable violations;
11. avoid changing input artifacts after validation;
12. keep operational authorization outside the protocol result.

Natural-language explanation MUST NOT convert a deterministic failure into a
pass. Missing, malformed, stale, conflicting, unresolved, or unverifiable
critical input MUST fail closed.

## 9. Source and acquisition policy

Source policy is a governance profile, not a universal ranking of truth.
Implementations MAY declare authority tiers `A`, `B`, `C`, and `D`, ordered
from strongest to weakest within that policy. Policies MAY require minimum
source counts, minimum independently controlled source groups, and a minimum
tier. A runtime caller MAY strengthen but MUST NOT weaken institutional policy.

Supported 0.1 access modes are `public_anonymous`, `public_identified`,
`api_key`, `oauth`, and `custom`. The protocol records non-secret policy
metadata; it MUST NOT carry credentials.

An identified-public-source acquisition receipt records:

- receipt and source identifiers;
- retrieval time;
- request policy version;
- response content hash;
- satisfaction of identity requirements;
- the applicable identity profile identifier.

A receipt is an attestation, not cryptographic proof that a request was sent as
declared. Stronger acquisition profiles MAY use signed HTTP exchanges,
transparency logs, trusted execution evidence, or independent archiving.

## 10. Conformance

Conformance is claimed by capability, not by a single all-or-nothing badge.

### 10.1 Core Artifact Producer (CAP)

A CAP MUST emit one or more artifact types that satisfy the common envelope and
type-specific schema. It MUST publish its supported versions, artifact types,
hash profile, and extension behavior.

### 10.2 Core Artifact Validator (CAV)

A CAV MUST validate the common envelope, all claimed artifact types, expiry,
hashes, critical extensions, and type-specific rules. It MUST publish
deterministic conformance results for the official positive and negative test
vectors.

### 10.3 Evidence Governance Processor (EGP)

An EGP MUST implement evidence-card validation, admission, source-policy
evaluation, duplicate and conflict handling, and claim-to-evidence linkage.

### 10.4 Review and Validity Processor (RVP)

An RVP MUST implement independent hash-linked review, the ordered validity
state machine, non-mutating failure, expiry handling, and the external promotion
boundary.

### 10.5 Full 0.1 implementation

A full implementation MUST conform as CAP, CAV, EGP, and RVP. It MUST pass the
published interoperability suite using canonical artifacts generated by an
independent implementation.

Self-attestation MAY be used during draft development. A public conformance
claim for a stable release SHOULD include test-suite version, implementation
version, platform, results, and artifact hashes. Certification and trademarks
require a separate governance policy.

## 11. Error model

Validators MUST return stable machine-readable error codes in addition to
human-readable messages. Codes MUST identify at least:

- malformed syntax;
- unsupported version;
- unsupported critical extension;
- missing or invalid field;
- hash or signature mismatch;
- expired or revoked artifact;
- unresolved reference;
- source-policy rejection;
- evidence conflict or insufficient independence;
- self-review or unresolved challenge;
- invalid state transition;
- prohibited authority claim.

Error codes are protocol API and MUST follow compatibility rules. Human-readable
messages MAY change without a protocol version change.

The reference implementation defines this registry in
`atmanatic_research/error_codes.py` as the `ERROR_CODES` frozenset, with a
shared `ContractError` base exception carrying a `.code` attribute.
`ArtifactContractError`, `ProposalContractError`, `EvidenceContractError`, and
`SourcePolicyError` all raise with an explicit code from this registry. The
validity-transition `ValidationResult` violation list does not yet carry
structured codes; that remains open work tracked in the master implementation
roadmap.

## 12. Security considerations

Protocol conformance is not equivalent to system security. Implementers MUST
consider at least:

- forged producer or reviewer identities;
- hash substitution and ambiguous serialization;
- replay, rollback, and out-of-order event delivery;
- schema confusion and unsafe polymorphism;
- malicious links, attachments, verifier inputs, and generated code;
- reviewer collusion and correlated model failures;
- stale, poisoned, selectively quoted, or withdrawn evidence;
- denial of service through oversized artifacts or expensive verification;
- credential leakage through artifacts or diagnostics;
- unauthorized interpretation of research artifacts as action approval.

**Proposed.** Signed profiles MUST bind the canonical artifact bytes, protocol
version, artifact type, producer identity, signature algorithm, and key
identifier. They MUST define key rotation, compromise, revocation, and
verification-time semantics. Algorithms MUST be registry-controlled and permit
cryptographic agility.

Parsers SHOULD impose limits on artifact size, nesting depth, collection size,
reference expansion, and verification resources. Verifiers processing
untrusted inputs SHOULD run in isolated sandboxes without production secrets or
network access.

## 13. Privacy and human-rights considerations

Artifacts SHOULD contain the minimum information required for verification.
They MUST NOT require private chain-of-thought. Producers SHOULD exchange
concise conclusions, evidence references, findings, tool results, and decision
records instead.

Identity fields may contain personal or sensitive organizational information.
Profiles MUST define data minimization, retention, access, correction, and
deletion policy. Hashing personal data does not necessarily anonymize it.
Immutable logs SHOULD store redacted or pseudonymous records where full
identity is unnecessary, while retaining an accountable resolution mechanism.

Protocol users SHOULD assess disparate impact, accessibility, contestability,
and due process when artifacts influence consequential decisions. A person
affected by a claim SHOULD have a channel to inspect applicable evidence,
challenge errors, and obtain a human decision where law or policy requires it.

## 14. Interoperability and test requirements

Before 0.1 can be called stable, the project MUST publish:

1. normative JSON Schemas for every core artifact;
2. canonicalization and hashing specifications;
3. positive, negative, boundary, and adversarial test vectors;
4. a stable machine-readable error registry;
5. version and extension negotiation rules;
6. at least two independent implementations in different codebases;
7. a reproducible interoperability report showing cross-validation;
8. fuzzing and parser resource-limit results;
9. a security threat model and disclosure process;
10. migration rules from the current Python packet representation.

Interoperability requires that implementation A can generate artifacts accepted
by implementation B and vice versa, with the same validity decisions and error
codes for normative vectors. Two wrappers around one shared validator do not
count as independent implementations.

## 15. Versioning and compatibility

**Proposed.** Protocol versions use `major.minor` notation independently from
library package versions.

- A minor revision MAY add optional non-critical fields, artifact types,
  registry values, and clarifications that do not change existing decisions.
- A major revision is REQUIRED when existing valid artifacts become invalid,
  existing invalid artifacts become valid, field meaning changes, canonical
  bytes change, or security semantics change incompatibly.
- Deprecation MUST name the replacement, first deprecated version, and earliest
  removal version.
- Implementations MUST declare exactly which protocol versions and profiles
  they support.

Version negotiation belongs in a transport binding. A recipient MUST NOT
silently reinterpret an unsupported version as a supported one.

## 16. Registries

**Proposed.** The project MUST maintain public, reviewable registries for:

- artifact types and media types;
- extension identifiers and criticality;
- validity levels and transition-event types;
- review, verification, promotion, revocation, and evidence statuses;
- hash, canonicalization, and signature algorithms;
- machine-readable error codes;
- transport and domain profiles.

Each registry requires an allocation policy, change history, designated expert
or review group, collision rules, and reserved ranges for private experiments.
Registry updates MUST NOT silently redefine deployed values.

## 17. Governance and standards path

An official standard requires an institutionally credible process in addition
to a sound specification. Atmanatic SHOULD establish:

1. a public specification repository and issue tracker;
2. a royalty-free patent and copyright contribution policy;
3. a code of conduct and transparent contributor rules;
4. named editors and a technically diverse review group;
5. published meeting notes, issue dispositions, and change logs;
6. a security contact and coordinated vulnerability disclosure policy;
7. a reference implementation that does not define the standard by itself;
8. independent implementations and recurring interoperability events;
9. a trademark and conformance-mark policy separate from protocol copyright;
10. a succession process so the protocol can outlive one company or founder.

The likely standards path is:

1. publish Atmanatic Protocol drafts and implementation reports openly;
2. obtain multi-vendor and public-sector or academic deployment evidence;
3. submit the narrow interoperable protocol to an appropriate body;
4. keep domain profiles in separate specifications.

IETF is a plausible venue if the work centers on Internet exchange formats,
security, discovery, and transport bindings. W3C is plausible if it centers on
Web data models, credentials, and provenance interoperability. ISO/IEC JTC 1 or
an accredited national body is plausible for broader governance and conformity
assessment. The project SHOULD seek early liaison rather than claiming a venue
before implementer consensus exists.

## 18. Reference implementation boundary

The current repository is the initial Python reference implementation. The
protocol core is the normative artifact model and processing behavior described
here, not any Python module layout.

The following are core candidates:

- artifact lineage and type-specific contract validation;
- evidence-card validation and admission;
- claim-to-evidence linkage;
- source-policy evaluation as an optional governance profile;
- adversarial claim review structure;
- review-backed validity transitions;
- verification and promotion record envelopes.

The following are not protocol core:

- proposer/referee loop execution;
- model providers and prompts;
- databases and `PacketStore` paths;
- network acquisition and credentials;
- verifier binaries and sandboxes;
- human-review interfaces;
- deployment, signing, trading, or transaction systems;
- Atmanatic branding and institutional operations.

Atmanatic MAY publish branded products and hosted services that implement the
protocol. Such products MUST NOT add hidden requirements to protocol
conformance.

## 19. Implementation status at Draft 0.1

| Capability | Status in current repository |
| --- | --- |
| Typed validity packet and six-level ladder | Implemented |
| One-step automatic advancement | Implemented |
| Automatic promotion prohibition | Implemented |
| Evidence-card structural validation | Implemented |
| Evidence admission and conflict checks | Implemented |
| Claim-to-admitted-evidence linkage | Implemented |
| Source and acquisition policy profile | Implemented |
| Measurable falsifier shape | Implemented |
| Common lineage envelope | Implemented for review, verification, and promotion records |
| Independent hash-linked review advancement | Implemented |
| Provider-neutral referee loop | Implemented, non-core |
| Canonical JSON wire representation | Implemented (`atmanatic_research/canonical.py`) |
| Normative JSON Schemas | Not implemented |
| Hash recomputation and verification | Implemented (`compute_content_hash`, `verify_content_hash`) |
| Digital signatures and key lifecycle | Not implemented |
| Transition, revocation, and transparency events | Not implemented |
| Stable machine-readable errors | Implemented (`atmanatic_research/error_codes.py`) |
| Strict RFC 3339 timestamp enforcement | Implemented (`atmanatic_research/timestamps.py`) |
| Critical/non-critical extension handling | Implemented in `validate_artifact_lineage` and its dependents |
| Extension and algorithm registries | Not implemented |
| Independent non-Python implementation | Not implemented |
| Cross-implementation conformance report | Not implemented |
| External standards-body adoption | Not initiated |

## 20. Draft 0.1 exit criteria

Draft 0.1 is complete when:

- this specification is reviewed against every public validator and test;
- ambiguities and code/spec mismatches are tracked as issues;
- schemas, canonicalization, media types, and error codes are proposed;
- conformance fixtures cover each MUST and MUST NOT that can be automated;
- one second implementation validates the same fixtures;
- core protocol packages no longer imply ownership by product orchestration;
- public documentation distinguishes protocol, implementation, profiles, and
  Atmanatic products;
- governance, contribution, security, and intellectual-property policies are
  publicly reviewable.

## Appendix A. Initial protocol work program

The recommended sequence after this draft is:

1. freeze field semantics and resolve the typed-packet/common-envelope gap;
2. publish JSON Schemas and canonical positive and negative fixtures;
3. select canonical JSON and define the hash projection;
4. introduce stable error codes and a conformance result format;
5. implement immutable transition and revocation events;
6. add signatures only after canonical bytes and identity semantics are stable;
7. create a small independent implementation, preferably in another language;
8. run bidirectional interoperability and publish all results;
9. open governance and invite implementer review;
10. approach a standards body with implementation evidence, not aspiration
alone.

## Appendix B. Open design questions

The 0.1 working group must resolve:

- whether JSON is the sole canonical encoding or one representation of a data
  model with deterministic JSON and CBOR encodings;
- whether identifiers are URIs, UUIDs, content identifiers, or producer-scoped
  strings;
- which JSON canonicalization and signature standards are adopted;
- how producer and reviewer identities bind to keys or verifiable credentials;
- how revocation and current status are discovered without a central service;
- how evidence is disclosed selectively without breaking hash linkage;
- which independence claims are machine-verifiable versus policy assertions;
- how large or confidential evidence is referenced and made available for
  authorized audit;
- which requirements belong in the universal core versus domain profiles;
- which standards organization and licensing commitments best protect open,
  durable adoption.