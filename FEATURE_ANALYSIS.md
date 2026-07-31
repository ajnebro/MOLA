# A critical look at the 49-feature set

An internal analysis of the feature set MOLA implements, based on the 72 problems characterized
under [`examples/benchmarks/`](examples/benchmarks/).

## What this is, and what it is not

This is **not a rebuttal of [Liefooghe et al. (GECCO 2021)](https://doi.org/10.1145/3449639.3459353)**.
That paper designed its features for a specific setting — bi-objective problems from its own
MO-ICOP generator, all sharing the variable space `[-5,5]^d`, used to discriminate between four
MOEAs — and within that setting the features demonstrably work, reaching over 85% accuracy at
picking one of the statistically best algorithms.

The observations below arise almost entirely from taking those features **outside** that setting,
which is precisely what MOLA does: arbitrary problems, arbitrary variable spaces, arbitrary
objective counts, arbitrary frameworks. A limitation that appears only outside a paper's stated
scope is a boundary of validity, not an error. Knowing where that boundary lies is what makes the
features usable in the wider setting.

Claims here are of three kinds, and they are not equally strong:

- **Structural** — follows from the feature definitions or MOLA's source code. Certain, independent
  of any data.
- **Empirical** — measured over the 72 characterized problems. Indicative, with the caveats in
  [Limitations](#limitations-of-this-analysis).
- **Judgment** — my assessment. Argued, not proven.

## Method

Every number is produced by
[`examples/benchmarks/analyze_feature_set.py`](examples/benchmarks/analyze_feature_set.py), run
over the committed CSVs: 72 problems across five suites (RE, RWA, DTLZ, ZCAT at 2 and 3
objectives), one sample per problem, seed 42, `n = 200·D`. Re-run it to re-derive the table below
after any change to the data.

---

## Findings

### 1. The effective dimensionality is about 5, not 49 — *empirical + structural*

Three features are **exact algebraic functions of other features**, which Table 1 states openly as
their definition. Reconstructing them from their parents reproduces the stored value to floating
point:

| Feature | Reconstruction | Max error over 72 problems |
|---|---|---|
| `dist_f_dist_x_avg_neig` | `dist_f_avg_neig / dist_x_avg_neig` | 1.9e-07 |
| `diff_f_dist_x_avg_neig` | `diff_f_avg_neig / dist_x_avg_neig` | 3.9e-08 |
| `nd_per_plo` | `nd_n / plo_n` | 9.6e-16 |

Beyond those, **23 of the 1 176 feature pairs correlate above |ρ| = 0.95**, led by
`rank_avg`~`rank_ent` (0.9965), `hv_avg_neig`~`nhv_avg_neig` (0.9954) and
`dist_f_cor_neig`~`diff_f_cor_neig` (0.9943). A PCA over the standardized features gives the
overall picture:

| Principal components | Variance explained |
|---|---|
| 1 | 36.0% |
| 2 | 54.0% |
| 3 | 67.7% |
| 5 | **82.6%** |
| 10 | 94.9% |

Part of this is structural and by design: the 13 ruggedness features are, by construction, the
neighbour-correlation of the 13 evolvability measures. If two evolvability measures are correlated,
their `_cor_neig` counterparts inherit that correlation. The class duplicates the one above it by
definition.

**Implication.** The 49 features should not be treated as 49 independent descriptors — in any
distance, clustering, or regularized model, they are closer to 5–10 effective degrees of freedom.

### 2. Four features describe the sampler, not the problem — *structural*

`dist_x_avg`, `dist_x_max`, `dist_x_avg_neig` and `dist_x_cor_neig` are computed **entirely from
the decision-variable sample**; no objective value enters them at any point. Two problems that
share variable bounds, sampling design and seed therefore receive identical values regardless of
how different their objective functions are.

The ZCAT suite makes this visible, since all 20 problems share `D = 30` and the same bounds:

```text
across the 20 ZCAT problems at M=2, D=30:
  dist_x_avg           distinct = 1   (0.469915)
  dist_x_max           distinct = 1   (68.155518)
  dist_x_avg_neig      distinct = 1   (23.929948)
  dist_x_cor_neig      distinct = 1   (0.197124)
  dist_f_max           distinct = 14  (objective-space contrast)
```

Twenty problems designed to differ structurally, four features that cannot tell them apart at all —
while an objective-space feature separates 14 of them. When these four *do* vary across problems,
what varies is the **geometry of the bounding box**, not the landscape.

There is an internal tension worth recording here. `CLAUDE.md` excludes a candidate feature
`DIST_X_MAX_ANALYTICALLY` — the box diagonal — on the grounds that it is "a static problem-geometry
constant, not a sample-based landscape statistic". But `dist_x_max` is a sample estimate of that
same constant: measured 68.16 against an analytic diagonal of 97.24 for ZCAT at `D = 30`, a ratio
of 0.70 that reflects how far an LHS sample falls short of the corners, not anything about the
problem.

**Implication.** These four are best read as problem-metadata proxies. They are not wrong, but they
carry no landscape information, and in a fixed-design study they are constants.

### 3. Two thirds of the features track D or M on their own — *empirical*

**34 of 49 features reach |ρ| > 0.5 against `num_var` or `num_obj` alone**, with several close to
being pure dimension proxies:

| Feature | \|ρ\| vs D | \|ρ\| vs M |
|---|---|---|
| `dist_x_cor_neig` | **0.960** | 0.302 |
| `eval_aws` | 0.901 | 0.560 |
| `slo_n` | 0.885 | 0.144 |
| `dist_f_cor_neig` | 0.875 | 0.287 |
| `diff_f_cor_neig` | 0.875 | 0.298 |

The likely driver is a design decision rather than the features themselves: the neighbourhood size
is fixed at **`k = D`**, so the 34 neighbourhood-derived features measure local structures whose
very definition changes with dimension. Comparing a `D = 2` problem (each solution has 2 neighbours)
against a `D = 30` problem (30 neighbours) compares different objects.

This compounds with a limitation `CLAUDE.md` already records: at `D = 30`, 6 000 points in
30 dimensions are sparse enough that "nearest neighbours" are not local in any useful sense.

**Implication.** In a study spanning several dimensions, part of what a model learns from these
features is the problem's dimension — which is usually known anyway.

### 4. The adaptive walk is degenerate at this sampling density — *empirical*

| Feature | min | median | max |
|---|---|---|---|
| `length_aws` | 0.000 | **1.250** | 2.533 |
| `eval_aws` | 3.000 | 41.617 | 53.800 |
| `slo_n` | 0.010 | 0.016 | 0.611 |
| `plo_n` | 0.067 | 0.214 | 1.000 |

`length_aws` is **exactly zero for 3 problems and below 1 for 24 of 72**. Walks terminate almost
immediately: a median walk takes a single step before reaching a Pareto local optimum.

The reason is structural. In single-objective landscape analysis, adaptive-walk length is
informative because the walk explores the actual landscape. Here the walk is simulated over a
precomputed graph of `200·D` sampled points — deliberately, since the paper is explicit that this
costs no extra evaluations — and that graph is too sparse to support a long dominating chain. Two
of the three features MOLA's own matrix rates "High" difficulty therefore yield nearly a constant.

The same caveat applies more mildly to `slo_n` (median 0.016): a "local optimum" here means "no
sampled neighbour improves", which is a property of the sampling density as much as of the problem.

### 5. The paper's most important feature is nearly `hv` — *empirical*

The paper's own importance analysis (Fig. 2) ranks `hv_avg_neig` top for all four MOEAs. In this
data, **ρ(`hv_avg_neig`, `hv`) = 0.978** and **ρ(`hv_avg_neig`, `nhv_avg_neig`) = 0.9954**.

Two things follow. First, `hv_avg_neig` is — despite its `_neig` suffix — **not a neighbourhood
feature at all**: it is each solution's own box hypervolume against the shared reference point,
averaged over the sample, and it takes no neighbourhood argument. It is one of only 15 features
that do not touch the neighbourhood graph. The name is inherited from Table 1, where the
qualifier "average **(single)** solution's hypervolume" carries the distinction.

Second, and more substantively: since algorithm performance in the paper is measured *as*
normalised hypervolume, a top-ranked predictor that is itself essentially the sample's hypervolume
is closer to a restatement of the target than to a landscape property. **The authors note this
themselves** — "the fact that algorithm performance is measured in terms of hypervolume partly
explains the importance of these features" — so this is an amplification of their own caveat, not a
counter-claim. It is worth keeping in view when reusing the importance ranking to justify a reduced
feature set.

### 6. One legitimate problem yields five undefined features — *empirical*

`RE61` produces `NaN` for `sup_cor_neig`, `inf_cor_neig`, `inc_cor_neig`, `lnd_cor_neig` and
`lsupp_cor_neig`. The cause is correct behaviour, not a defect: every sampled solution is mutually
incomparable (`nd_n = 1.0`, `inc_avg_neig = 1.0`), so the underlying measure is constant and
Spearman's coefficient is undefined.

**Implication.** A perfectly valid problem can return an incomplete feature vector, so any model
built on these features needs an imputation policy. It is also a reminder that `RE61` itself
deserves inspection — a 6-objective problem in 3 variables where nothing dominates anything.

---

## Is the set complete?

No — and the gaps are systematic rather than incidental. Ordered by how much I think each would
add (*judgment*, though the first two are widely established in the landscape-analysis literature):

**1. Pareto front geometry.** The most serious gap. Nothing describes the *shape* of the
approximated front: convexity beyond the coarse proxy `supp_n`, **disconnectedness**, or
**degeneracy**. This matters concretely — DTLZ5 and DTLZ6 have degenerate fronts, DTLZ7 and ZDT3
disconnected ones, and decomposition-based algorithms such as MOEA/D are highly sensitive to both.
The information is already present in the sample; no extra evaluations would be needed.

**2. Variable interaction and separability.** The dominant driver of difficulty in continuous
optimization, and entirely absent. There is a clean historical explanation: the paper states it is
transferring features from *combinatorial* multi-objective landscape analysis, and separability is
not a concept that transfers — it would have to be designed for the continuous case from scratch.

**3. Per-objective scaling and conditioning.** All objective-space features are aggregates. Nothing
captures the relative ranges of individual objectives, which determines whether an algorithm needs
normalization and strongly affects decomposition- and indicator-based methods.

**4. Classical ruggedness.** The "ruggedness" class here is the neighbour-correlation of
evolvability measures — a valid notion, but a different one from the random-walk autocorrelation
and correlation length used in classical fitness landscape analysis. That family is absent.

**5. Constraints.** No feature uses constraint values. `CLAUDE.md` scopes this out deliberately and
that is right for the paper's unconstrained benchmark, but RE and RWA are real-world suites where
constraints are part of the problem.

The paper's own conclusions point the same way, proposing that "additional features could be
considered and combined as well, including single- and multi-objective continuous landscape
features" — that is, integration with ELA.

## Recommendations

*Judgment, in the order I would act on them:*

1. **Add front-geometry features** (disconnectedness, curvature, degeneracy). Best return on
   effort, and computable from the existing sample at zero evaluation cost.
2. **Add a small set of per-objective ELA features** (separability, non-linearity) over the same
   sample. Also free in evaluations, and it is the direction the paper's own conclusions propose.
3. **Document the redundancy rather than removing it.** Dropping features would break comparability
   with the paper, which is MOLA's main reason to exist. Recording that the effective
   dimensionality is 5–10 is enough to stop anyone treating the 49 as independent.
4. **Expose `k` as a parameter.** Keep `k = D` as the default for comparability, but make the
   coupling between neighbourhood size and dimension visible and adjustable.

## Limitations of this analysis

Stated plainly, because they bound how far the empirical claims carry:

- **72 problems, one seed each.** Feature values are statistics of a sample; a single seed per
  problem gives no estimate of their variance. Quantifying that is exactly the unbuilt
  stability analysis in [`USE_CASES.md`](USE_CASES.md) §3.4.
- **Five heterogeneous suites pooled together.** Correlations computed across heterogeneous groups
  can mislead — two suites that are internally uncorrelated can appear correlated when pooled
  (Simpson's paradox). Finding 3 in particular would be stronger if reproduced within suites.
- **Different problem sizes.** The pooled set spans `D` from 2 to 30 and `M` from 2 to 7, which is
  what makes Finding 3 visible in the first place, but also means the pooled correlations partly
  measure that spread.

The **structural** findings do not depend on any of this: the algebraic redundancies (Finding 1),
the variable-space-only features (Finding 2), the 34/49 neighbourhood count and the `hv_avg_neig`
naming (Finding 5) follow from the definitions and the source code, and would hold for any dataset.

## See also

- [`USE_CASES.md`](USE_CASES.md) — what the feature set is for; §2.2 is the use case this document
  instantiates.
- [`CLAUDE.md`](CLAUDE.md) — the full feature matrix and every design decision referenced here.
- [`notebooks/`](notebooks/) — what each individual feature means.
