/** Proposal envelope contract, mirroring atmanatic_research/proposal_contracts.py. */

import {
  ContractError,
  MALFORMED_SYNTAX,
  MISSING_OR_INVALID_FIELD,
  PROHIBITED_AUTHORITY_CLAIM,
  UNSUPPORTED_VERSION,
} from "../errorCodes.js";
import { TimestampError, parseRfc3339 } from "../timestamps.js";
import type { JsonRecord } from "./commonEnvelope.js";

export const PROPOSAL_SCHEMA_VERSION = 1;
const SHA256 = /^[0-9a-fA-F]{64}$/;

export class ProposalContractError extends ContractError {}

function nonEmptyString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.trim() === "") {
    throw new ProposalContractError(`${field} must be a non-empty string`, MISSING_OR_INVALID_FIELD);
  }
  return value;
}

export function validateProposalEnvelope(value: unknown): JsonRecord {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new ProposalContractError("proposal envelope must be an object", MALFORMED_SYNTAX);
  }
  const record = value as JsonRecord;
  if (record.schema_version !== PROPOSAL_SCHEMA_VERSION) {
    throw new ProposalContractError(
      `schema_version must be ${PROPOSAL_SCHEMA_VERSION}`,
      UNSUPPORTED_VERSION
    );
  }
  const proposalId = nonEmptyString(record.proposal_id, "proposal_id");
  const parentProposalId = record.parent_proposal_id;
  if (parentProposalId !== null && parentProposalId !== undefined) {
    const parent = nonEmptyString(parentProposalId, "parent_proposal_id");
    if (parent === proposalId) {
      throw new ProposalContractError(
        "parent_proposal_id must differ from proposal_id",
        MISSING_OR_INVALID_FIELD
      );
    }
  }
  nonEmptyString(record.producer, "producer");
  const createdAt = nonEmptyString(record.created_at, "created_at");
  try {
    parseRfc3339(createdAt, "created_at");
  } catch (error) {
    if (error instanceof TimestampError) {
      throw new ProposalContractError(error.message, MISSING_OR_INVALID_FIELD);
    }
    throw error;
  }
  const contentHash = nonEmptyString(record.content_hash, "content_hash");
  if (!SHA256.test(contentHash)) {
    throw new ProposalContractError("content_hash must be a SHA-256 hex digest", MALFORMED_SYNTAX);
  }

  const evidenceRefs = record.evidence_refs;
  if (
    !Array.isArray(evidenceRefs) ||
    evidenceRefs.length === 0 ||
    !evidenceRefs.every((item) => typeof item === "string" && item.trim() !== "")
  ) {
    throw new ProposalContractError(
      "evidence_refs must be a non-empty list of strings",
      MISSING_OR_INVALID_FIELD
    );
  }
  if (new Set(evidenceRefs).size !== evidenceRefs.length) {
    throw new ProposalContractError("evidence_refs must be unique", MISSING_OR_INVALID_FIELD);
  }
  const toolVersions = record.tool_versions;
  if (
    toolVersions === null ||
    typeof toolVersions !== "object" ||
    Array.isArray(toolVersions) ||
    Object.keys(toolVersions).length === 0 ||
    !Object.entries(toolVersions as JsonRecord).every(
      ([name, version]) =>
        name.trim() !== "" && typeof version === "string" && version.trim() !== ""
    )
  ) {
    throw new ProposalContractError(
      "tool_versions must be a non-empty mapping of names to versions",
      MISSING_OR_INVALID_FIELD
    );
  }
  const payload = record.payload;
  if (
    payload === null ||
    typeof payload !== "object" ||
    Array.isArray(payload) ||
    Object.keys(payload).length === 0
  ) {
    throw new ProposalContractError("payload must be a non-empty object", MISSING_OR_INVALID_FIELD);
  }
  if (record.execution_authorized !== false) {
    throw new ProposalContractError("execution_authorized must be false", PROHIBITED_AUTHORITY_CLAIM);
  }
  return record;
}
