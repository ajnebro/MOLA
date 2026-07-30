"""Minimal end-to-end example: sample, evaluate, and characterize a jMetalPy problem.

No CLI, no interchange file -- just the two Python API calls MOLA is built around. Run directly:

    python examples/quickstart.py

For the CLI equivalent of this same workflow, see `mola run --help`; for a narrated walkthrough
covering both, see `examples/getting_started.ipynb`.
"""

from jmetal.problem import ZDT1

from mola.adapters.jmetalpy import sample_problem
from mola.characterize import characterize


def main() -> None:
    """Sample, evaluate, and characterize ZDT1, then print a few representative features."""
    problem = ZDT1(number_of_variables=5)
    sample = sample_problem(problem, sample_size=500, seed=42)
    result = characterize(sample)

    print(
        f"Characterized {sample.problem}: {sample.size} solutions, "
        f"{sample.number_of_variables} variables, {sample.number_of_objectives} objectives"
    )
    print()
    for name in ("nd_n", "hv", "dist_x_avg", "rank_ent", "slo_n", "length_aws"):
        print(f"{name}: {result[name]:.4f}")
    print(f"... and {len(result) - 6} more features (see CLAUDE.md's feature matrix for all 49)")


if __name__ == "__main__":
    main()
