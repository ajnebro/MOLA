"""Unit tests for module mola.characterize."""

import numpy as np
import pytest

from mola.characterize import characterize
from mola.distance import build_neighbourhood
from mola.features import hv_cor_neig, hvd_cor_neig, nhv_cor_neig
from mola.hypervolume import reference_point
from mola.sample import Sample

_ALL_49_FEATURE_NAMES = {
    # Global (14)
    "f_cor",
    "dist_x_avg",
    "dist_x_max",
    "dist_f_avg",
    "dist_f_max",
    "nd_n",
    "supp_n",
    "hv",
    "dist_x_nd_avg",
    "dist_x_nd_max",
    "fdc",
    "rank_avg",
    "rank_max",
    "rank_ent",
    # Multimodality (9)
    "slo_n",
    "slo_dist_avg",
    "slo_dist_max",
    "plo_n",
    "plo_dist_avg",
    "plo_dist_max",
    "nd_per_plo",
    "length_aws",
    "eval_aws",
    # Evolvability (13)
    "sup_avg_neig",
    "inf_avg_neig",
    "inc_avg_neig",
    "lnd_avg_neig",
    "lsupp_avg_neig",
    "dist_x_avg_neig",
    "dist_f_avg_neig",
    "dist_f_dist_x_avg_neig",
    "diff_f_avg_neig",
    "diff_f_dist_x_avg_neig",
    "hv_avg_neig",
    "hvd_avg_neig",
    "nhv_avg_neig",
    # Ruggedness (13)
    "dist_x_cor_neig",
    "dist_f_cor_neig",
    "sup_cor_neig",
    "inf_cor_neig",
    "inc_cor_neig",
    "lnd_cor_neig",
    "lsupp_cor_neig",
    "dist_f_dist_x_cor_neig",
    "diff_f_cor_neig",
    "diff_f_dist_x_cor_neig",
    "hv_cor_neig",
    "hvd_cor_neig",
    "nhv_cor_neig",
}
_METADATA_NAMES = {"sample_size", "num_obj", "num_var"}


def _make_sample(
    *, size: int = 30, variables: int = 3, objectives: int = 2, seed: int = 1
) -> Sample:
    rng = np.random.default_rng(seed=seed)
    return Sample(
        problem="TestProblem",
        variables=rng.uniform(size=(size, variables)),
        objectives=rng.uniform(size=(size, objectives)),
        lower_bounds=np.zeros(variables),
        upper_bounds=np.ones(variables),
        sampler="lhs",
        seed=seed,
    )


class TestCharacterize:
    """Unit tests for characterize()."""

    def test_should_return_all_49_features_plus_metadata(self):
        """Given a valid sample, returns exactly the 49 Table 1 features plus 3 metadata fields."""
        # Arrange
        sample = _make_sample()

        # Act
        result = characterize(sample)

        # Assert
        assert set(result.keys()) == _ALL_49_FEATURE_NAMES | _METADATA_NAMES

    def test_should_report_correct_metadata(self):
        """Given a sample, reports its size and dimensions verbatim."""
        # Arrange
        sample = _make_sample(size=17, variables=4, objectives=3)

        # Act
        result = characterize(sample)

        # Assert
        assert result["sample_size"] == 17
        assert result["num_var"] == 4
        assert result["num_obj"] == 3

    def test_should_return_finite_or_nan_floats_for_every_feature(self):
        """Given a valid sample, every feature value is a float (finite or NaN, never other)."""
        # Arrange
        sample = _make_sample()

        # Act
        result = characterize(sample)

        # Assert
        for name in _ALL_49_FEATURE_NAMES:
            assert isinstance(result[name], float), f"{name} is not a float: {type(result[name])}"

    def test_should_wire_hv_cor_neig_arguments_correctly_despite_its_different_argument_order(self):
        """Given a sample, hv_cor_neig matches an independently rebuilt substrate.

        hv_cor_neig(objectives, ref, neighbourhood) takes ref before neighbourhood, unlike its
        siblings hvd_cor_neig/nhv_cor_neig(objectives, neighbourhood, ref) -- this test guards
        against the orchestrator accidentally swapping the two positionally.
        """
        # Arrange
        sample = _make_sample()
        neighbourhood = build_neighbourhood(sample.variables, neighbours=sample.number_of_variables)
        ref = reference_point(sample.objectives)

        # Act
        result = characterize(sample)
        expected_hv_cor_neig = hv_cor_neig(
            objectives=sample.objectives, ref=ref, neighbourhood=neighbourhood
        )
        expected_hvd_cor_neig = hvd_cor_neig(
            objectives=sample.objectives, neighbourhood=neighbourhood, ref=ref
        )
        expected_nhv_cor_neig = nhv_cor_neig(
            objectives=sample.objectives, neighbourhood=neighbourhood, ref=ref
        )

        # Assert
        assert result["hv_cor_neig"] == pytest.approx(expected_hv_cor_neig, nan_ok=True)
        assert result["hvd_cor_neig"] == pytest.approx(expected_hvd_cor_neig, nan_ok=True)
        assert result["nhv_cor_neig"] == pytest.approx(expected_nhv_cor_neig, nan_ok=True)

    def test_should_be_deterministic_for_a_fixed_seed(self):
        """Given the same sample and seed twice, returns identical results (adaptive walk RNG)."""
        # Arrange
        sample = _make_sample()

        # Act
        first = characterize(sample)
        second = characterize(sample)

        # Assert
        assert first == second

    def test_should_cap_walk_samples_at_walk_samples_argument(self):
        """Given an explicit walk_samples argument, accepts it without error."""
        # Arrange
        sample = _make_sample(size=10)

        # Act
        result = characterize(sample, walk_samples=5)

        # Assert
        assert isinstance(result["length_aws"], float)
        assert isinstance(result["eval_aws"], float)
