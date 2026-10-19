"""Unit tests for module mola.report."""

import json
import math

from mola.report import FEATURE_PROFILE, Characterization, Provenance


def _make_characterization() -> Characterization:
    provenance = Provenance(
        mola_version="0.3.0",
        feature_profile=FEATURE_PROFILE,
        geometry="bound",
        neighbours=3,
        walk_samples=10,
        problem="P",
        sampler="lhs",
        seed=7,
        schema_version=1,
        sample_size=10,
        num_obj=2,
        num_var=3,
    )
    return Characterization(
        features={"nd_n": 0.2, "fdc": math.nan},
        causes={"fdc": "|ND| = 2: at least 3 non-dominated solutions are needed"},
        provenance=provenance,
    )


class TestCharacterization:
    """Unit tests for Characterization."""

    def test_should_flatten_to_the_three_metadata_fields_then_the_features(self):
        """as_flat_dict() returns 0.2.0's layout: sample_size, num_obj, num_var, features."""
        # Arrange
        characterization = _make_characterization()

        # Act
        flat = characterization.as_flat_dict()

        # Assert
        assert list(flat) == ["sample_size", "num_obj", "num_var", "nd_n", "fdc"]
        assert flat["sample_size"] == 10
        assert math.isnan(flat["fdc"])

    def test_should_report_defined_and_undefined_features_with_their_status(self):
        """to_json_dict() gives each feature a value and a status, plus a cause if undefined."""
        # Arrange
        characterization = _make_characterization()

        # Act
        report = characterization.to_json_dict()

        # Assert
        assert report["features"]["nd_n"] == {"value": 0.2, "status": "defined"}
        assert report["features"]["fdc"] == {
            "value": None,
            "status": "undefined",
            "cause": characterization.causes["fdc"],
        }

    def test_should_include_every_provenance_field(self):
        """to_json_dict() carries the version, profile, geometry and neighbourhood size."""
        # Arrange
        characterization = _make_characterization()

        # Act
        report = characterization.to_json_dict()

        # Assert
        assert report["mola_version"] == "0.3.0"
        assert report["feature_profile"] == FEATURE_PROFILE
        assert report["geometry"] == "bound"
        assert report["neighbours"] == 3
        assert report["walk_samples"] == 10
        assert report["seed"] == 7

    def test_should_serialize_to_strict_json(self):
        """to_json_dict() never contains NaN, so strict JSON serialization succeeds."""
        # Arrange
        characterization = _make_characterization()

        # Act
        text = json.dumps(characterization.to_json_dict(), allow_nan=False)

        # Assert
        assert json.loads(text)["features"]["fdc"]["value"] is None
