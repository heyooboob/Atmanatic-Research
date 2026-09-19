# Atmanatic Recognition and PyPI Plan

## Current posture

Atmanatic Research remains independently owned and private while the reference
implementation, protocol corpus, release process, and consumer documentation
stabilize. Public visibility is deferred until the project has the review and
adoption materials needed for a credible first release.

The project should build recognition through demonstrated interoperability,
independent review, reproducible conformance results, and consumer adoption.
Recognition must not be presented as formal standards approval until an
appropriate external process has accepted the work.

## Common avenues for recognition and adoption

### Standards and neutral governance

- **OASIS Open**: first organization to investigate for vendor-neutral protocol
  stewardship and a standards-track process.
- **IEEE Standards Association**: later option if the protocol needs formal
  standards recognition and has sufficient implementation and adoption evidence.
- **W3C**: possible avenue if the protocol develops a strong web, provenance,
  or linked-data interoperability profile.
- **IETF**: appropriate only if Atmanatic defines an Internet transport,
  exchange, or application-layer protocol with a clear networking scope.

### Research and implementation communities

- **Research Data Alliance**: research provenance, evidence exchange, and
  cross-implementation interoperability.
- **Linux Foundation / LF AI & Data**: neutral open-source ecosystem support
  and adoption among AI infrastructure projects.
- **MLCommons**: evaluation, benchmarking, reproducibility, and AI ecosystem
  interoperability.
- **ACM**: research publication, practitioner visibility, and scholarly
  discussion; not necessarily the long-term protocol host.
- **NIST**: research, policy, and AI risk-management alignment; generally a
  collaborator or reference point rather than the project's owner.

The Apache Software Foundation is a useful governance reference, but Apache-2.0
licensing does not imply ASF affiliation or endorsement.

## Recognition sequence

1. Stabilize the private implementation and protocol contracts.
2. Publish the signed first release and the Protocol 0.1 conformance package.
3. Demonstrate independent implementation results and consumer examples.
4. Prepare a concise standards and adoption brief that states scope, status,
   non-goals, governance needs, and evidence of interoperability.
5. Approach OASIS Open first, while engaging RDA, LF AI & Data, and MLCommons
   as implementation and adoption communities.
6. Reassess IEEE, W3C, and IETF after public review clarifies the protocol's
   concrete scope and deployment model.

## PyPI sequencing

The next PyPI step is **account setup and trusted-publisher configuration, not
publication**.

The package name `atmanatic-research` should be registered under a dedicated
project-maintainer identity. PyPI ownership means administrative control over
who may publish releases; it is separate from copyright, licensing, standards
recognition, and repository ownership.

GitHub Actions trusted publishing should be configured only after the first
release is ready. It should replace long-lived PyPI tokens and be restricted to
the intended repository, workflow, environment, and release context.

Before publication:

- confirm the package name remains available;
- establish the dedicated maintainer identity and recovery controls;
- prepare the first signed release and release assets;
- configure the PyPI trusted publisher for the release workflow;
- verify the package metadata, license, documentation links, and consumer
  installation path;
- perform a test publication only if the selected release process supports one;
- publish the first release deliberately and record its provenance.

No account registration, ownership claim, or package publication is authorized
by this note alone.
