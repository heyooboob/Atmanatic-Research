# Atmanatic Repository Boundary Plan

Status: approved target architecture
Effective: 2026-09-16

## Objective

Produce an independently cloneable, installable, testable, and releasable
Atmanatic project. External consumers connect only through documented,
versioned research contracts.

## Target projects

### Atmanatic Research Institution

Owns domain-neutral research and validity capabilities:

- evidence, provenance, claims, and falsification contracts
- validity packets and review rules
- deterministic text and research transformations
- source-policy evaluation as a generic policy library
- research storage and research API, when needed
- Atmanatic documentation, release process, and tests

Atmanatic must not depend on any external consumer, wallet, treasury, capital,
execution system, command-center state, or consumer filesystem paths.

### External consumers

External consumers own their own source configuration, operational evidence,
retrieval, orchestration, databases, execution, documentation, release
processes, and tests. They consume Atmanatic artifacts through a published
package or API and must not import Atmanatic repository internals or share
Atmanatic state files.

## Integration contract

The initial integration boundary is versioned JSON-compatible artifacts:

- evidence cards
- validity packets
- research claims
- provenance records
- review outcomes
- falsification records

The contract must specify schema version, producer, creation time, content
hash, expiry/revalidation rules, and execution authority. Atmanatic output is
never an execution authorization.

The preferred implementation order is:

1. Publish `atmanatic-research` as an independently installable package.
2. Publish schemas and a small client/server adapter, if remote operation is required.
3. Migrate external consumers to the released package or API.
4. Remove all source-tree imports across the project boundary.

## Shim retirement

1. Freeze any legacy compatibility modules.
2. Keep internal consumers on canonical Atmanatic APIs only.
3. Add deprecation warnings and a removal version to each shim.
4. Migrate external callers or provide a separately versioned legacy package.
5. Delete shims once the compatibility window closes.
6. Run the separation audit in CI on both projects.

A shim is not retired merely because tests pass. It is retired when no supported
consumer imports it and the released integration boundary no longer references
it.

## Baseline on 2026-09-16

The separation audit is intentionally failing in the transitional monorepo:
Atmanatic has no imports of external consumers. Public imports of the released
Atmanatic package are allowed for consumers. Any legacy compatibility shims
must be removed or isolated in a separately versioned legacy package before
the final audit can pass.

## Shim retirement milestone on 2026-09-16

The five in-tree compatibility shims were removed after all internal consumers
and tests migrated to Atmanatic's public package surface. The separation audit
now passes with zero violations. The remaining work is repository packaging
and physical project separation: consumers must use the released wheel or API
from an independent Atmanatic project rather than a shared source tree.

## Packaging milestone on 2026-09-16

Root `pyproject.toml` now builds `atmanatic-research` version `0.1.7` with
only `atmanatic_research` and `validity_protocol` packages and no runtime
dependencies. The wheel was inspected successfully: it contains no
consumer files. External consumers still need to use this released artifact
instead of an in-tree namespace before the separation audit can pass.

## Migration phases

1. **Contract extraction**: complete the domain-neutral modules and schemas.
2. **Atmanatic packaging**: add independent build metadata, dependencies, CI,
   release versioning, and a clean test suite.
3. **Consumer decoupling**: replace source imports with the released package or
   API; keep consumer configuration and state behind consumer-owned interfaces.
4. **Repository split**: copy history or create independent repository roots,
   then prove each project works with the other project absent.
5. **Shim removal**: remove compatibility modules and legacy aliases after the
   published removal version.

## Final acceptance test

The split is complete only when all of these pass:

- Atmanatic can be cloned, installed, tested, and released without any consumer repository.
- Each consumer can be cloned, installed, tested, and run without Atmanatic source code present.
- The only connection is a documented, versioned research contract.
- Neither project imports another project's private modules.
- Neither project depends on another project's filesystem, databases, environment variables, credentials, or runtime processes.
- The separation audit passes with zero violations.
- Compatibility shims are deleted or isolated in a separately versioned legacy package.
