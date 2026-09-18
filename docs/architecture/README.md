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

## Core principle

No layer grants authority by implication. Optimization improves throughput. Memory preserves continuity. Verification enforces deterministic validity. Authority remains explicitly separate.
