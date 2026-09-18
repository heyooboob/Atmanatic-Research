/** Runs the shared interop fixture corpus against this TypeScript
 * implementation and asserts it reproduces the same verdict and error code
 * as the Python reference implementation for every fixture.
 *
 * This is the TypeScript half of the bidirectional interoperability harness
 * described in interop/README.md. It reads the same
 * interop/fixtures/manifest.json the Python side reads; neither side owns
 * the fixtures, both sides are graded against them.
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import assert from "node:assert/strict";

import { ContractError } from "../src/errorCodes.js";
import { validateArtifactLineage } from "../src/contracts/commonEnvelope.js";
import { validateEvidenceCard } from "../src/contracts/evidenceCard.js";
import { validateProposalEnvelope } from "../src/contracts/proposalEnvelope.js";
import {
  validatePromotionRecord,
  validateReviewOutcome,
  validateVerificationResult,
} from "../src/contracts/reviewAndPromotion.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const INTEROP_ROOT = join(HERE, "..", "..", "..");
const FIXTURES_DIR = join(INTEROP_ROOT, "fixtures");

type Validator = (value: unknown) => unknown;

const VALIDATORS: Record<string, Validator> = {
  artifact_lineage: validateArtifactLineage,
  evidence_card: validateEvidenceCard,
  proposal_envelope: validateProposalEnvelope,
  review_outcome: validateReviewOutcome,
  verification_result: validateVerificationResult,
  promotion_record: validatePromotionRecord,
};

interface ManifestEntry {
  artifact_type: string;
  case_id: string;
  path: string;
}

interface Fixture {
  case_id: string;
  artifact_type: string;
  description: string;
  input: unknown;
  expected: { verdict: "accept" | "reject"; error_code?: string | null };
}

function actualVerdict(validator: Validator, input: unknown): { verdict: string; code: string | null } {
  try {
    validator(input);
    return { verdict: "accept", code: null };
  } catch (error) {
    if (error instanceof ContractError) {
      return { verdict: "reject", code: error.code };
    }
    // Non-ContractError failures still count as a rejection, matching the
    // Python harness's `except ValueError` fallback, but carry no code.
    return { verdict: "reject", code: null };
  }
}

const manifest: ManifestEntry[] = JSON.parse(
  readFileSync(join(FIXTURES_DIR, "manifest.json"), "utf-8")
);

test("interop fixture corpus", async (t) => {
  assert.ok(manifest.length > 0, "manifest must not be empty");
  for (const entry of manifest) {
    await t.test(`${entry.artifact_type}/${entry.case_id}`, () => {
      const fixture: Fixture = JSON.parse(
        readFileSync(join(FIXTURES_DIR, entry.path), "utf-8")
      );
      const validator = VALIDATORS[fixture.artifact_type];
      assert.ok(validator, `no TypeScript validator registered for '${fixture.artifact_type}'`);

      const { verdict, code } = actualVerdict(validator, fixture.input);
      assert.equal(
        verdict,
        fixture.expected.verdict,
        `case '${fixture.case_id}': expected verdict '${fixture.expected.verdict}' but got '${verdict}'`
      );
      if (fixture.expected.verdict === "reject" && fixture.expected.error_code) {
        assert.equal(
          code,
          fixture.expected.error_code,
          `case '${fixture.case_id}': expected error_code '${fixture.expected.error_code}' but got '${code}'`
        );
      }
    });
  }
});
