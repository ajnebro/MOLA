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
Evolved from **MOORPHOLOGY** (https://gitlab.com/jfaldanam-phd/moorphology) — a
jMetal-6.1 Java implementation of a subset of the same feature set (~19 of the paper's 49 landscape
features; see "Feature implementation matrix" below — confirmed 2026-07-24 by reading the actual
paper, not just MOORPHOLOGY's own README). This is a **from-scratch rewrite, not a fork**, prompted
by an EMO2027-program analysis session (2026-07-23) that found: (a) several real correctness bugs
in MOORPHOLOGY's feature computations, uncaught because none of its tests exercise the landscape
features themselves (only static problem info + 2 helper functions); (b) a hard coupling to jMetal
6.1 Java, unable to characterize problems from other ecosystems (notably jMetalPy); (c) MOORPHOLOGY
covers only a fraction of the paper's actual feature set, entirely missing the multimodality class
and every hypervolume-based feature — which the paper's own predictive-importance analysis ranks
among the most informative. See the bug audit below — it is the concrete starting checklist for
this rewrite.

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

## Architecture (confirmed 2026-07-25)
- **Core engine: Python** (numpy/scipy/pandas, plus `jmetalpy` and `moocore` — see "Reuse map" in
  Design decisions) — natural fit for jMetalPy (no interchange *file* needed: the adapter imports
  and evaluates a jMetalPy problem in-process, then hands the core the same structured sample) and
  for a companion statistical-analysis script in the same spirit as MOORPHOLOGY's existing
  `statistical_analysis.py` (Shapiro-Wilk normality check across repeated characterizations).
  Dependencies are pinned in [`environment.yml`](environment.yml) (Conda env `MOLA`).
- **Interchange format**: CSV + a sidecar metadata JSON — full schema in "Interchange schema" under
  Design decisions. `f_1..f_m` must already be in minimization form (see "Optimization sense").
- **jMetal (Java) adapter**: minimal — Latin Hypercube sample, evaluate, write to the interchange
  file. No feature computation in Java at all. Lives in this repo (see "Java adapter location").
- **jMetalPy adapter**: same, in Python — a thin wrapper (or an "import a problem class and sample
  it" CLI mode), emitting the in-memory interchange record rather than a file since both ends are
  already Python. It still owns evaluation; the core still receives only the structured sample.

## Feature set (the paper's full 49-feature set — corrected 2026-07-24)
MOLA implements all **49 landscape features** defined by Liefooghe et al. 2021's Table 1, across
four classes: **Global (14)**, **Multimodality (9)**, **Evolvability (13)**, **Ruggedness (13)**.
Feature-by-feature status, difficulty, and notes are in "Feature implementation matrix" below —
that table is the authoritative per-feature reference; this section only summarises.

This supersedes an earlier, narrower reading of "Feature set" that listed ~19 names matching only
MOORPHOLOGY's own coverage (including `NEIGH_DIST_X_MAX`/`NEIGH_DIST_F_MAX`, which turned out not
to be paper features at all — the paper's Table 1 only defines the `_AVG` neighbour-distance
variant, MOORPHOLOGY invented the `_MAX` one by analogy). See "Feature set scope" in Design
decisions for the correction history.

Also always reported, but not "landscape features" in the paper's sense (basic sample metadata,
zero design ambiguity): **SAMPLE_SIZE**, **NUM_OBJ**, **NUM_VAR**. The paper's 5 problem-dependent
features (`d, k, seed_n, nd_seed_n, dom_seed_n`) are explicitly **out of scope** — they're specific
to the MO-ICOP benchmark generator's construction (seeds, interpolation power) and don't generalise
to arbitrary problems (RE21, ZDT, DTLZ, WFG, ...), which is exactly what MOLA targets. `d` (number
of variables) is already covered by NUM_VAR.

Normalization: every `*_MAX` feature (DIST_X_MAX, DIST_F_MAX, DIST_X_ND_MAX) is reported **raw**;
every `*_AVG` distance feature is max-min **normalized** against its space's global empirical
range. Full rule and rationale in "Normalization reference" below — broader than MOORPHOLOGY's own
README wording ("except DIST_X_MAX and DIST_F_MAX"), which doesn't match what its code actually
does.

## Feature implementation matrix (added 2026-07-24)
Per-feature design/porting status against the paper's Table 1. Status vocabulary: `reliable` =
correct in MOORPHOLOGY, port mechanically; `buggy` = MOORPHOLOGY has it but wrong, redesign (see
Audit below); `new` = not in MOORPHOLOGY, design resolved this session (see Design decisions);
`implemented` = built and tested in MOLA itself, Notes points at the module. Update a row to
`implemented` in the same commit as the feature, not as a separate pass — that's what let this
column go stale the one time it was skipped (`dist_x_avg`, caught and fixed 2026-07-25).
Difficulty is engineering effort, not importance. Totals: **21 Low, 25 Medium, 3 High** — only
`supp_n`, `length_aws`, `eval_aws` are genuinely hard (convex hull + adaptive-walk simulation);
everything else is either a direct port or mechanical given the neighbourhood graph/per-solution
arrays other features already build.

**Global (14)** — 9 Low, 4 Medium, 1 High

| Feature | Difficulty | Status | Notes |
|---|---|---|---|
| `f_cor` | Low | implemented | `mola.features.f_cor` |
| `dist_x_avg` | Low | implemented | `mola.features.dist_x_avg` |
| `dist_x_max` | Low | implemented | `mola.features.dist_x_max` — raw, not normalized |
| `dist_f_avg` | Medium | implemented | `mola.features.dist_f_avg` — correct F-space normalizer |
| `dist_f_max` | Low | implemented | `mola.features.dist_f_max` — raw, not normalized |
| `nd_n` | Low | implemented | `mola.features.nd_n` |
| `supp_n` | High | new | ConvexHull on ND subset; degenerate-case fallback |
| `hv` | Medium | new | `moocore.hypervolume`; shared whole-sample ref point |
| `dist_x_nd_avg` | Medium | implemented | `mola.features.dist_x_nd_avg` — pair-filter + divisor fixed |
| `dist_x_nd_max` | Low | implemented | `mola.features.dist_x_nd_max` — raw; NaN if \|ND\| < 2 |
| `fdc` | Medium | implemented | `mola.features.fdc` |
| `rank_avg` | Low | implemented | `mola.features.rank_avg` |
| `rank_max` | Low | implemented | `mola.features.rank_max` |
| `rank_ent` | Low | implemented | `mola.features.rank_ent` — base-2 entropy, confirmed against MOORPHOLOGY's source |

**Multimodality (9)** — 4 Low, 3 Medium, 2 High

| Feature | Difficulty | Status | Notes |
|---|---|---|---|
| `slo_n` | Medium | implemented | `mola.features.multimodality.slo_n` — `mola.multimodality.single_objective_local_optima` |
| `slo_dist_avg` | Medium | implemented | `mola.features.multimodality.slo_dist_avg` — NaN if every objective has \|S_m\| < 2 |
| `slo_dist_max` | Medium | implemented | `mola.features.multimodality.slo_dist_max` — raw; same NaN rule |
| `plo_n` | Low | implemented | `mola.features.multimodality.plo_n` |
| `plo_dist_avg` | Low | implemented | `mola.features.multimodality.plo_dist_avg` — NaN if \|PLO\| < 2 |
| `plo_dist_max` | Low | implemented | `mola.features.multimodality.plo_dist_max` — raw; NaN if \|PLO\| < 2 |
| `nd_per_plo` | Low | implemented | `mola.features.multimodality.nd_per_plo` = `nd_n / plo_n` |
| `length_aws` | High | new | adaptive-walk simulation, genuinely new algorithm |
| `eval_aws` | High | new | byproduct of the same walk |

**Evolvability (13)** — 6 Low, 7 Medium

| Feature | Difficulty | Status | Notes |
|---|---|---|---|
| `sup_avg_neig` | Low | implemented | `mola.features.evolvability.sup_avg_neig` — genuine pairwise dominance via `mola.dominance`, not MOORPHOLOGY's rank comparison |
| `inf_avg_neig` | Low | implemented | `mola.features.evolvability.inf_avg_neig` |
| `inc_avg_neig` | Low | implemented | `mola.features.evolvability.inc_avg_neig` |
| `lnd_avg_neig` | Medium | buggy | local/global rank mismatch |
| `lsupp_avg_neig` | Medium | buggy | same mismatch |
| `dist_x_avg_neig` | Medium | implemented | `mola.features.evolvability.dist_x_avg_neig` — redesigned on `mola.distance.neighbour_distances`, not ported |
| `dist_f_avg_neig` | Medium | implemented | `mola.features.evolvability.dist_f_avg_neig` |
| `dist_f_dist_x_avg_neig` | Low | implemented | `mola.features.evolvability.dist_f_dist_x_avg_neig` — ratio of the two rows above |
| `diff_f_avg_neig` | Medium | implemented | `mola.features.evolvability.diff_f_avg_neig` — `mola.distance.neighbour_diff_f` |
| `diff_f_dist_x_avg_neig` | Low | implemented | `mola.features.evolvability.diff_f_dist_x_avg_neig` — ratio |
| `hv_avg_neig` | Medium | implemented | `mola.features.evolvability.hv_avg_neig` — `mola.hypervolume.singleton_hypervolume`, **not** `moocore.hv_contributions` |
| `hvd_avg_neig` | Low | implemented | `mola.features.evolvability.hvd_avg_neig` — difference over the `hv_avg_neig` array |
| `nhv_avg_neig` | Medium | new | `moocore.hypervolume` per neighbourhood |

**Ruggedness (13)** — 2 Low, 11 Medium

| Feature | Difficulty | Status | Notes |
|---|---|---|---|
| `dist_x_cor_neig` | Low | implemented | `mola.features.ruggedness.dist_x_cor_neig` — `mola.ruggedness.neighbour_correlation`, not MOORPHOLOGY's `\|\|`/`&&` guard |
| `dist_f_cor_neig` | Low | implemented | `mola.features.ruggedness.dist_f_cor_neig` |
| `sup_cor_neig` | Medium | implemented | `mola.features.ruggedness.sup_cor_neig` |
| `inf_cor_neig` | Medium | implemented | `mola.features.ruggedness.inf_cor_neig` |
| `inc_cor_neig` | Medium | implemented | `mola.features.ruggedness.inc_cor_neig` |
| `lnd_cor_neig` | Medium | new | blocked on `lnd_avg_neig`, not yet implemented |
| `lsupp_cor_neig` | Medium | new | blocked on `lsupp_avg_neig`, not yet implemented |
| `dist_f_dist_x_cor_neig` | Medium | implemented | `mola.features.ruggedness.dist_f_dist_x_cor_neig` — per-solution ratio, then correlated (unlike the evolvability namesake) |
| `diff_f_cor_neig` | Medium | implemented | `mola.features.ruggedness.diff_f_cor_neig` |
| `diff_f_dist_x_cor_neig` | Medium | implemented | `mola.features.ruggedness.diff_f_dist_x_cor_neig` — same per-solution-ratio pattern |
| `hv_cor_neig` | Medium | implemented | `mola.features.ruggedness.hv_cor_neig` |
| `hvd_cor_neig` | Medium | implemented | `mola.features.ruggedness.hvd_cor_neig` — `mola.hypervolume.neighbour_hypervolume_difference` |
| `nhv_cor_neig` | Medium | new | blocked on `nhv_avg_neig`, not yet implemented (needs `moocore`) |

**Problem-dependent (5) — out of scope**

`d`, `k`, `seed_n`, `nd_seed_n`, `dom_seed_n` — all MO-ICOP-generator-specific, don't generalize to
arbitrary problems. `d` (number of variables) is already covered by MOLA's `NUM_VAR` metadata field.

## Audit of MOORPHOLOGY's current implementation (carried over, 2026-07-23)
**Reliable as-is — safe to port with only mechanical translation:**
- `proportionOfNonDominated` (ND%), `rankMaximum`, `rankAverage`, `rankEntropy` — global-ranking
  only, no bug found.
- `distanceXMaximum`, `distanceXAverage`, `distanceFMaximum` — correct accumulation.
- `neighbourDistanceXMaximum`, `neighbourDistanceFMaximum` — correct (`Math.max`-accumulated, not
  touched by the sum-accumulator bug below).
- `neighboursCorrelationOfAverageDistanceX/F` (Spearman) — has a `||`-instead-of-`&&` length-check
  bug, but it's a non-issue once the neighbourhood size is more than 1-2 (i.e. any problem with a
  handful of decision variables or more).

