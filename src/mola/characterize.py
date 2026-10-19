"""The orchestrator: characterize a Sample by computing all 49 landscape features in one call.

Every feature function elsewhere in this package takes exactly the substrate pieces it needs
(a `Ranking`, a `Neighbourhood`, a `Normalizer`, ...) rather than a whole `Sample`, so each stays
testable and reasoned about in isolation. This module is the one place that builds that shared
substrate once per sample and calls every feature — the entry point everything else was built
towards.

Every feature call below uses keyword arguments, deliberately: several functions accept the same
handful of substrate types (`objectives`, `neighbourhood`, `ref`, ...) but not always in the same
order (`hv_cor_neig` takes `ref` before `neighbourhood`; `hvd_cor_neig` and `nhv_cor_neig` take it
after) — positional calls across 49 near-identical signatures would be a real, silent way to wire
the wrong value into the wrong slot.
"""

import math
from dataclasses import dataclass

import numpy as np

from mola import __version__, features
from mola.distance import Neighbourhood, build_neighbourhood
from mola.dominance import (
    LocalNondominance,
    NeighbourhoodDominance,
    local_nondominance,
    neighbourhood_dominance,
)
from mola.geometry import DEFAULT_GEOMETRY, Geometry, decision_space
from mola.hypervolume import reference_point
from mola.multimodality import DEFAULT_WALK_COUNT, AdaptiveWalks, adaptive_walks
from mola.normalization import Normalizers, build_normalizers
from mola.ranking import Ranking, rank_solutions
from mola.report import FEATURE_PROFILE, Characterization, Provenance
from mola.sample import Sample


@dataclass(slots=True, frozen=True)
class _Substrate:
    """Everything built once per sample and shared across every feature."""

    neighbourhood: Neighbourhood
    ranking: Ranking
    dominance: NeighbourhoodDominance
    local: LocalNondominance
    normalizers: Normalizers
    ref: np.ndarray
    walks: AdaptiveWalks


def _global_features(
    variables: np.ndarray, objectives: np.ndarray, substrate: _Substrate
) -> dict[str, float]:
    ranking = substrate.ranking
    return {
        "f_cor": features.f_cor(objectives=objectives),
        "dist_x_avg": features.dist_x_avg(
            variables=variables, normalizer=substrate.normalizers.variable_space
        ),
        "dist_x_max": features.dist_x_max(variables=variables),
        "dist_f_avg": features.dist_f_avg(
            objectives=objectives, normalizer=substrate.normalizers.objective_space
        ),
        "dist_f_max": features.dist_f_max(objectives=objectives),
        "nd_n": features.nd_n(ranking=ranking),
        "supp_n": features.supp_n(objectives=objectives, ranking=ranking),
        "hv": features.hv(objectives=objectives, ranking=ranking, ref=substrate.ref),
        "dist_x_nd_avg": features.dist_x_nd_avg(
            variables=variables, ranking=ranking, normalizer=substrate.normalizers.variable_space
        ),
        "dist_x_nd_max": features.dist_x_nd_max(variables=variables, ranking=ranking),
        "fdc": features.fdc(variables=variables, objectives=objectives, ranking=ranking),
        "rank_avg": features.rank_avg(ranking=ranking),
        "rank_max": features.rank_max(ranking=ranking),
        "rank_ent": features.rank_ent(ranking=ranking),
    }


def _multimodality_features(
    variables: np.ndarray, objectives: np.ndarray, substrate: _Substrate
) -> dict[str, float]:
    neighbourhood = substrate.neighbourhood
    return {
        "slo_n": features.slo_n(objectives=objectives, neighbourhood=neighbourhood),
        "slo_dist_avg": features.slo_dist_avg(
            variables=variables,
            objectives=objectives,
            neighbourhood=neighbourhood,
            normalizer=substrate.normalizers.variable_space,
        ),
        "slo_dist_max": features.slo_dist_max(
            variables=variables, objectives=objectives, neighbourhood=neighbourhood
        ),
        "plo_n": features.plo_n(dominance=substrate.dominance),
        "plo_dist_avg": features.plo_dist_avg(
            variables=variables,
            dominance=substrate.dominance,
            normalizer=substrate.normalizers.variable_space,
        ),
        "plo_dist_max": features.plo_dist_max(variables=variables, dominance=substrate.dominance),
        "nd_per_plo": features.nd_per_plo(ranking=substrate.ranking, dominance=substrate.dominance),
        "length_aws": features.length_aws(walks=substrate.walks),
        "eval_aws": features.eval_aws(walks=substrate.walks),
    }


