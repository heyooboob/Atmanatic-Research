/** Stable machine-readable error codes shared by protocol validators.
 * Mirrors atmanatic_research/error_codes.py; this registry is protocol API,
 * not implementation-specific: additive changes only, never repurposed.
 */

export const MALFORMED_SYNTAX = "malformed_syntax";
export const UNSUPPORTED_VERSION = "unsupported_version";
export const UNSUPPORTED_CRITICAL_EXTENSION = "unsupported_critical_extension";
export const MISSING_OR_INVALID_FIELD = "missing_or_invalid_field";
export const HASH_MISMATCH = "hash_mismatch";
export const EXPIRED_OR_REVOKED = "expired_or_revoked";
export const UNRESOLVED_REFERENCE = "unresolved_reference";
export const SOURCE_POLICY_REJECTED = "source_policy_rejected";
export const EVIDENCE_CONFLICT = "evidence_conflict";
export const SELF_REVIEW_OR_UNRESOLVED = "self_review_or_unresolved";
export const INVALID_STATE_TRANSITION = "invalid_state_transition";
export const PROHIBITED_AUTHORITY_CLAIM = "prohibited_authority_claim";

export const ERROR_CODES: ReadonlySet<string> = new Set([
  MALFORMED_SYNTAX,
  UNSUPPORTED_VERSION,
  UNSUPPORTED_CRITICAL_EXTENSION,
  MISSING_OR_INVALID_FIELD,
  HASH_MISMATCH,
  EXPIRED_OR_REVOKED,
  UNRESOLVED_REFERENCE,
  SOURCE_POLICY_REJECTED,
  EVIDENCE_CONFLICT,
  SELF_REVIEW_OR_UNRESOLVED,
  INVALID_STATE_TRANSITION,
  PROHIBITED_AUTHORITY_CLAIM,
]);

/** Base contract violation carrying a stable machine-readable error code. */
export class ContractError extends Error {
  readonly code: string;

  constructor(message: string, code: string) {
    if (!ERROR_CODES.has(code)) {
      throw new Error(`unknown error code: ${code}`);
    }
    super(message);
    this.name = "ContractError";
    this.code = code;
  }
}
