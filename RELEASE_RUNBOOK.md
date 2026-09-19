# Atmanatic Release Runbook

This is the operational procedure for cutting, signing, verifying, and, if
necessary, rolling back a release of `atmanatic-research`. It is the
"rollback runbook" deliverable of Phase 8
(`ATMANATIC_VERIFIABLE_AGENTIC_RESEARCH_IMPLEMENTATION_PLAN.md` section 13),
and it documents the mechanical tools already in the repository — it does not
introduce new authority. Nothing in this procedure authorizes deployment or
execution; a release manifest's `execution_authorized` field is always
`false`.

## Components

- [`scripts/inspect_release.py`](scripts/inspect_release.py) — builds the
  wheel, hashes it, and fails closed if it contains anything outside
  `atmanatic_research`/`validity_protocol`.
- [`scripts/scan_dependencies.py`](scripts/scan_dependencies.py) — runs
  `pip-audit` against the environment; fails closed if the scanner itself is
  missing.
- [`scripts/check_release_tag.py`](scripts/check_release_tag.py) — proves a
  git tag (`vMAJOR.MINOR.PATCH`) matches `[project].version` in
  `pyproject.toml`.
- [`scripts/generate_release_key.py`](scripts/generate_release_key.py) —
  one-time, manual key bootstrap. Never run in CI.
- [`scripts/sign_release.py`](scripts/sign_release.py) — builds and signs a
  release manifest binding a tag to the wheel's SHA-256, using
  `atmanatic_research.signing` and the key registered in
  `release/keys.jsonl`.
- [`scripts/verify_release_manifest.py`](scripts/verify_release_manifest.py) —
  re-verifies a signed manifest's content hash, signature, and (optionally)
  binding to an actual wheel file.
- `release/keys.jsonl` — the append-only registry of release signing keys
  (public material and revocation history only; never a private key). It is
  committed once bootstrapped; see "Bootstrapping the signing key" below.

## Prerequisites (one-time, per signing key)

1. A maintainer runs, locally, never in CI:
   ```
   python scripts/generate_release_key.py --producer "<name or role>"
   ```
2. This appends an `active` key record to `release/keys.jsonl` and prints the
   new private key exactly once. Store it only as the
   `ATMANATIC_RELEASE_PRIVATE_KEY` secret in CI. It must never be committed,
   logged, or stored anywhere else.
3. Commit the updated `release/keys.jsonl` (public material only) as its own
   reviewed change.

## Cutting a release

1. Land the reviewed change on the default branch; CI (`.github/workflows/ci.yml`,
   job `python`) must pass: full test suite, repository-split acceptance
   test, wheel inspection, and dependency scan.
2. Bump `[project].version` in `pyproject.toml` in its own commit.
3. Tag that commit `vMAJOR.MINOR.PATCH` matching the new version exactly, and
   push the tag.
4. The tag push triggers the `release` job in `.github/workflows/ci.yml`,
   which:
   - waits for the `python` and `typescript` jobs on the same commit;
   - runs `scripts/check_release_tag.py` — fails closed if the tag and
     `pyproject.toml` disagree;
   - runs `scripts/sign_release.py --tag <tag>` — builds the wheel, computes
     its hash, and signs a manifest with the CI secret key; fails closed if
     that key is not `active` in `release/keys.jsonl`;
   - runs `scripts/verify_release_manifest.py dist/release_manifest.json` —
     re-verifies the manifest before anything is published;
    - builds `dist/atmanatic-protocol-0.1-conformance.zip`;
    - publishes the wheel, signed manifest, conformance archive, and generated
       interoperability report as assets on the GitHub Release.
5. Retain that artifact (and the wheel it describes) as the release's
   provenance record. Retain the prior release's manifest and wheel too —
   never delete the last known-good artifact when publishing a new one.

## Verifying a release later

Given a retained `release_manifest.json` and (optionally) the wheel it
describes:

```
python scripts/verify_release_manifest.py path/to/release_manifest.json --wheel path/to/the.whl
```

This independently re-checks the manifest's own content hash, its signature
against the currently active key in `release/keys.jsonl`, and — if a wheel is
given — that the wheel's actual bytes match the hash the manifest declares.
Any failure is specific (hash mismatch, signature mismatch, or key not
active) rather than a generic pass/fail.

## Rollback procedure

Rollback restores a previously verified artifact; it never mutates a
consumer's operational state, and it never re-signs or reinterprets a past
release.

1. Identify the last known-good tag and its retained
   `release_manifest.json` + wheel.
2. Run `scripts/verify_release_manifest.py` against that manifest (see
   above). If it still verifies, the artifact is safe to restore as-is.
3. If verification fails only because the signing key used at the time has
   since been revoked (see "Key compromise" below), that is expected and does
   not itself indicate the artifact was tampered with — the manifest's
   `content_hash` check and the wheel-binding check are the tamper-evidence
   signals; a revoked key only means no *new* releases may use it.
4. Reinstall the retained wheel into the consumer's environment. Do not
   rebuild it from source at rollback time — rebuilding produces new bytes
   with a new hash, defeating the purpose of retaining the artifact.
5. Quarantine (do not delete) the failed release's artifact and manifest for
   post-incident review.
6. Record the rollback (from tag, to tag, reason, operator, timestamp)
   wherever the consuming system keeps its own operational log; that log is
   the consumer's responsibility, not this repository's.

## Key compromise or rotation

1. Revoke the affected key:
   ```python
   from pathlib import Path
   from atmanatic_research import KeyRegistry
   KeyRegistry(Path("release/keys.jsonl")).revoke(key_id, reason="compromised")
   ```
   (or `reason="superseded"` / `"no_longer_used"` / `"policy_violation"` —
   `atmanatic_research.signing.KEY_REVOCATION_REASONS` is the finite,
   enforced taxonomy; no other reason string is accepted.)
2. Commit the updated `release/keys.jsonl` immediately — a revoked key must
   stop verifying new releases as soon as the registry is updated, since
   `verify_signed_record_with_registry()` fails closed the moment a key is no
   longer `active`.
3. Bootstrap a new key (see "Prerequisites" above) and update the
   `ATMANATIC_RELEASE_PRIVATE_KEY` CI secret.
4. Signatures produced by the revoked key while it was active remain valid
   *historical* attestations (their content hash and signature bytes do not
   change); revocation only prevents `verify_signed_record_with_registry()`
   from treating that key as currently trustworthy going forward. Rotating
   the key never requires re-signing already-published releases.

## Dependency scanning

`scripts/scan_dependencies.py` runs `pip-audit --strict` and fails on any
reported finding, or if `pip-audit` itself is missing (a missing scanner is
never treated as a clean scan). It runs in the `python` CI job on every push
and pull request, not just on tags, since dependency advisories are not tied
to a release event. If it fails on a tag commit, do not tag a release until
the finding is resolved or explicitly accepted and documented.

## What this runbook is not

- Not an operational deployment procedure for any specific consumer; consumer
  deployment, execution, and rollback of their own operational state are
  explicitly out of scope for Atmanatic
  (`ATMANATIC_REPOSITORY_BOUNDARY_PLAN.md`).
- Not a substitute for human release approval — nothing here grants
  execution authority; every manifest declares `execution_authorized: false`.
