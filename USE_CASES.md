# MOLA use cases

MOLA turns a continuous multi-objective problem into a **49-number feature vector** describing its
landscape. That vector is never the end goal — it is the input to something else. This document
lists what that something else can be.

The list has two sources. The first is MOLA's reference paper, [Liefooghe et al.
(GECCO 2021)](https://doi.org/10.1145/3449639.3459353), whose title is *"Landscape features **and
automated algorithm selection**"*: the features were designed as predictors, and §1 of that paper
covers the use cases they were built for. The second is MOLA itself, which goes beyond the paper's
scope — the paper only ever ran on its own MO-ICOP problem generator, whereas MOLA characterizes
any problem from any framework, which opens up uses the paper never had reason to consider.

## How to read this

- **✅ Works today** — MOLA's own output answers the question. Routine analysis of that output
  (loading a CSV, a `groupby`, a scatter plot) still counts as ✅; the substance is MOLA's.
- **⚙️ Needs more** — MOLA supplies an input, but the answer requires something MOLA cannot
  produce: measured **algorithm performance data**, or a **modelling / projection method**. Each
  entry names exactly what is missing.

Nothing here is hypothetical about MOLA's side: every ✅ is backed by code in this repository, and
the numbers quoted come from the CSVs committed under [`examples/benchmarks/`](examples/benchmarks/),
which characterize 72 problems across five suites (RE, RWA, DTLZ, and ZCAT at 2 and 3 objectives).

---

## 1. Algorithm selection and performance prediction

The paper's own use cases. **Every entry in this group is ⚙️ for the same reason**: it needs a
dataset of measured algorithm performance — MOEAs actually run on the same problems, their results
recorded — which MOLA does not produce and is not intended to. MOLA gives you the `X` matrix; this
group needs a `y` vector too. The paper built its own `y` by running four MOEAs (NSGA-II, GDE3,
MOEA/D-DE-DRA, DECMO2++) on 1 200 problems, 100 independent runs each.

### 1.1 Feature–performance correlation analysis ⚙️

Correlate each of the 49 features against how well an algorithm performs, one feature at a time
(§4.2, Fig. 1). The cheapest entry point in this group: no model to train, just a Spearman
correlation per feature. It answers "which landscape properties go with good or bad performance
for this algorithm?" and produces the kind of picture that guides everything below.

**Needs:** performance data. No model.

### 1.2 Algorithm performance prediction ⚙️

Train a regression model from features to expected performance, so you can estimate how well an
algorithm will do on an unseen problem without running it (§4.3). The paper used random forests
and reached R² between 0.86 and 0.89 across its four MOEAs — over 85% of the variance in
hypervolume explained by the features alone.

**Needs:** performance data, plus a regression model (the paper used `randomForest` in R;
scikit-learn is the obvious Python equivalent).

### 1.3 Automated algorithm selection ⚙️

The paper's headline result: train a classifier that, given a problem's features, recommends which
algorithm to run (§5). Reported accuracy on unseen problems is worth stating precisely, because
there are two different numbers — the classifier picks the single best algorithm in **more than
75%** of cases, and picks *one of* the statistically indistinguishable best algorithms in **more
than 85%**. In hypervolume terms it lands within 0.5% of the virtual best (an oracle that always
picks correctly), and it more than halves the error of a feature-less baseline.

**Needs:** performance data, plus a classification model.

### 1.4 Interpretable selection rules ⚙️

The same goal as 1.3 but optimizing for explanation rather than accuracy: fit a shallow decision
tree and read the rules off it (§5.1, Fig. 4). The paper's depth-4 CART tree reaches 22.58% error —
worse than the random forest — but tells you *why*: its root split is on `dist_f_max`, i.e. how
spread out the sampled solutions are in objective space, with NSGA-II favoured when they are more
scattered and MOEA/D-DE-DRA otherwise. Use this when you want to understand the landscape–algorithm
relationship, not just exploit it.

**Needs:** performance data, plus a decision-tree model.

### 1.5 Feature importance analysis ⚙️

Rank the features by how much they contribute to a trained model's predictions (§4.3 Fig. 2, §5.1
Fig. 3), which tells you which landscape properties actually matter. The paper's finding is
non-obvious and worth knowing before you decide to compute a reduced feature set: the two
hypervolume-based **evolvability** features `hv_avg_neig` and `nhv_avg_neig` top the importance
ranking for all four MOEAs, while for *discriminating between* algorithms the single most
important feature is `dist_f_max`. Multimodality and ruggedness features rank low for predicting
performance yet matter for telling algorithms apart — so importance depends on which question you
are asking.

