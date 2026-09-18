# Architecture Documentation

This directory contains the grounded architecture and implementation standards for the Atmanatic research stack.

The goal is to document the system in a way that is:
- grounded in the actual repository contracts and validation logic,
- operationally testable,
- fail-closed by default,
- explicit about the separation between optimization, memory, verification, and authority.

## Contents

- [layered_stack.md](layered_stack.md) — architecture overview and grounded layer responsibilities
- [implementation_checklist.md](implementation_checklist.md) — per-file invariant and validation plan
- [hardening_standards.md](hardening_standards.md) — cross-cutting standards for idempotence, determinism, and fail-closed behavior
- [test_strategy.md](test_strategy.md) — module-by-module test strategy and acceptance criteria
- [eigenvector_graph_analysis.md](eigenvector_graph_analysis.md) — bounded, non-authorizing graph analysis for the optimization/memory layers
- [../foundations/mathematical_principles.md](../foundations/mathematical_principles.md) — shared mathematical definitions used across the architecture appendix

## Status

See [ATMANATIC_MASTER_IMPLEMENTATION_ROADMAP.md](../../ATMANATIC_MASTER_IMPLEMENTATION_ROADMAP.md)
for the narrative, step-by-step implementation history; this table is the
per-file snapshot, ordered per the sequencing note in
[implementation_checklist.md](implementation_checklist.md). All 24 modules
exist and are covered by passing tests as of 2026-09-18 (171 Python tests, 26
TypeScript tests); "Notes" below records depth/caveats, not existence.

| # | Module | Status | Notes |
| --- | --- | --- | --- |
| 1 | `atmanatic_research/error_codes.py` | Implemented | shared registry backing every other module's `.code` |
| 2 | `atmanatic_research/timestamps.py` | Implemented | strict RFC 3339, explicit UTC offset required |
| 3 | `atmanatic_research/canonical.py` | Implemented | cross-language hash parity proven against `interop/reference-ts` |
| 4 | `atmanatic_research/artifact_contracts.py` | Implemented | includes critical/non-critical extension handling |
| 5 | `atmanatic_research/evidence_contracts.py` | Implemented | |
| 6 | `atmanatic_research/proposal_contracts.py` | Implemented | covered by the interop fixture corpus |
| 7 | `atmanatic_research/intelligence_contracts.py` | Implemented | legacy benchmark/export/soak/API-v2 contracts |
| 8 | `atmanatic_research/source_policy.py` | Implemented | |
| 9 | `atmanatic_research/evidence_admission.py` | Implemented | |
| 10 | `atmanatic_research/truth_review.py` | Implemented | |
| 11 | `atmanatic_research/validity_standard.py` | Implemented | |
| 12 | `validity_protocol/levels.py` | Implemented | |
| 13 | `validity_protocol/packet.py` | Implemented | |
| 14 | `validity_protocol/validator.py` | Implemented | |
| 15 | `validity_protocol/jsonl.py` | Implemented | shared by `PacketStore` and `LifecycleEventLog`; no quarantine-and-continue on a corrupt line |
| 16 | `validity_protocol/store.py` | Implemented | |
| 17 | `atmanatic_research/validity_governance.py` | Implemented | includes `promote_packet` |
| 18 | `atmanatic_research/lifecycle_events.py` | Implemented | revocation-reason taxonomy (protocol draft §7.2) not built |
| 19 | `atmanatic_research/orchestration.py` | Implemented | |
| 20 | `atmanatic_research/orchestration_audit.py` | Implemented | |
| 21 | `atmanatic_research/text_processing.py` | Implemented | |
| 22 | `atmanatic_research/graph_analysis.py` | Implemented | not wired into any consumer by design; governing isolation enforced |
| 23 | `atmanatic_research/verification_adapters.py` | Implemented, narrow pilot | no sandbox needed yet — checks fixed code, not untrusted input |
| 24 | `atmanatic_research/benchmark_harness.py` | Implemented | committed corpus covers 6 of 24 modules; expansion tracked in the roadmap |

Cross-cutting, not in the per-module list above:

| Area | Status | Notes |
| --- | --- | --- |
| Second implementation | Implemented, partial scope | `interop/reference-ts` — 6 core contracts + canonical hashing; not source policy, evidence admission, or orchestration |
| Interoperability report | Implemented | `interop/generate_report.py` → `interop/INTEROPERABILITY_REPORT.md`, currently 19/19 fixtures agree |
| CI | Implemented | `.github/workflows/ci.yml` — Python matrix, TypeScript, interoperability report |
| Formal verifier sandbox | Not implemented | required before any adapter accepts untrusted specifications/code |
| Signing / key lifecycle | Not implemented | protocol draft §12 |
| Extension/algorithm registries | Not implemented | protocol draft §16 |

## Core principle

No layer grants authority by implication. Optimization improves throughput. Memory preserves continuity. Verification enforces deterministic validity. Authority remains explicitly separate.
