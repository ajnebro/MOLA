# MOLA — Multi-Objective Landscape Analyzer

Characterizes the landscape features of continuous multi-objective optimization problems,
independent of the framework the problem is implemented in.

## Purpose
Extracts the feature set defined in Liefooghe, Verel, Lacroix, Zăvoianu & McCall, "Landscape
features and automated algorithm selection for multi-objective interpolated continuous
optimisation problems," GECCO 2021 (https://doi.org/10.1145/3449639.3459353): distances among
sampled solutions in variable/objective space, neighbourhood dominance structure, and
non-dominated-sorting rank statistics (entropy, average, max).

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
  for a companion statistical-analysis script (Shapiro-Wilk normality check across repeated
  characterizations). Dependencies are pinned in [`environment.yml`](environment.yml) (Conda env
  `MOLA`).
- **Interchange format**: CSV + a sidecar metadata JSON — full schema in "Interchange schema" under
  Design decisions. `f_1..f_m` must already be in minimization form (see "Optimization sense").
- **jMetal (Java) adapter**: minimal — Latin Hypercube sample, evaluate, write to the interchange
  file. No feature computation in Java at all. Lives in this repo (see "Java adapter location").
- **jMetalPy adapter**: same, in Python — a thin wrapper (or an "import a problem class and sample
  it" CLI mode), emitting the in-memory interchange record rather than a file since both ends are
  already Python. It still owns evaluation; the core still receives only the structured sample.

## Feature set (the paper's full 49-feature set)
MOLA implements all **49 landscape features** defined by Liefooghe et al. 2021's Table 1, across
four classes: **Global (14)**, **Multimodality (9)**, **Evolvability (13)**, **Ruggedness (13)**.
Feature-by-feature status, difficulty, and notes are in "Feature implementation matrix" below —
that table is the authoritative per-feature reference; this section only summarises. Note the
paper's Table 1 only defines the `_AVG` neighbour-distance variant for each space — there is no
`NEIGH_DIST_X_MAX`/`NEIGH_DIST_F_MAX` in the paper's own feature set.

Also always reported, but not "landscape features" in the paper's sense (basic sample metadata,
zero design ambiguity): **SAMPLE_SIZE**, **NUM_OBJ**, **NUM_VAR**. The paper's 5 problem-dependent
features (`d, k, seed_n, nd_seed_n, dom_seed_n`) are explicitly **out of scope** — they're specific
to the MO-ICOP benchmark generator's construction (seeds, interpolation power) and don't generalise
to arbitrary problems (RE21, ZDT, DTLZ, WFG, ...), which is exactly what MOLA targets. `d` (number
of variables) is already covered by NUM_VAR.

Normalization: every `*_MAX` feature (DIST_X_MAX, DIST_F_MAX, DIST_X_ND_MAX) is reported **raw**;
every `*_AVG` distance feature is max-min **normalized** against its space's global empirical
range. Full rule and rationale in "Normalization reference" below.

## Feature implementation matrix
Per-feature reference against the paper's Table 1: implementation difficulty and the module each
feature lives in. `implemented` = built and tested in MOLA itself, Notes points at the module.
Update a row to `implemented` in the same commit as the feature, not as a separate pass — that's
what let this column go stale the one time it was skipped (`dist_x_avg`, caught and fixed
2026-07-25). Difficulty is engineering effort, not importance. Totals: **21 Low, 25 Medium, 3
High** — only `supp_n`, `length_aws`, `eval_aws` are genuinely hard (convex hull + adaptive-walk
simulation); everything else is either a direct port or mechanical given the neighbourhood
graph/per-solution arrays other features already build.

**Global (14)** — 9 Low, 4 Medium, 1 High

