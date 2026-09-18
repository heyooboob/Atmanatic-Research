import unittest

from atmanatic_research import (
    GraphAnalysisError,
    build_graph_analysis_artifact,
    build_graph_snapshot,
    personalized_pagerank,
    validate_graph_analysis_result,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _nodes():
    return [
        {"node_id": "claim-1", "node_type": "claim", "content_hash": HASH_A},
        {"node_id": "evidence-1", "node_type": "evidence_card", "content_hash": HASH_B},
        {"node_id": "evidence-2", "node_type": "evidence_card", "content_hash": HASH_C},
    ]


def _edges():
    return [
        {
            "edge_id": "edge-1",
            "relation_type": "supports",
            "source_id": "evidence-1",
            "target_id": "claim-1",
            "weight": 1.0,
        },
        {
            "edge_id": "edge-2",
            "relation_type": "supports",
            "source_id": "evidence-2",
            "target_id": "claim-1",
            "weight": 1.0,
        },
    ]


class GraphSnapshotTests(unittest.TestCase):
    def test_input_order_does_not_affect_snapshot_hash(self):
        nodes = _nodes()
        edges = _edges()
        forward = build_graph_snapshot(nodes, edges)
        backward = build_graph_snapshot(list(reversed(nodes)), list(reversed(edges)))
        self.assertEqual(forward.snapshot_hash, backward.snapshot_hash)

    def test_unknown_node_type_rejected(self):
        with self.assertRaises(GraphAnalysisError):
            build_graph_snapshot([{"node_id": "n1", "node_type": "bogus", "content_hash": HASH_A}], [])

    def test_unknown_relation_type_rejected(self):
        nodes = _nodes()
        with self.assertRaises(GraphAnalysisError):
            build_graph_snapshot(
                nodes,
                [
                    {
                        "edge_id": "edge-x",
                        "relation_type": "bogus",
                        "source_id": "evidence-1",
                        "target_id": "claim-1",
                    }
                ],
            )

    def test_duplicate_node_id_rejected(self):
        with self.assertRaises(GraphAnalysisError):
            build_graph_snapshot(_nodes() + _nodes()[:1], [])

    def test_edge_referencing_unknown_node_rejected(self):
        with self.assertRaises(GraphAnalysisError):
            build_graph_snapshot(
                _nodes(),
                [
                    {
                        "edge_id": "edge-x",
                        "relation_type": "supports",
                        "source_id": "missing-node",
                        "target_id": "claim-1",
                    }
                ],
            )

    def test_negative_and_non_finite_weights_rejected(self):
        for bad_weight in (-1.0, float("nan"), float("inf")):
            with self.subTest(weight=bad_weight):
                with self.assertRaises(GraphAnalysisError):
                    build_graph_snapshot(
                        _nodes(),
                        [
                            {
                                "edge_id": "edge-x",
                                "relation_type": "supports",
                                "source_id": "evidence-1",
                                "target_id": "claim-1",
                                "weight": bad_weight,
                            }
                        ],
                    )

    def test_duplicate_edge_id_with_different_content_rejected(self):
        edges = _edges()
        conflicting = dict(edges[0])
        conflicting["weight"] = 5.0
        with self.assertRaises(GraphAnalysisError):
            build_graph_snapshot(_nodes(), edges + [conflicting])


class PersonalizedPageRankTests(unittest.TestCase):
    def test_scores_are_finite_non_negative_and_ordered(self):
        snapshot = build_graph_snapshot(_nodes(), _edges())
        result = personalized_pagerank(snapshot, ["claim-1"])
        self.assertTrue(result.converged)
        scores = [entry["score"] for entry in result.ranked_nodes]
        self.assertTrue(all(score >= 0 for score in scores))
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_disconnected_graph_converges(self):
        nodes = [
            {"node_id": "a", "node_type": "claim", "content_hash": HASH_A},
            {"node_id": "b", "node_type": "claim", "content_hash": HASH_B},
        ]
        snapshot = build_graph_snapshot(nodes, [])
        result = personalized_pagerank(snapshot, ["a"])
        self.assertTrue(result.converged)

    def test_dangling_node_mass_redistributes_to_seed(self):
        # claim-1 has no outgoing edges (dangling); its mass must return to the seed.
        snapshot = build_graph_snapshot(_nodes(), _edges())
        result = personalized_pagerank(snapshot, ["claim-1"], max_iterations=500)
        total = sum(entry["score"] for entry in result.ranked_nodes)
        self.assertAlmostEqual(total, 1.0, places=6)

    def test_failure_to_converge_emits_structured_finding(self):
        snapshot = build_graph_snapshot(_nodes(), _edges())
        result = personalized_pagerank(snapshot, ["evidence-1"], max_iterations=1)
        self.assertFalse(result.converged)
        self.assertIn("not_converged", result.findings)

    def test_unknown_seed_node_rejected(self):
        snapshot = build_graph_snapshot(_nodes(), _edges())
        with self.assertRaises(GraphAnalysisError):
            personalized_pagerank(snapshot, ["missing-node"])

    def test_empty_seed_rejected(self):
        snapshot = build_graph_snapshot(_nodes(), _edges())
        with self.assertRaises(GraphAnalysisError):
            personalized_pagerank(snapshot, [])


class GraphAnalysisArtifactTests(unittest.TestCase):
    def test_artifact_round_trips_through_validator(self):
        snapshot = build_graph_snapshot(_nodes(), _edges())
        result = personalized_pagerank(snapshot, ["claim-1"])
        artifact = build_graph_analysis_artifact(
            artifact_id="graph-analysis-1",
            parent_artifact_ids=[],
            producer="graph-analysis-service",
            created_at="2026-09-18T12:00:00+00:00",
            snapshot=snapshot,
            seed_node_ids=["claim-1"],
            edge_types=["supports"],
            parameters={
                "damping_factor": 0.85,
                "convergence_tolerance": 1e-12,
                "max_iterations": 200,
                "dangling_node_policy": "redistribute_to_seed",
            },
            result=result,
            limitations=["Structural relevance is not truth, independence, or authority."],
        )
        validated = validate_graph_analysis_result(artifact)
        self.assertEqual(validated["execution_authorized"], False)

    def test_artifact_rejects_execution_authorized_true(self):
        record = {
            "schema_version": 1,
            "artifact_id": "graph-analysis-1",
            "producer": "graph-analysis-service",
            "execution_authorized": True,
            "analysis_kind": "personalized_pagerank",
            "graph_snapshot_hash": HASH_A,
            "configuration_hash": HASH_B,
            "content_hash": HASH_C,
            "seed_node_ids": ["claim-1"],
            "edge_types": ["supports"],
            "ranked_nodes": [],
            "limitations": ["note"],
        }
        with self.assertRaises(GraphAnalysisError):
            validate_graph_analysis_result(record)

    def test_out_of_order_ranked_nodes_rejected(self):
        record = {
            "schema_version": 1,
            "artifact_id": "graph-analysis-1",
            "producer": "graph-analysis-service",
            "execution_authorized": False,
            "analysis_kind": "personalized_pagerank",
            "graph_snapshot_hash": HASH_A,
            "configuration_hash": HASH_B,
            "content_hash": HASH_C,
            "seed_node_ids": ["claim-1"],
            "edge_types": ["supports"],
            "ranked_nodes": [
                {"node_id": "a", "score": 0.1},
                {"node_id": "b", "score": 0.9},
            ],
            "limitations": ["note"],
        }
        with self.assertRaises(GraphAnalysisError):
            validate_graph_analysis_result(record)

    def test_missing_limitations_rejected(self):
        record = {
            "schema_version": 1,
            "artifact_id": "graph-analysis-1",
            "producer": "graph-analysis-service",
            "execution_authorized": False,
            "analysis_kind": "personalized_pagerank",
            "graph_snapshot_hash": HASH_A,
            "configuration_hash": HASH_B,
            "content_hash": HASH_C,
            "seed_node_ids": ["claim-1"],
            "edge_types": ["supports"],
            "ranked_nodes": [],
            "limitations": [],
        }
        with self.assertRaises(GraphAnalysisError):
            validate_graph_analysis_result(record)


if __name__ == "__main__":
    unittest.main()
