/** Review outcome, verification result, and promotion record contracts,
 * mirroring the corresponding validators in
 * atmanatic_research/artifact_contracts.py.
 */

import {
  ArtifactContractError,
  baseLineage,
  nonEmptyString,
  sha256,
  stringList,
} from "./commonEnvelope.js";
import type { JsonRecord } from "./commonEnvelope.js";
import {
  MISSING_OR_INVALID_FIELD,
  PROHIBITED_AUTHORITY_CLAIM,
  SELF_REVIEW_OR_UNRESOLVED,
} from "../errorCodes.js";

const VERIFICATION_STATUSES = new Set(["verified", "failed", "timed_out", "not_evaluated"]);
const PROMOTION_STATUSES = new Set(["approved", "rejected", "expired", "revoked"]);
const REVIEW_OUTCOMES = new Set(["challenged_and_resolved", "rejected", "insufficient_evidence"]);

export function validateVerificationResult(
  value: unknown,
  supportedExtensions?: Iterable<string>
): JsonRecord {
  const record = baseLineage(value, supportedExtensions);
  nonEmptyString(record, "verifier_name");
  nonEmptyString(record, "verifier_version");
  sha256(record.input_artifact_hash, "input_artifact_hash");
  stringList(record, "specification_ids");
  if (!VERIFICATION_STATUSES.has(record.status as string)) {
    throw new ArtifactContractError(
      `status must be one of: ${[...VERIFICATION_STATUSES].sort().join(", ")}`,
      MISSING_OR_INVALID_FIELD
    );
  }
  const diagnostics = record.diagnostics ?? [];
  if (!Array.isArray(diagnostics) || !diagnostics.every((item) => typeof item === "string")) {
    throw new ArtifactContractError("diagnostics must be a list of strings", MISSING_OR_INVALID_FIELD);
  }
  const resourceUsage = record.resource_usage ?? {};
  if (resourceUsage === null || typeof resourceUsage !== "object" || Array.isArray(resourceUsage)) {
    throw new ArtifactContractError("resource_usage must be an object", MISSING_OR_INVALID_FIELD);
  }
  nonEmptyString(record, "environment_id");
  return record;
}

export function validatePromotionRecord(
  value: unknown,
  supportedExtensions?: Iterable<string>
): JsonRecord {
  const record = baseLineage(value, supportedExtensions);
  nonEmptyString(record, "approver");
  sha256(record.approved_artifact_hash, "approved_artifact_hash");
  nonEmptyString(record, "approved_scope");
  nonEmptyString(record, "approved_at");
  nonEmptyString(record, "rollback_target");
  if (!PROMOTION_STATUSES.has(record.status as string)) {
    throw new ArtifactContractError(
      `status must be one of: ${[...PROMOTION_STATUSES].sort().join(", ")}`,
      MISSING_OR_INVALID_FIELD
    );
  }
  if (record.status === "approved" && record.execution_authorized !== false) {
    throw new ArtifactContractError(
      "promotion records remain non-authorizing artifacts",
      PROHIBITED_AUTHORITY_CLAIM
    );
  }
  return record;
}

export function validateReviewOutcome(
  value: unknown,
  supportedExtensions?: Iterable<string>
): JsonRecord {
  const record = baseLineage(value, supportedExtensions);
  const reviewer = nonEmptyString(record, "reviewer");
  if (reviewer.trim().toLowerCase() === (record.producer as string).trim().toLowerCase()) {
    throw new ArtifactContractError("reviewer must be distinct from producer", SELF_REVIEW_OR_UNRESOLVED);
  }
  sha256(record.subject_artifact_hash, "subject_artifact_hash");
  stringList(record, "challenge_findings");
  if (!REVIEW_OUTCOMES.has(record.outcome as string)) {
    throw new ArtifactContractError(
      `outcome must be one of: ${[...REVIEW_OUTCOMES].sort().join(", ")}`,
      MISSING_OR_INVALID_FIELD
    );
  }
  if (record.outcome === "challenged_and_resolved" && !record.resolution) {
    throw new ArtifactContractError(
      "resolution is required for a resolved challenge",
      SELF_REVIEW_OR_UNRESOLVED
    );
  }
  if ("resolution" in record) nonEmptyString(record, "resolution");
  return record;
}
