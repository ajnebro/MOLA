"""A characterization's full result: feature values, why any are undefined, and provenance.

Feature values depend on more than the sample: on the definitions MOLA implements, on the
decision-space geometry and on the neighbourhood size. A :class:`Characterization` carries all of
them, so that two feature vectors are only compared when they were computed the same way
(research/phase0/recommender_contract.md, rules 2 and 5).
"""

import math
from dataclasses import asdict, dataclass

FEATURE_PROFILE = "paper49-v1"
"""Version of MOLA's definitions of the 49 features.

``paper49-v1`` is the first versioned profile (MOLA 0.3.0): exact supported points and the
whole-sample normalization of ``dist_x_avg_neig``/``dist_f_avg_neig``. It changes whenever the
definition of any feature changes, so that values from different definitions are never mixed.
"""


@dataclass(slots=True, frozen=True)
class Provenance:
    """How a characterization was computed, and from which sample.

    Attributes:
        mola_version: Version of MOLA that computed the features.
        feature_profile: Version of the feature definitions (:data:`FEATURE_PROFILE`).
        geometry: Decision-space geometry profile (`mola.geometry`).
        objective_scaling: Objective-space scaling profile (`mola.geometry.ObjectiveScaling`).
        neighbours: Neighbourhood size `k` actually used, after capping at `n - 1`.
        walk_samples: Number of adaptive walks actually averaged, after capping at `n`.
        problem: Name of the sampled problem.
        sampler: Sampling design that produced the sample.
        seed: Seed of the sample, also used to draw the walks' starting points.
        schema_version: Interchange schema version of the sample.
        sample_size: Number of sampled solutions (`n`).
        num_obj: Number of objectives (`M`).
        num_var: Number of decision variables (`D`).
    """

    mola_version: str
    feature_profile: str
    geometry: str
    neighbours: int
    walk_samples: int
    problem: str
    sampler: str
    seed: int | None
    schema_version: int
    sample_size: int
    num_obj: int
    num_var: int
    objective_scaling: str = "raw"


@dataclass(slots=True, frozen=True)
class Characterization:
    """The 49 feature values of one sample, the cause of each undefined one, and provenance.

    Attributes:
        features: Every Table 1 feature by name, in a fixed order. Undefined features are NaN.
        causes: For each undefined (non-finite) feature, a short explanation of why it is
            undefined on this sample. Defined features do not appear.
        provenance: How the features were computed.
    """

    features: dict[str, float]
    causes: dict[str, str]
    provenance: Provenance

    def as_flat_dict(self) -> dict[str, float]:
        """Return the 0.2.0-compatible result: three metadata fields, then the 49 features.

        Returns:
            ``sample_size``, ``num_obj`` and ``num_var``, followed by every feature value.
        """
        return {
            "sample_size": self.provenance.sample_size,
            "num_obj": self.provenance.num_obj,
            "num_var": self.provenance.num_var,
            **self.features,
        }

    def to_json_dict(self) -> dict:
        """Return a JSON-serializable report: provenance fields, then one entry per feature.

        Each feature entry holds its ``value`` (``None`` when undefined, never NaN), its
        ``status`` (``"defined"`` or ``"undefined"``) and, when undefined, its ``cause``.

        Returns:
            A dict ready for ``json.dumps``.
        """
        entries = {}
        for name, value in self.features.items():
            if math.isfinite(value):
                entries[name] = {"value": value, "status": "defined"}
            else:
                entries[name] = {"value": None, "status": "undefined", "cause": self.causes[name]}
        return {**asdict(self.provenance), "features": entries}