def _evolvability_features(
    variables: np.ndarray, objectives: np.ndarray, substrate: _Substrate
) -> dict[str, float]:
    neighbourhood = substrate.neighbourhood
    dominance = substrate.dominance
    local = substrate.local
    normalizers = substrate.normalizers
    ref = substrate.ref
    return {
        "sup_avg_neig": features.sup_avg_neig(dominance=dominance, neighbourhood=neighbourhood),
        "inf_avg_neig": features.inf_avg_neig(dominance=dominance, neighbourhood=neighbourhood),
        "inc_avg_neig": features.inc_avg_neig(dominance=dominance, neighbourhood=neighbourhood),
        "lnd_avg_neig": features.lnd_avg_neig(local=local, neighbourhood=neighbourhood),
        "lsupp_avg_neig": features.lsupp_avg_neig(local=local, neighbourhood=neighbourhood),
        "dist_x_avg_neig": features.dist_x_avg_neig(
            variables=variables,
            neighbourhood=neighbourhood,
            normalizer=normalizers.variable_space,
        ),
        "dist_f_avg_neig": features.dist_f_avg_neig(
            objectives=objectives,
            neighbourhood=neighbourhood,
            normalizer=normalizers.objective_space,
        ),
        "dist_f_dist_x_avg_neig": features.dist_f_dist_x_avg_neig(
            objectives=objectives,
            variables=variables,
            neighbourhood=neighbourhood,
            objective_normalizer=normalizers.objective_space,
            variable_normalizer=normalizers.variable_space,
        ),
        "diff_f_avg_neig": features.diff_f_avg_neig(
            objectives=objectives, neighbourhood=neighbourhood
        ),
        "diff_f_dist_x_avg_neig": features.diff_f_dist_x_avg_neig(
            objectives=objectives,
            variables=variables,
            neighbourhood=neighbourhood,
            variable_normalizer=normalizers.variable_space,
        ),
        "hv_avg_neig": features.hv_avg_neig(objectives=objectives, ref=ref),
        "hvd_avg_neig": features.hvd_avg_neig(
            objectives=objectives, neighbourhood=neighbourhood, ref=ref
        ),
        "nhv_avg_neig": features.nhv_avg_neig(
            objectives=objectives, neighbourhood=neighbourhood, ref=ref
        ),
    }


def _ruggedness_features(
    variables: np.ndarray, objectives: np.ndarray, substrate: _Substrate
) -> dict[str, float]:
    neighbourhood = substrate.neighbourhood
    dominance = substrate.dominance
    local = substrate.local
    ref = substrate.ref
    return {
        "dist_x_cor_neig": features.dist_x_cor_neig(
            variables=variables, neighbourhood=neighbourhood
        ),
        "dist_f_cor_neig": features.dist_f_cor_neig(
            objectives=objectives, neighbourhood=neighbourhood
        ),
        "sup_cor_neig": features.sup_cor_neig(dominance=dominance, neighbourhood=neighbourhood),
        "inf_cor_neig": features.inf_cor_neig(dominance=dominance, neighbourhood=neighbourhood),
        "inc_cor_neig": features.inc_cor_neig(dominance=dominance, neighbourhood=neighbourhood),
        "lnd_cor_neig": features.lnd_cor_neig(local=local, neighbourhood=neighbourhood),
        "lsupp_cor_neig": features.lsupp_cor_neig(local=local, neighbourhood=neighbourhood),
        "dist_f_dist_x_cor_neig": features.dist_f_dist_x_cor_neig(
            objectives=objectives, variables=variables, neighbourhood=neighbourhood
        ),
        "diff_f_cor_neig": features.diff_f_cor_neig(
            objectives=objectives, neighbourhood=neighbourhood
        ),
        "diff_f_dist_x_cor_neig": features.diff_f_dist_x_cor_neig(
            objectives=objectives, variables=variables, neighbourhood=neighbourhood
        ),
        "hv_cor_neig": features.hv_cor_neig(
            objectives=objectives, ref=ref, neighbourhood=neighbourhood
        ),
        "hvd_cor_neig": features.hvd_cor_neig(
            objectives=objectives, neighbourhood=neighbourhood, ref=ref
        ),
        "nhv_cor_neig": features.nhv_cor_neig(
            objectives=objectives, neighbourhood=neighbourhood, ref=ref
        ),
    }


def _undefined_cause(name: str, substrate: _Substrate) -> str:
    """Explain why feature `name` came out non-finite on this sample."""
    nondominated = substrate.ranking.nondominated.size
    pareto_local_optima = int(np.count_nonzero(substrate.dominance.dominating == 0))
    if name in ("dist_x_nd_avg", "dist_x_nd_max"):
        return f"|ND| = {nondominated}: at least 2 non-dominated solutions are needed"
    if name == "fdc":
        if nondominated < 3:
            return (
                f"|ND| = {nondominated}: at least 3 non-dominated solutions (2 distance pairs) "
                f"are needed"
            )
        return "the distances among non-dominated solutions are constant in one space"
    if name in ("plo_dist_avg", "plo_dist_max"):
        return f"{pareto_local_optima} Pareto local optima: at least 2 are needed"
    if name in ("slo_dist_avg", "slo_dist_max"):
        return "every objective has fewer than 2 single-objective local optima"
    if name == "f_cor":
        return "an objective is constant over the sample"
    if name in ("dist_f_dist_x_avg_neig", "diff_f_dist_x_avg_neig"):
        return "dist_x_avg_neig is 0: every neighbour lies at the minimum pairwise distance"
    if name.endswith("_cor_neig"):
        return "the per-solution measure is constant, or undefined, over the neighbour pairs"
    return "non-finite value"


