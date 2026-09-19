# Atmanatic Protocol 0.1 Conformance Review Package

This directory publishes the review inputs for Atmanatic Protocol 0.1. The
protocol remains a working draft; this package is for independent conformance
and interoperability review.

## Published inputs

- `../ATMANATIC_PROTOCOL_0.1_DRAFT.md` - normative protocol meaning and
  processing rules.
- `schemas/` - normative JSON Schemas for the common envelope, evidence card,
  proposal envelope, review outcome, verification result, and promotion record.
- `../atmanatic_research/canonical.py` - canonical JSON and content-hash rules.
- `fixtures/canonical_hash_parity.json` - fixed cross-language SHA-256 vector.
- `fixtures/` and `fixtures/manifest.json` - the complete 19-case conformance
  corpus and its case index.
- `../atmanatic_research/error_codes.py` - the machine-readable error-code
  registry used by the fixture expectations.
- `reference-ts/` - an independent TypeScript reference implementation for the
  current protocol-core slice.
- `README.md` - reproduction and interoperability instructions.

The generated `dist/atmanatic-protocol-0.1-conformance.zip` contains these
inputs plus `CONFORMANCE_MANIFEST.json`, which records a SHA-256 for every
included source file.

## Independent review procedure

1. Verify every archive hash in `CONFORMANCE_MANIFEST.json`.
2. Read the protocol draft and schemas without importing the Python package.
3. Implement the declared validators in a separate repository.
4. Reproduce the canonical hash parity vector.
5. Run every fixture and compare verdicts and machine-readable error codes.
6. Test at least one artifact produced by the independent implementation with
   the Atmanatic reference implementation, and the reverse direction.
7. Publish the implementation commit, runtime versions, raw results, scope,
   deviations, and unsupported areas.

Agreement in this package is partial interoperability evidence, not a claim of
universal truth, source authority, or execution permission.
