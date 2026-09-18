# Atmanatic Protocol 0.1 Interoperability Corpus

This directory is the Draft 0.1 interoperability contract described in
[ATMANATIC_PROTOCOL_0.1_DRAFT.md](../ATMANATIC_PROTOCOL_0.1_DRAFT.md) section 14
and [ATMANATIC_MASTER_IMPLEMENTATION_ROADMAP.md](../ATMANATIC_MASTER_IMPLEMENTATION_ROADMAP.md)
Step 8. It is not part of the `atmanatic-research` package and is not shipped
in the wheel; it exists to let an independent implementation prove it agrees
with the Python reference implementation on real inputs.

## Contents

- `schemas/` — normative JSON Schemas (draft 2020-12) for the protocol core
  artifact types: the common envelope, evidence cards, proposal envelopes,
  review outcomes, verification results, and promotion records.
- `fixtures/<artifact_type>/<case_id>.json` — generated fixtures, each pairing
  an input artifact with its actual, verified verdict (`accept` or `reject`
  plus the exact error code) as produced by the Python reference validators.
- `fixtures/manifest.json` — the full fixture index.
- `generate_fixtures.py` — regenerates every fixture from the live validators.
  It fails closed (refuses to write) if a case's declared expectation does not
  match what the validator actually does, so fixtures cannot silently drift
  from real behavior.
- `verify_fixtures.py` — re-checks every committed fixture against current
  validator behavior; this is what CI should run to catch drift when a
  validator changes without regenerating fixtures.

## What counts as interoperability evidence

Two implementations are interoperable for a given artifact type only when,
for every fixture of that type, both implementations produce:

1. the same accept/reject verdict, and
2. for rejections, the same error code from the shared registry
   (`atmanatic_research/error_codes.py` / `interop/schemas`).

Agreement on English error *messages* is explicitly not required — only the
verdict and the machine-readable code are protocol API.

## What this is not

- Not a substitute for the normative prose in the protocol draft — the
  fixtures illustrate the rules, they do not replace them.
- Not evidence of interoperability by itself. A second implementation must
  actually load these fixtures and be run against them; until that exists,
  this corpus only proves the Python reference implementation is internally
  consistent with itself (see `verify_fixtures.py`).
- Not a place for domain-specific, product-specific, or consumer-specific
  cases. Only protocol-core artifact types belong here.

## Regenerating fixtures

Run from the repository root:

```
python interop/generate_fixtures.py
python interop/verify_fixtures.py
```

Both scripts exit non-zero on any drift or mismatch.
