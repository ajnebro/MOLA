"""Apply MOLA to every problem in jMetalPy's RWA (real-world applications) benchmark suite.

Samples, evaluates, and characterizes each of the 10 RWA problems, writing one CSV row per problem
with its 49 features plus sample_size/num_obj/num_var. These problems aren't in jMetalPy's flat
`jmetal.problem` namespace (only in `jmetal.problem.multiobjective.rwa`), so this goes through the
Python API directly rather than the CLI, which only resolves names from that flat namespace. Run
directly:

    python examples/benchmarks/characterize_rwa_benchmark.py
"""

import inspect
from pathlib import Path

import pandas as pd
from jmetal.core.problem import FloatProblem
from jmetal.problem.multiobjective import rwa as rwa_problems

from mola.adapters.jmetalpy import sample_problem
from mola.characterize import characterize

SEED = 42
OUTPUT_PATH = Path(__file__).resolve().parent / "rwa_features.csv"


def _problem_classes(module) -> list[type[FloatProblem]]:
    """Every FloatProblem subclass defined directly in `module` (not merely imported into it)."""
    return [
        cls
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if cls.__module__ == module.__name__ and issubclass(cls, FloatProblem)
    ]


def main() -> None:
    """Characterize every RWA problem and write one CSV row per problem."""
    rows = []
    for problem_class in _problem_classes(rwa_problems):
        problem = problem_class()
        sample = sample_problem(problem, seed=SEED)
        result = characterize(sample)
        rows.append({"problem": sample.problem, **result})
        print(
            f"{sample.problem:17s} D={sample.number_of_variables:2d} "
            f"M={sample.number_of_objectives}  nd_n={result['nd_n']:.3f}  hv={result['hv']:.4g}"
        )

    frame = pd.DataFrame(rows).sort_values("problem").reset_index(drop=True)
    frame.to_csv(OUTPUT_PATH, index=False)
    print(f"\nWrote {len(frame)} problems x {frame.shape[1]} columns to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
