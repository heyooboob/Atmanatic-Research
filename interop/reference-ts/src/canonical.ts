/** Canonical JSON serialization and content-hash projection, mirroring
 * atmanatic_research/canonical.py. Object keys are sorted, separators are
 * compact, and non-finite numbers are rejected. `content_hash` and
 * `signature` are excluded from the hashed projection.
 */

import { createHash } from "node:crypto";

const EXCLUDED_HASH_FIELDS = new Set(["content_hash", "signature"]);

export class CanonicalizationError extends Error {}

function checkFinite(value: unknown): void {
  if (typeof value === "number" && !Number.isFinite(value)) {
    throw new CanonicalizationError(
      "canonical JSON does not permit NaN or infinite numbers"
    );
  }
  if (Array.isArray(value)) {
    for (const item of value) checkFinite(item);
  } else if (value !== null && typeof value === "object") {
    for (const item of Object.values(value as Record<string, unknown>)) {
      checkFinite(item);
    }
  }
}

/** Serialize `value` with sorted object keys and compact separators, matching
 * the Python reference's `json.dumps(value, sort_keys=True, separators=(",", ":"))`.
 */
function canonicalStringify(value: unknown): string {
  if (value === null || typeof value === "boolean" || typeof value === "number") {
    return JSON.stringify(value);
  }
  if (typeof value === "string") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map(canonicalStringify).join(",")}]`;
  }
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    const keys = Object.keys(record).sort();
    const entries = keys.map(
      (key) => `${JSON.stringify(key)}:${canonicalStringify(record[key])}`
    );
    return `{${entries.join(",")}}`;
  }
  throw new CanonicalizationError(`cannot canonicalize value of type ${typeof value}`);
}

export function canonicalJsonBytes(value: unknown): Buffer {
  checkFinite(value);
  return Buffer.from(canonicalStringify(value), "utf-8");
}

export function projectForHash(
  record: Record<string, unknown>
): Record<string, unknown> {
  if (record === null || typeof record !== "object") {
    throw new CanonicalizationError("record must be an object");
  }
  const projected: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(record)) {
    if (!EXCLUDED_HASH_FIELDS.has(key)) projected[key] = value;
  }
  return projected;
}

export function computeContentHash(record: Record<string, unknown>): string {
  const projected = projectForHash(record);
  return createHash("sha256").update(canonicalJsonBytes(projected)).digest("hex");
}

export function verifyContentHash(record: Record<string, unknown>): boolean {
  const declared = record?.content_hash;
  if (typeof declared !== "string") return false;
  return declared.toLowerCase() === computeContentHash(record).toLowerCase();
}
