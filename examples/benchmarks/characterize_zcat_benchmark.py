"""Apply MOLA to every problem in jMetalPy's ZCAT benchmark suite, for 2 and 3 objectives.

Samples, evaluates, and characterizes each of ZCAT1-ZCAT20 at its default configuration (D=30
decision variables, complicated_pareto_set=False, level=1, bias=False, imbalance=False) -- only
number_of_objectives varies. Writes one CSV per objective count, one row per problem, each with
its 49 features plus sample_size/num_obj/num_var.

ZCAT problems are in jMetalPy's flat `jmetal.problem` namespace, so a single one can also be run
through the CLI directly (e.g. `mola sample ZCAT11 out.csv`), though the CLI has no way to request
a non-default `number_of_objectives` -- ZCATx()'s own default is 2, so the 3-objective half of
this script needs the Python API regardless.

NOTE: as of jmetalpy 1.9.0 on PyPI, ZCAT support is not yet published there -- this script needs
jMetalPy installed from a source checkout that includes `zcat.py` (confirmed present in the
project's own local jMetalPy checkout, committed but not yet released).

Run directly:

    python examples/benchmarks/characterize_zcat_benchmark.py
"""

import inspect
from pathlib import Path

import pandas as pd
from jmetal.core.problem import FloatProblem
from jmetal.problem.multiobjective import zcat as zcat_problems

from mola.adapters.jmetalpy import sample_problem
from mola.characterize import characterize

SEED = 42
OUTPUT_DIR = Path(__file__).resolve().parent


def _problem_classes(module) -> list[type[FloatProblem]]:
    """Every concrete FloatProblem subclass defined directly in `module` (ZCAT1..ZCAT20).

    Excludes the abstract `ZCAT` base itself, which takes a required `problem_id` the ZCATx
    subclasses already fix internally.
    """
    return [
        cls
        for name, cls in inspect.getmembers(module, inspect.isclass)
        if cls.__module__ == module.__name__ and issubclass(cls, FloatProblem) and name != "ZCAT"
    ]


def _characterize_suite(number_of_objectives: int) -> pd.DataFrame:
    rows = []
    for problem_class in _problem_classes(zcat_problems):
        problem = problem_class(number_of_objectives=number_of_objectives)
        sample = sample_problem(problem, seed=SEED)
        result = characterize(sample)
        rows.append({"problem": sample.problem, **result})
        print(
            f"{sample.problem:8s} M={number_of_objectives} D={sample.number_of_variables:2d} "
            f"nd_n={result['nd_n']:.3f}  hv={result['hv']:.4g}"
        )
    return pd.DataFrame(rows).sort_values("problem").reset_index(drop=True)


def main() -> None:
    """Characterize every ZCAT problem at 2 and 3 objectives, one CSV per objective count."""
    for number_of_objectives in (2, 3):
        print(f"\n--- {number_of_objectives} objectives ---")
        frame = _characterize_suite(number_of_objectives)
        output_path = OUTPUT_DIR / f"zcat_{number_of_objectives}obj_features.csv"
        frame.to_csv(output_path, index=False)
        print(f"Wrote {len(frame)} problems x {frame.shape[1]} columns to {output_path}")


if __name__ == "__main__":
    main()