**Needs:** performance data, plus a model that exposes feature importances.

---

## 2. Benchmark and problem analysis

MOLA's own territory, beyond the paper. These need no algorithm runs at all.

### 2.1 Characterizing a benchmark suite ✅

Run MOLA over every problem in a suite and get one row of 49 features per problem. Already done
four times over in [`examples/benchmarks/`](examples/benchmarks/) — RE, RWA, DTLZ, and ZCAT — in
50 to 75 lines per script, much of it docstring. This is the foundation the rest of this section
builds on.

### 2.2 Benchmark diversity and redundancy ⚙️

Given a suite's feature matrix, ask whether its problems are actually landscape-distinct or whether
they cluster — i.e. whether a suite is as diverse as it claims. There is already a visible hint in
the committed data: across all 20 ZCAT problems at 2 objectives, `nd_n` spans only 0.0017 to
0.0022, so on that axis the suite is nearly uniform. Whether that holds across the other 48
features is exactly the question this use case answers.

**Needs:** a clustering or dimensionality-reduction step over the feature matrix — light work
(pandas plus scikit-learn), but not something MOLA does.
[`FEATURE_ANALYSIS.md`](FEATURE_ANALYSIS.md) is a worked instance of this use case, and
[`analyze_feature_set.py`](examples/benchmarks/analyze_feature_set.py) the script behind it.

### 2.3 Placing a real-world problem against synthetic benchmarks ⚙️

"Is my real-world problem anything like the synthetic ones algorithms are usually tuned on?" With
RE and RWA (real-world) and DTLZ and ZCAT (synthetic) characterized in the same feature space, this
becomes a nearest-neighbour lookup between rows of committed CSVs. Useful both for choosing which
benchmark results transfer to your problem, and for arguing that a benchmark suite is or isn't
representative.

