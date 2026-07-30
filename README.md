# MOLA — Multi-Objective Landscape Analyzer

**🚧 Work in progress.** The landscape-feature engine is complete — all 49 features implemented
and tested, tied together by an orchestrator that computes all of them for a sample in one call.
The jMetal (Java) and jMetalPy sampling adapters and a CLI are still to come. See
[`CLAUDE.md`](CLAUDE.md) for the full design brief.

## What it does

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
per-feature breakdown, and [`notebooks/`](notebooks/) for a worked example of every feature against
real, executed data.

## Design principle

MOLA's core is a framework-independent analyzer: it never calls a problem's `evaluate()` directly,
only ever consuming a documented structured sample (decision vectors + objective vectors +
minimal problem metadata). Thin per-framework **adapters** — jMetal (Java), jMetalPy (Python),
and potentially others — sample and evaluate problems in their native ecosystem and hand the result
to the core in that shared format.

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
`jmetalpy`) is LGPL-2.1-or-later, unlike the rest of MOLA's MIT/BSD-family dependencies. As a
separately-installed dependency this places no obligation on MOLA's own MIT terms — see
[`CLAUDE.md`](CLAUDE.md) for the details.

## Development

This project follows:
- [`GIT_GUIDELINES.md`](GIT_GUIDELINES.md) — commit conventions
- [`JAVA_CODING_GUIDELINES.md`](JAVA_CODING_GUIDELINES.md) — Java code style (jMetal adapter)
- [`PYTHON_CODING_GUIDELINES.md`](PYTHON_CODING_GUIDELINES.md) — Python code style (core engine,
  jMetalPy adapter)

See [`CLAUDE.md`](CLAUDE.md) for the full architecture, feature set, and design decisions.

## License

[MIT](LICENSE), matching jMetal and jMetalPy.
