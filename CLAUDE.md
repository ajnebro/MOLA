# MOLA — Multi-Objective Landscape Analyzer

Characterizes the landscape features of continuous multi-objective optimization problems,
independent of the framework the problem is implemented in.

## Purpose
Extracts the feature set defined in Liefooghe, Verel, Lacroix, Zăvoianu & McCall, "Landscape
features and automated algorithm selection for multi-objective interpolated continuous
optimisation problems," GECCO 2021 (https://doi.org/10.1145/3449639.3459353): distances among
sampled solutions in variable/objective space, neighbourhood dominance structure, and
non-dominated-sorting rank statistics (entropy, average, max).

## Origin
Evolved from **MOORPHOLOGY** (`$HOME/Softw/moorphology`, GitLab jfaldanam-phd/moorphology) — a
jMetal-6.1 Java implementation of the same feature set. This is a **from-scratch rewrite, not a
fork**, prompted by an EMO2027-program analysis session (2026-07-23) that found: (a) several real
correctness bugs in MOORPHOLOGY's feature computations, uncaught because none of its tests
exercise the landscape features themselves (only static problem info + 2 helper functions); (b) a
hard coupling to jMetal 6.1 Java, unable to characterize problems from other ecosystems (notably
jMetalPy). See the bug audit below — it is the concrete starting checklist for this rewrite.

## Design principle: framework-independent via an interchange contract
The core engine's only input is a **structured sample** — decision vectors + objective vectors +
minimal problem metadata (name/bounds/M/D) — conforming to the documented interchange schema. It
**never** receives a problem object and **never** calls `evaluate()` itself. The boundary is the
*schema*, not a specific transport: an adapter may hand the core a written sample file **or** an
in-memory table with the identical columns — either way the core sees only "structured samples in,
features out".

Per-framework **adapters** own all evaluation and stay thin: Latin-Hypercube sample → evaluate →
emit the interchange record. A jMetalPy adapter may import a problem class and evaluate it
in-process (no file on disk needed), but it still hands the core the same structured sample; the
problem object never crosses into the core. Any framework that can produce the schema can be
characterized — jMetal (Java), jMetalPy (Python), pymoo, PlatEMO, ... — without touching the core.

## Recommended architecture (confirm/revise in the implementation session — not locked in)
- **Core engine: Python** (numpy/scipy/pandas) — natural fit for jMetalPy (no interchange *file*
  needed: the adapter imports and evaluates a jMetalPy problem in-process, then hands the core the
  same structured sample) and for a companion
  statistical-analysis script in the same spirit as MOORPHOLOGY's existing
  `statistical_analysis.py` (Shapiro-Wilk normality check across repeated characterizations).
- **Interchange format**: CSV or Parquet, columns `[problem, sample_id, x_1..x_d, f_1..f_m]`, plus
  a small metadata JSON (bounds, problem name, M, D) — exact schema TBD in the dev session.
  `f_1..f_m` must already be in minimization form (see "Optimization sense" in Design decisions).
- **jMetal (Java) adapter**: minimal — Latin Hypercube sample, evaluate, write to the interchange
  file. No feature computation in Java at all.
