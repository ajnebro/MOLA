# MOLA — Multi-Objective Landscape Analyzer

**🚧 Work in progress.** MOLA is currently in the design phase — no code has been implemented yet.
See [`CLAUDE.md`](CLAUDE.md) for the full design brief driving the initial implementation.

## What it will do

MOLA characterizes the landscape features of continuous multi-objective optimization problems,
independent of the framework the problem is implemented in. It extracts the feature set defined in:

> Arnaud Liefooghe, Sébastien Verel, Benjamin Lacroix, Alexandru-Ciprian Zăvoianu, and John McCall.
> 2021. Landscape features and automated algorithm selection for multi-objective interpolated
> continuous optimisation problems. *Proceedings of the Genetic and Evolutionary Computation
> Conference* (GECCO '21), 421–429. https://doi.org/10.1145/3449639.3459353

These features cover distances among sampled solutions in variable/objective space, neighbourhood
dominance structure, and non-dominated-sorting rank statistics.

## Design principle

MOLA's core will be a framework-independent analyzer: it never calls a problem's `evaluate()`
directly, only ever consuming a documented structured sample (decision vectors + objective vectors
+ minimal problem metadata). Thin per-framework **adapters** — jMetal (Java), jMetalPy (Python),
and potentially others — sample and evaluate problems in their native ecosystem and hand the result
to the core in that shared format.

## Origin

MOLA is a from-scratch rewrite of [MOORPHOLOGY](https://gitlab.com/jfaldanam-phd/moorphology), a
jMetal-6.1 Java implementation of the same feature set. The rewrite fixes several correctness bugs
found in MOORPHOLOGY's feature computations and removes its hard coupling to a single framework.

## Development

This project follows:
- [`GIT_GUIDELINES.md`](GIT_GUIDELINES.md) — commit conventions
- [`JAVA_CODING_GUIDELINES.md`](JAVA_CODING_GUIDELINES.md) — Java code style (jMetal adapter)
- [`PYTHON_CODING_GUIDELINES.md`](PYTHON_CODING_GUIDELINES.md) — Python code style (core engine,
  jMetalPy adapter)

See [`CLAUDE.md`](CLAUDE.md) for the full architecture, feature set, and design decisions.
