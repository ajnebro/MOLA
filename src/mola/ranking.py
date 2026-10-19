"""Non-dominated sorting over a sample's objective vectors.

Thin, index-oriented wrapper over :func:`moocore.pareto_rank`. Reusing a library implementation
is deliberate: ad hoc reimplementation of dominance and ranking logic is precisely what shipped
several silent, untested defects in MOLA's predecessor. MOLA 0.2.0 wrapped jMetalPy's
``FastNonDominatedRanking`` instead; ``moocore`` (already a dependency, through jMetalPy and the
hypervolume features) returns identical ranks, duplicates included (phase 0, E10), without
building one Python object per solution, which dominated the run time at ``n = 200 * D``
(phase 0, E22).
"""

from dataclasses import dataclass

import moocore
import numpy as np


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

    rank = np.asarray(moocore.pareto_rank(objectives), dtype=int)
    fronts = tuple(np.flatnonzero(rank == index) for index in range(int(rank.max()) + 1))

    return Ranking(rank=rank, fronts=fronts)
