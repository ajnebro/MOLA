# Examples

Two independent groups, kept in separate subdirectories on purpose — see `CLAUDE.md`'s Design
decisions, "`examples/` vs `notebooks/`", for the full rationale.

- [`getting_started/`](getting_started/) — **onboarding.** A minimal Python-API script
  (`quickstart.py`), a narrated "install → run → read the result" notebook covering both the CLI
  and the Python API (`getting_started.ipynb`), and a small checked-in interchange-format sample
  (`sample.csv` / `sample.json`). Start here if you're new to MOLA.
- [`benchmarks/`](benchmarks/) — **worked benchmark-suite use cases.** Scripts that apply MOLA to
  every problem in a jMetalPy benchmark suite and write one CSV row per problem:
  `characterize_re_benchmark.py`, `characterize_rwa_benchmark.py` (real-world problems, neither
  suite in jMetalPy's flat `jmetal.problem` namespace, so these go through the Python API rather
  than the CLI), `characterize_dtlz_benchmark.py` (the synthetic DTLZ1-DTLZ7 suite, 3 objectives by
  default — these *are* in the flat namespace, so a single one can also be run via `mola run
  DTLZ2`), and `characterize_zcat_benchmark.py` (the synthetic ZCAT1-ZCAT20 suite, run once at 2
  objectives and once at 3, everything else at its default — **requires jMetalPy installed from a
  source checkout**, since ZCAT support isn't in the `jmetalpy` release on PyPI yet). Generated
  output: `re_features.csv`, `rwa_features.csv`, `dtlz_features.csv`, `zcat_2obj_features.csv`,
  `zcat_3obj_features.csv`.

For what each of the 49 landscape features actually *means*, see [`notebooks/`](../notebooks/)
instead — neither group here repeats that content.
