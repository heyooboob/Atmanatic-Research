# Eigenvector Graph Analysis

## Purpose

This guide defines a bounded graph-analysis capability for Atmanatic Research.
It uses eigenvector-derived methods to improve retrieval, workload ordering, and
provenance inspection. It does not measure truth, increase evidence confidence,
admit evidence, advance validity, or authorize an action.

The capability belongs to the optimization and memory layers. Verification and
authority layers consume its output only as non-binding context.

Shared definitions and cross-cutting implementation boundaries are maintained
in the [Mathematical Principles](../foundations/mathematical_principles.md)
glossary.

## Architectural Rule

Graph analysis MAY identify relevant artifacts, review priorities, source
concentration, and unusual provenance clusters. It MUST NOT decide whether a
claim is true, a source is authoritative, evidence is admitted, a packet may
advance, or an action may execute.

A high score means that a node has a declared structural relationship to other
nodes in the selected graph. It does not mean that the node is correct,
independent, safe, or trustworthy.

## Graph Model

Represent a snapshot as a directed, typed graph $G = (V, E)$. Each node has a
stable identifier, type, content hash, and declared attributes. Each edge has a
stable identifier, relation type, direction, optional non-negative weight, and
the hashes of the records from which it was derived.

Initial node types SHOULD map directly to repository concepts:

- `source`
- `evidence_card`
- `claim`
- `proposal`
- `review_finding`
- `review_outcome`
- `artifact`

Initial relation types SHOULD remain narrow and explicit:

- `sourced_from`: evidence card to source
- `supports`: evidence card to claim
- `challenges`: review finding or counterclaim to claim
- `reviews`: review outcome to artifact
- `derives_from`: child artifact or proposal to parent artifact
- `responds_to`: revised proposal to review finding

Do not infer an edge merely because two texts are similar. A derived edge MUST
have a declared rule, processor version, and source-record hashes. Semantic
similarity may be a separate, explicitly labelled retrieval-only edge type only
after its model and threshold are recorded.

## Methods

### Eigenvector Centrality

Given a non-negative adjacency matrix $A$, eigenvector centrality finds $x$ such
that:

$$
Ax = \lambda x
$$

Each score depends on the scores of neighboring nodes. This detects structural
connectedness, but it is unsuitable for trust: a circular cluster can assign
itself high scores without independent evidence.

Use raw eigenvector centrality only for offline diagnostics on a connected,
carefully defined graph. Do not use it as the default runtime ranker. It can be
misleading for disconnected graphs, periodic directed graphs, and graphs with
multiple dominant components.

### Personalized PageRank

Use personalized PageRank as the default relevance ranker:

$$
p = \alpha P^T p + (1 - \alpha)s
$$

Here, $P$ is a normalized transition matrix, $s$ is a declared seed vector, and
$\alpha$ is a damping factor in $(0, 1)$. The seed vector makes the result
relevant to a particular question, claim, or evidence set. Damping ensures
convergence and finite scores for sparse or disconnected graphs.

### HITS and Spectral Clustering

HITS computes hub and authority vectors:

$$
a = A^T h, \qquad h = Aa
$$

It can inspect support patterns in a bipartite evidence-to-claim graph. Never
expose its `authority` score as source authority or validity; name it
`support_structure_score` and use it only for inspection.

Spectral clustering uses eigenvectors of the graph Laplacian $L = D - A$ to
identify communities. Use it to batch related research, find duplicate inquiry
paths, or identify evidence islands lacking cross-group corroboration. It does
not classify truth, source quality, or reviewer independence.

## Best Use Cases

### Query-Bounded Evidence Retrieval

1. Build a graph from admitted, non-expired records visible to the caller's
   policy scope.
2. Seed PageRank from the requested question, proposal, claim, or evidence IDs.
3. Permit only declared retrieval edge types such as `sourced_from`, `supports`,
   `reviews`, and `derives_from`.
4. Return top nodes with explanatory edge paths and the graph snapshot hash.
5. Treat results as candidates; run normal evidence, review, and validity checks.

Use this when a reviewer needs bounded, connected context without replaying all
historical artifacts.

### Review Queue Prioritization

1. Build a dependency graph from `derives_from`, `supports`, `challenges`, and
   `responds_to` edges.
2. Compute deterministic downstream-impact count and separate PageRank seeded
   from unresolved findings.
3. Sort by severity, impact count, rank, then stable identifier.
4. Store each component value rather than collapsing them into one opaque score.

Use this when unresolved findings affect many derived artifacts.

### Provenance Concentration Detection

1. Collect a claim's supporting evidence and sources.
2. Group sources by existing `independence_group` metadata.
3. Calculate the Herfindahl concentration index:

$$
H = \sum_{g \in groups} q_g^2
$$

where $q_g$ is a group's fraction of supporting sources or weighted support.
4. Emit a non-binding provenance warning above a declared threshold.
5. Route the warning to a provenance auditor; never change source tiers,
   confidence, or admission results.

Use this to reveal apparent corroboration that traces to one organization or
data origin.

### Citation-Ring Inspection

1. Detect strongly connected components over a fixed time window.
2. Compare each component's internal-edge share with external support and
   independence-group diversity.
3. Emit an explainable warning listing members, edge counts, group counts, and
   snapshot hash.
4. Require inspection of original evidence. The warning has no favorable or
   adverse validity effect by itself.

