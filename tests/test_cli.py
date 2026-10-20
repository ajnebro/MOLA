"""Unit tests for module mola.cli."""

import json

import numpy as np
import pandas as pd
from typer.testing import CliRunner

from mola.cli import app
from mola.sample import Sample, write_sample

runner = CliRunner()


def _reject_non_standard_constant(name: str) -> None:
    raise AssertionError(f"report contains the non-standard JSON constant {name}")


def _make_sample_file(
    tmp_path,
    *,
    size: int = 20,
    variables: int = 3,
    objectives: int = 2,
    upper_bound: float = 1.0,
):
    """Write a small interchange sample fixture under tmp_path, return its CSV path."""
    rng = np.random.default_rng(seed=0)
    sample = Sample(
        problem="TestProblem",
        variables=rng.uniform(size=(size, variables)),
        objectives=rng.uniform(size=(size, objectives)),
        lower_bounds=np.zeros(variables),
        upper_bounds=np.full(variables, upper_bound),
        sampler="lhs",
        seed=0,
    )
    csv_path = tmp_path / "sample.csv"
    write_sample(sample, csv_path)
    return csv_path


class TestSampleCommand:
    """Unit tests for `mola sample`."""

    def test_should_write_an_interchange_sample_file(self, tmp_path):
        """Given a known jMetalPy problem, writes a CSV + sidecar JSON with the requested size."""
        # Arrange
        output = tmp_path / "sample.csv"

        # Act
        result = runner.invoke(
            app,
            [
                "sample",
                "ZDT1",
                str(output),
                "--variables",
                "3",
                "--sample-size",
                "10",
                "--seed",
                "1",
            ],
        )

        # Assert
        assert result.exit_code == 0
        assert output.is_file()
        assert output.with_suffix(".json").is_file()
        frame = pd.read_csv(output)
        assert len(frame) == 10

    def test_should_exit_with_error_on_unknown_problem(self, tmp_path):
        """Given an unknown problem name, exits non-zero with a clean message, no traceback."""
        # Arrange
        output = tmp_path / "sample.csv"

        # Act
        result = runner.invoke(app, ["sample", "NotAProblem", str(output)])

        # Assert
        assert result.exit_code == 1
        assert "not a jMetalPy FloatProblem" in result.output
        assert not output.exists()