- **jMetalPy adapter**: same, in Python — a thin wrapper (or an "import a problem class and sample
  it" CLI mode), emitting the in-memory interchange record rather than a file since both ends are
  already Python. It still owns evaluation; the core still receives only the structured sample.

## Feature set (unchanged from Liefooghe et al. 2021 / MOORPHOLOGY's README)
SAMPLE_SIZE, NUM_OBJ, NUM_VAR, ND_N, DIST_X_AVG/MAX, DIST_X_ND_AVG/MAX, DIST_F_AVG/MAX,
NEIGH_DIST_X/F_AVG/MAX, SUP_AVG_NEIG, INF_AVG_NEIG, INC_AVG_NEIG, LND_AVG_NEIG, LSUP_AVG_NEIG,
RANK_AVG, RANK_MAX, RANK_ENTROPY. This is MOLA's full scope — nothing beyond it (see "Feature set
scope" in Design decisions).

Normalization: every `*_MAX` feature (DIST_X_MAX, DIST_F_MAX, DIST_X_ND_MAX, NEIGH_DIST_X_MAX,
NEIGH_DIST_F_MAX) is reported **raw**; every `*_AVG` distance feature is max-min **normalized**
against its space's global empirical range. Full rule and rationale in "Normalization reference"
below — this is broader than MOORPHOLOGY's own README wording ("except DIST_X_MAX and
DIST_F_MAX"), which doesn't match what its code actually does.

## Audit of MOORPHOLOGY's current implementation (carried over, 2026-07-23)
**Reliable as-is — safe to port with only mechanical translation:**
- `proportionOfNonDominated` (ND%), `rankMaximum`, `rankAverage`, `rankEntropy` — global-ranking
  only, no bug found.
- `distanceXMaximum`, `distanceXAverage`, `distanceFMaximum` — correct accumulation.
- `neighbourDistanceXMaximum`, `neighbourDistanceFMaximum` — correct (`Math.max`-accumulated, not
  touched by the sum-accumulator bug below).
- `averageProportionOfDominatingNeighbours` / `...DominatedNeighbours` / `...IncomparableNeighbours`
  — correct `+=` accumulation, and compares reference vs. neighbour on the *same* global ranking
  throughout (unlike the LND/LSUP pair below).
- `neighboursCorrelationOfAverageDistanceX/F` (Spearman) — has a `||`-instead-of-`&&` length-check
  bug, but it's a non-issue once the neighbourhood size is more than 1-2 (i.e. any problem with a
  handful of decision variables or more).

**Broken in MOORPHOLOGY — redesign, don't mechanically port this logic:**
- `distanceFAverage` — normalized using a "DIST_F_MIN" that is actually computed from
  variable-space distance, not objective-space (`ProblemCharacterization.java:160`).
- `distanceXNonDominatedMaximum`/`Average` — the "both non-dominated" pair filter checks the same
  sample index twice (`i` and `i`, not `i` and `j`, line 163); the average also divides a pairwise
  sum by a per-solution count instead of a pair count (line 173).
- `neighbourDistanceXAverage`/`FAverage` — the accumulator uses `=` instead of `+=` (lines 217,
  219): the "average" is actually just the last-processed sample's neighbourhood mean.
- `averageProportionOfLocallyNonDominatedNeighbours` / `...SupportedLocallyNonDominated...` —
  mixes a *local* sub-ranking's rank for the reference solution with the *global* ranking's rank
  for its neighbours (lines 246-253) — an internally inconsistent comparison.
- `getNeighbours` (off-by-one): the loop "spends" its first iteration on the self-distance-0 point
  before excluding it, so it returns `d-1` neighbours, not `d`.
- Complexity: the non-dominated-pair check uses `List.contains()` inside an O(n²) loop → O(n³)
  with `n = 200*d`; use a hash-set/boolean array instead.
- CI (`.gitlab-ci.yml`) only runs `mvn assembly:single`, never `mvn test` — none of the above were
  ever caught by CI. MOLA should run its tests in CI from the start.

## Design decisions (resolved 2026-07-24)
Five questions raised in the first design pass are now settled:

- **Neighbourhood definition.** Neighbourhood size `k = D` (number of decision variables),
  matching MOORPHOLOGY (`ProblemCharacterization.java:108`); neighbours are the `k` nearest
  samples by distance in **decision** space. Two bugs get fixed regardless of this choice:
  `getNeighbours`'s off-by-one (it spends its first pick on the self-point and returns `k-1`
  neighbours, not `k`) and the SUP/INF/INC/LND/LSUP proportions dividing by `k` instead of the
  actual neighbour count.
