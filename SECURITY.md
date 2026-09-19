# Security Policy

## Scope

This policy covers the `atmanatic-research` reference implementation, the
`validity_protocol` package, protocol schemas and fixtures, and GitHub Actions
workflows in this repository.

The project is a protocol core and validation library. It does not receive,
store, or authorize consumer credentials, transactions, deployments, or live
execution. Reports about a consumer system should identify the affected
consumer boundary as well as the Atmanatic component involved.

## Reporting a vulnerability

Please do not open a public issue for an undisclosed vulnerability. Use the
repository's **Security** tab to create a private vulnerability report or
GitHub Security Advisory. If private reporting is unavailable, contact the
repository owner through GitHub and include `SECURITY` in the subject.

Include the affected commit or release, security impact, reproducible steps or
a minimal proof of concept, required environment and configuration, and any
known mitigation or disclosure deadline. Do not include secrets, private keys,
personal data, or live consumer data.

## Response targets

- Acknowledgement: within 7 calendar days.
- Initial triage: within 14 calendar days.
- Remediation or a status update: within 30 calendar days when practical.

These are targets, not a guarantee. The project may request coordinated
disclosure and will credit reporters who want attribution.

## Supported versions

Only the latest tagged release and the current default branch receive security
triage. Consumers should upgrade to the latest release before requesting a
backport.

## Security boundaries

Validation success is bounded evidence about declared inputs. It is not a claim
of universal truth and does not grant execution authority. Vulnerabilities that
could cause malformed, stale, conflicting, unverifiable, or authority-claiming
artifacts to be accepted are security-relevant.
