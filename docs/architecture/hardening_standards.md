# Hardening Standards

This document defines the baseline engineering rules that all modules should follow.

## 1. Fail-closed principles

- Invalid, malformed, stale, duplicate, or contradictory input must be rejected.
- A missing required check is treated as a rejection, not a pass.
- Every externally visible decision must be explainable by structured metadata.

## 2. Idempotence

The system should not produce different outcomes from the same valid operation repeated in the same context.

Examples:
- validating the same proposal twice should not create a second state
- admitting the same evidence twice should not create a new decision state
- re-running the same review loop under the same inputs should not mutate the final result

## 3. Determinism

Where possible, outputs should be fully determined by input and the declared rules. Avoid hidden time, randomness, ambient state, or implicit trust.

## 4. No implicit authority

No artifact, record, review outcome, or proof should silently authorize execution.

Rules:
- execution_authorized must remain false by default
- external authority remains outside the research artifact model
- action is gated by an explicit authority boundary

## 5. Replayability

The system must preserve enough metadata to reconstruct a decision trail.

Good replayability requires:
- explicit identifiers
- stable ordering
- content hashes
- lineage metadata
- review output and responses preserved

## 6. Structured rejection

Every invalid path should produce a specific reason, not a generic failure. This supports audits and deterministic repairs.

## 7. Separation of concerns

- proposal generation is not review
- evidence validation is not truth validation
- review is not action
- optimization is not authority
- memory is not ownership

---

## Cross-layer policy summary

A system is hardened when it satisfies the following:

- schema conformance is required
- provenance is required
- evidence is admitted only under policy
- review is structured and bounded
- validity transitions remain explicit
- authority remains external and explicit
- all outcomes are replayable and auditable
