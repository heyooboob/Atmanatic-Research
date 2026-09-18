# Module-by-Module Test Strategy

This section outlines the recommended validation strategy for each module.

## Test categories

1. Happy path
2. Invalid input rejection
3. Duplicate / replay prevention
4. Boundary and authority enforcement
5. Determinism / idempotence
6. Time-budget and loop termination
7. Structured escalation and auditability

## Should be enforced by default

- every public function has a valid input and invalid input test
- every rejection path has a specific assertion message or error type
- every module has at least one repeated-operation stability test
- every module has a path that confirms no hidden authorization is granted

## Recommended module tests

### proposal_contracts.py
- valid envelope accepted
- invalid schema rejected
- missing field rejected
- invalid hash rejected
- duplicate evidence refs rejected
- execution_authorized=True rejected

### artifact_contracts.py
- valid artifact accepted
- invalid metadata rejected
- invalid hash rejected
- hidden authority rejected
- replay stable

### evidence_contracts.py
- valid evidence accepted
- invalid confidence rejected
- invalid timestamp rejected
- empty source_ids rejected
- non-dict details rejected

### evidence_admission.py
- valid evidence admitted
- stale card rejected
- conflicting evidence rejected
- claim references missing from admitted set rejected
- duplicates rejected

### orchestration.py
- accepted review passes
- unresolved findings reject
- no-progress revision rejects
- repeated proposal state rejects
- time budget exhausts cleanly
- escalation returns explicit request

### truth_review.py
- valid review accepted
- self-authored review rejected
- hash mismatch rejected
- missing resolution rejected

### source_policy.py
- valid registry accepted
- invalid source rejected
- wrong agent rejected
- source below tier rejected
- public source without receipt rejected
- receipt mismatch rejected

### validity_governance.py
- valid transition accepted
- invalid state jump rejected
- delayed transition rejected
- hash mismatch rejected
- human promotion separated from automatic verification

### text_processing.py
- stable normalization on repeated runs
- no silent semantic loss
- distinct input remains distinct

### validity_standard.py
- valid level accepted
- invalid level rejected
- uncertainty distinct from success

### validity_protocol modules
- packet accepted when valid
- malformed packet rejected
- duplicate packet rejected
- serialization stable across read/write
- level transitions explicit and valid

---

## Final test rule

If a module cannot prove deterministic behavior, rejection of malformed input, and explicit authority separation, it is not hardened enough for the protocol baseline.
