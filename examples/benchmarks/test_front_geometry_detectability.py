"""Can Pareto front geometry be recovered from a fixed-cost LHS sample? Measured, not argued.

This script exists to document a **negative result** (`FEATURE_ANALYSIS.md`, Finding 7). An earlier
draft of that document recommended adding front-geometry features -- disconnectedness, degeneracy --
on the grounds that the information was already present in the sample at zero extra evaluation
cost. This script was written to check that claim, and refutes it.

The test uses DTLZ because its front geometry is known analytically: DTLZ1 is a linear simplex,
DTLZ2/3/4 are concave spherical surfaces, DTLZ5/6 are *degenerate* (the front is a curve, not a
surface), and DTLZ7 is *disconnected* (four regions at M=3). If geometry were recoverable from the
sample's non-dominated subset, the two structural properties would separate those groups.

Run directly, from the repository root:

    python examples/benchmarks/test_front_geometry_detectability.py
"""

import numpy as np
from jmetal.core.problem import FloatProblem
from jmetal.problem import DTLZ1, DTLZ2, DTLZ3, DTLZ4, DTLZ5, DTLZ6, DTLZ7
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial import cKDTree
from scipy.spatial.distance import pdist

from mola.adapters.jmetalpy import sample_problem
from mola.ranking import rank_solutions

SEED = 42
GAP_FACTOR = 4.0
"""A component boundary is a gap this many times the median nearest-neighbour spacing."""

GROUND_TRUTH = {
    "DTLZ1": "linear",
    "DTLZ2": "concave",
    "DTLZ3": "concave",
    "DTLZ4": "concave",
    "DTLZ5": "DEGENERATE (curve)",
    "DTLZ6": "DEGENERATE (curve)",
    "DTLZ7": "DISCONNECTED (4 regions)",
}


def nondominated_objectives(problem: FloatProblem) -> np.ndarray:
    """Latin-Hypercube-sample a problem and return its non-dominated objective vectors."""
    sample = sample_problem(problem, seed=SEED)
    ranking = rank_solutions(sample.objectives)
    return sample.objectives[ranking.nondominated]


def intrinsic_dimensionality(points: np.ndarray) -> np.ndarray:
    """Cumulative explained variance per principal component.

    A surface embedded in 3-D objective space needs two components to be well explained; a
    degenerate front, being a curve, should need only one.
    """
    centred = points - points.mean(axis=0)
    _, singular_values, _ = np.linalg.svd(centred, full_matrices=False)
    return np.cumsum(singular_values**2 / (singular_values**2).sum())


def connected_components(points: np.ndarray) -> int:
    """Count clusters under single-linkage, cutting at a large multiple of typical spacing."""
    if len(points) <= 3:
        return -1
    nearest = cKDTree(points).query(points, k=2)[0][:, 1]
    threshold = GAP_FACTOR * np.median(nearest)
    labels = fcluster(linkage(pdist(points), "single"), threshold, criterion="distance")
    return len(set(labels))


def distance_from_true_front() -> None:
    """Quantify the root cause: the sampled ND set is not the front, it is a surface above it."""
    problem = DTLZ2()
    nd = nondominated_objectives(problem)
    # DTLZ2's true Pareto front is the unit-sphere octant, i.e. sum(f_i^2) = 1.
    radius = np.sqrt((nd**2).sum(axis=1))
    print("Root cause -- DTLZ2, whose true front lies at radius 1.0:")
    print(
        f"  sampled ND set radius: min={radius.min():.2f} "
        f"median={np.median(radius):.2f} max={radius.max():.2f}"
    )
    print(f"  the ND set sits {(np.median(radius) - 1) * 100:.0f}% beyond the true front,")
    print(f"  and holds only {len(nd)} points.\n")


def main() -> None:
    """Run both geometry tests over the DTLZ suite and print the comparison table."""
    distance_from_true_front()

    header = f"{'problem':8s} {'|ND|':>5s} {'PC1%':>7s} {'PC1+2%':>7s} {'parts':>6s}"
    print(f"{header}   ground truth")
    print("-" * 77)
    for problem_class in (DTLZ1, DTLZ2, DTLZ3, DTLZ4, DTLZ5, DTLZ6, DTLZ7):
        problem = problem_class()
        nd = nondominated_objectives(problem)
        explained = intrinsic_dimensionality(nd)
        components = connected_components(nd)
        print(
            f"{problem.name():8s} {len(nd):5d} {explained[0] * 100:6.1f}% "
            f"{explained[1] * 100:6.1f}% {components:6d}   {GROUND_TRUTH[problem.name()]}"
        )

    print(
        "\nVerdict: neither property survives the sampling.\n"
        "  degeneracy   -- DTLZ6 (degenerate) is indistinguishable from DTLZ2 (not), while\n"
        "                  DTLZ7 (not degenerate) scores the highest PC1 of all.\n"
        "  connectivity -- DTLZ7 (4 true regions) yields 2 components, while the connected\n"
        "                  DTLZ4 yields many, its x^100 bias creating spurious density gaps.\n"
        "Convexity is the exception, and the paper already covers it via supp_n."
    )


if __name__ == "__main__":
    main()
