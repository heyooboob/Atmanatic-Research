import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from atmanatic_research.truth_review import require_truth_review, review_claim  # noqa: E402


class TruthReviewTests(unittest.TestCase):
    def test_complete_claim_passes_adversarial_review(self):
        claim = {
            "claim": "The local evidence index is current.",
            "source_ids": ["source-1", "source-2"],
            "falsifier": "A source refresh exceeds its freshness window.",
            "counterclaim": "The index may contain a stale source despite a recent heartbeat.",
            "uncertainty": "Freshness is bounded to the observed source windows.",
            "author": "research-agent",
            "independent_reviewer": "review-agent",
            "review_outcome": "challenged_and_resolved",
        }
        self.assertTrue(review_claim(claim).admitted)
        self.assertIs(require_truth_review(claim), claim)

    def test_missing_challenge_fields_block_claim(self):
        result = review_claim({"claim": "Looks healthy", "source_ids": ["source-1"]})
        self.assertFalse(result.admitted)
        self.assertIn("claim has no falsification condition", result.reasons)
        self.assertIn("claim has no counterclaim", result.reasons)
        self.assertIn("claim has not passed adversarial review", result.reasons)

    def test_author_cannot_be_independent_reviewer(self):
        result = review_claim({
            "claim": "Observed",
            "source_ids": ["source-1"],
            "falsifier": "Contradictory observation",
            "counterclaim": "Could be stale",
            "uncertainty": "Limited sample",
            "author": "same-agent",
            "independent_reviewer": "same-agent",
            "review_outcome": "challenged_and_resolved",
        })
        self.assertFalse(result.admitted)
        self.assertIn("claim author cannot independently review the same claim", result.reasons)

    def test_measurable_falsifier_requires_complete_measurement_condition(self):
        claim = {
            "claim": "Source refresh latency remains below the decision window.",
            "source_ids": ["source-1"],
            "falsifier": "The p95 refresh latency exceeds 300 seconds over 24 hours.",
            "falsifier_kind": "measurable",
            "falsifier_measurement": {
                "metric": "source_refresh_latency_p95",
                "operator": ">",
                "threshold": 300,
                "unit": "seconds",
                "observation_window": "24 hours",
            },
            "counterclaim": "Burst load may cause refresh latency to exceed the window.",
            "uncertainty": "The observation excludes upstream outages.",
            "author": "research-agent",
            "independent_reviewer": "review-agent",
            "review_outcome": "challenged_and_resolved",
        }
        self.assertTrue(review_claim(claim).admitted)

        del claim["falsifier_measurement"]["observation_window"]
        result = review_claim(claim)
        self.assertFalse(result.admitted)
        self.assertIn(
            "falsifier_measurement is missing fields: observation_window",
            result.reasons,
        )

    def test_measurable_falsifier_rejects_invalid_operator_and_threshold(self):
        claim = {
            "claim": "Error rate is bounded.",
            "source_ids": ["source-1"],
            "falsifier": "The error rate exceeds the declared limit.",
            "falsifier_kind": "measurable",
            "falsifier_measurement": {
                "metric": "error_rate",
                "operator": "approximately",
                "threshold": "high",
                "unit": "percent",
                "observation_window": "100 requests",
            },
            "counterclaim": "The fixture may underrepresent failures.",
            "uncertainty": "Only the declared request window was observed.",
            "author": "research-agent",
            "independent_reviewer": "review-agent",
            "review_outcome": "challenged_and_resolved",
        }
        result = review_claim(claim)
        self.assertFalse(result.admitted)
        self.assertIn("falsifier_measurement operator is invalid", result.reasons)
        self.assertIn("falsifier_measurement threshold must be numeric", result.reasons)

        claim["falsifier_kind"] = ["measurable"]
        claim["falsifier_measurement"]["operator"] = [">"]
        result = review_claim(claim)
        self.assertFalse(result.admitted)
        self.assertIn("claim falsifier_kind must be qualitative or measurable", result.reasons)


if __name__ == "__main__":
    unittest.main()