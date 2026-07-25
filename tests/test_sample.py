"""Unit tests for module mola.sample."""

import json

import numpy as np
import pytest

from mola.sample import SCHEMA_VERSION, Sample, metadata_path_for, read_sample, write_sample


def _make_sample(*, size: int = 3, variables: int = 2, objectives: int = 2) -> Sample:
    rng = np.random.default_rng(seed=0)
    return Sample(
        problem="TestProblem",
        variables=rng.uniform(size=(size, variables)),
        objectives=rng.uniform(size=(size, objectives)),
        lower_bounds=np.zeros(variables),
        upper_bounds=np.ones(variables),
        sampler="lhs",
        seed=42,
    )


class TestSampleValidation:
    """Unit tests for Sample's construction-time validation."""

    def test_should_expose_size_and_dimensions(self):
        """Given a valid sample, exposes its size and per-space dimensions."""
        # Arrange & Act
        sample = _make_sample(size=5, variables=3, objectives=2)

        # Assert
        assert sample.size == 5
        assert sample.number_of_variables == 3
        assert sample.number_of_objectives == 2

    def test_should_raise_error_when_solution_counts_disagree(self):
        """Given mismatched variable/objective solution counts, raises ValueError."""
        # Arrange
        variables = np.zeros((3, 2))
        objectives = np.zeros((4, 2))

        # Act & Assert
        with pytest.raises(ValueError, match="disagree"):
            Sample(
                problem="P",
                variables=variables,
                objectives=objectives,
                lower_bounds=np.zeros(2),
                upper_bounds=np.ones(2),
                sampler="lhs",
            )

    def test_should_raise_error_when_empty(self):
        """Given zero solutions, raises ValueError."""
        # Arrange
        variables = np.zeros((0, 2))
        objectives = np.zeros((0, 2))

        # Act & Assert
        with pytest.raises(ValueError, match="at least one solution"):
            Sample(
                problem="P",
                variables=variables,
                objectives=objectives,
                lower_bounds=np.zeros(2),
                upper_bounds=np.ones(2),
                sampler="lhs",
            )

    @pytest.mark.parametrize("bad_shape_attr", ["variables", "objectives"])
    def test_should_raise_error_when_arrays_not_two_dimensional(self, bad_shape_attr):
        """Given a 1-D variables or objectives array, raises ValueError."""
        # Arrange
        arrays = {"variables": np.zeros((3, 2)), "objectives": np.zeros((3, 2))}
        arrays[bad_shape_attr] = np.zeros(3)

        # Act & Assert
        with pytest.raises(ValueError, match="2-dimensional"):
            Sample(
                problem="P",
                lower_bounds=np.zeros(2),
                upper_bounds=np.ones(2),
                sampler="lhs",
                **arrays,
            )

    @pytest.mark.parametrize("bad_shape_attr", ["lower_bounds", "upper_bounds"])
    def test_should_raise_error_when_bounds_do_not_match_number_of_variables(self, bad_shape_attr):
        """Given a bounds array with the wrong length, raises ValueError."""
        # Arrange
        bounds = {"lower_bounds": np.zeros(2), "upper_bounds": np.ones(2)}
        bounds[bad_shape_attr] = np.zeros(5)

        # Act & Assert
        with pytest.raises(ValueError, match=bad_shape_attr):
            Sample(
                problem="P",
                variables=np.zeros((3, 2)),
                objectives=np.zeros((3, 2)),
                sampler="lhs",
                **bounds,
            )


class TestSampleInterchange:
    """Unit tests for writing and reading the CSV + sidecar JSON interchange format."""

    def test_should_round_trip_through_csv_and_json(self, tmp_path):
        """Given a sample written to CSV+JSON, reading it back reproduces every field."""
        # Arrange
        original = _make_sample(size=4, variables=3, objectives=2)
        csv_path = tmp_path / "sample.csv"

        # Act
        write_sample(original, csv_path)
        restored = read_sample(csv_path)

        # Assert
        assert restored.problem == original.problem
        assert restored.sampler == original.sampler
        assert restored.seed == original.seed
        assert restored.schema_version == SCHEMA_VERSION
        np.testing.assert_allclose(restored.variables, original.variables)
        np.testing.assert_allclose(restored.objectives, original.objectives)
        np.testing.assert_allclose(restored.lower_bounds, original.lower_bounds)
        np.testing.assert_allclose(restored.upper_bounds, original.upper_bounds)

    def test_should_write_sidecar_json_next_to_csv(self, tmp_path):
        """Given a sample, writing it also writes a matching sidecar metadata JSON."""
        # Arrange
        sample = _make_sample()
        csv_path = tmp_path / "sample.csv"

        # Act
        write_sample(sample, csv_path)

        # Assert
        assert metadata_path_for(csv_path).is_file()
        metadata = json.loads(metadata_path_for(csv_path).read_text())
        assert metadata["problem"] == "TestProblem"
        assert metadata["sample_size"] == sample.size
        assert metadata["sampler"] == "lhs"
        assert metadata["seed"] == 42

    def test_should_raise_file_not_found_when_metadata_missing(self, tmp_path):
        """Given a CSV with no sidecar JSON, raises FileNotFoundError."""
        # Arrange
        csv_path = tmp_path / "orphan.csv"
        csv_path.write_text("problem,sample_id,x_1,f_1\nP,0,0.0,0.0\n")

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            read_sample(csv_path)

    def test_should_raise_error_on_unsupported_schema_version(self, tmp_path):
        """Given a metadata JSON with a future schema_version, raises ValueError."""
        # Arrange
        sample = _make_sample()
        csv_path = tmp_path / "sample.csv"
        write_sample(sample, csv_path)
        metadata = json.loads(metadata_path_for(csv_path).read_text())
        metadata["schema_version"] = SCHEMA_VERSION + 1
        metadata_path_for(csv_path).write_text(json.dumps(metadata))

        # Act & Assert
        with pytest.raises(ValueError, match="schema version"):
            read_sample(csv_path)

    def test_should_raise_error_when_csv_missing_columns(self, tmp_path):
        """Given a CSV missing declared variable/objective columns, raises ValueError."""
        # Arrange
        sample = _make_sample(variables=2, objectives=2)
        csv_path = tmp_path / "sample.csv"
        write_sample(sample, csv_path)
        csv_path.write_text("problem,sample_id,x_1,f_1\nP,0,0.0,0.0\n")

        # Act & Assert
        with pytest.raises(ValueError, match="missing columns"):
            read_sample(csv_path)
