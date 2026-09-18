/** CLI: runs the shared fixture corpus against this TypeScript implementation
 * and prints a JSON summary to stdout (verdict/code per case, plus the
 * canonical-hash-parity result). Used by interop/generate_report.py to build
 * the cross-implementation interoperability report; kept separate from
 * `test/fixtures.test.ts` so the report generator doesn't have to parse a
 * test-runner's output format.
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { ContractError } from "./errorCodes.js";
import { computeContentHash } from "./canonical.js";
import { validateArtifactLineage } from "./contracts/commonEnvelope.js";
import { validateEvidenceCard } from "./contracts/evidenceCard.js";
import { validateProposalEnvelope } from "./contracts/proposalEnvelope.js";
import {
  validatePromotionRecord,
  validateReviewOutcome,
  validateVerificationResult,
} from "./contracts/reviewAndPromotion.js";

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

function actualVerdict(validator: Validator, input: unknown): { verdict: string; code: string | null } {
  try {
    validator(input);
    return { verdict: "accept", code: null };
  } catch (error) {
    if (error instanceof ContractError) return { verdict: "reject", code: error.code };
    return { verdict: "reject", code: null };
  }
}

function main(): void {
  const manifest: ManifestEntry[] = JSON.parse(
    readFileSync(join(FIXTURES_DIR, "manifest.json"), "utf-8")
  );

  const results = manifest.map((entry) => {
    const fixture = JSON.parse(readFileSync(join(FIXTURES_DIR, entry.path), "utf-8"));
    const validator = VALIDATORS[fixture.artifact_type];
    const { verdict, code } = validator
      ? actualVerdict(validator, fixture.input)
      : { verdict: "unsupported", code: null };
    return {
      case_id: fixture.case_id,
      artifact_type: fixture.artifact_type,
      expected_verdict: fixture.expected.verdict,
      expected_code: fixture.expected.error_code ?? null,
      actual_verdict: verdict,
      actual_code: code,
    };
  });

  const parity = JSON.parse(
    readFileSync(join(FIXTURES_DIR, "canonical_hash_parity.json"), "utf-8")
  );
  const parityActual = computeContentHash(parity.record);

  process.stdout.write(
    JSON.stringify(
      {
        implementation: "typescript",
        node_version: process.version,
        results,
        canonical_hash_parity: {
          expected_sha256: parity.expected_sha256,
          actual_sha256: parityActual,
          matches: parityActual === parity.expected_sha256,
        },
      },
      null,
      2
    )
  );
}

main();
