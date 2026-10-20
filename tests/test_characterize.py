"""Unit tests for module mola.characterize."""

import math
from dataclasses import replace

import numpy as np
import pytest

from mola import __version__
from mola.characterize import characterize, characterize_report
from mola.distance import build_neighbourhood
from mola.features import (
    dist_f_avg_neig,
    dist_x_avg_neig,
    hv_cor_neig,
    hvd_cor_neig,
    nhv_cor_neig,
)
from mola.hypervolume import reference_point
from mola.normalization import build_normalizers
from mola.report import FEATURE_PROFILE
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

    def test_should_normalize_the_average_neighbour_distances(self):
        """Given a sample, the two neighbour-distance features use the whole-sample ranges."""
        # Arrange
        sample = _make_sample()
        neighbourhood = build_neighbourhood(sample.variables, neighbours=sample.number_of_variables)
        normalizers = build_normalizers(sample.variables, sample.objectives)

        # Act
        result = characterize(sample)

        # Assert
        assert result["dist_x_avg_neig"] == pytest.approx(
            dist_x_avg_neig(sample.variables, neighbourhood, normalizers.variable_space)
        )
        assert result["dist_f_avg_neig"] == pytest.approx(
            dist_f_avg_neig(sample.objectives, neighbourhood, normalizers.objective_space)
        )
        assert result["dist_f_dist_x_avg_neig"] == pytest.approx(
            result["dist_f_avg_neig"] / result["dist_x_avg_neig"]
        )

    def test_should_be_invariant_to_per_variable_affine_maps_under_the_bound_geometry(self):
        """Given the same sample in other units (bounds included), all 49 features match."""
        # Arrange
        sample = _make_sample(size=40, variables=3, objectives=2)
        scale = np.array([1e-3, 5.0, 250.0])
        shift = np.array([-4.0, 100.0, 0.5])
        rescaled = replace(
            sample,
            variables=sample.variables * scale + shift,
            lower_bounds=sample.lower_bounds * scale + shift,
            upper_bounds=sample.upper_bounds * scale + shift,
        )

        # Act
        result = characterize(sample)
        rescaled_result = characterize(rescaled)

        # Assert
        for name in _ALL_49_FEATURE_NAMES:
            assert rescaled_result[name] == pytest.approx(result[name], nan_ok=True), name

    def test_should_depend_on_the_units_under_the_raw_geometry(self):
        """Given heterogeneous rescaling, the raw geometry changes decision-space features."""
        # Arrange
        sample = _make_sample(size=40, variables=3, objectives=2)
        scale = np.array([1e-3, 5.0, 250.0])
        rescaled = replace(
            sample,
            variables=sample.variables * scale,
            lower_bounds=sample.lower_bounds * scale,
            upper_bounds=sample.upper_bounds * scale,
        )

        # Act
        result = characterize(sample, geometry="raw")
        rescaled_result = characterize(rescaled, geometry="raw")

        # Assert
        assert rescaled_result["dist_x_max"] != pytest.approx(result["dist_x_max"])

    def test_should_use_the_requested_neighbourhood_size(self):
        """Given neighbours=5, builds the graph with k = 5 instead of D."""
        # Arrange
        sample = _make_sample(variables=3)
        neighbourhood = build_neighbourhood(sample.variables, neighbours=5)
        normalizers = build_normalizers(sample.variables, sample.objectives)

        # Act
        result = characterize(sample, neighbours=5)

        # Assert
        assert result["dist_x_avg_neig"] == pytest.approx(
            dist_x_avg_neig(sample.variables, neighbourhood, normalizers.variable_space)
        )

    def test_should_be_invariant_to_per_objective_scaling_under_sample_objective_scaling(self):
        """Given objectives in other units, all 49 features match under the sample profile."""
        # Arrange: powers of two keep the rescaling exact in floating point
        sample = _make_sample(size=40, variables=3, objectives=2)
        rescaled = replace(sample, objectives=sample.objectives * np.array([2.0**-6, 2.0**9]))

        # Act
        result = characterize(sample, objective_scaling="sample")
        rescaled_result = characterize(rescaled, objective_scaling="sample")

        # Assert
        for name in _ALL_49_FEATURE_NAMES:
            assert rescaled_result[name] == pytest.approx(result[name], nan_ok=True), name

    def test_should_depend_on_objective_units_under_raw_objective_scaling(self):
        """Given objectives in other units, the raw profile changes the hypervolume."""
        # Arrange
        sample = _make_sample(size=40, variables=3, objectives=2)
        rescaled = replace(sample, objectives=sample.objectives * np.array([2.0**-6, 2.0**9]))

        # Act
        result = characterize(sample)
        rescaled_result = characterize(rescaled)

        # Assert
        assert rescaled_result["hv"] != pytest.approx(result["hv"])


class TestCharacterizeReport:
    """Unit tests for characterize_report()."""

    def test_should_match_the_flat_result_of_characterize(self):
        """Given a sample, the report's features are characterize()'s 49 values."""
        # Arrange
        sample = _make_sample()

        # Act
        report = characterize_report(sample)
        flat = characterize(sample)

        # Assert
        assert set(report.features) == _ALL_49_FEATURE_NAMES
        for name in _ALL_49_FEATURE_NAMES:
            assert report.features[name] == pytest.approx(flat[name], nan_ok=True)

    def test_should_record_the_geometry_neighbourhood_size_and_walk_count_used(self):
        """Given explicit settings, the provenance records what was actually used."""
        # Arrange: k = 50 and 100 walks are both capped by n = 30
        sample = _make_sample(size=30)

        # Act
        report = characterize_report(sample, geometry="raw", neighbours=50, walk_samples=100)

        # Assert
        assert report.provenance.geometry == "raw"
        assert report.provenance.neighbours == 29
        assert report.provenance.walk_samples == 30
        assert report.provenance.feature_profile == FEATURE_PROFILE
        assert report.provenance.mola_version == __version__

    def test_should_default_to_k_equal_to_the_number_of_variables(self):
        """Given no neighbours argument, records k = D."""
        # Arrange
        sample = _make_sample(variables=4)

        # Act
        report = characterize_report(sample)

        # Assert
        assert report.provenance.neighbours == 4
        assert report.provenance.geometry == "bound"

    def test_should_give_a_cause_for_every_undefined_feature(self):
        """Given a sample with a single non-dominated solution, explains each NaN."""
        # Arrange: solution 0 dominates every other one, so |ND| = 1
        sample = _make_sample()
        objectives = sample.objectives + 1.0
        objectives[0] = 0.0
        sample = replace(sample, objectives=objectives)

        # Act
        report = characterize_report(sample)

        # Assert
        undefined = {name for name, value in report.features.items() if math.isnan(value)}
        assert undefined == set(report.causes)
        assert report.causes["dist_x_nd_avg"].startswith("|ND| = 1")
        assert report.causes["fdc"].startswith("|ND| = 1")

    def test_should_record_the_objective_scaling(self):
        """Given the sample objective profile, the provenance records it."""
        # Arrange
        sample = _make_sample()

        # Act
        report = characterize_report(sample, objective_scaling="sample")

        # Assert
        assert report.provenance.objective_scaling == "sample"
        assert characterize_report(sample).provenance.objective_scaling == "raw"
