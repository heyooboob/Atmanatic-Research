# Truth Validity Standard

This standard governs claims presented for human promotion. It establishes
bounded operational validity, not universal truth.

## Required packet

Every claim or slice must identify:

- scope and intended operating environment;
- direct observations and their timestamps;
- evidence references and provenance;
- falsification condition and counterclaim;
- uncertainty and known limitations;
- independent reviewer and challenge outcome;
- rollback path;
- expiry and revalidation policy.

## Validity levels

1. `observed`: directly measured but not independently checked.
2. `tested`: defined checks pass in a bounded environment.
3. `validated_in_scope`: behavior matches the acceptance contract under declared conditions.
4. `independently_verified`: a separate reviewer confirms the evidence and limitations.
5. `awaiting_human_promotion`: all gates pass, but no automatic authority is granted.
6. `promoted`: an explicit human approver accepts the bounded target and rollback plan.

No level means universally true. Expiry, drift, source changes, policy changes, or
material environment changes require revalidation.

## Anti-sycophancy rules

- The claim author cannot be its independent reviewer.
- A claim must include a falsifier, counterclaim, uncertainty statement, and resolved challenge.
- Advancement to an independently reviewed level requires a separate resolved
    review artifact whose subject hash matches the packet content hash.
- A claim declared measurable must identify its metric, comparison operator,
  threshold, unit, and observation window.
- Missing, stale, conflicting, or unverifiable evidence blocks readiness.
- Agreement is not evidence unless the sources are independently grounded.
- Unsupported certainty is treated as a failure condition.

## Authority boundary

The validity package is read-only and paper-only. Human approval is required for
promotion. No packet can grant signing, submission, live execution, or autonomous
authority.