- **Normalization reference.** Two normalizers, each the global empirical min/max of pairwise
  distances across the whole sample in their own space: `(DIST_X_MIN, DIST_X_MAX)` for decision
  space, `(DIST_F_MIN, DIST_F_MAX)` for objective space. `(DIST_X_MIN, DIST_X_MAX)` normalizes
  DIST_X_AVG, DIST_X_ND_AVG, and NEIGH_DIST_X_AVG; `(DIST_F_MIN, DIST_F_MAX)` normalizes
  DIST_F_AVG and NEIGH_DIST_F_AVG — always the whole-sample range, never a range recomputed over
  a subset (non-dominated pairs, a neighbourhood). Fixes the `distanceFAverage` bug: the F
  normalizer must accumulate from objective-space distance, not variable-space
  (`ProblemCharacterization.java:160`). Every `*_MAX` feature stays raw (see "Feature set" above).
- **Feature set scope.** MOLA implements exactly the paper's feature set (see "Feature set"
  above) — no more. Two quantities MOORPHOLOGY emits beyond that are explicitly **out of scope**:
  the Spearman `neighboursCorrelationOfAverageDistanceX/F` (not in MOORPHOLOGY's README either),
  and DIST_X_MAX_ANALYTICALLY (the box-diagonal bound — documented in MOORPHOLOGY's README, but
  it's a static problem-geometry constant, not a sample-based landscape statistic, and isn't in
  the paper's set).
- **Stochasticity & reproducibility.** One characterization run = one LHS sample = one interchange
  record = one feature vector; the core has no repetition logic. Repeated-sampling workflows
  (e.g. a Shapiro-Wilk normality check in the spirit of MOORPHOLOGY's `statistical_analysis.py`)
  are an outer loop over independent invocations, each with its own seed — mirrors MOORPHOLOGY's
  own shell-loop workflow (its README) rather than baking repetition into the schema or the core.
- **Optimization sense.** The interchange contract mandates minimization: `f_1..f_m` must already
  be in minimization form when written. Adapters negate natively-maximized objectives during
  evaluation (jMetal and jMetalPy already normalize to minimization by convention, so this is
  nearly free). The core's dominance/ranking logic assumes minimization uniformly — no
  per-objective sense metadata.

## Not yet decided (settle in the implementation session)
- Exact interchange file schema/format (column names/types, file format) — constrained by the
  decisions above (one sample per record, `f_1..f_m` minimization-form) but not yet pinned down.
- Core language confirmation (Python is the working recommendation, not locked in).
- Whether the jMetal-side adapter is its own tiny project or a small addition to an existing one.
- Test strategy: hand-computed fixture front(s) with known landscape stats, one per feature, from
  the start — this is exactly the gap that let MOORPHOLOGY's bugs ship. The decisions above pin
  down what each fixture must assert (e.g. exact `k`, exact normalizer, minimization-only
  dominance).

## Coding, testing, and Git guidelines
MOLA adopts the jMetal/Evolver-family conventions; the guides are vendored in this repo (keep them
in sync with their upstreams — edit upstream first, then re-vendor):
- **Git & commits** — [`GIT_GUIDELINES.md`](GIT_GUIDELINES.md): Conventional Commits, atomic
  commits, build-and-test before committing. From Evolver (identical to jMetal's).
- **Java code** (the jMetal Java sampling adapter) —
  [`JAVA_CODING_GUIDELINES.md`](JAVA_CODING_GUIDELINES.md): Google Java Style, Java 21+, JUnit 6
  Given-When-Then / AAA testing. From jMetal/Evolver.
- **Python code** (the core engine, the jMetalPy adapter, the statistical-analysis script) —
  [`PYTHON_CODING_GUIDELINES.md`](PYTHON_CODING_GUIDELINES.md): Python 3.11+, ruff-enforced, pytest
  AAA testing. From jMetalPy.

CI must run the tests from day one — both `pytest` and, for the Java adapter, `mvn test`.
MOORPHOLOGY's CI never ran `mvn test`, which is exactly why its feature bugs shipped.

## Status
Empty scaffold as of 2026-07-23. No code yet — implementation happens in a dedicated future
session.
