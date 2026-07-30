"""Single-objective local optima and the multi-objective adaptive walk (paper §4.1.2).

A single-objective local optimum (slo) is a sampled solution with no neighbour that improves a
*given* objective — inherently per-objective, unlike a Pareto local optimum (plo, which reuses
`mola.dominance`'s dominating-neighbour count directly and needs no substrate of its own).

The adaptive walk is a different, genuinely new simulation: starting from a solution, repeatedly
move to the first neighbour (closest to furthest) that dominates the current one, until none does.
"""

from dataclasses import dataclass

import numpy as np
from jmetal.util.comparator import DominanceComparator

from mola.distance import Neighbourhood

DEFAULT_WALK_COUNT = 30
"""Number of independent adaptive walks averaged by :func:`adaptive_walks`, capped at ``n``."""


def single_objective_local_optima(
    objectives: np.ndarray, neighbourhood: Neighbourhood
) -> np.ndarray:
    """Per-solution, per-objective single-objective-local-optimum mask.

    Solution `i` is a local optimum for objective `m` iff none of its neighbours has a strictly
    smaller `f_m` (Design decisions, "Multimodality").

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        neighbourhood: The sample's neighbourhood graph.

    Returns:
        Boolean mask, shape (n, M): True where solution `i` is a local optimum for objective `m`.
    """
    neighbour_values = objectives[neighbourhood.indices]
    reference_values = objectives[:, None, :]
    return (neighbour_values >= reference_values).all(axis=1)


@dataclass(slots=True, frozen=True)
class Walk:
    """The outcome of one adaptive walk (paper §4.1.2).

    Attributes:
        length: Number of accepted (dominating) moves before reaching a Pareto local optimum.
        evaluations: Total neighbours inspected across the whole walk — lookups against the
            precomputed sample, not calls to a real evaluation function (see `adaptive_walk`).
    """

    length: int
    evaluations: int


@dataclass(slots=True, frozen=True)
class AdaptiveWalks:
    """The outcome of several independent adaptive walks, one per starting solution.

    Attributes:
        lengths: Each walk's length, shape ``(samples,)``.
        evaluations: Each walk's evaluation count, shape ``(samples,)``.
    """

    lengths: np.ndarray
    evaluations: np.ndarray


def adaptive_walk(objectives: np.ndarray, neighbourhood: Neighbourhood, start: int) -> Walk:
    """Simulate one multi-objective adaptive walk from a starting solution (paper §4.1.2).

    At each step, scans the current solution's neighbours closest-to-furthest and accepts the
    first one that dominates it; stops when no neighbour dominates (the walk has reached a Pareto
    local optimum). Simulated entirely over the precomputed neighbourhood graph — the paper is
    explicit this needs **no additional evaluations**, despite Table 1's "calls to the evaluation
    function" phrasing for `eval_aws` (that phrase describes what it *would* cost live, not what
    MOLA actually spends; Design decisions). Cycling is impossible by construction — each move is
    a strict dominance improvement — so no visited-set bookkeeping is needed for correctness.

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        neighbourhood: The sample's neighbourhood graph, with neighbours ordered closest-to-
            furthest (`mola.distance.build_neighbourhood`'s own ordering).
        start: Index of the solution to start the walk from.

    Returns:
        The walk's length and evaluation count.
    """
    comparator = DominanceComparator()
    current = start
    length = 0
    evaluations = 0
    while True:
        next_solution = None
        for neighbour in neighbourhood.indices[current]:
            evaluations += 1
            if comparator.dominance_test(objectives[neighbour], objectives[current]) < 0:
                next_solution = neighbour
                break
        if next_solution is None:
            return Walk(length=length, evaluations=evaluations)
        current = next_solution
        length += 1


def adaptive_walks(
    objectives: np.ndarray,
    neighbourhood: Neighbourhood,
    *,
    samples: int = DEFAULT_WALK_COUNT,
    seed: int | None = None,
) -> AdaptiveWalks:
    """Simulate several independent adaptive walks from distinct random starting solutions.

    **Judgment call** (Design decisions): the paper says "different starting points" without
    specifying how many or how chosen — MOLA draws `min(samples, n)` distinct solutions uniformly
    at random.

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        neighbourhood: The sample's neighbourhood graph.
        samples: Requested number of walks. Capped at `n` when the sample is smaller.
        seed: Seed for the random starting-point draw — the run's own seed, per Design decisions,
            "Stochasticity & reproducibility".

    Returns:
        Each walk's length and evaluation count.
    """
    rng = np.random.default_rng(seed)
    count = objectives.shape[0]
    starts = rng.choice(count, size=min(samples, count), replace=False)

    lengths = np.empty(starts.size, dtype=int)
    evaluations = np.empty(starts.size, dtype=int)
    for index, start in enumerate(starts):
        walk = adaptive_walk(objectives, neighbourhood, int(start))
        lengths[index] = walk.length
        evaluations[index] = walk.evaluations

    return AdaptiveWalks(lengths=lengths, evaluations=evaluations)
