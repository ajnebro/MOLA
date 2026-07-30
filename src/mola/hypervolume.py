"""The shared hypervolume reference point and the singleton box-hypervolume.

Every hypervolume-based feature (`hv`, `hv_avg_neig`, `hvd_avg_neig`, `nhv_avg_neig`, and their
ruggedness `_cor_neig` counterparts) shares **one** reference point per sample — the element-wise
maximum of the whole sample's objectives, no padding — rather than each recomputing its own
(Design decisions, "`hv` and the shared hypervolume reference point").
"""

import moocore
import numpy as np

from mola.distance import Neighbourhood


def reference_point(objectives: np.ndarray) -> np.ndarray:
    """The shared hypervolume reference point: element-wise maximum over the whole sample.

    Computed from the *whole* sample, not just the non-dominated subset: `hv_avg_neig`,
    `hvd_avg_neig`, and `nhv_avg_neig` score every solution, dominated or not, and each needs
    `f_m(i) <= ref_m` for every `m` to have a well-defined, non-negative individual hypervolume.

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).

    Returns:
        The per-objective maximum, shape (M,).
    """
    return objectives.max(axis=0)


def singleton_hypervolume(objectives: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """Each solution's own box-hypervolume against the shared reference point.

    Table 1's "(single)" qualifier on `hv_avg_neig` — "average **(single)** solution's
    hypervolume" — is load-bearing: each solution is scored in isolation against `ref`, a closed
    form equivalent to `moocore.hypervolume` on a singleton set. **Deliberately not**
    `moocore.hv_contributions`: contributions measure marginal value relative to the rest of the
    set, which would make this collapse toward measuring `nd_n` rather than a per-solution signal
    (Design decisions, verified numerically distinct).

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        ref: The shared reference point, shape (M,), from :func:`reference_point`.

    Returns:
        Per-solution hypervolume, shape (n,): ``prod_m max(0, ref_m - f_m(i))``.
    """
    return np.prod(np.maximum(0.0, ref - objectives), axis=1)


def neighbour_hypervolume_difference(
    objectives: np.ndarray, neighbourhood: Neighbourhood, ref: np.ndarray
) -> np.ndarray:
    """Per-solution, per-neighbour absolute difference in singleton hypervolume.

    Shared by `hvd_avg_neig` (its sample-wide mean) and `hvd_cor_neig` (its own per-solution mean,
    correlated across neighbour pairs) — both reuse the same `singleton_hypervolume` array rather
    than each recomputing it.

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        neighbourhood: The sample's neighbourhood graph.
        ref: The shared reference point, shape (M,), from :func:`reference_point`.

    Returns:
        Per-solution, per-neighbour ``|hv(i) - hv(j)|``, shape ``(n, neighbourhood.size)``.
    """
    hv = singleton_hypervolume(objectives, ref)
    return np.abs(hv[:, None] - hv[neighbourhood.indices])


def neighbourhood_hypervolume(
    objectives: np.ndarray, neighbourhood: Neighbourhood, ref: np.ndarray
) -> np.ndarray:
    """Per-solution hypervolume of the whole neighbourhood (excluding the solution itself).

    Table 1's "hypervolume from the **whole neighbourhood**" is genuinely set-based, unlike
    `singleton_hypervolume`: the joint hypervolume of `i`'s `k` neighbours against the shared
    `ref`, via `moocore.hypervolume` — no pre-filtering of dominated neighbours needed, since
    `moocore.hypervolume` already handles overlapping dominated regions correctly.

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        neighbourhood: The sample's neighbourhood graph.
        ref: The shared reference point, shape (M,), from :func:`reference_point`.

    Returns:
        Per-solution hypervolume of ``{objectives[j] : j in N(i)}``, shape ``(n,)``.
    """
    return np.array(
        [
            moocore.hypervolume(objectives[neighbours], ref=ref)
            for neighbours in neighbourhood.indices
        ]
    )
