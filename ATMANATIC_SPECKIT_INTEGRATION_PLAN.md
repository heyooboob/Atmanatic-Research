# Atmanatic and GitHub Spec Kit Integration Plan

**Status:** Proposed integration profile
**Date:** 2026-09-18
**Scope:** Optional consumer adapter; no dependency on Spec Kit in the protocol core

## 1. Strategic position

Atmanatic remains the vendor-neutral trust, evidence, verification, and validity
boundary. GitHub Spec Kit is an optional workflow and agent-runtime consumer.
Atmanatic MUST NOT require Spec Kit, an AI coding agent, a model provider, or a
Spec Kit project layout in order to parse or validate a core artifact.

The integration boundary is JSON-compatible Atmanatic artifacts. A Spec Kit
adapter may read Spec Kit Markdown and repository state, but it must convert
those inputs into Atmanatic envelopes before they can influence a governed
validity decision.

```text
Spec Kit workflow                         Atmanatic governance
-----------------                         -------------------
idea / assessment       ->                proposal envelope
spec.md                 ->                proposal or specification reference
plan.md                 ->                bounded implementation proposal
tasks.md                ->                proposal lineage and obligations
implementation         ->                evidence and verification results
converge                ->                review findings and unresolved gaps
human workflow          ->                explicit promotion record
```

The arrows are mappings, not equivalences. A Markdown artifact is not
automatically evidence, a completed task is not automatically verification, and
Spec Kit convergence is not automatically independent review.

## 2. Ownership boundary

### Spec Kit owns

- natural-language intake and feature discovery;
- project constitution and software-development conventions;
- requirements clarification;
- technical planning and task decomposition;
- coding-agent integration and command registration;
- source-code edits and repository-local workflows;
- implementation progress and convergence reports.

### Atmanatic owns

- artifact identity, schema, lineage, and canonical content hashes;
- evidence-card structure and decision-grade admission;
- source-policy evaluation and acquisition receipts;
- falsifiers, counterclaims, uncertainty, and limitations;
- independent review and hash-linked challenge outcomes;
- deterministic verification-result envelopes;
- bounded validity transitions, expiry, revalidation, and revocation;
- explicit separation between promotion and execution authority.

### Neither side may infer

- that a Spec Kit constitution is an independent review;
- that a checked task means the implementation is verified;
- that a passing test proves an external-world claim;
- that a converged feature is safe to deploy;
- that an Atmanatic promotion record authorizes execution.

## 3. Proposed adapter surfaces

The first adapter should be provider-neutral and read-only with respect to
Spec Kit source artifacts. It should expose functions equivalent to:

```python
build_spec_kit_proposal(spec_document, *, plan_document=None, tasks_document=None, ...)
record_spec_kit_evidence(proposal, evidence_cards, ...)
record_spec_kit_review(proposal, findings, ...)
record_spec_kit_verification(proposal, verification, ...)
```

The adapter should return ordinary Atmanatic dictionaries or typed values and
must reuse existing public validators rather than introduce a parallel contract
family.

It should not invoke the Spec Kit CLI, install integrations, execute an agent,
modify source code, or approve a validity transition in its initial scope.

## 4. Artifact mapping

| Spec Kit input | Atmanatic representation | Required treatment |
| --- | --- | --- |
| `constitution.md` | governance context or processor metadata | policy input; never evidence of factual correctness |
| `intake.md`, `problem.md`, `concept.md` | proposal payload and lineage | untrusted assertions; preserve assumptions and open questions |
| `decision.md` | proposal decision metadata | `go` is not validity; `kill` and `needs-clarification` remain explicit outcomes |
| `spec.md` | proposal payload or referenced specification artifact | hash the exact content; preserve scope, actors, constraints, and acceptance criteria |
| `plan.md` | implementation proposal payload | record technical assumptions and tool versions; do not treat plan completion as verification |
| `tasks.md` | proposal obligations / implementation checklist | checked state is an assertion requiring independent evidence |
| `research.md` | evidence candidates | each source claim must become an admitted evidence card before decision use |
| `quickstart.md` | verification specification reference | identifies intended checks; does not establish that checks ran |
| `contracts/` | specification identifiers and verification obligations | useful input to verification-result envelopes |
| `analyze` output | review findings or consistency evidence | retain source references and unresolved findings |
| `converge` output | review outcome candidate | must be independently represented and hash-linked before validity advancement |
| bug `assessment.md` | proposal and suspected-cause record | diagnosis is not proof of cause |
| bug `fix.md` | implementation evidence candidate | exact changes and deviations require repository evidence |
| bug `test.md` | verification-result candidate | only actual executed checks may receive `verified`; otherwise use `partial` or `not_evaluated` |