| Feature | Difficulty | Status | Notes |
|---|---|---|---|
| `f_cor` | Low | implemented | `mola.features.f_cor` |
| `dist_x_avg` | Low | implemented | `mola.features.dist_x_avg` |
| `dist_x_max` | Low | implemented | `mola.features.dist_x_max` — raw, not normalized |
| `dist_f_avg` | Medium | implemented | `mola.features.dist_f_avg` — correct F-space normalizer |
| `dist_f_max` | Low | implemented | `mola.features.dist_f_max` — raw, not normalized |
| `nd_n` | Low | implemented | `mola.features.nd_n` |
| `supp_n` | High | implemented | `mola.features.supp_n` — ConvexHull on ND subset; QhullError/`\|ND\|<=M` fall back to 1.0 |
| `hv` | Medium | implemented | `mola.features.hv` — `moocore.hypervolume`; shared whole-sample ref point |
| `dist_x_nd_avg` | Medium | implemented | `mola.features.dist_x_nd_avg` — pair-filter + divisor fixed |
| `dist_x_nd_max` | Low | implemented | `mola.features.dist_x_nd_max` — raw; NaN if \|ND\| < 2 |
| `fdc` | Medium | implemented | `mola.features.fdc` |
| `rank_avg` | Low | implemented | `mola.features.rank_avg` |
| `rank_max` | Low | implemented | `mola.features.rank_max` |
| `rank_ent` | Low | implemented | `mola.features.rank_ent` — base-2 entropy (judgment call, paper doesn't state a log base) |

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
| `length_aws` | High | implemented | `mola.features.multimodality.length_aws` — adaptive-walk simulation, genuinely new algorithm |
| `eval_aws` | High | implemented | `mola.features.multimodality.eval_aws` — byproduct of the same walk |

**Evolvability (13)** — 6 Low, 7 Medium

| Feature | Difficulty | Status | Notes |
|---|---|---|---|
| `sup_avg_neig` | Low | implemented | `mola.features.evolvability.sup_avg_neig` — genuine pairwise dominance via `mola.dominance` |
| `inf_avg_neig` | Low | implemented | `mola.features.evolvability.inf_avg_neig` |
| `inc_avg_neig` | Low | implemented | `mola.features.evolvability.inc_avg_neig` |
| `lnd_avg_neig` | Medium | implemented | `mola.features.evolvability.lnd_avg_neig` — local/global rank mismatch fixed |
| `lsupp_avg_neig` | Medium | implemented | `mola.features.evolvability.lsupp_avg_neig` — uses `mola.hull.supported_mask` |
| `dist_x_avg_neig` | Medium | implemented | `mola.features.evolvability.dist_x_avg_neig` — redesigned on `mola.distance.neighbour_distances`, not ported |
| `dist_f_avg_neig` | Medium | implemented | `mola.features.evolvability.dist_f_avg_neig` |
| `dist_f_dist_x_avg_neig` | Low | implemented | `mola.features.evolvability.dist_f_dist_x_avg_neig` — ratio of the two rows above |
| `diff_f_avg_neig` | Medium | implemented | `mola.features.evolvability.diff_f_avg_neig` — `mola.distance.neighbour_diff_f` |
| `diff_f_dist_x_avg_neig` | Low | implemented | `mola.features.evolvability.diff_f_dist_x_avg_neig` — ratio |
| `hv_avg_neig` | Medium | implemented | `mola.features.evolvability.hv_avg_neig` — `mola.hypervolume.singleton_hypervolume`, **not** `moocore.hv_contributions` |
| `hvd_avg_neig` | Low | implemented | `mola.features.evolvability.hvd_avg_neig` — difference over the `hv_avg_neig` array |
| `nhv_avg_neig` | Medium | implemented | `mola.features.nhv_avg_neig` — `mola.hypervolume.neighbourhood_hypervolume` |

**Ruggedness (13)** — 2 Low, 11 Medium

| Feature | Difficulty | Status | Notes |
|---|---|---|---|
| `dist_x_cor_neig` | Low | implemented | `mola.features.ruggedness.dist_x_cor_neig` — `mola.ruggedness.neighbour_correlation` |
| `dist_f_cor_neig` | Low | implemented | `mola.features.ruggedness.dist_f_cor_neig` |
| `sup_cor_neig` | Medium | implemented | `mola.features.ruggedness.sup_cor_neig` |
| `inf_cor_neig` | Medium | implemented | `mola.features.ruggedness.inf_cor_neig` |
| `inc_cor_neig` | Medium | implemented | `mola.features.ruggedness.inc_cor_neig` |
| `lnd_cor_neig` | Medium | implemented | `mola.features.ruggedness.lnd_cor_neig` |
| `lsupp_cor_neig` | Medium | implemented | `mola.features.ruggedness.lsupp_cor_neig` |
| `dist_f_dist_x_cor_neig` | Medium | implemented | `mola.features.ruggedness.dist_f_dist_x_cor_neig` — per-solution ratio, then correlated (unlike the evolvability namesake) |
| `diff_f_cor_neig` | Medium | implemented | `mola.features.ruggedness.diff_f_cor_neig` |
| `diff_f_dist_x_cor_neig` | Medium | implemented | `mola.features.ruggedness.diff_f_dist_x_cor_neig` — same per-solution-ratio pattern |
| `hv_cor_neig` | Medium | implemented | `mola.features.ruggedness.hv_cor_neig` |
| `hvd_cor_neig` | Medium | implemented | `mola.features.ruggedness.hvd_cor_neig` — `mola.hypervolume.neighbour_hypervolume_difference` |
| `nhv_cor_neig` | Medium | implemented | `mola.features.nhv_cor_neig` |

**Problem-dependent (5) — out of scope**

`d`, `k`, `seed_n`, `nd_seed_n`, `dom_seed_n` — all MO-ICOP-generator-specific, don't generalize to
arbitrary problems. `d` (number of variables) is already covered by MOLA's `NUM_VAR` metadata field.

## Design decisions (resolved 2026-07-24)
Five questions raised in the first design pass are now settled:

- **Neighbourhood definition.** Neighbourhood size `k = D` (number of decision variables);
  neighbours are the `k` nearest samples by distance in **decision** space, excluding the
  solution itself by index (not by zero-distance position, so duplicate decision vectors can't
  displace it). The SUP/INF/INC/LND/LSUP proportions always divide by the actual neighbour count,
  never an assumed `k`.
- **Normalization reference.** Two normalizers, each the global empirical min/max of pairwise
  distances across the whole sample in their own space: `(DIST_X_MIN, DIST_X_MAX)` for decision
  space, `(DIST_F_MIN, DIST_F_MAX)` for objective space. `(DIST_X_MIN, DIST_X_MAX)` normalizes
  DIST_X_AVG, DIST_X_ND_AVG, and NEIGH_DIST_X_AVG; `(DIST_F_MIN, DIST_F_MAX)` normalizes
  DIST_F_AVG and NEIGH_DIST_F_AVG — always the whole-sample range, never a range recomputed over
  a subset (non-dominated pairs, a neighbourhood). The F normalizer always accumulates from
  objective-space distance, never variable-space. Every `*_MAX` feature stays raw (see "Feature
  set" above). This rule applies uniformly across every class, including the multimodality
  class's `slo_dist_avg`/`plo_dist_avg` (`(DIST_X_MIN, DIST_X_MAX)`, same as `dist_x_nd_avg`,
  since they're all distances among a subset of the sample in variable space) and their
  `*_dist_max` siblings, which stay raw like every other `*_MAX`.
- **Feature set scope.** MOLA implements the paper's **full 49-feature set** (see "Feature set"
  and "Feature implementation matrix" above). The Spearman correlations
  (`dist_x_cor_neig`/`dist_f_cor_neig`, ruggedness class, Table 1) are genuine paper features, in
  scope along with their 11 ruggedness siblings. DIST_X_MAX_ANALYTICALLY (the box-diagonal bound —
  a static problem-geometry constant, not a sample-based landscape statistic) is confirmed absent
  from the paper's Table 1 and stays **out of scope**, alongside the 5 problem-dependent features
  (see "Feature set" above).
- **Stochasticity & reproducibility.** One characterization run = one LHS sample = one interchange
  record = one feature vector; the core has no repetition logic. Repeated-sampling workflows
  (e.g. a Shapiro-Wilk normality check across independent runs) are an outer loop over independent
  invocations, each with its own seed, rather than baking repetition into the schema or the core.
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
- **Ruggedness's per-measure correlation procedure.** One generic procedure, applied uniformly to
  all 13 evolvability measures (§4.1.4: "for each of the thirteen measures, we compute the
  Spearman correlation coefficient over each pair of neighbours"): for every directed edge
  `(i, j)` with `j∈N(i)`, append `(measure[i], measure[j])` to two parallel arrays, then one
  `scipy.stats.spearmanr` call per measure over the whole edge set. The two arrays come from one
  shared edge loop and cannot disagree in length by construction, so no length check is ever
  needed. Applies without exception to the hv-trio, `diff_f`, and `dist_f_dist_x` measures too.
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
- **Java adapter implementation** (resolved 2026-07-30). Lives in
  [`jmetal-adapter/`](jmetal-adapter/) — a standalone Maven module (`org.uma.mola:jmetal-adapter`),
  not part of a multi-module aggregator, since MOLA's root is a Python project. Depends on jMetal
  7.6-SNAPSHOT (`jmetal-core` + `jmetal-problem`, the latter bundled — not test-scoped — so built-in
  problems like ZDT1 resolve out of the box, mirroring how `jmetalpy` gives the Python adapter the
  same problems for free) from Sonatype's snapshots repository, `https://oss.sonatype.org/content/
  repositories/snapshots` — the same dependency and repository Evolver already relies on, since
  jMetal has no stable release past 6.6 on Maven Central. Key implementation choices:
  - **No MAXIMIZE/MINIMIZE negation needed.** Confirmed by grepping jMetal's `jmetal-core` and
    `jmetal-problem` source for `MAXIMIZE`: zero hits anywhere. Unlike jMetalPy's `obj_directions`
    convention (Python adapter's "Optimization sense" negation step), Java jMetal has no
    per-objective direction concept at all — every `Problem.evaluate()` is assumed to already write
    minimization-form objectives. The Java adapter is simpler here by construction, not by
    oversight.
  - **Problem resolution: reflection over a fully-qualified class name**
    (`org.uma.mola.adapter.jmetal.ProblemResolver`), e.g.
    `org.uma.jmetal.problem.multiobjective.zdt.ZDT1`. Java has no equivalent of Python's flat,
    enumerable module namespace (`getattr(jmetal.problem, name)`), so this is the natural fit
    rather than a hand-maintained name registry. `--variables N` is passed as the sole constructor
    argument only when given, since not every problem accepts it (ZDT1/ZDT4 do; most RE/RWA
    problems, fixed-dimension by construction, only have a no-arg constructor).
  - **LHS algorithm**: independent per-dimension stratum permutation (via `Collections.shuffle`,
    not a hand-rolled Fisher-Yates) plus a random offset within each stratum — the same "scrambled"
    design as the Python side's `scipy.stats.qmc.LatinHypercube(scramble=True)` (Design decisions,
    "Sampling strategy"). Bit-for-bit matching across the two implementations was never the goal,
    only a statistically equivalent one.
  - **CSV/JSON writing is hand-rolled**, not a library dependency (`InterchangeSampleWriter`): the
    schema is small, fixed, and fully known ahead of time, so adding a JSON library for it would
    cut against the adapter's explicitly "minimal" design (Architecture, above). Verified end to
    end, not just by construction: a file written by the Java adapter was read directly by `mola
    characterize` (the Python CLI) and produced a correct 49-feature result — the actual, executed
    proof the interchange contract holds across the language boundary, not merely two
    independently-written schemas that happen to agree on paper.
  - **No CLI argument-parsing library** (`Main`/`CommandLineOptions` hand-parse `--variables`/
    `--sample-size`/`--seed`): matches the jMetal/Evolver ecosystem's own convention (grepped both
    repos for picocli/JCommander/commons-cli — zero hits; example "runner" classes there use plain
    positional args or none), and the surface is small enough (one command, three optional flags)
    that a library would be net overhead. `Main.run(String[]) -> int` is kept separate from
    `Main.main` specifically so tests can invoke it without triggering `System.exit`.
- **License: MIT** (resolved 2026-07-25), matching jMetal and jMetalPy — the projects MOLA depends
  on and is designed to be used alongside. Chosen over GPL-3.0/LGPL-3.0 on adoption grounds: MOLA's
  value is as *the* reference implementation of all 49 of the paper's features, so it should be
  importable without friction from pymoo (Apache-2.0), PlatEMO, or industrial pipelines. This also
  matches the permissive norm of the scientific Python stack
  (numpy/scipy/pandas are BSD). Note that `moocore`'s **LGPL-2.1-or-later** never constrained this:
  the LGPL is explicitly designed to be linked from any license, and `moocore` is a separate
  pip/conda dependency, not vendored into MOLA's source — so MIT is unaffected. The one nuance
  worth recording: anyone bundling MOLA *and* `moocore` into a single distributable artifact (a
  frozen binary, say) takes on LGPL obligations for the `moocore` portion; normal pip/conda
  installation does not. Copyleft would in any case have been mostly moot for the dominant use
  case — running MOLA as a tool over a sample and consuming its CSV/JSON output places no
  obligations on the caller's code under any of the three licenses.

- **CLI: Typer, three commands** (resolved 2026-07-30). `src/mola/cli.py` exposes `mola sample`
  (write an interchange file from a jMetalPy problem), `mola characterize` (compute the 49
  features from an existing interchange file, from any adapter), and `mola run` (the two combined,
  no intermediate file — the most convenient entry point for scripted or AI-agent use). Typer was
  chosen over plain `argparse` specifically because it renders rich `--help` text straight from
  type hints and docstrings with very little code — the project's own explicit "very well
  documented CLI" requirement made concrete, at the cost of one new dependency (on `conda-forge`,
  unlike `jmetalpy`/`moocore`). `--output`'s format (`.json` vs `.csv`) is inferred from the
  path's suffix rather than a separate `--format` flag — one less thing to keep in sync, and an
  unrecognized suffix is a clear CLI error rather than a silent guess. Errors expected at this I/O
  boundary (unknown problem name, malformed sample file, bad `--output` suffix) are caught and
  reported as a one-line message with a non-zero exit code via Typer's own mechanism
  (`typer.echo(..., err=True)` + `typer.Exit`), not the `Ok[T] | Err` pattern
  `PYTHON_CODING_GUIDELINES.md` §4 reserves for I/O-boundary code — that type doesn't exist
  anywhere in the codebase yet, and three commands don't justify introducing it.
- **AI-agent discoverability: `llms.txt`, not `--json`/not an MCP server** (resolved 2026-07-30,
  via `AskUserQuestion`). A root-level [`llms.txt`](llms.txt) follows the `llmstxt.org` convention:
  short, link-heavy, leads with the single most useful copy-pasteable command (`mola run PROBLEM
  --variables N`). Two adjacent options were explicitly declined for now: a dedicated `--json`
  output flag (already redundant — `mola run`/`mola characterize --output result.json` already
  produce a machine-parseable result) and an MCP server exposing MOLA as a directly-callable agent
  tool (a standalone subproject with its own process/dependencies/maintenance surface, out of
  proportion to what was asked here).
- **`examples/` vs `notebooks/`** (resolved 2026-07-30). `examples/getting_started/` is
  onboarding — `quickstart.py` (the Python API, no CLI, no Jupyter) and `getting_started.ipynb` (a
  narrated "install → run → read the result" walkthrough covering both the CLI and the Python API)
  — plus `sample.csv`/`sample.json`, a small checked-in interchange-format example. Deliberately
  distinct from `notebooks/`, which documents what each of the 49 features *means*; `examples/`
  never re-explains a feature's definition, only points to `notebooks/` for that.
  `examples/benchmarks/` is a second, later-added group — `characterize_re_benchmark.py` and
  `characterize_rwa_benchmark.py`, applying MOLA to every problem in jMetalPy's RE/RWA real-world
  suites and writing one CSV row per problem — kept in its own subdirectory rather than the flat
  top level once `examples/` grew past the original onboarding pair, so the folder's two purposes
  (first-five-minutes onboarding vs. worked real-world use cases) stay visually and structurally
  separate. Both scripts go through the Python API directly, not the CLI: neither RE nor RWA is in
  jMetalPy's flat `jmetal.problem` namespace the CLI's problem resolver searches (only in
  `jmetal.problem.multiobjective.re`/`.rwa`), confirmed by direct lookup rather than assumed. RE91
  is skipped by both scripts with a printed reason: 4 of its 11 "variables" have infinite bounds
  and are overwritten with fresh Gaussian noise inside its own `evaluate()` regardless of what's
  sampled — a quirk of that one jMetalPy problem's implementation, not something a general-purpose
  LHS sampler can honor, discovered by actually running the script against all 16 RE problems.

## Not yet decided
Nothing left. Test strategy — hand-computed fixture front(s) with known landscape stats, one per
feature — was the last open item; it's now been carried out for all 49 features (129 passing
tests), not just decided. License was the other, resolved 2026-07-25 (see above).

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

CI must run the tests from day one — both `pytest` and, for the Java adapter, `mvn test`. Untested
feature logic is exactly the kind of thing that ships silent bugs.

## Status
All 49 landscape features implemented and tested, documented across four per-class Jupyter
notebooks (`notebooks/`) with real, executed examples rather than hand-typed numbers. This closes
out the feature-computation core.

The orchestrator (`mola.characterize.characterize(sample) -> dict[str, float]`) is also done: it
builds the shared substrate exactly once per sample (neighbourhood graph, ranking, pairwise/local
neighbourhood dominance, the two normalizers, the shared hypervolume reference point, one batch of
seeded adaptive walks) and calls every one of the 49 feature functions with explicit keyword
arguments — deliberately, since a couple of the ruggedness `*_cor_neig` functions don't share a
consistent `ref`/`neighbourhood` argument order, and positional calls across 49 near-identical
signatures would be a real, silent way to wire the wrong value into the wrong slot. Returns the 49
feature values plus the 3 always-reported metadata fields (`sample_size`, `num_obj`, `num_var`).

The jMetalPy adapter (`mola.adapters.jmetalpy.sample_problem(problem) -> Sample`) is also done:
Latin Hypercube samples a jMetalPy `FloatProblem` (`n = 200 * D` by default, `scramble=True`,
matching Design decisions), evaluates every sampled solution in-process, and negates any objective
whose `obj_directions[i]` is `MAXIMIZE` so the returned `Sample` is in minimization form —
confirmed against jMetalPy's own source that concrete problems (ZDT, DTLZ, the RWA suite, ...)
write *raw* objective values and rely on `obj_directions` for sense, not pre-negated ones, so this
negation is a genuine correctness step, not a formality. An end-to-end integration test
(`tests/test_integration.py`) samples a real `ZDT1` instance and feeds it straight through
`characterize()`.

The CLI (`mola`, `src/mola/cli.py`) is also done: three Typer commands (`sample`, `characterize`,
`run`, see the "CLI" Design decision), each documented in depth via its own `--help`.
`examples/getting_started/` (a runnable script, a narrated onboarding notebook, a checked-in
interchange-format example), `examples/benchmarks/` (RE/RWA real-world benchmark-suite
characterization scripts), and a root-level `llms.txt` cover onboarding and worked use cases for
human users and AI-agent tooling respectively (see the "AI-agent discoverability" and
"`examples/` vs `notebooks/`" Design decisions).

152 passing tests total (hand-computed fixtures throughout; orchestrator wiring tests that
independently rebuild the substrate to catch argument-order mistakes; adapter tests including a
synthetic mixed-direction problem that isolates the MAXIMIZE-negation logic; one end-to-end
integration test; CLI tests covering every command's success and failure paths via Typer's
`CliRunner`).

The jMetal (Java) sampling adapter (`jmetal-adapter/`, see the "Java adapter implementation" Design
decision) is also done: Latin Hypercube samples and evaluates any jMetal `DoubleProblem` resolved
by fully-qualified class name, writing the same CSV + sidecar JSON interchange format the Python
side reads — verified by an actual executed round trip, not just a schema comparison: a file
written by `jmetal-adapter`'s `Main` was read directly by `mola characterize` and produced a
correct 49-feature result. 32 passing JUnit 6 tests (Given-When-Then naming, `@Nested`/
`@DisplayName`, AAA), covering the LHS algorithm's stratification property, reflection-based
problem resolution (including its failure paths), the interchange writer, and `Main`'s argument
handling. `mvn package` produces a runnable fat jar (`jmetal-adapter-<version>-jar-with-
dependencies.jar`, `Main` as its manifest entry point).

Not yet started: the statistical-analysis companion script (Shapiro-Wilk normality check across
repeated runs) is the only piece of the original architecture left.