def characterize_report(
    sample: Sample,
    *,
    walk_samples: int = DEFAULT_WALK_COUNT,
    geometry: Geometry = DEFAULT_GEOMETRY,
    neighbours: int | None = None,
) -> Characterization:
    """Compute all 49 landscape features (paper Table 1) for one sample, with provenance.

    Builds the shared substrate exactly once — the neighbourhood graph, the non-dominated
    ranking, pairwise and local neighbourhood dominance, the two whole-sample normalizers, the
    shared hypervolume reference point, and a batch of adaptive walks (seeded from `sample.seed`,
    per "Stochasticity & reproducibility") — then calls every feature function with exactly the
    pieces it needs.

    The decision vectors are first scaled by `geometry` (`mola.geometry`), and the scaled
    vectors are used both to build the neighbourhood graph and to measure every decision-space
    distance.

    Args:
        sample: The sample to characterize.
        walk_samples: Number of independent adaptive walks to average over `length_aws`/
            `eval_aws`, capped at `sample.size`. Defaults to `mola.multimodality.
            DEFAULT_WALK_COUNT` (30, a MOLA judgment call: the paper does not say how many
            starting points it uses).
        geometry: Decision-space geometry profile. Defaults to `bound`, which maps each
            variable to [0, 1] through its declared bounds; `raw` reproduces MOLA 0.2.0's
            choice.
        neighbours: Neighbourhood size `k`. Defaults to `D`, the number of decision variables
            (Design decisions, "Neighbourhood definition"). Capped at `n - 1`.

    Returns:
        The 49 feature values keyed by their Table 1 names, the cause of each undefined one, and
        how they were computed (`mola.report.Provenance`).

    Raises:
        ValueError: If `geometry` is unknown, or is `bound` while some bound is infinite; or if
            `neighbours` is not positive.
    """
    geometry = Geometry(geometry)
    variables = decision_space(sample, geometry)
    objectives = sample.objectives

    neighbourhood = build_neighbourhood(
        variables, neighbours=sample.number_of_variables if neighbours is None else neighbours
    )
    substrate = _Substrate(
        neighbourhood=neighbourhood,
        ranking=rank_solutions(objectives),
        dominance=neighbourhood_dominance(objectives, neighbourhood),
        local=local_nondominance(objectives, neighbourhood),
        normalizers=build_normalizers(variables, objectives),
        ref=reference_point(objectives),
        walks=adaptive_walks(objectives, neighbourhood, samples=walk_samples, seed=sample.seed),
    )

    values = {
        **_global_features(variables, objectives, substrate),
        **_multimodality_features(variables, objectives, substrate),
        **_evolvability_features(variables, objectives, substrate),
        **_ruggedness_features(variables, objectives, substrate),
    }
    causes = {
        name: _undefined_cause(name, substrate)
        for name, value in values.items()
        if not math.isfinite(value)
    }
    provenance = Provenance(
        mola_version=__version__,
        feature_profile=FEATURE_PROFILE,
        geometry=geometry.value,
        neighbours=neighbourhood.size,
        walk_samples=int(substrate.walks.lengths.size),
        problem=sample.problem,
        sampler=sample.sampler,
        seed=sample.seed,
        schema_version=sample.schema_version,
        sample_size=sample.size,
        num_obj=sample.number_of_objectives,
        num_var=sample.number_of_variables,
    )
    return Characterization(features=values, causes=causes, provenance=provenance)


def characterize(
    sample: Sample,
    *,
    walk_samples: int = DEFAULT_WALK_COUNT,
    geometry: Geometry = DEFAULT_GEOMETRY,
    neighbours: int | None = None,
) -> dict[str, float]:
    """Compute all 49 landscape features (paper Table 1) for one sample, plus its basic metadata.

    The same computation as :func:`characterize_report`, returned in MOLA 0.2.0's flat form.
    Prefer :func:`characterize_report` whenever the values are stored or compared, since only it
    records the geometry, the neighbourhood size and why a feature is undefined.

    Args:
        sample: The sample to characterize.
        walk_samples: See :func:`characterize_report`.
        geometry: See :func:`characterize_report`.
        neighbours: See :func:`characterize_report`.

    Returns:
        A dict keyed by each Table 1 feature's own name (`f_cor`, `dist_x_avg`, ..., `nhv_cor_neig`
        — all 49), plus three always-reported metadata fields that are not "landscape features" in
        the paper's sense: `sample_size`, `num_obj`, `num_var`. Undefined features are NaN.

    Raises:
        ValueError: See :func:`characterize_report`.
    """
    return characterize_report(
        sample, walk_samples=walk_samples, geometry=geometry, neighbours=neighbours
    ).as_flat_dict()
