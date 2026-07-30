"""End-to-end integration tests: an adapter's Sample feeding straight into characterize()."""

from jmetal.problem import ZDT1

from mola.adapters.jmetalpy import sample_problem
from mola.characterize import characterize

_METADATA_NAMES = {"sample_size", "num_obj", "num_var"}


class TestJMetalPyEndToEnd:
    """Sampling a real jMetalPy problem and characterizing it end to end."""

    def test_should_characterize_a_jmetalpy_problem_sampled_in_process(self):
        """Given a jMetalPy ZDT1 problem, sample_problem + characterize produce a full result."""
        # Arrange
        problem = ZDT1(number_of_variables=5)

        # Act
        sample = sample_problem(problem, sample_size=100, seed=123)
        result = characterize(sample)

        # Assert
        assert len(result) == 52
        assert result["sample_size"] == 100
        assert result["num_var"] == 5
        assert result["num_obj"] == 2
        for name, value in result.items():
            if name not in _METADATA_NAMES:
                assert isinstance(value, float), f"{name} is not a float: {type(value)}"
