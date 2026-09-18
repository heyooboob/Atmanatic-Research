/** Common artifact envelope validation, mirroring
 * atmanatic_research/artifact_contracts.py's `_base_lineage`.
 */

import {
  ContractError,
  MALFORMED_SYNTAX,
  MISSING_OR_INVALID_FIELD,
  PROHIBITED_AUTHORITY_CLAIM,
  UNSUPPORTED_CRITICAL_EXTENSION,
  UNSUPPORTED_VERSION,
} from "../errorCodes.js";
import { TimestampError, parseRfc3339 } from "../timestamps.js";

export const ARTIFACT_SCHEMA_VERSION = 1;
const SHA256 = /^[0-9a-fA-F]{64}$/;

export class ArtifactContractError extends ContractError {}

export type JsonRecord = Record<string, unknown>;

function asObject(value: unknown, name: string): JsonRecord {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new ArtifactContractError(`${name} must be an object`, MALFORMED_SYNTAX);
  }
  return value as JsonRecord;
}

function nonEmptyString(record: JsonRecord, key: string, name?: string): string {
  const value = record[key];
  if (typeof value !== "string" || value.trim() === "") {
    throw new ArtifactContractError(
      `${name ?? key} must be a non-empty string`,
      MISSING_OR_INVALID_FIELD
    );
  }
  return value;
}

function timestamp(value: unknown, key: string): void {
  try {
    parseRfc3339(value, key);
  } catch (error) {
    if (error instanceof TimestampError) {
      throw new ArtifactContractError(error.message, MISSING_OR_INVALID_FIELD);
    }
    throw error;
  }
}

function sha256(value: unknown, key: string): void {
  if (typeof value !== "string" || !SHA256.test(value)) {
    throw new ArtifactContractError(`${key} must be a SHA-256 hex digest`, MALFORMED_SYNTAX);
  }
}

function stringList(record: JsonRecord, key: string, required = true): string[] {
  const value = record[key];
  if (!Array.isArray(value) || (required && value.length === 0)) {
    throw new ArtifactContractError(
      `${key} must be a non-empty list of strings`,
      MISSING_OR_INVALID_FIELD
    );
  }
  if (!value.every((item) => typeof item === "string" && item.trim() !== "")) {
    throw new ArtifactContractError(`${key} must contain non-empty strings`, MISSING_OR_INVALID_FIELD);
  }
  return value as string[];
}

function extensions(record: JsonRecord, supportedExtensions?: Iterable<string>): void {
  const ext = record.extensions;
  const critical = (record.critical_extensions as unknown) ?? [];
  if (ext === undefined && Array.isArray(critical) && critical.length === 0) return;
  if (ext !== undefined && (ext === null || typeof ext !== "object" || Array.isArray(ext))) {
    throw new ArtifactContractError("extensions must be an object", MALFORMED_SYNTAX);
  }
  if (
    !Array.isArray(critical) ||
    !critical.every((item) => typeof item === "string" && item.trim() !== "")
  ) {
    throw new ArtifactContractError(
      "critical_extensions must be a list of strings",
      MISSING_OR_INVALID_FIELD
    );
  }
  const extObject = (ext ?? {}) as JsonRecord;
  const allowed = new Set(supportedExtensions ?? []);
  for (const key of critical as string[]) {
    if (!(key in extObject)) {
      throw new ArtifactContractError(
        `critical extension '${key}' is not declared in extensions`,
        MISSING_OR_INVALID_FIELD
      );
    }
    if (!allowed.has(key)) {
      throw new ArtifactContractError(
        `critical extension '${key}' is not supported by this implementation`,
        UNSUPPORTED_CRITICAL_EXTENSION
      );
    }
  }
}

export function baseLineage(
  value: unknown,
  supportedExtensions?: Iterable<string>
): JsonRecord {
  const record = asObject(value, "artifact");
  if (record.schema_version !== ARTIFACT_SCHEMA_VERSION) {
    throw new ArtifactContractError(
      `schema_version must be ${ARTIFACT_SCHEMA_VERSION}`,
      UNSUPPORTED_VERSION
    );
  }
  nonEmptyString(record, "artifact_id");
  stringList(record, "parent_artifact_ids", false);
  nonEmptyString(record, "producer");
  timestamp(record.created_at, "created_at");
  sha256(record.content_hash, "content_hash");
  if (record.execution_authorized !== false) {
    throw new ArtifactContractError(
      "execution_authorized must be false",
      PROHIBITED_AUTHORITY_CLAIM
    );
  }
  if ("processor_version" in record) nonEmptyString(record, "processor_version");
  if ("expires_at" in record) timestamp(record.expires_at, "expires_at");
  if ("revalidation_policy" in record) nonEmptyString(record, "revalidation_policy");
  extensions(record, supportedExtensions);
  return record;
}

export function validateArtifactLineage(
  value: unknown,
  supportedExtensions?: Iterable<string>
): JsonRecord {
  return baseLineage(value, supportedExtensions);
}

export { nonEmptyString, sha256, stringList, timestamp, asObject };
