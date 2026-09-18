/** Unit tests for canonical JSON and content-hash behavior, independent of
 * the shared fixture corpus (which only checks accept/reject verdicts, not
 * byte-level canonicalization).
 */

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  CanonicalizationError,
  canonicalJsonBytes,
  computeContentHash,
  projectForHash,
  verifyContentHash,
} from "../src/canonical.js";

test("key order does not affect canonical bytes", () => {
  const first = canonicalJsonBytes({ b: 1, a: 2 });
  const second = canonicalJsonBytes({ a: 2, b: 1 });
  assert.deepEqual(first, second);
});

test("rejects non-finite numbers, including nested", () => {
  assert.throws(() => canonicalJsonBytes({ value: NaN }), CanonicalizationError);
  assert.throws(() => canonicalJsonBytes({ value: Infinity }), CanonicalizationError);
  assert.throws(
    () => canonicalJsonBytes({ outer: [{ inner: NaN }] }),
    CanonicalizationError
  );
});

test("content_hash and signature are excluded from the hash projection", () => {
  const record = { a: 1, content_hash: "stale", signature: "stale-sig" };
  assert.deepEqual(projectForHash(record), { a: 1 });
});

test("identical content produces an identical hash regardless of field order", () => {
  const first = { artifact_id: "a-1", producer: "agent", content_hash: "irrelevant" };
  const second = { content_hash: "different", producer: "agent", artifact_id: "a-1" };
  assert.equal(computeContentHash(first), computeContentHash(second));
});

test("verifyContentHash detects tampering", () => {
  const record: Record<string, unknown> = { artifact_id: "a-1", producer: "agent" };
  record.content_hash = computeContentHash(record);
  assert.equal(verifyContentHash(record), true);
  record.producer = "tampered-agent";
  assert.equal(verifyContentHash(record), false);
});

test("cross-language canonical hash parity fixture matches the shared expectation", () => {
  const here = dirname(fileURLToPath(import.meta.url));
  const fixturePath = join(here, "..", "..", "..", "fixtures", "canonical_hash_parity.json");
  const parity = JSON.parse(readFileSync(fixturePath, "utf-8"));
  assert.equal(computeContentHash(parity.record), parity.expected_sha256);
});
