/** Evidence card contract, mirroring atmanatic_research/evidence_contracts.py. */

import {
  ContractError,
  MALFORMED_SYNTAX,
  MISSING_OR_INVALID_FIELD,
} from "../errorCodes.js";
import { TimestampError, parseRfc3339 } from "../timestamps.js";
import type { JsonRecord } from "./commonEnvelope.js";

const REQUIRED_FIELDS = [
  "evidence_id",
  "claim",
  "source_ids",
  "agent",
  "observed_at",
  "confidence",
  "content_hash",
  "status",
  "details",
] as const;

export class EvidenceContractError extends ContractError {}

export function validateEvidenceCard(value: unknown): JsonRecord {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new EvidenceContractError("evidence card must be an object", MALFORMED_SYNTAX);
  }
  const card = value as JsonRecord;
  const missing = REQUIRED_FIELDS.filter((field) => !(field in card));
  if (missing.length > 0) {
    throw new EvidenceContractError(
      `evidence card is missing fields: ${missing.join(", ")}`,
      MISSING_OR_INVALID_FIELD
    );
  }
  if (typeof card.evidence_id !== "string" || card.evidence_id.trim() === "") {
    throw new EvidenceContractError("evidence_id must be a non-empty string", MISSING_OR_INVALID_FIELD);
  }
  if (typeof card.claim !== "string" || card.claim.trim() === "") {
    throw new EvidenceContractError("claim must be a non-empty string", MISSING_OR_INVALID_FIELD);
  }
  const sourceIds = card.source_ids;
  if (
    !Array.isArray(sourceIds) ||
    sourceIds.length === 0 ||
    !sourceIds.every((item) => typeof item === "string" && item.trim() !== "")
  ) {
    throw new EvidenceContractError(
      "source_ids must be a non-empty list of strings",
      MISSING_OR_INVALID_FIELD
    );
  }
  if (typeof card.agent !== "string" || card.agent.trim() === "") {
    throw new EvidenceContractError("agent must be a non-empty string", MISSING_OR_INVALID_FIELD);
  }
  try {
    parseRfc3339(card.observed_at, "observed_at");
  } catch (error) {
    if (error instanceof TimestampError) {
      throw new EvidenceContractError(error.message, MISSING_OR_INVALID_FIELD);
    }
    throw error;
  }
  if (
    typeof card.confidence !== "number" ||
    !Number.isFinite(card.confidence) ||
    card.confidence < 0 ||
    card.confidence > 1
  ) {
    throw new EvidenceContractError("confidence must be between 0 and 1", MISSING_OR_INVALID_FIELD);
  }
  if (typeof card.content_hash !== "string" || card.content_hash.trim() === "") {
    throw new EvidenceContractError("content_hash must be a non-empty string", MISSING_OR_INVALID_FIELD);
  }
  if (typeof card.status !== "string" || card.status.trim() === "") {
    throw new EvidenceContractError("status must be a non-empty string", MISSING_OR_INVALID_FIELD);
  }
  if (card.details === null || typeof card.details !== "object" || Array.isArray(card.details)) {
    throw new EvidenceContractError("details must be an object", MISSING_OR_INVALID_FIELD);
  }
  return card;
}