**Broken in MOORPHOLOGY — redesign, don't mechanically port this logic:**
- `averageProportionOfDominatingNeighbours` / `...DominatedNeighbours` / `...IncomparableNeighbours`
  — **correction, 2026-07-30**: previously listed as reliable ("compares reference vs. neighbour on
  the same global ranking throughout") — that description undersold the bug. It compares *global
  ranks* (`ranking.getRank(reference)` vs. `ranking.getRank(neighbour)`, lines 220-233), not
  pairwise dominance between the two. These are not equivalent: two solutions can sit in different
  global fronts without either directly dominating the other, since front assignment reflects the
  whole sample's structure, not just the pair. The paper is explicit this is pairwise ("proportions
  of dominating, dominated, and incomparable **neighbours**", §4.1.3) — found by reading
  MOORPHOLOGY's source directly (not assumed) while building MOLA's own version; see `sup_avg_neig`
  in Design decisions for the fix (genuine pairwise `DominanceComparator.dominance_test`, not rank
  comparison).
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
  **Clarified 2026-07-30**: this list predates the full 49-feature scope and reads as exhaustive,
  but "Feature set" above states the rule generally ("every `*_AVG` distance feature is max-min
  normalized") — the general rule is what's intended. It extends unchanged to the multimodality
  class's `slo_dist_avg`/`plo_dist_avg` (`(DIST_X_MIN, DIST_X_MAX)`, same as `dist_x_nd_avg`, since
  they're all distances among a subset of the sample in variable space) and their `*_dist_max`
  siblings stay raw, consistent with every other `*_MAX`.
- **Feature set scope — corrected 2026-07-24.** MOLA implements the paper's **full 49-feature
  set** (see "Feature set" and "Feature implementation matrix" above), not the ~19-feature subset
  originally assumed here. **Correction**: this decision originally also excluded the Spearman
  `neighboursCorrelationOfAverageDistanceX/F` as "not in the paper's set" — that was wrong, decided
  before reading the actual paper text. They *are* paper features (`dist_x_cor_neig`/
  `dist_f_cor_neig`, ruggedness class, Table 1), now in scope along with their 11 ruggedness
  siblings. The other half of the original exclusion stays correct: DIST_X_MAX_ANALYTICALLY (the
  box-diagonal bound — documented in MOORPHOLOGY's README, but it's a static problem-geometry
  constant, not a sample-based landscape statistic) is confirmed absent from the paper's Table 1
  and stays **out of scope**, alongside the 5 problem-dependent features (see "Feature set" above).
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

Eight more, resolved 2026-07-24 for the ~30 features added when scope expanded to the paper's full
49 (a Plan agent produced the definitions below, grounded directly in paper §4.1.1–4.1.4 and
Table 1; judgment calls the paper doesn't fully specify are marked explicitly):

- **`f_cor`.** Spearman correlation among the objective values measured on the sample (§4.1.1). For
  M=2 (the paper's own benchmark) this is one Spearman correlation between the two objective
  columns. **Judgment call, beyond the paper's literal bi-objective scope**: for M>2, MOLA uses the
  mean of the C(M,2) pairwise Spearman correlations — signed, not `abs()`, since a negative
  pairwise correlation is a real conflicting-objectives signal (the paper itself plots signed
  correlations, Fig. 1) that averaging magnitudes would destroy.
- **`supp_n` — supported non-dominated solutions.** Supported = on the convex hull of the ND
  subset's objective vectors (classical linear-scalarization definition, Ehrgott [10], cited
  directly in §4.1.1). Denominator is `|ND|`, not `n` — §4.1.1 says "proportion of supported points
  **therein**," referring back to "non-dominated solutions," distinct from `nd_n`'s "among the
  sample" phrasing. Computed via `scipy.spatial.ConvexHull` on the ND subset's objective vectors; a
  point is supported iff it lies on a facet whose outward normal is entirely ≤0 (the
  minimizing-direction facet). If `|ND| ≤ M`, every ND point is supported by construction (too few
  points to span a dominating simplex) — skip `ConvexHull` and return `1.0`. **Judgment call**: on
  the rarer `QhullError` case (coplanar/rank-deficient ND set with `|ND| > M`), MOLA also falls back
  to `1.0`, but documents this sub-case as an approximation, not exact — expected practically
  unreachable for continuous, LHS-sampled objectives.
- **`hv` and the shared hypervolume reference point.** The paper defines `hv` (hypervolume of the
  ND subset, §4.1.1) but never states a reference point — genuinely unspecified (§3.3's hypervolume
  is a different quantity: algorithm-performance normalization against the problem's *known* true
  Pareto front, not usable here). **Judgment call**: one reference point per sample, the
  element-wise max of `f_m` over the *whole* sample (not just ND) for each objective `m`, no
  padding — mirrors the "one shared normalizer, never a subset-recomputed range" pattern already
  established for X/F distance normalization above. Shared by every hypervolume-based feature:
  `hv`, `hv_avg_neig`, `hvd_avg_neig`, `nhv_avg_neig`, and their `_cor_neig` counterparts. Computed
  via `moocore.hypervolume(F_nd, ref)` (a `jmetalpy` dependency — see "Reuse map" below).
- **`fdc` — fitness-distance correlation.** Spearman correlation between pairwise variable-space
  distance and pairwise objective-space distance, over all C(k,2) pairs among the `k=|ND|` solutions
  (§4.1.1, "denoted as fitness-distance-correlation in [18]"). Explicitly distinct from two
  similarly-shaped features: ruggedness's `dist_x_cor_neig`/`dist_f_cor_neig` correlate a
  per-solution *average*-distance-to-neighbours measure across *neighbour* pairs over the *whole*
  sample, not raw pairwise distances restricted to ND solutions; evolvability's
  `dist_f_dist_x_avg_neig` is a *ratio*, not a correlation. `k<2` → zero pairs → `NaN` (propagated,
  not special-cased; confirmed this is `scipy.stats.spearmanr`'s own behaviour on empty input).
- **Multimodality (all 9).** `slo` (single-objective local optimum, §4.1.2) is inherently
  per-objective: "no improving neighbour for a given objective." `slo_n` = mean over objectives `m`
  of `|{i : no neighbour of i improves f_m}| / n` (Table 1's own wording: "proportion… per
  objective"). **Judgment call**: `slo_dist_avg`/`slo_dist_max` apply the same per-objective-then-
  mean-across-M pattern (Table 1 doesn't restate "per objective" for these two rows, but introduces
  no alternative aggregation either). `plo` (Pareto local optimum: no dominating neighbour, §4.1.2)
  reuses the dominating-neighbour count already computed for `sup_avg_neig` — `plo = (sup_count ==
  0)`, no new dominance machinery; `nd_per_plo = nd_n / plo_n` (Table 1's own parenthetical).
  Adaptive walk (`length_aws`/`eval_aws`, §4.1.2): from a starting solution, scan its neighbours
  closest-to-furthest, accept the first one that *dominates* the current solution, repeat until no
  neighbour dominates (walk has reached a plo); simulated entirely over the precomputed
  neighbourhood graph — the paper is explicit this needs **no additional evaluations**, despite
  Table 1's "calls to the evaluation function" phrasing for `eval_aws` (that phrase describes what
  it *would* cost live, not what MOLA actually spends). **Judgment call**: the paper says "different
  starting points" without specifying how many/how chosen — MOLA draws `min(30, n)` distinct
  solutions from the sample uniformly at random (using the run's own seed, per "Stochasticity &
  reproducibility" above); `length_aws`/`eval_aws` are the mean over those walks.
- **Evolvability's missing six.** `dist_f_dist_x_avg_neig = dist_f_avg_neig / dist_x_avg_neig` and
  `diff_f_dist_x_avg_neig = diff_f_avg_neig / dist_x_avg_neig` (Table 1's own parenthetical
  formulas). **Judgment call**: `diff_f_avg_neig` ("average difference per objective with
  neighbours") = mean over neighbours `j` of [mean over objectives `m` of `|f_m(i)-f_m(j)|`] —
  unsigned, matching every other averaged distance-like feature in this family, since the
  neighbour relation is directional (`j∈N(i)` doesn't imply `i∈N(j)`) and a signed average could
  cancel out real structure. `hv_avg_neig` ("average **(single)** solution's hypervolume" — the
  "(single)" qualifier is load-bearing): each solution's own box-hypervolume against the shared
  `ref`, `∏_m max(0, ref_m − f_m(i))`, a vectorized closed form — **not** `moocore.hv_contributions`
  (verified numerically distinct: contributions measure marginal value *relative to the rest of the
  set*, which would make this collapse toward measuring `nd_n` rather than a per-solution signal).
  `hvd_avg_neig` = mean over neighbours of `|hv(i) − hv(j)|`, reusing the `hv_avg_neig` array.
  `nhv_avg_neig` ("hypervolume from the **whole neighbourhood**") is genuinely set-based, unlike
  the singleton `hv_avg_neig`: `moocore.hypervolume(F[N(i)], ref)`, the joint HV of `i`'s neighbours
  (excluding `i` itself).
- **Ruggedness's missing eleven.** Same Spearman-over-neighbour-pairs procedure MOORPHOLOGY already
  has (buggily) for 2 of the 13 evolvability measures, applied uniformly to all 13 (§4.1.4: "for
  each of the thirteen measures, we compute the Spearman correlation coefficient over each pair of
  neighbours"): for every directed edge `(i, j)` with `j∈N(i)`, append `(measure[i], measure[j])`
  to two parallel arrays, then one `scipy.stats.spearmanr` call per measure over the whole edge set.
  Structurally immune to MOORPHOLOGY's `||`-vs-`&&` length-guard bug — the two arrays come from one
  shared edge loop and cannot disagree in length by construction, so no length check is needed at
  all. Applies without exception to the new hv-trio, `diff_f`, and `dist_f_dist_x` measures too.
- **Reuse map — jmetalpy/moocore vs. new MOLA logic.** Confirmed by direct inspection of jMetalPy
  (`/Users/ajnebro/Softw/jMetal/jMetalPy`, MIT-licensed): non-dominated sorting/ranking (feeds
  `dist_x_nd_avg/max`, `supp_n`, `hv`, `fdc`, `rank_*`) → `jmetal.util.ranking
  .FastNonDominatedRanking` (`.get_nondominated()`, per-solution rank via `.attributes
  ["dominance_ranking"]` after `.compute_ranking()`). Pairwise dominance (`plo`, the adaptive walk,
  the existing `sup/inf/inc`) → `jmetal.util.comparator.DominanceComparator.dominance_test(v1, v2)`,
  a static method on raw objective vectors. Set-based hypervolume (`hv`, `nhv_avg_neig`,
  `nhv_cor_neig`) → `moocore.hypervolume(data, ref)`, the same call jMetalPy's own
  `jmetal.core.quality_indicator.HyperVolume` delegates to (confirmed: that module imports
  `moocore` and `scipy.spatial` directly). New MOLA-only logic, nothing to reuse: `supp_n`'s
  `ConvexHull` facet test (grepped jMetalPy for "supported"/"convex hull" — zero hits), every
  Spearman call (`f_cor`, `fdc`, all 13 `*_cor_neig`), `slo`/adaptive-walk bookkeeping, and the
  singleton `hv_avg_neig`/`hvd_avg_neig` formulas (deliberately not `moocore.hv_contributions` —
  see above). `moocore` is a **required transitive dependency of jmetalpy** (imported at module
  level in `jmetal/core/quality_indicator.py`), not an optional extra.

Three more, resolved 2026-07-25 — the last structural questions blocking implementation:

- **Interchange schema.** **CSV**, not Parquet: writable from Java with no extra dependency
  (Parquet would mean pulling `parquet-mr` into the adapter purely for serialization, against the
  "adapters stay thin" principle), inspectable by eye, and at this scale (`n = 200·D` rows) the
  performance difference is irrelevant. One sample file plus a **sidecar metadata JSON** sharing its
  basename. CSV columns: `problem, sample_id, x_1..x_D, f_1..f_M` — `problem` is redundant within a
  single file but makes concatenating several problems' samples into one DataFrame trivial for the
  repeated-run statistical workflow, without joining against the JSON. Metadata JSON keys:
  `schema_version` (so the format can evolve without breaking old files), `problem`,
  `number_of_variables`, `number_of_objectives`, `lower_bounds`, `upper_bounds`, `sample_size`,
  `sampler`, `seed`. Bounds are carried for traceability only — no feature computation reads them,
  since every normalizer is empirical over the sample (see "Normalization reference" above).
  Constraint values are **out of scope**: none of the 49 features uses them, and the paper's
  benchmark is unconstrained by construction. Reopen if constrained problems are ever targeted.
- **Sampling strategy.** Latin Hypercube, `n = 200·D` (paper §4.1/§4.2). The justification is
  **comparability, not technical superiority**: the 49 features are statistics *of the sample*, not
  invariants of the problem, so changing the design changes every value and breaks comparison with
  the paper's own results — and LHS is also the prevailing convention in continuous landscape
  analysis (flacco/ELA, cited by the paper), which matters if MOLA features are ever combined with
  ELA features over a shared sample. Secondary but decisive for MOLA specifically: the Java and
  Python adapters must produce statistically equivalent samples or cross-ecosystem feature
  comparison — MOLA's whole premise — breaks; plain LHS is a few lines in both, whereas matching a
  scrambled Sobol' sequence bit-for-bit across scipy and a hand-written Java implementation is
  fiddly. **Implementation detail worth pinning**: the paper uses R `lhs::randomLHS`, which places
  points *uniformly at random within* each stratum; the scipy equivalent is
  `scipy.stats.qmc.LatinHypercube(d, scramble=True)` — the default. `scramble=False` centres points
  in their strata and is **not** what the paper does; an easy silent divergence. Known limitation,
  documented rather than solved: plain LHS only guarantees 1-D marginal stratification (a "diagonal"
  LHS is a valid LHS with poor coverage), and at `D=30` a 6000-point sample in 30 dimensions is
  sparse enough that the `k=D` nearest-neighbour graph underpinning 35 of the 49 features is
  weakly meaningful — inherited from the paper's feature set, not fixable by changing sampler.
  Recording `sampler` in the metadata JSON keeps the choice reversible at near-zero cost, since
  sampling lives entirely adapter-side and the core never sees it.
- **Java adapter location.** A subdirectory of **this** repository (monorepo), not a separate
  project and not a contribution to jMetal. Keeps the interchange contract and both of its
  producers in one place, and matches this repo already vendoring
  [`JAVA_CODING_GUIDELINES.md`](JAVA_CODING_GUIDELINES.md) specifically for that code. Note neither
  jMetal nor jMetalPy currently ships Latin Hypercube sampling (verified 2026-07-25 — jMetal has
  only generic `util/pseudorandom` and `util/sequencegenerator`), so the adapter implements LHS
  itself either way; there is no existing utility to reuse or extend.
- **License: MIT** (resolved 2026-07-25), matching jMetal and jMetalPy — the projects MOLA depends
  on and is designed to be used alongside. Chosen over GPL-3.0/LGPL-3.0 on adoption grounds: MOLA's
  value is as *the* reference implementation of these 49 features (MOORPHOLOGY's are buggy and
  cover ~19), so it should be importable without friction from pymoo (Apache-2.0), PlatEMO, or
  industrial pipelines. This also matches the permissive norm of the scientific Python stack
  (numpy/scipy/pandas are BSD). Note that `moocore`'s **LGPL-2.1-or-later** never constrained this:
  the LGPL is explicitly designed to be linked from any license, and `moocore` is a separate
  pip/conda dependency, not vendored into MOLA's source — so MIT is unaffected. The one nuance
  worth recording: anyone bundling MOLA *and* `moocore` into a single distributable artifact (a
  frozen binary, say) takes on LGPL obligations for the `moocore` portion; normal pip/conda
  installation does not. Copyleft would in any case have been mostly moot for the dominant use
  case — running MOLA as a tool over a sample and consuming its CSV/JSON output places no
  obligations on the caller's code under any of the three licenses.

## Not yet decided (settle in the implementation session)
- Test strategy: hand-computed fixture front(s) with known landscape stats, one per feature, from
  the start — this is exactly the gap that let MOORPHOLOGY's bugs ship. The decisions above pin
  down what each fixture must assert (e.g. exact `k`, exact normalizer, minimization-only
  dominance). Now spans 49 fixtures' worth of assertions, not ~19 — see "Feature implementation
  matrix" above for the full list.

This is now the only open item — license was the other, resolved 2026-07-25 (see above).

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
Design complete as of 2026-07-25, no code yet. Every structural question is settled — feature set
(49), per-feature semantics, neighbourhood, normalizers, interchange schema, sampling, and repo
layout — leaving only the two items under "Not yet decided" (test fixtures, license), neither of
which blocks starting implementation. Next step: the shared substrate the feature table's "Low"
rows all assume (neighbourhood graph, non-dominated ranking, the two normalizers), with its own
tests, then features one at a time by difficulty within each class.
