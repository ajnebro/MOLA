# Examples

Two independent groups, kept in separate subdirectories on purpose — see `CLAUDE.md`'s Design
decisions, "`examples/` vs `notebooks/`", for the full rationale.

- [`getting_started/`](getting_started/) — **onboarding.** A minimal Python-API script
  (`quickstart.py`), a narrated "install → run → read the result" notebook covering both the CLI
  and the Python API (`getting_started.ipynb`), and a small checked-in interchange-format sample
  (`sample.csv` / `sample.json`). Start here if you're new to MOLA.
- [`benchmarks/`](benchmarks/) — **worked real-world use cases.** Two scripts that apply MOLA to
  every problem in jMetalPy's RE and RWA real-world benchmark suites and write one CSV row per
  problem (`characterize_re_benchmark.py`, `characterize_rwa_benchmark.py`), plus their generated
  output (`re_features.csv`, `rwa_features.csv`).

For what each of the 49 landscape features actually *means*, see [`notebooks/`](../notebooks/)
instead — neither group here repeats that content.
