# MOLA — Multi-Objective Landscape Analyzer

**🚧 Work in progress.** MOLA is currently in the design phase — no code has been implemented yet.
See [`CLAUDE.md`](CLAUDE.md) for the full design brief driving the initial implementation.

## What it will do

MOLA characterizes the landscape features of continuous multi-objective optimization problems,
independent of the framework the problem is implemented in. It extracts the full feature set
defined in:

> Arnaud Liefooghe, Sébastien Verel, Benjamin Lacroix, Alexandru-Ciprian Zăvoianu, and John McCall.
> 2021. Landscape features and automated algorithm selection for multi-objective interpolated
> continuous optimisation problems. *Proceedings of the Genetic and Evolutionary Computation
> Conference* (GECCO '21), 421–429. https://doi.org/10.1145/3449639.3459353

**49 landscape features across four classes** — global, multimodality, evolvability, and
ruggedness — covering distances among sampled solutions in variable/objective space, multimodality
and evolvability measures (including hypervolume-based ones), neighbourhood dominance structure,
non-dominated-sorting rank statistics, and landscape ruggedness (neighbour-to-neighbour
correlations). See [`CLAUDE.md`](CLAUDE.md)'s "Feature implementation matrix" for the full,
per-feature breakdown.

## Design principle

MOLA's core will be a framework-independent analyzer: it never calls a problem's `evaluate()`
directly, only ever consuming a documented structured sample (decision vectors + objective vectors
+ minimal problem metadata). Thin per-framework **adapters** — jMetal (Java), jMetalPy (Python),
and potentially others — sample and evaluate problems in their native ecosystem and hand the result
to the core in that shared format.

## Origin

MOLA is a from-scratch rewrite of [MOORPHOLOGY](https://gitlab.com/jfaldanam-phd/moorphology), a
jMetal-6.1 Java implementation of a subset of the same feature set (~19 of the paper's 49). The
rewrite fixes several correctness bugs found in MOORPHOLOGY's feature computations, removes its
hard coupling to a single framework, and implements the paper's full feature set.

## Setup

MOLA's Python core needs a dedicated virtual environment — either Conda or `venv` — before
installing dependencies.

**Conda (recommended — matches the pinned versions used during development):**

```bash
conda env create -f environment.yml
conda activate MOLA
```

**venv:** create and activate a Python 3.11+ virtual environment, then `pip install` the same
packages listed in [`environment.yml`](environment.yml) (numpy, pandas, scipy, jmetalpy, moocore,
plus pytest/ruff for development).

This doesn't cover the jMetal (Java) sampling adapter, which needs Java 21+ and Maven instead.

Note: `moocore` (used directly for hypervolume-based features, and pulled in transitively via
`jmetalpy`) is LGPL-2.1-or-later, unlike the rest of MOLA's MIT/BSD-family dependencies — see
[`CLAUDE.md`](CLAUDE.md) for the license-compatibility note.

## Development

This project follows:
- [`GIT_GUIDELINES.md`](GIT_GUIDELINES.md) — commit conventions
- [`JAVA_CODING_GUIDELINES.md`](JAVA_CODING_GUIDELINES.md) — Java code style (jMetal adapter)
- [`PYTHON_CODING_GUIDELINES.md`](PYTHON_CODING_GUIDELINES.md) — Python code style (core engine,
  jMetalPy adapter)

See [`CLAUDE.md`](CLAUDE.md) for the full architecture, feature set, and design decisions.