## 5. Minimum trust pipeline

A governed Spec Kit result should follow this sequence:

1. Read the selected Spec Kit artifacts as untrusted input.
2. Canonicalize and hash the exact bytes or normalized document projection.
3. Create an Atmanatic proposal envelope with producer, lineage, tool versions,
   scope, and `execution_authorized=False`.
4. Convert source-backed claims into evidence cards.
5. Apply source policy, freshness, conflict, provenance, and admission checks.
6. Require falsifiers, counterclaims, uncertainty, limitations, and rollback
   information for any claim intended for validity advancement.
7. Run independent challenge through the Atmanatic referee/review contract.
8. Record deterministic verification results with input hash, specification
   identifiers, diagnostics, resource usage, and environment.
9. Advance the validity packet only through the existing ordered transitions.
10. Require a separate, explicit human promotion record for `promoted`.
11. Keep execution, deployment, signing, and transaction authority outside the
    adapter.

## 6. Phase plan

### Phase A: profile and fixtures

- Freeze this mapping as an integration profile.
- Add representative Spec Kit Markdown fixtures without importing Spec Kit.
- Define canonical document projection rules and hash expectations.
- Add negative fixtures for missing scope, unchecked obligations, unsupported
  claims of verification, and hidden authority.

### Phase B: read-only artifact adapter

- Implement a small adapter that accepts document text and metadata supplied by
  the caller.
- Produce validated proposal envelopes and lineage records.
- Preserve source references, assumptions, unresolved questions, and tool
  versions without interpreting them as truth.
- Add deterministic replay tests.

### Phase C: evidence and verification bridge

- Map research citations and executed test receipts into evidence cards.
- Require caller-supplied acquisition receipts for governed external sources.
- Convert actual test or verifier output into verification-result envelopes.
- Reject claims of verification when no execution receipt or verifier result is
  present.

### Phase D: Spec Kit workflow integration

- Add an optional Spec Kit extension or command integration outside the core
  package.
- Emit Atmanatic artifacts after `specify`, `plan`, `tasks`, `implement`, and
  `converge`.
- Keep the adapter provider-neutral and allow the Spec Kit integration to be
  installed independently.
- Make every generated artifact carry a protocol version and content hash.

### Phase E: governed promotion consumer

- Add a separate human-facing workflow that reviews the Atmanatic packet,
  evidence, verification result, expiry, and rollback path.
- Keep promotion records separate from Spec Kit task completion.
- Do not connect promotion directly to deployment or operational execution.

## 7. Explicit non-goals

This integration does not:

- embed Spec Kit into `atmanatic-research` runtime dependencies;
- make Markdown a normative protocol representation;
- trust an AI agent because it is a registered Spec Kit integration;
- treat a constitution as a source authority;
- replace source-policy or evidence-admission checks;
- expose private chain-of-thought;
- execute arbitrary Spec Kit commands inside the protocol validator;
- grant deployment, signing, trading, transaction, or autonomous authority;
- claim that passing software tests proves an external-world proposition.

## 8. Strategic conclusion

Spec Kit is a strong candidate for the workflow and agent-runtime side of an
Atmanatic deployment, especially for producing proposals, implementation plans,
task obligations, and code-change evidence. Atmanatic should remain the
independent boundary that decides whether those outputs are structurally valid,
evidence-backed, challenged, verified in scope, stale, or eligible for a
separate human promotion decision.

The integration is successful only if Spec Kit can be removed without changing
Atmanatic protocol semantics, and if an Atmanatic consumer can validate the
result without running Spec Kit.
