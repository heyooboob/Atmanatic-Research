# Mathematical Principles

## Purpose

This document is the canonical reference for mathematical and formal
principles used by Atmanatic Research. It defines each principle's permitted
purpose, required inputs and recorded outputs, and authority boundary.

Mathematical results may improve retrieval, scheduling, inspection, validation,
or research design. They MUST NOT by themselves establish truth, admit evidence,
advance validity, or authorize an action.

Architecture guides define a particular capability and link here for shared
definitions. This document does not replace domain-specific statistical plans,
source policies, or human governance.

## Conformance Terms

- **Implemented** means the principle is represented by current repository
  contracts or deterministic logic.
- **Specified** means the principle is defined for a documented capability but
  has not yet been implemented in the reference library.
- **Proposed** means the principle is recommended for a future, versioned
  capability and has no protocol effect until its contract and tests exist.

## Cross-Cutting Rules

Every implementation of a principle in this document MUST:

1. declare its algorithm or rule version and configuration;
2. identify its input artifacts and record their content hashes where the
   result is persisted;
3. reject non-finite numeric inputs and ambiguous units;
4. preserve deterministic ordering, tie-breaking, and replay behavior;
5. expose assumptions, limitations, and uncertainty in the result;
6. remain non-authorizing unless a separate authority-layer policy explicitly
   consumes a verified artifact.

## Implemented Principles

### Finite-State Validity Transitions

**Status:** Implemented  
**Application:** `validity_protocol`

Validity is modeled as an ordered, bounded state machine. A packet advances
only when the target transition's declared invariants pass; invalid or expired
packets fail closed. Transitions are monotonic except for explicit rejection,
revocation, or expiry semantics.

**Functional requirement:** A transition validator MUST evaluate the declared
target state against the identified packet and MUST NOT infer promotion from
confidence, graph rank, or successful orchestration alone.

**Boundary:** Reaching a validity level is bounded readiness under declared
conditions, not universal truth or execution authorization.

### Set Cardinality and Independence Constraints

**Status:** Implemented  
**Application:** `source_policy.py`, `evidence_admission.py`

Evidence policies require a minimum number of distinct sources and, where
configured, a minimum number of distinct `independence_group` values. This is a
set-cardinality constraint, not a claim-confidence calculation.

For source set $S$ and independence-group set $G(S)$, a policy may require:

$$
|S| \geq m \quad \text{and} \quad |G(S)| \geq k
$$

**Functional requirement:** Source identifiers and independence groups MUST be
validated before counting. Repeated citations of one source or group MUST NOT
increase the relevant count.

**Boundary:** Meeting the threshold admits policy-eligible provenance; it does
not establish that sources agree, are correct, or independently prove a claim.

### Temporal Validity and Freshness

**Status:** Implemented  
**Application:** evidence admission, acquisition receipts, validity packets

Timestamps define whether an observation is future-dated, a receipt is
time-qualified, or a packet remains within its declared validity interval.

For evaluation time $t$ and expiry $t_e$, an unexpired packet requires:

$$
t < t_e
$$

**Functional requirement:** Implementations MUST use timezone-aware ISO 8601
timestamps, compare against a declared evaluation time, and retain expired
records for historical replay rather than silently treating them as current.

**Boundary:** Freshness indicates temporal eligibility, not factual accuracy.

### Cryptographic Content Addressing

**Status:** Implemented  
**Application:** proposal, artifact, receipt, and review contracts

A SHA-256 digest binds a record reference to a particular canonical content
representation. The digest is a deterministic integrity identifier:

$$
h = \operatorname{SHA256}(\operatorname{canonicalize}(x))
$$

**Functional requirement:** Hash-bearing references MUST use the specified
canonical form and reject malformed digests. A hash-linked review MUST identify
the exact reviewed artifact content.

**Boundary:** A matching hash establishes content identity and tamper evidence
within the selected representation; it does not establish provenance truth,
semantic correctness, or signer authority.

### Predicate Logic and Fail-Closed Validation

**Status:** Implemented  
**Application:** all contract validators

Admission and transition checks are conjunctions of explicit predicates. A
record is eligible only when every required predicate holds:

$$
\operatorname{eligible}(x) = \bigwedge_{i=1}^{n} P_i(x)
$$

**Functional requirement:** Unknown critical fields, failed predicates, and
validator errors MUST produce rejection or a structured violation. Validators
MUST return reasons sufficient for review and replay.

