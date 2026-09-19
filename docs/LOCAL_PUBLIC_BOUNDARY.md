# Local/Public Boundary

This repository has two related but distinct surfaces:

| Surface | Purpose | Authority |
| --- | --- | --- |
| Local working state | Planning, experiments, patches, tests, generated reports, and release preparation | Maintainer development space; may be incomplete or unstable |
| Public release surface | Published package, schemas, fixtures, conformance archive, signed manifest, and release documentation | Supported consumer interface; must be reproducible and reviewed |

## Development rule

Use the local working tree to plan, build, patch, test, and review changes. Local
state may include ignored configuration, databases, logs, caches, retrieval
indexes, and generated artifacts. Those files are implementation aids, not
public protocol commitments.

Protocol behavior, schemas, fixtures, public APIs, and release metadata are
tracked explicitly in the repository. A local experiment is not part of the
public contract until it is committed and passes the repository acceptance
checks.

## Skill audit boundary

The released wheel contains the reusable skill contracts and audit machinery:
manifests, audit results, schemas, and the `atmanatic-skill` command. A
consumer uses those APIs locally to evaluate the skills it actually runs.

Consumer-owned `skills.json`, `skill_runs.json`, `skill-store/`, `runs/`, logs,
transcripts, and generated output files are local evaluation data. They are
ignored by default and are not public package contents or release evidence.
The audit workflow does not upload telemetry, automatically change a skill
version, or promote a local result into the wheel.

Skill-version updates require sufficient local evidence, an explicit review of
the proposed behavior and compatibility impact, updated tests/documentation,
and a normal release commit that passes the public gates. Local run data may
inform that proposal, but it is not itself a public protocol artifact.

## Public gate

The public-facing package and release workflow are the main promotion gate.
Before a change becomes supported publicly:

1. Keep the change in a focused commit or pull request.
2. Run the local checks in [CONTRIBUTING.md](../CONTRIBUTING.md).
3. Require the full GitHub Actions workflow to pass, including Python tests,
   TypeScript interoperability, repository-boundary checks, wheel inspection,
   and dependency scanning.
4. For a release, require the version/tag check, exact wheel build, signed
   manifest verification, conformance archive, and release approval described
   in [RELEASE_RUNBOOK.md](../RELEASE_RUNBOOK.md).
5. Publish only the verified package and release assets. Consumers should use a
   tagged release or published package, not a working tree or unreviewed branch.

A passing local test is evidence for development. A passing public gate is the
condition for treating the resulting artifact as a supported interface.

## Boundary rules

- Do not commit local secrets, credentials, consumer data, runtime state, or
  generated caches.
- Do not let local model providers, orchestration systems, storage, or tools
  become dependencies of the protocol core.
- Do not describe an experimental local capability as publicly supported until
  it has a tracked contract, tests, documentation, and release coverage.
- Keep public changes reversible through ordinary commits, tagged releases,
  signed manifests, and retained prior artifacts.
- Use the released package or public conformance materials to test consumer
  integration; do not require consumers to import repository internals.

The local workspace is where change is made. The public release surface is
where compatibility is claimed.
