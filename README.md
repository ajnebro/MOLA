# MOLA — Multi-Objective Landscape Analyzer

**🚧 Work in progress.** The landscape-feature engine is complete — all 49 features implemented
and tested, tied together by an orchestrator that computes all of them for a sample in one call.
Both sampling adapters (jMetalPy and jMetal/Java) and a documented CLI are done too, so problems
defined in either ecosystem can be characterized end to end. See [`CLAUDE.md`](CLAUDE.md) for the
full design brief.

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

**venv:** create and activate a Python 3.11+ virtual environment, then `pip install -e .` from the
repository root (installs numpy, pandas, scipy, jmetalpy, moocore, typer — everything listed in
[`environment.yml`](environment.yml) — plus registers the `mola` command below).

This doesn't cover the jMetal (Java) sampling adapter, which needs Java 21+ and Maven instead —
see "Java (jMetal) adapter" below.

Note: `moocore` (used directly for hypervolume-based features, and pulled in transitively via
`jmetalpy`) is LGPL-2.1-or-later, unlike the rest of MOLA's MIT/BSD-family dependencies. As a
separately-installed dependency this places no obligation on MOLA's own MIT terms — see
[`CLAUDE.md`](CLAUDE.md) for the details.

## CLI usage

Once installed, the `mola` command has three subcommands — each documented in full via its own
`mola <command> --help`, including a copy-pasteable example:

```bash
# Sample, evaluate, and characterize a jMetalPy problem in one step -- no file needed.
mola run ZDT1 --variables 5 --sample-size 1000 --seed 42

# ...or split it in two: write a reusable interchange sample file first...
mola sample ZDT1 sample.csv --variables 5 --sample-size 1000 --seed 42

# ...then compute its features (works on a sample file from any adapter, not just this one).
mola characterize sample.csv --output result.json
```

Every command prints its result as plain `key: value` lines; add `--output result.json` (or
`.csv`) to also save the full 52-field result to a file. See [`examples/`](examples/) — split into
[`getting_started/`](examples/getting_started/) (a runnable script and a narrated walkthrough of
both the CLI and the Python API) and [`benchmarks/`](examples/benchmarks/) (two ready-made
scripts, [`characterize_re_benchmark.py`](examples/benchmarks/characterize_re_benchmark.py) and
[`characterize_rwa_benchmark.py`](examples/benchmarks/characterize_rwa_benchmark.py), which
characterize every problem in jMetalPy's RE and RWA real-world suites and write one CSV row per
problem) — and [`llms.txt`](llms.txt) for a short summary aimed at AI-agent tooling.

## Java (jMetal) adapter

[`jmetal-adapter/`](jmetal-adapter/) is a standalone Maven module (Java 21+) that Latin-Hypercube-
samples and evaluates any jMetal `DoubleProblem`, writing the same interchange file format the
Python CLI reads — the whole point being that `mola characterize` doesn't care which adapter
produced its input. Build and run it directly:

```bash
cd jmetal-adapter
mvn package
java -jar target/jmetal-adapter-*-jar-with-dependencies.jar \
    org.uma.jmetal.problem.multiobjective.zdt.ZDT1 sample.csv \
    --variables 5 --sample-size 1000 --seed 42

# Back on the Python side:
mola characterize sample.csv
```

The first positional argument is a jMetal problem's fully-qualified class name (Java has no
enumerable module namespace to look up a short name in, unlike jMetalPy). Run the jar with no
arguments, or `--help`, for the full option list.

## Development

This project follows:
- [`GIT_GUIDELINES.md`](GIT_GUIDELINES.md) — commit conventions
- [`JAVA_CODING_GUIDELINES.md`](JAVA_CODING_GUIDELINES.md) — Java code style (jMetal adapter)
- [`PYTHON_CODING_GUIDELINES.md`](PYTHON_CODING_GUIDELINES.md) — Python code style (core engine,
  jMetalPy adapter)

See [`CLAUDE.md`](CLAUDE.md) for the full architecture, feature set, and design decisions.

## License

[MIT](LICENSE), matching jMetal and jMetalPy.