**Boundary:** Logical validity is conformance to declared predicates, not a
proof that a real-world assertion is true.

### Bounded Iteration and Resource Limits

**Status:** Implemented  
**Application:** orchestration revision loops and time budgets

Review and revision run under finite revision and time budgets. This turns
unbounded search into an explicit resource-constrained process.

**Functional requirement:** The limit, elapsed-budget behavior, and terminal
reason MUST be recorded. Exhaustion MUST reject or escalate rather than imply
acceptance.

**Boundary:** A proposal that fits a budget is not thereby preferred, correct,
or authorized.

## Specified Graph Principles

### Eigenvector Centrality

**Status:** Specified  
**Application:** offline provenance and structural diagnostics

For non-negative adjacency matrix $A$, find a score vector $x$ satisfying:

$$
Ax = \lambda x
$$

**Functional requirement:** Use only on a declared, stable graph snapshot;
record direction convention and component handling.

**Boundary:** Centrality measures structural connectedness. It MUST NOT be used
as a measure of truth, source authority, independence, or validity.

### Personalized PageRank

**Status:** Specified  
**Application:** query-bounded retrieval and review prioritization

Given normalized transition matrix $P$, seed vector $s$, and damping factor
$\alpha \in (0, 1)$:

$$
p = \alpha P^T p + (1 - \alpha)s
$$

**Functional requirement:** Record seed IDs, eligible edge types, damping,
convergence tolerance, iteration limit, dangling-node handling, snapshot hash,
and deterministic score tie-breaks.

**Boundary:** The result ranks retrieval relevance within a graph. It MUST NOT
change evidence admission, confidence, validity, or execution authorization.

### HITS Support Structure

**Status:** Specified  
**Application:** inspection of evidence-to-claim support topology

HITS computes hub and authority-shaped vectors:

$$
a = A^T h, \qquad h = Aa
$$

**Functional requirement:** Any output exposed by this system MUST be named
`support_structure_score`, with the graph and relation types recorded.

**Boundary:** HITS terminology MUST NOT be interpreted as institutional source
authority or claim validity.

### Spectral Clustering

**Status:** Specified  
**Application:** research batching, duplicate-path inspection, and evidence
island detection

Spectral methods use eigenvectors of a graph Laplacian, commonly:

$$
L = D - A
$$

where $D$ is the degree matrix.

**Functional requirement:** Record graph symmetrization choices, cluster count
or selection rule, and any random seed. Surface clusters as review context.

**Boundary:** Cluster membership does not classify truth, quality, or reviewer
independence.

### Herfindahl Concentration Index

**Status:** Specified  
**Application:** provenance-concentration warnings

For group shares $q_g$ over a claim's support base:

$$
H = \sum_{g \in G} q_g^2
$$

**Functional requirement:** Define the support population, weighting scheme,
independence-group mapping, threshold, and warning-rule version. Retain all
component shares in the output.

**Boundary:** Concentration identifies a possible corroboration weakness. It
MUST trigger inspection only and MUST NOT automatically favor or reject a
claim.

### Strongly Connected Components

**Status:** Specified  
**Application:** citation-ring and circular-provenance inspection

A strongly connected component is a maximal directed subgraph in which every
node is reachable from every other node.

**Functional requirement:** Compare a component's internal-edge share, external
support, time window, and group diversity. Emit an explainable warning with the
snapshot hash.

**Boundary:** A cycle is not proof of deception, error, or invalidity; it is a
reason to inspect original evidence.

## Proposed Research Principles

### Uncertainty Semantics and Calibration

**Status:** Proposed  
**Primary application:** evidence and claim outcome evaluation

Each numeric confidence value needs a declared semantic type: forecast
probability, interval coverage level, evidence-strength score, or another
profile-defined quantity. Only calibrated forecast probabilities may be scored
against binary outcomes.

For forecasts $p_i$ and observed outcomes $y_i \in \{0, 1\}$, the Brier score is:

$$
\operatorname{Brier} = \frac{1}{n}\sum_{i=1}^{n}(p_i-y_i)^2
$$

**Implementation guide:** Add a versioned `uncertainty_assessment` artifact
linked to resolved claim outcomes. Require forecast horizon, outcome definition,
cohort-selection rule, scoring rule, sample size, and calibration interval.
Do not reinterpret existing `confidence` values retroactively.

