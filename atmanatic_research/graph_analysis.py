"""Bounded, non-authorizing graph analysis for the optimization/memory layers.

See docs/architecture/eigenvector_graph_analysis.md for the full specification
and required boundary controls. Nothing in this module may influence evidence
admission, truth review, or validity advancement; scores are structural
relevance signals, not truth, independence, or authority.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import Any, Collection, Mapping

from .canonical import canonical_json_bytes, compute_content_hash
from .error_codes import (
    ContractError,
    MALFORMED_SYNTAX,
    MISSING_OR_INVALID_FIELD,
    PROHIBITED_AUTHORITY_CLAIM,
    UNRESOLVED_REFERENCE,
    UNSUPPORTED_VERSION,
)

GRAPH_ANALYSIS_SCHEMA_VERSION = 1
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")

NODE_TYPES = frozenset(
    {
        "source",
        "evidence_card",
        "claim",
        "proposal",
        "review_finding",
        "review_outcome",
        "artifact",
    }
)
RELATION_TYPES = frozenset(
    {"sourced_from", "supports", "challenges", "reviews", "derives_from", "responds_to"}
)
ANALYSIS_KINDS = frozenset({"personalized_pagerank"})


class GraphAnalysisError(ContractError):
    """Raised when a graph analysis input or artifact violates its contract."""


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: str
    content_hash: str
    attributes: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    relation_type: str
    source_id: str
    target_id: str
    weight: float
    source_record_hashes: tuple[str, ...] = ()


@dataclass(frozen=True)
class GraphSnapshot:
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    snapshot_hash: str


@dataclass(frozen=True)
class GraphAnalysisResult:
    ranked_nodes: tuple[dict[str, Any], ...]
    findings: tuple[str, ...]
    converged: bool
    iterations: int


def _require_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GraphAnalysisError(f"{name} must be a non-empty string", code=MISSING_OR_INVALID_FIELD)
    return value


def _require_hash(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise GraphAnalysisError(f"{name} must be a SHA-256 hex digest", code=MALFORMED_SYNTAX)
    return value.lower()


def _node_from_record(record: Any) -> GraphNode:
    if not isinstance(record, dict):
        raise GraphAnalysisError("node record must be an object", code=MALFORMED_SYNTAX)
    node_id = _require_str(record.get("node_id"), "node_id")
    node_type = record.get("node_type")
    if node_type not in NODE_TYPES:
        raise GraphAnalysisError(f"unknown node_type: {node_type!r}", code=MISSING_OR_INVALID_FIELD)
    content_hash = _require_hash(record.get("content_hash"), "content_hash")
    attributes = record.get("attributes", {})
    if not isinstance(attributes, dict):
        raise GraphAnalysisError("attributes must be an object", code=MISSING_OR_INVALID_FIELD)
    return GraphNode(node_id=node_id, node_type=node_type, content_hash=content_hash, attributes=dict(attributes))


def _edge_from_record(record: Any) -> GraphEdge:
    if not isinstance(record, dict):
        raise GraphAnalysisError("edge record must be an object", code=MALFORMED_SYNTAX)
    edge_id = _require_str(record.get("edge_id"), "edge_id")
    relation_type = record.get("relation_type")
    if relation_type not in RELATION_TYPES:
        raise GraphAnalysisError(f"unknown relation_type: {relation_type!r}", code=MISSING_OR_INVALID_FIELD)
    source_id = _require_str(record.get("source_id"), "source_id")
    target_id = _require_str(record.get("target_id"), "target_id")
    weight = record.get("weight", 1.0)
    if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not math.isfinite(weight) or weight < 0:
        raise GraphAnalysisError(
            f"edge '{edge_id}' weight must be a non-negative finite number", code=MISSING_OR_INVALID_FIELD
        )
    source_record_hashes = record.get("source_record_hashes", [])
    if not isinstance(source_record_hashes, list):
        raise GraphAnalysisError("source_record_hashes must be a list", code=MISSING_OR_INVALID_FIELD)
    hashes = tuple(_require_hash(item, "source_record_hashes item") for item in source_record_hashes)
    return GraphEdge(
        edge_id=edge_id,
        relation_type=relation_type,
        source_id=source_id,
        target_id=target_id,
        weight=float(weight),
        source_record_hashes=hashes,
    )


def _snapshot_projection(nodes: tuple[GraphNode, ...], edges: tuple[GraphEdge, ...]) -> dict[str, Any]:
    return {
        "nodes": [
            {
                "node_id": node.node_id,
                "node_type": node.node_type,
                "content_hash": node.content_hash,
                "attributes": node.attributes,
            }
            for node in nodes
        ],
        "edges": [
            {
                "edge_id": edge.edge_id,
                "relation_type": edge.relation_type,
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "weight": edge.weight,
                "source_record_hashes": list(edge.source_record_hashes),
            }
            for edge in edges
        ],
    }


def build_graph_snapshot(node_records: Collection[Any], edge_records: Collection[Any]) -> GraphSnapshot:
    """Validate raw node/edge records and return a canonically ordered, hashed snapshot.

    Input order never affects the result: nodes and edges are sorted by their
    stable identifiers before hashing and ranking.
    """
    nodes = [_node_from_record(record) for record in node_records]
    seen_node_ids: set[str] = set()
    for node in nodes:
        if node.node_id in seen_node_ids:
            raise GraphAnalysisError(f"duplicate node_id: {node.node_id}", code=MISSING_OR_INVALID_FIELD)
        seen_node_ids.add(node.node_id)

    edges = [_edge_from_record(record) for record in edge_records]
    seen_edges: dict[str, GraphEdge] = {}
    for edge in edges:
        existing = seen_edges.get(edge.edge_id)
        if existing is not None and existing != edge:
            raise GraphAnalysisError(
                f"duplicate edge_id with different content: {edge.edge_id}", code=MISSING_OR_INVALID_FIELD
            )
        seen_edges[edge.edge_id] = edge
    deduplicated_edges = list(seen_edges.values())

    for edge in deduplicated_edges:
        if edge.source_id not in seen_node_ids or edge.target_id not in seen_node_ids:
            raise GraphAnalysisError(
                f"edge '{edge.edge_id}' references an unknown node", code=UNRESOLVED_REFERENCE
            )

    ordered_nodes = tuple(sorted(nodes, key=lambda node: node.node_id))
    ordered_edges = tuple(sorted(deduplicated_edges, key=lambda edge: edge.edge_id))
    snapshot_hash = hashlib.sha256(
        canonical_json_bytes(_snapshot_projection(ordered_nodes, ordered_edges))
    ).hexdigest()
    return GraphSnapshot(nodes=ordered_nodes, edges=ordered_edges, snapshot_hash=snapshot_hash)


def personalized_pagerank(
    snapshot: GraphSnapshot,
    seed_node_ids: Collection[str],
    *,
    edge_types: Collection[str] | None = None,
    damping_factor: float = 0.85,
    tolerance: float = 1e-12,
    max_iterations: int = 200,
) -> GraphAnalysisResult:
    """Compute deterministic personalized PageRank scores over `snapshot`.

    Dangling nodes redistribute their mass to the seed distribution. Failure to
    converge within `max_iterations` emits a structured `not_converged` finding
    rather than a partial or silent success.
    """
    if not seed_node_ids:
        raise GraphAnalysisError("seed_node_ids must be a non-empty collection", code=MISSING_OR_INVALID_FIELD)
    if not 0.0 < damping_factor < 1.0:
        raise GraphAnalysisError("damping_factor must be strictly between 0 and 1", code=MISSING_OR_INVALID_FIELD)
    if max_iterations < 1:
        raise GraphAnalysisError("max_iterations must be a positive integer", code=MISSING_OR_INVALID_FIELD)

    allowed_relations = frozenset(edge_types) if edge_types is not None else RELATION_TYPES
    unknown_relations = allowed_relations - RELATION_TYPES
    if unknown_relations:
        raise GraphAnalysisError(
            f"unknown edge_types: {sorted(unknown_relations)}", code=MISSING_OR_INVALID_FIELD
        )

    node_ids = [node.node_id for node in snapshot.nodes]
    node_index = {node_id: index for index, node_id in enumerate(node_ids)}
    seed_ids = list(dict.fromkeys(seed_node_ids))
    for seed_id in seed_ids:
        if seed_id not in node_index:
            raise GraphAnalysisError(
                f"seed node '{seed_id}' is not present in the snapshot", code=UNRESOLVED_REFERENCE
            )

    node_count = len(node_ids)
    seed_vector = [0.0] * node_count
    seed_weight = 1.0 / len(seed_ids)
    for seed_id in seed_ids:
        seed_vector[node_index[seed_id]] += seed_weight

    outgoing: list[list[tuple[int, float]]] = [[] for _ in range(node_count)]
    out_totals = [0.0] * node_count
    for edge in snapshot.edges:
        if edge.relation_type not in allowed_relations:
            continue
        source_index = node_index[edge.source_id]
        target_index = node_index[edge.target_id]
        outgoing[source_index].append((target_index, edge.weight))
        out_totals[source_index] += edge.weight

    normalized = [
        [(target, weight / out_totals[source]) for target, weight in outgoing[source]]
        if out_totals[source] > 0
        else []
        for source in range(node_count)
    ]
    dangling_indices = [source for source in range(node_count) if out_totals[source] <= 0]

    scores = list(seed_vector)
    converged = False
    iterations_used = 0
    for iteration in range(1, max_iterations + 1):
        iterations_used = iteration
        next_scores = [0.0] * node_count
        dangling_mass = sum(scores[source] for source in dangling_indices)
        for source in range(node_count):
            contribution = scores[source]
            if contribution == 0.0:
                continue
            for target, share in normalized[source]:
                next_scores[target] += damping_factor * contribution * share
        for index in range(node_count):
            next_scores[index] += damping_factor * dangling_mass * seed_vector[index]
            next_scores[index] += (1.0 - damping_factor) * seed_vector[index]
        residual = sum(abs(next_scores[index] - scores[index]) for index in range(node_count))
        scores = next_scores
        if residual < tolerance:
            converged = True
            break

    findings: list[str] = [] if converged else ["not_converged"]
    ranked = sorted(
        ({"node_id": node_ids[index], "score": scores[index]} for index in range(node_count)),
        key=lambda entry: (-entry["score"], entry["node_id"]),
    )
    return GraphAnalysisResult(
        ranked_nodes=tuple(ranked), findings=tuple(findings), converged=converged, iterations=iterations_used
    )


def build_graph_analysis_artifact(
    *,
    artifact_id: str,
    parent_artifact_ids: Collection[str],
    producer: str,
    created_at: str,
    snapshot: GraphSnapshot,
    seed_node_ids: Collection[str],
    edge_types: Collection[str],
    parameters: Mapping[str, Any],
    result: GraphAnalysisResult,
    limitations: Collection[str],
    algorithm_version: str = "1.0.0",
    analysis_kind: str = "personalized_pagerank",
) -> dict[str, Any]:
    """Assemble the versioned, non-authorizing graph-analysis artifact."""
    configuration_hash = hashlib.sha256(canonical_json_bytes(dict(parameters))).hexdigest()
    record: dict[str, Any] = {
        "schema_version": GRAPH_ANALYSIS_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "parent_artifact_ids": list(parent_artifact_ids),
        "producer": producer,
        "created_at": created_at,
        "execution_authorized": False,
        "analysis_kind": analysis_kind,
        "algorithm_version": algorithm_version,
        "graph_snapshot_hash": snapshot.snapshot_hash,
        "configuration_hash": configuration_hash,
        "seed_node_ids": list(dict.fromkeys(seed_node_ids)),
        "edge_types": sorted(set(edge_types)),
        "parameters": dict(parameters),
        "ranked_nodes": [dict(entry) for entry in result.ranked_nodes],
        "findings": list(result.findings),
        "limitations": list(limitations),
    }
    record["content_hash"] = compute_content_hash(record)
    return record


def validate_graph_analysis_result(record: dict[str, Any]) -> dict[str, Any]:
    """Validate a graph-analysis artifact per its non-authorizing artifact contract."""
    if not isinstance(record, dict):
        raise GraphAnalysisError("graph analysis artifact must be an object", code=MALFORMED_SYNTAX)
    if record.get("schema_version") != GRAPH_ANALYSIS_SCHEMA_VERSION:
        raise GraphAnalysisError(
            f"schema_version must be {GRAPH_ANALYSIS_SCHEMA_VERSION}", code=UNSUPPORTED_VERSION
        )
    for field_name in ("artifact_id", "producer"):
        if not isinstance(record.get(field_name), str) or not record[field_name].strip():
            raise GraphAnalysisError(f"{field_name} must be a non-empty string", code=MISSING_OR_INVALID_FIELD)
    if record.get("execution_authorized") is not False:
        raise GraphAnalysisError("execution_authorized must be false", code=PROHIBITED_AUTHORITY_CLAIM)
    if record.get("analysis_kind") not in ANALYSIS_KINDS:
        raise GraphAnalysisError("unknown analysis_kind", code=MISSING_OR_INVALID_FIELD)
    _require_hash(record.get("graph_snapshot_hash"), "graph_snapshot_hash")
    _require_hash(record.get("configuration_hash"), "configuration_hash")
    _require_hash(record.get("content_hash"), "content_hash")

    seeds = record.get("seed_node_ids")
    if not isinstance(seeds, list) or not seeds or len(seeds) != len(set(seeds)):
        raise GraphAnalysisError(
            "seed_node_ids must be a non-empty list of unique strings", code=MISSING_OR_INVALID_FIELD
        )

    edge_types_declared = record.get("edge_types")
    if not isinstance(edge_types_declared, list) or not all(
        relation in RELATION_TYPES for relation in edge_types_declared
    ):
        raise GraphAnalysisError("edge_types must contain known relation types", code=MISSING_OR_INVALID_FIELD)

    ranked_nodes = record.get("ranked_nodes")
    if not isinstance(ranked_nodes, list):
        raise GraphAnalysisError("ranked_nodes must be a list", code=MISSING_OR_INVALID_FIELD)
    seen_ids: set[str] = set()
    previous_key: tuple[float, str] | None = None
    for entry in ranked_nodes:
        if not isinstance(entry, dict):
            raise GraphAnalysisError("each ranked node entry must be an object", code=MALFORMED_SYNTAX)
        node_id = entry.get("node_id")
        if not isinstance(node_id, str) or not node_id.strip():
            raise GraphAnalysisError("ranked node_id must be a non-empty string", code=MISSING_OR_INVALID_FIELD)
        if node_id in seen_ids:
            raise GraphAnalysisError(f"duplicate ranked node_id: {node_id}", code=MISSING_OR_INVALID_FIELD)
        seen_ids.add(node_id)
        score = entry.get("score")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or score < 0:
            raise GraphAnalysisError(
                f"ranked node '{node_id}' score must be a finite non-negative number",
                code=MISSING_OR_INVALID_FIELD,
            )
        key = (-float(score), node_id)
        if previous_key is not None and key < previous_key:
            raise GraphAnalysisError(
                "ranked_nodes must be ordered by descending score then ascending node_id",
                code=MISSING_OR_INVALID_FIELD,
            )
        previous_key = key

    limitations = record.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise GraphAnalysisError(
            "limitations must be a non-empty list of strings", code=MISSING_OR_INVALID_FIELD
        )

    findings = record.get("findings", [])
    if not isinstance(findings, list) or not all(isinstance(item, str) for item in findings):
        raise GraphAnalysisError("findings must be a list of strings", code=MISSING_OR_INVALID_FIELD)

    return record
