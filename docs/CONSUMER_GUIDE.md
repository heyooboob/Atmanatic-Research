# Consumer Guide

This guide helps a consumer adopt Atmanatic without coupling the consumer's
workspace to this repository's storage, transport, credentials, models, or
execution systems.

## Choose an integration level

### Level 1: Boundary validation

Install the Python package and validate artifacts at the point where one
producer's output becomes another system's input.

```powershell
python -m pip install atmanatic-research
```

Start with `validate_artifact_lineage()` or the validator that matches the
artifact type. Treat a successful result as bounded structural validation, not
as proof of universal truth or permission to act.

### Level 2: Evidence and review governance

Add evidence admission, source-policy checks, independent review, verification
results, validity transitions, expiry, and revalidation. Persist the returned
artifacts in storage owned by the consumer and retain the exact package,
schema, policy, and tool versions used for each decision.

### Level 3: Cross-language conformance

Use the public schemas, fixtures, canonical-hash vector, and machine-readable
error codes. Run the independent TypeScript reference implementation or build
a separate implementation in the consumer's language. Record the artifact
scope, implementation version, runtime, verdicts, error codes, and unsupported
features.

## Integration checklist

1. Pin a released package version, not an unreviewed branch or working tree.
2. Declare the supported protocol and artifact schema versions.
3. Validate at the consumer boundary before storing, forwarding, or acting on
   an artifact.
4. Preserve producer identity, timestamps, content hashes, evidence references,
   review linkage, and validity expiry.
5. Reject malformed, stale, conflicting, unverifiable, or authority-claiming
   artifacts. Do not silently repair them.
6. Keep credentials, model calls, transport, storage, deployment, and
   execution authority in the consumer system.
7. Add tests for accepted inputs, rejected inputs, expiry, conflicting evidence,
   self-review, and unchanged state after a failed transition.
8. Record the exact Atmanatic release, schema version, policy configuration,
   runtime, and relevant tool versions for replay.
9. Revalidate when the artifact, evidence, source policy, package, model, or
   operating environment materially changes.
10. Define a human escalation and rollback path before consuming a result in a
    consequential workflow.

## Capability and limitation matrix

| Capability | Available now | Consumer responsibility |
| --- | --- | --- |
| Artifact and lineage validation | Python reference implementation | Choose the boundary and persist the result |
| Evidence admission and source policy | Python reference implementation | Supply domain rules, acquisition context, and storage |
| Review and referee loops | Provider-neutral Python contracts | Supply reviewer/proposer implementations and timeouts |
| Canonical serialization and hashing | Python and TypeScript interoperability slice | Preserve canonical bytes and record versions |
| Protocol schemas and fixtures | Protocol 0.1 draft corpus | Declare supported scope and test unsupported types |
| Transport, API, queue, or event delivery | Not provided | Implement authentication, delivery, retries, and ordering |
| Databases and durable audit storage | Not provided | Own retention, access control, backup, and replay |
| Model providers or agent orchestration | Not provided | Own prompts, models, tools, budgets, and isolation |
| Deployment, signing authority, transactions, or execution | Not provided | Keep authority explicit and outside the protocol core |
| Universal truth or factual correctness | Not provided | Perform domain-specific research and human governance |

The TypeScript reference currently covers the published protocol-core
interoperability slice. Source policy, evidence admission, orchestration, and
lifecycle capabilities remain Python-focused unless a consumer implements and
verifies them independently.

## Local Skill Evaluation

The wheel includes the reusable skill manifest, audit, schema, and CLI
machinery. Consumers run it against their own transcripts and observed actions
using consumer-owned local state. Files such as `skills.json`, `skill_runs.json`,
`skill-store/`, transcripts, logs, and generated outputs are not uploaded by
Atmanatic and are not part of the public release surface.

Local audit results can support a later skill-version proposal. A skill version
changes only through a reviewed source, test, documentation, and release
commit; observed consumer usage never changes the installed wheel implicitly.

## Reporting problems

Use the public issue templates for:

- reproducible implementation defects;
- protocol or conformance questions;
- focused feature or contract proposals.

Include the package version or commit, runtime and operating system, smallest
safe reproduction, expected behavior, observed behavior, and relevant schema,
fixture, or error code. Do not include secrets, private keys, personal data,
consumer data, or credentials.

For suspected security vulnerabilities, do not open a public issue. Follow
[SECURITY.md](../SECURITY.md) and use GitHub's private vulnerability reporting
when available.

## Reporting interoperability results

Consumers implementing the protocol should publish or privately submit:

- implementation language and version;
- package or commit version;
- supported artifact types and schema versions;
- fixture verdicts and machine-readable error codes;
- canonical-hash parity results;
- runtime and operating-system details;
- deviations, unsupported areas, and known limitations;
- at least one artifact tested in both directions when possible.

Interoperability agreement is evidence that implementations follow the same
contract for the tested scope. It is not proof of universal truth, safety,
authority, or execution permission.

## First-contact path

For a new integration, begin with the README's first validation example, then
read the [Protocol 0.1 draft](../ATMANATIC_PROTOCOL_0.1_DRAFT.md), the
[conformance review package](../interop/CONFORMANCE_REVIEW.md), and the
[contribution guide](../CONTRIBUTING.md). Keep the first deployment in a
bounded, observable environment and require human review for consequential use.
