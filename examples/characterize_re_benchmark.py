"""Apply MOLA to every problem in jMetalPy's RE (real-world engineering) benchmark suite.

Samples, evaluates, and characterizes each of the 16 RE2x/RE3x/RE4x/RE6x/RE9x problems, writing
one CSV row per problem with its 49 features plus sample_size/num_obj/num_var. These problems
aren't in jMetalPy's flat `jmetal.problem` namespace (only in `jmetal.problem.multiobjective.re`),
so this goes through the Python API directly rather than the CLI, which only resolves names from
that flat namespace. Run directly:

    python examples/characterize_re_benchmark.py
"""

import inspect
import math
from pathlib import Path

import pandas as pd
from jmetal.core.problem import FloatProblem
from jmetal.problem.multiobjective import re as re_problems

from mola.adapters.jmetalpy import sample_problem
from mola.characterize import characterize

SEED = 42
OUTPUT_PATH = Path(__file__).resolve().parent / "re_features.csv"


def _problem_classes(module) -> list[type[FloatProblem]]:
    """Every FloatProblem subclass defined directly in `module` (not merely imported into it)."""
    return [
        cls
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if cls.__module__ == module.__name__ and issubclass(cls, FloatProblem)
    ]


def _has_finite_bounds(problem: FloatProblem) -> bool:
    return all(
        math.isfinite(lo) and math.isfinite(hi)
        for lo, hi in zip(problem.lower_bound, problem.upper_bound, strict=True)
    )


def main() -> None:
    """Characterize every RE problem and write one CSV row per problem."""
    rows = []
    for problem_class in _problem_classes(re_problems):
        problem = problem_class()
        if not _has_finite_bounds(problem):
            # RE91 has 4 unbounded "variables" that its own evaluate() overwrites with fresh
            # Gaussian noise on every call, regardless of what's sampled -- a quirk of that one
            # problem's jMetalPy implementation, not something a general LHS sampler can honor.
            print(f"{problem.name():8s} skipped: has non-finite variable bounds")
            continue
        sample = sample_problem(problem, seed=SEED)
        result = characterize(sample)
        rows.append({"problem": sample.problem, **result})
        print(
            f"{sample.problem:8s} D={sample.number_of_variables:2d} "
            f"M={sample.number_of_objectives}  nd_n={result['nd_n']:.3f}  hv={result['hv']:.4g}"
        )

    frame = pd.DataFrame(rows).sort_values("problem").reset_index(drop=True)
    frame.to_csv(OUTPUT_PATH, index=False)
    print(f"\nWrote {len(frame)} problems x {frame.shape[1]} columns to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
