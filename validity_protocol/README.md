# validity_protocol

A standalone, domain-agnostic implementation of the claim-validation discipline
described in [TRUTH_VALIDITY_STANDARD.md](../TRUTH_VALIDITY_STANDARD.md).

This package has no dependency on downstream products, wallets, or
crypto/trading code. It does not know or care what domain a claim comes from.

It is deliberately separate from any consumer's internal validator. This
package provides a richer, portable schema that can outlive any one product's
internal implementation.

## What it does

- `ValidityPacket`: the required evidence bundle a claim must carry (scope,
  observations, evidence references, falsifier, counterclaim, uncertainty,
  limitations, rollback path, expiry, revalidation policy).
- `ValidityLevel`: the six-stage ladder (`observed` -> `tested` ->
  `validated_in_scope` -> `independently_verified` -> `awaiting_human_promotion`
  -> `promoted`).
- `validate_packet(packet, level=...)`: checks a packet's completeness and the
  anti-sycophancy rules (author cannot be reviewer, review/challenge required
  before independent verification, expired packets fail) for a given level.
- `advance(packet, target)`: moves a packet forward one level at a time. It can
  never set `PROMOTED` — that transition always requires a separate, explicit
  human-approval record outside this library.
- `PacketStore`: optional append-only JSON-lines persistence; the storage path
  is always supplied by the caller.

## What it deliberately does not do

- It does not decide whether a claim is true — only whether its own stated
  evidence is complete and internally consistent.
- It does not grant promotion/execution authority. `PROMOTED` can only be
  recorded by something outside this library, by an explicit human action.
- It does not import or depend on any downstream product, wallet, or financial
  execution code, so it can be reused by any unrelated claim pipeline.

## Status

Evidence-stage only (see `AGENTIC_VALIDITY_STANDARD_PLAN.md` Phase 1/2). Not
yet published externally, not yet piloted outside this repository.
