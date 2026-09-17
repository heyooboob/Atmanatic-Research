# Atmanatic Research Boundary Charter

**Status:** active boundary decision  
**Effective:** 2026-09-17

## Entity

Atmanatic Research Institution is an independent, domain-agnostic research
institution. It produces evidence, validity packets, falsification records,
provenance, and research methods.

External consumers may use Atmanatic methods under an explicit integration or
license relationship, but they do not define Atmanatic or own its identity.

## Boundary rules

- Atmanatic must not require downstream products, wallets, capital, or live execution.
- External consumers may depend on Atmanatic research contracts, but the dependency is one-way.
- Atmanatic outputs are informational and validation-oriented; they do not authorize execution.
- External consumers retain responsibility for policy, custody, capital, execution, and operational risk.
- Shared code must have a domain-neutral owner or an explicit compatibility adapter.
- Public Atmanatic material must stand on its own and must not present one consumer as its product, division, or operating layer.

## Technical migration policy

The implementation proceeds in reversible slices:

1. Establish canonical Atmanatic namespaces for domain-neutral contracts.
2. Publish stable, versioned artifact schemas.
3. Move only domain-neutral implementation into the Atmanatic namespace.
4. Keep execution and operational controls owned by external consumers.
5. Remove compatibility adapters only after consumers and release checks no longer depend on them.

## Current implementation ownership

Atmanatic owns:

- research artifact contracts;
- bounded validity checks;
- adversarial truth review;
- evidence admission;
- deterministic text processing;
- source-policy evaluation;
- validity-packet schemas, advancement, and caller-supplied storage.

External consumers own:

- source acquisition and operational configuration;
- evidence persistence and search infrastructure;
- retrieval orchestration;
- operational filesystems and databases;
- execution systems and operational adapters.

Compatibility adapters are transitional implementation details, not ownership
claims. New domain-neutral research code belongs under `atmanatic_research` or
`validity_protocol`.

## Relationship statement

Atmanatic remains valuable without any particular consumer. External consumers
remain responsible for their own operational governance regardless of which
research methods they adopt.