class TestCharacterizeCommand:
    """Unit tests for `mola characterize`."""

    def test_should_print_all_49_features_plus_metadata(self, tmp_path):
        """Given a valid sample file, prints exactly 52 "key: value" lines."""
        # Arrange
        sample_path = _make_sample_file(tmp_path)

        # Act
        result = runner.invoke(app, ["characterize", str(sample_path)])

        # Assert
        assert result.exit_code == 0
        lines = result.output.strip().splitlines()
        assert len(lines) == 52
        assert lines[0].startswith("sample_size:")
        assert any(line.startswith("nhv_cor_neig:") for line in lines)

    def test_should_write_json_output(self, tmp_path):
        """Given --output with a .json suffix, writes the full result as a JSON object."""
        # Arrange
        sample_path = _make_sample_file(tmp_path)
        output = tmp_path / "result.json"

        # Act
        result = runner.invoke(app, ["characterize", str(sample_path), "--output", str(output)])

        # Assert
        assert result.exit_code == 0
        saved = json.loads(output.read_text())
        assert len(saved) == 52
        assert saved["sample_size"] == 20

    def test_should_write_csv_output(self, tmp_path):
        """Given --output with a .csv suffix, writes the full result as a single-row table."""
        # Arrange
        sample_path = _make_sample_file(tmp_path)
        output = tmp_path / "result.csv"

        # Act
        result = runner.invoke(app, ["characterize", str(sample_path), "--output", str(output)])

        # Assert
        assert result.exit_code == 0
        frame = pd.read_csv(output)
        assert frame.shape == (1, 52)

    def test_should_exit_with_error_on_missing_sample_file(self, tmp_path):
        """Given a nonexistent sample path, exits non-zero with a clean message."""
        # Arrange
        missing = tmp_path / "does_not_exist.csv"

        # Act
        result = runner.invoke(app, ["characterize", str(missing)])

        # Assert
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_should_exit_with_error_on_unrecognized_output_suffix(self, tmp_path):
        """Given an --output path with an unsupported suffix, exits non-zero with a clean error."""
        # Arrange
        sample_path = _make_sample_file(tmp_path)
        output = tmp_path / "result.txt"

        # Act
        result = runner.invoke(app, ["characterize", str(sample_path), "--output", str(output)])

        # Assert
        assert result.exit_code == 1
        assert "unrecognized --output suffix" in result.output
        assert not output.exists()

    def test_should_write_the_full_report_as_strict_json(self, tmp_path):
        """Given --report, writes every feature's status plus provenance, with no NaN."""
        # Arrange
        sample_path = _make_sample_file(tmp_path)
        report = tmp_path / "report.json"

        # Act
        result = runner.invoke(app, ["characterize", str(sample_path), "--report", str(report)])

        # Assert
        assert result.exit_code == 0
        saved = json.loads(report.read_text(), parse_constant=_reject_non_standard_constant)
        assert saved["geometry"] == "bound"
        assert saved["neighbours"] == 3
        assert saved["feature_profile"] == "paper49-v1"
        assert len(saved["features"]) == 49
        assert {entry["status"] for entry in saved["features"].values()} <= {
            "defined",
            "undefined",
        }

    def test_should_pass_the_geometry_and_neighbourhood_size_through(self, tmp_path):
        """Given --geometry raw and -k 2, the report records both."""
        # Arrange
        sample_path = _make_sample_file(tmp_path)
        report = tmp_path / "report.json"

        # Act
        result = runner.invoke(
            app,
            [
                "characterize",
                str(sample_path),
                "--geometry",
                "raw",
                "-k",
                "2",
                "--report",
                str(report),
            ],
        )

        # Assert
        assert result.exit_code == 0
        saved = json.loads(report.read_text())
        assert saved["geometry"] == "raw"
        assert saved["neighbours"] == 2

    def test_should_exit_with_error_on_unbounded_variables_under_the_bound_geometry(self, tmp_path):
        """Given infinite bounds, the default geometry fails cleanly; raw still works."""
        # Arrange
        sample_path = _make_sample_file(tmp_path, upper_bound=np.inf)

        # Act
        bound_result = runner.invoke(app, ["characterize", str(sample_path)])
        raw_result = runner.invoke(app, ["characterize", str(sample_path), "--geometry", "raw"])

        # Assert
        assert bound_result.exit_code == 1
        assert "needs finite bounds" in bound_result.output
        assert raw_result.exit_code == 0

    def test_should_reject_an_unknown_geometry(self, tmp_path):
        """Given an unknown --geometry value, exits with Typer's usage error."""
        # Arrange
        sample_path = _make_sample_file(tmp_path)

        # Act
        result = runner.invoke(app, ["characterize", str(sample_path), "--geometry", "sample"])

        # Assert
        assert result.exit_code == 2

    def test_should_pass_the_objective_scaling_through(self, tmp_path):
        """Given --objective-scaling sample, the report records it."""
        # Arrange
        sample_path = _make_sample_file(tmp_path)
        report = tmp_path / "report.json"

        # Act
        result = runner.invoke(
            app,
            [
                "characterize",
                str(sample_path),
                "--objective-scaling",
                "sample",
                "--report",
                str(report),
            ],
        )

        # Assert
        assert result.exit_code == 0
        assert json.loads(report.read_text())["objective_scaling"] == "sample"


class TestRunCommand:
    """Unit tests for `mola run`."""

    def test_should_characterize_a_jmetalpy_problem_end_to_end(self):
        """Given a known jMetalPy problem, samples, evaluates, and prints all 52 result keys."""
        # Act
        result = runner.invoke(
            app, ["run", "ZDT1", "--variables", "3", "--sample-size", "10", "--seed", "1"]
        )

        # Assert
        assert result.exit_code == 0
        lines = result.output.strip().splitlines()
        assert len(lines) == 52
        assert lines[0] == "sample_size: 10"

    def test_should_exit_with_error_on_unknown_problem(self):
        """Given an unknown problem name, exits non-zero with a clean message, no traceback."""
        # Act
        result = runner.invoke(app, ["run", "NotAProblem"])

        # Assert
        assert result.exit_code == 1
        assert "not a jMetalPy FloatProblem" in result.output

    def test_should_write_a_report_for_a_jmetalpy_problem(self, tmp_path):
        """Given --report, `mola run` writes the same report as `mola characterize`."""
        # Arrange
        report = tmp_path / "report.json"

        # Act
        result = runner.invoke(
            app,
            ["run", "ZDT1", "--variables", "3", "--sample-size", "10", "--seed", "1"]
            + ["--report", str(report)],
        )

        # Assert
        assert result.exit_code == 0
        saved = json.loads(report.read_text())
        assert saved["problem"] == "ZDT1"
        assert saved["seed"] == 1
        assert saved["sample_size"] == 10
