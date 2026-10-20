"""Decision-space geometry: how decision vectors are scaled before any feature sees them.

The neighbourhood graph and every decision-space distance depend on the units each variable is
expressed in. A geometry fixes those units once per sample, and both the graph and the distances
use the same scaled vectors (research/decisions/decisions.md, D1):

* ``bound`` (the default) maps each variable to [0, 1] through its declared bounds. Every one of
  the 49 features is then unchanged by a positive affine change of units applied to any variable,
  together with its bounds (phase 0, E6).
* ``raw`` uses the decision vectors as they are, which is what MOLA 0.2.0 did. Features then
  depend on the units: with heterogeneous bounds, the graph can share fewer than 15 % of its
  neighbours with the ``bound`` graph (phase 0, E4).

Objective space has its own profile, ``ObjectiveScaling``:

* ``raw`` (the default) keeps the objective values as they are, as the paper's definitions do.
  Features measured in objective units (the hypervolume family, ``dist_f_max``, the ``diff_f``
  measures) then span orders of magnitude between problems whose objectives use different units.
* ``sample`` maps each objective to [0, 1] through its minimum and maximum over the sample. Every
  one of the 49 features is then unchanged by a positive affine change of units of any objective,
  which dominance-based optimizers such as NSGA-II do not see either.
"""

from enum import StrEnum

import numpy as np

from mola.sample import Sample


class Geometry(StrEnum):
    """The decision-space geometry profiles MOLA can characterize under."""

    BOUND = "bound"
    RAW = "raw"


DEFAULT_GEOMETRY = Geometry.BOUND
"""The geometry used when none is given (research/decisions/decisions.md, D1)."""


class ObjectiveScaling(StrEnum):
    """The objective-space scaling profiles MOLA can characterize under."""

    RAW = "raw"
    SAMPLE = "sample"


DEFAULT_OBJECTIVE_SCALING = ObjectiveScaling.RAW
"""The objective scaling used when none is given: raw, as in the paper's definitions."""


def decision_space(sample: Sample, geometry: Geometry) -> np.ndarray:
    """Return the sample's decision vectors as seen under a geometry.

    Under ``bound``, a fixed variable (lower bound equal to upper bound) maps to 0 for every
    solution, so it contributes nothing to any distance.

    Args:
        sample: The sample whose decision vectors to scale.
        geometry: The geometry profile to apply.

    Returns:
        Decision vectors, shape ``(n, D)``. Under ``raw``, the sample's own array.

    Raises:
        ValueError: If the geometry is ``bound`` and any bound is infinite.
    """
    geometry = Geometry(geometry)
    if geometry is Geometry.RAW:
        return sample.variables

    lower, upper = sample.lower_bounds, sample.upper_bounds
    unbounded = np.flatnonzero(~(np.isfinite(lower) & np.isfinite(upper)))
    if unbounded.size > 0:
        raise ValueError(
            f"the 'bound' geometry needs finite bounds, but variable(s) "
            f"{(unbounded + 1).tolist()} are unbounded; use the 'raw' geometry instead"
        )
    span = upper - lower
    fixed = span == 0.0
    scaled = (sample.variables - lower) / np.where(fixed, 1.0, span)
    scaled[:, fixed] = 0.0
    return scaled


def objective_space(sample: Sample, scaling: ObjectiveScaling) -> np.ndarray:
    """Return the sample's objective vectors as seen under an objective-scaling profile.

    Under ``sample``, each objective is min-max scaled over the sample; an objective that is
    constant over the sample maps to 0. Minimization is preserved, since the map is increasing.

    Args:
        sample: The sample whose objective vectors to scale.
        scaling: The objective-scaling profile to apply.

    Returns:
        Objective vectors, shape ``(n, M)``. Under ``raw``, the sample's own array.
    """
    scaling = ObjectiveScaling(scaling)
    if scaling is ObjectiveScaling.RAW:
        return sample.objectives
    lower = sample.objectives.min(axis=0)
    span = sample.objectives.max(axis=0) - lower
    constant = span == 0.0
    scaled = (sample.objectives - lower) / np.where(constant, 1.0, span)
    scaled[:, constant] = 0.0
    return scaled