**Boundary:** Calibration measures the reliability of a forecast process over a
defined cohort. It does not validate any individual claim or grant authority.

### Bayesian Evidence Updating With Dependence Declarations

**Status:** Proposed  
**Primary application:** domain-profiled synthesis of evidence

Bayes' rule updates a stated prior using an explicitly modeled likelihood:

$$
P(H \mid E) = \frac{P(E \mid H)P(H)}{P(E)}
$$

**Implementation guide:** Introduce a non-authorizing `evidence_synthesis`
artifact with hypothesis ID, prior source, likelihood model version,
conditional-independence assumptions, dependence groups, sensitivity analysis,
and posterior interval. Require a domain profile to define permitted priors and
likelihood elicitation before calculation.

**Boundary:** A posterior is conditional on its model and assumptions. It MUST
NOT replace independence requirements, evidence admission, adversarial review,
or human promotion.

### Causal Models and Counterfactual Identification

**Status:** Proposed  
**Primary application:** intervention and policy claims

Support and provenance links do not establish that an intervention caused an
outcome. A causal claim needs explicit variables, directed causal assumptions,
confounders, and an identified target estimand, such as:

$$
\operatorname{ATE} = \mathbb{E}[Y(1) - Y(0)]
$$

**Implementation guide:** Create a versioned `causal_evaluation_plan` that
declares treatment, outcome, population, causal graph or equivalent assumptions,
confounder strategy, estimand, identification method, positivity assumptions,
and falsification checks. A completed evaluation MUST link to its plan and
source evidence.

**Boundary:** Causal identification is valid only under declared assumptions;
it does not make a recommendation executable.

### Expected Value of Information

**Status:** Proposed  
**Primary application:** research and review queue prioritization

Expected value of information compares the best expected utility after an
observation with the best expected utility available now:

$$
\operatorname{EVI}(X) =
\mathbb{E}[\max_a U(a \mid X)] - \max_a \mathbb{E}[U(a)]
$$

**Implementation guide:** Add an optimization-only `research_priority` artifact
with candidate question, decision context, utility model version, cost estimate,
uncertainty model, EVI estimate, and sensitivity range. Use it to order work
within a declared budget.

**Boundary:** Utility models encode stakeholder choices. EVI MAY prioritize
investigation but MUST NOT choose an action, determine truth, or bypass review.

### Sequential Testing and Stopping Rules

**Status:** Proposed  
**Primary application:** measurable falsifiers and empirical evaluations

Repeatedly inspecting data can inflate error rates unless the evaluation plan
declares how evidence will be collected and when the study stops. A sequential
plan precommits a target effect, error budget, sample or information threshold,
and stopping rule.

**Implementation guide:** Extend measurable-claim references with a versioned
`evaluation_plan` artifact. Require metric definition, unit, population,
observation window, effect size or practical threshold, null and alternative,
sampling rule, missing-data handling, stopping rule, and analysis version.

**Boundary:** Passing a predeclared test is evidence under that plan, not a
universal proof or operational authorization.

### Information Gain and Redundancy

**Status:** Proposed  
**Primary application:** source collection and retrieval efficiency

Information-theoretic analysis can estimate how much a candidate observation
changes uncertainty, or whether it is largely redundant with what is already
known. Mutual information is:

$$
I(X;Y) = \sum_{x,y} p(x,y) \log\frac{p(x,y)}{p(x)p(y)}
$$

**Implementation guide:** Use only in a profile that declares variables,
estimator, sample basis, missing-data policy, and uncertainty estimate. Emit a
non-binding retrieval or collection-priority signal alongside, never inside,
evidence admission.

**Boundary:** Estimated dependence is not provenance identity, source quality,
or truth. It complements rather than replaces explicit `independence_group`
metadata.

## Implementation Order

1. Define uncertainty semantics and add outcome-linked calibration artifacts.
2. Add evaluation plans for measurable falsifiers and sequential testing.
3. Add research-priority artifacts using value of information.
4. Introduce Bayesian synthesis only through reviewed domain profiles.
5. Add causal evaluation plans for domains that make intervention claims.
6. Add information-gain diagnostics once sufficient, well-defined data exists.

Each proposed capability requires its own versioned contract, pure validator,
deterministic test fixtures, invalid-input tests, boundary tests proving that it
cannot alter admission or authority decisions, and documentation of its domain
assumptions.