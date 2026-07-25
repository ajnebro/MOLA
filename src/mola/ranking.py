"""Non-dominated sorting over a sample's objective vectors.

Thin, index-oriented wrapper over jMetalPy's :class:`~jmetal.util.ranking.FastNonDominatedRanking`.
Reusing jMetalPy's implementation is deliberate: ad hoc reimplementation of dominance and ranking
logic is precisely what shipped several silent, untested defects in MOLA's predecessor.

The wrapper exists because jMetalPy's ranking speaks in solution objects, while every landscape
feature here reasons about *positions in the sample* — a non-dominated mask, a per-solution rank,
the number of solutions per rank. It also isolates the dependency: the internals can be replaced
without touching any feature, should the objects-per-solution representation prove too costly at
the paper's ``n = 200 * D`` sampling rate.
"""

from dataclasses import dataclass

import numpy as np
from jmetal.util.ranking import FastNonDominatedRanking


class _RankableSolution:
    """Minimal stand-in exposing the attributes jMetalPy's ranking requires."""

    __slots__ = ("attributes", "objectives")

    def __init__(self, objectives: list[float]) -> None:
        self.objectives = objectives
        self.attributes: dict[str, int] = {}


@dataclass(slots=True, frozen=True)
class Ranking:
    """A sample's partition into non-dominated fronts.

    Attributes:
        rank: Zero-based front index per solution, shape ``(n,)``. Rank ``0`` marks the
            non-dominated solutions.
        fronts: Solution indices per front, outermost first. ``fronts[r]`` holds exactly the
            positions where ``rank == r``, and no front is empty.
    """

    rank: np.ndarray
    fronts: tuple[np.ndarray, ...]

    @property
    def nondominated(self) -> np.ndarray:
        """Indices of the non-dominated solutions, i.e. the first front."""
        return self.fronts[0]

    @property
    def number_of_fronts(self) -> int:
        """Number of non-empty fronts the sample splits into."""
        return len(self.fronts)


def rank_solutions(objectives: np.ndarray) -> Ranking:
    """Sort a sample's objective vectors into non-dominated fronts.

    Dominance is evaluated under minimization throughout, matching the interchange contract:
    adapters are required to emit objectives already in minimization form.

    Args:
        objectives: Objective vectors in minimization form, shape ``(n, M)``.

    Returns:
        The per-solution ranks and the fronts they form.

    Raises:
        ValueError: If the sample is empty.
    """
    if objectives.shape[0] == 0:
        raise ValueError("cannot rank an empty sample")

    solutions = [_RankableSolution(values) for values in objectives.tolist()]
    FastNonDominatedRanking().compute_ranking(solutions)

    rank = np.fromiter(
        (solution.attributes["dominance_ranking"] for solution in solutions),
        dtype=int,
        count=len(solutions),
    )
    fronts = tuple(np.flatnonzero(rank == index) for index in range(int(rank.max()) + 1))

    return Ranking(rank=rank, fronts=fronts)
