# Contributing to Atmanatic Research

Thank you for helping improve the protocol and reference implementation.
Contributions should preserve deterministic behavior, explicit authority
boundaries, and the fail-closed validation model.

## Before opening an issue or pull request

1. Search existing issues and documentation.
2. For protocol changes, identify the affected artifact, schema, error code,
   interoperability fixture, and compatibility impact.
3. Do not include credentials, private keys, personal data, or consumer data.
   Report vulnerabilities through [SECURITY.md](SECURITY.md).

## Before making repository or release changes public

1. Check the current tree and the complete Git history for credentials, private
  keys, tokens, personal data, and consumer data.
2. Keep local configuration, databases, logs, model caches, retrieval indexes,
  and generated knowledge artifacts outside version control. The repository's
  `.gitignore` contains the baseline rules for these files.
3. If a secret has entered Git history, rotate it first. Removing the current
  file does not invalidate historical copies.
4. Use GitHub's private vulnerability reporting for undisclosed security
  issues; do not publish exploit details in an issue or pull request.
5. Review repository visibility, branch protection, dependency alerts, secret
  scanning, and workflow permissions before a public release.
6. Do not force-push rewritten history without a verified backup and explicit
  maintainer coordination.

## Local checks

From the repository root:

```powershell
python -m unittest discover -s tests -q
python scripts/verify_repository_split.py
python scripts/inspect_release.py
python interop/verify_fixtures.py
cd interop/reference-ts
npm ci
npm test
```

The full GitHub Actions workflow is the final acceptance check. A change is
not complete if it passes only a local subset while breaking the independent
TypeScript implementation, fixture corpus, wheel boundary, or package split.
The local working tree is for planning and implementation; the public package
and release workflow are the compatibility gate. See
[docs/LOCAL_PUBLIC_BOUNDARY.md](docs/LOCAL_PUBLIC_BOUNDARY.md).

## Design expectations

- Keep runtime dependencies at zero unless a dependency is essential to the
  protocol core. Optional capabilities belong in optional extras.
- Preserve stable machine-readable error codes and deterministic ordering.
- Reject malformed, stale, conflicting, unverifiable, or authority-claiming
  artifacts rather than silently repairing them.
- Keep consumer storage, transport, credentials, model providers, and
  execution authority outside the protocol core.
- Add focused tests for accepted and rejected behavior, including boundary
  cases and unchanged-state behavior after a failed transition.
- Update schemas, fixtures, interoperability tests, and documentation together
  when a protocol contract changes.

## Pull requests

Use a focused title and describe the problem, intended behavior, contract or
invariant changed, tests and commands run, compatibility impact, and remaining
limitations. Maintainers may request a protocol review or independent
implementation check before merging normative changes.