**Needs:** a distance or similarity computation over the feature matrix — and careful attention to
[the comparability caveat](#before-you-compare-problems) below, which bites hardest here.

### 2.4 Objective-count scaling ✅

Study how landscape features change as the number of objectives grows. The paper's own conclusions
name this as future work — it only ever ran bi-objective problems — while MOLA handles any `M`
throughout: [`characterize_zcat_benchmark.py`](examples/benchmarks/characterize_zcat_benchmark.py)
already characterizes the same 20 problems at M=2 and M=3, and the RWA suite reaches M=7
(`Ahmad2017`). The committed data shows the effect immediately: ZCAT's `nd_n` rises from
0.0017–0.0022 at M=2 to 0.0077–0.0118 at M=3, a roughly fourfold increase in the proportion of
non-dominated solutions.

### 2.5 Instance-space analysis ⚙️

Project the 49-dimensional feature space down to two dimensions and plot problems as points, in the
style of Smith-Miles' instance space analysis, to see the "map" of a problem domain — where suites
sit, which regions are crowded, and which are empty and therefore under-tested.

**Needs:** a dimensionality-reduction method (PCA, t-SNE, UMAP, or the projection used in the
instance-space literature).

---

## 3. Quality assurance and methodology

### 3.1 Sanity-checking a problem implementation ✅

Degenerate feature values are a signal that something is wrong with a problem's implementation or
its bounds. This is not hypothetical — characterizing the RE suite for this repository surfaced two
real cases. `RE61` scores `nd_n = 1.000`, meaning *every* sampled solution is non-dominated, and it
also has by far the largest `hv` of any problem characterized here (4.0×10³⁰). Separately, `RE91`
declares four variables with infinite bounds that its own `evaluate()` overwrites with fresh
Gaussian noise, which no sampler can honour — it is skipped by the RE script for that reason.
Neither was found by reading code; both fell out of running MOLA and looking at the numbers.

### 3.2 Cross-framework consistency checking ✅

The same problem implemented in jMetal (Java) and in jMetalPy should produce statistically
indistinguishable feature vectors. If it doesn't, one of the two implementations is wrong. MOLA's
two adapters ([`jmetal-adapter/`](jmetal-adapter/) and
[`mola.adapters.jmetalpy`](src/mola/adapters/jmetalpy.py)) write the same interchange format, so
both sides land in a directly comparable form. Note what this tests: not MOLA, but the
**frameworks**.

### 3.3 Sampling budget and cost control ✅

Computing MOLA's features costs exactly `n` evaluations — the sample size, and nothing more. That
makes characterization cost a knob you set (`--sample-size` on the CLI, `sample_size=` in the API),
defaulting to the paper's `n = 200·D`. The paper's §5.2 result is the useful one here: a sample of
just **500 solutions — 1 to 5% of a typical search budget — was enough to discriminate between
MOEAs as accurately as the full `200·D` sample**. So if features are feeding a selection decision,
the default is likely more than you need, and the saving comes straight off your evaluation budget.

### 3.4 Feature stability under resampling ⚙️

The features are statistics *of a sample*, not invariants of the problem: run MOLA twice with
different seeds and you get two different vectors. Quantifying that spread tells you which features
are trustworthy at a given sample size and which are noise. This is precisely the Shapiro-Wilk
companion script described in `CLAUDE.md`'s architecture — planned, and the one remaining unbuilt
piece of the original design.

**Needs:** an outer loop over seeded runs plus a statistical test. MOLA supports the loop today
(each run is independent and takes its own seed); the analysis script does not exist yet.

---

## 4. Ecosystem

### 4.1 Training-set design for automatic algorithm configuration ⚙️

Tools that automatically configure metaheuristics — such as [Evolver](https://github.com/jMetal/Evolver)
or irace — meta-optimize a configuration against a *training set* of problems, which is usually
chosen by convention. Landscape features offer a principled alternative: pick a training set that
is diverse in feature space rather than arbitrary, and verify that it actually covers the same
region as the problems you intend to deploy on. A configuration tuned on a training set that
occupies a different feature region than its target has no particular reason to transfer.

**Needs:** a selection or coverage criterion over the feature matrix, and integration with the
configurator's own workflow.

---

## Before you compare problems

Most of section 2 involves comparing feature vectors *across* problems, and not all 49 features
support that. The rule (full rationale in `CLAUDE.md`'s "Normalization reference" decision):

| Feature kind | Comparable across problems? |
|---|---|
| Proportions and correlations — `nd_n`, `supp_n`, `f_cor`, `fdc`, every `*_cor_neig` | **Yes.** Dimensionless by construction, bounded in [0, 1] or [-1, 1]. |
| `*_AVG` distance features — `dist_x_avg`, `dist_f_avg`, `dist_x_nd_avg`, … | **Relatively.** Normalized against *their own sample's* empirical min–max range, so they say "how spread out, relative to this problem's own spread" — not an absolute quantity. |
| `*_MAX` and every hypervolume feature — `dist_f_max`, `hv`, `hv_avg_neig`, `nhv_avg_neig`, … | **No.** Reported raw, in the problem's own objective units. |

The third row is not a theoretical concern. Across the five suites characterized in
[`examples/benchmarks/`](examples/benchmarks/), `hv` ranges from **0.53** (`Vaidyanathan2004`, RWA)
to **4.0×10³⁰** (`RE61`, RE) — thirty orders of magnitude, driven almost entirely by objective
scale rather than by landscape structure. Any clustering, distance, or projection over raw features
will be dominated by that spread. Standardize per feature across your problem set first, or
restrict yourself to the dimensionless rows.

This is a deliberate design choice, not an oversight: there is no universally valid distance or
objective range spanning problems as different as ZDT (unit hypercube) and RE21 (engineering
units), so MOLA normalizes *within* a sample and leaves cross-problem normalization to the analysis
that needs it — which is the only place the right reference set is known.

---

## References

- Arnaud Liefooghe, Sébastien Verel, Benjamin Lacroix, Alexandru-Ciprian Zăvoianu, and John McCall.
  2021. Landscape features and automated algorithm selection for multi-objective interpolated
  continuous optimisation problems. *GECCO '21*, 421–429.
  <https://doi.org/10.1145/3449639.3459353>
- [`README.md`](README.md) — installation and CLI usage.
- [`CLAUDE.md`](CLAUDE.md) — full design brief, the feature-by-feature matrix, and every design
  decision behind the numbers.
- [`FEATURE_ANALYSIS.md`](FEATURE_ANALYSIS.md) — a critical look at the feature set itself:
  redundancy, effective dimensionality, and what it does not capture. Read it before treating the
  49 features as independent descriptors.
- [`notebooks/`](notebooks/) — what each of the 49 features means, with executed examples.
- [`examples/benchmarks/`](examples/benchmarks/) — the committed feature CSVs referenced throughout.