## Required Boundary Controls

### Input Eligibility

The graph builder MUST validate each input record with its existing contract;
accept only declared IDs and relation types; exclude expired records unless a
historical replay explicitly requests them; and preserve conflicting records as
separate nodes while emitting a build warning.

It MUST reject unknown node or edge types, negative or non-finite weights,
duplicate edge IDs with different content, and malformed hashes. It MUST NOT
create evidence, change `confidence` or `status`, or write to a validity packet.

### Determinism and Replay

- Sort nodes and edges by stable ID before matrix construction.
- Record one edge-direction convention.
- Redistribute dangling-node mass to the seed distribution for PageRank.
- Record fixed iteration limit, convergence tolerance, and any random seed.
- Hash canonical graph snapshot and canonical configuration separately.
- Serialize output in descending score then ascending node-ID order.

### Governing Isolation

No function in `evidence_admission.py`, `truth_review.py`,
`validity_governance.py`, or `validity_protocol` may accept a graph score that
changes pass/fail behavior. Orchestration may place results in reviewer context,
but findings must still cite ordinary `evidence_refs`. A graph result is an audit
aid, not evidence in itself.

## Proposed Analysis Artifact

Implement results as a new versioned, non-authorizing artifact in
`atmanatic_research/graph_analysis.py`, using existing artifact conventions.

```json
{
  "schema_version": 1,
  "artifact_id": "graph-analysis-20260918-001",
  "parent_artifact_ids": ["proposal-042"],
  "producer": "graph-analysis-service",
  "created_at": "2026-09-18T12:00:00Z",
  "content_hash": "<sha256 of canonical artifact content>",
  "execution_authorized": false,
  "analysis_kind": "personalized_pagerank",
  "algorithm_version": "1.0.0",
  "graph_snapshot_hash": "<sha256 of canonical graph snapshot>",
  "configuration_hash": "<sha256 of canonical configuration>",
  "seed_node_ids": ["claim-001"],
  "edge_types": ["sourced_from", "supports", "reviews", "derives_from"],
  "parameters": {
    "damping_factor": 0.85,
    "convergence_tolerance": 1e-12,
    "max_iterations": 200,
    "dangling_node_policy": "redistribute_to_seed"
  },
  "ranked_nodes": [
    {
      "node_id": "evidence-019",
      "node_type": "evidence_card",
      "score": 0.123456789012,
      "explanation_edge_ids": ["edge-013", "edge-092"]
    }
  ],
  "findings": [],
  "limitations": ["Structural relevance is not truth, independence, or authority."]
}
```

The validator MUST require non-empty unique seed and ranked IDs; finite,
non-negative scores; order consistent with serialization; SHA-256 hashes; known
analysis and edge types; an explicit limitation; and `execution_authorized`
exactly `false`.

## Implementation Plan

### Phase 1: Pure Graph Construction

1. Add immutable `GraphNode`, `GraphEdge`, `GraphSnapshot`, and
   `GraphAnalysisResult` dataclasses in `graph_analysis.py`.
2. Implement a pure builder that accepts validated records and explicit relation
   declarations, then returns a canonically ordered snapshot.
3. Implement canonical JSON hashing with sorted object keys and stable array
   order. Do not hash Python object representations.
4. Add a graph validator that rejects malformed or ambiguous input before rank
   calculation.

### Phase 2: Personalized PageRank

1. Implement PageRank without a dependency unless scale justifies a vetted
   numerical library.
2. Normalize outgoing edge weights and reject invalid totals rather than produce
   `NaN`.
3. Redistribute dangling mass to the normalized seed vector.
4. Stop at declared $L_1$ residual tolerance, or emit structured `not_converged`
   finding at the fixed iteration limit.
5. Sort results by descending score, then ascending node ID.

### Phase 3: Audit Findings and Integration

1. Add independence-group concentration and strongly connected-component checks.
2. Version every warning rule and threshold in artifact configuration.
3. Project findings only as reviewer context or `provenance_auditor` prompts.
4. Add a disabled-by-default, caller-owned retrieval adapter. Do not invoke it
   from evidence admission or validity transition code.
5. Record runtime, graph size, convergence, and warning telemetry without
   collecting credentials or private identity values.

## Required Tests

Add `tests/test_graph_analysis.py` covering:

- identical canonical inputs produce identical hashes and ranks;
- input node and edge order cannot affect output;
- disconnected graphs converge under personalized PageRank;
- dangling nodes follow declared redistribution;
- invalid weights, `NaN`, infinity, unknown types, conflicting IDs, and unknown
  nodes are rejected with specific reasons;
- scores are finite, non-negative, and deterministically ordered;
- the artifact rejects `execution_authorized: true`;
- changing a score cannot change evidence admission, truth review, or validity
  advancement;
- a dense low-tier, single-independence-group citation ring emits a warning but
  receives no governing benefit;
- graph-informed reviewer findings still require ordinary `evidence_refs`;
- expired records are excluded except in explicitly labelled historical replay;
- failure to converge emits a structured finding, never partial success.

## Adoption Rule

Adopt a live graph-analysis feature only when its graph and configuration are
replayable; results are deterministic within declared numerical tolerance; every
score has inspectable edges and semantics; citation rings cannot improve
admission, truth review, validity, or authority; and normal protocol processing
continues if every graph result is ignored. Otherwise keep it offline only.