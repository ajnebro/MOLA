"""Unit tests for module mola.adapters.jmetalpy."""

import numpy as np
import pytest
from jmetal.core.problem import FloatProblem
from jmetal.core.solution import FloatSolution
from jmetal.problem import ZDT1

from mola.adapters.jmetalpy import DEFAULT_SAMPLE_SIZE_PER_VARIABLE, sample_problem


class _MaximizeOneObjectiveProblem(FloatProblem):
    """A 2-variable, 2-objective problem where both objectives are the same raw sum(x).

    One objective is declared MINIMIZE and the other MAXIMIZE, so a correct adapter must negate
    only the second -- letting a test assert the two returned columns are exact negatives of each
    other despite both being computed from the identical raw value.
    """

    def __init__(self):
        super().__init__()
        self.lower_bound = [0.0, 0.0]
        self.upper_bound = [1.0, 1.0]
        self.obj_directions = [self.MINIMIZE, self.MAXIMIZE]

    def number_of_objectives(self) -> int:
        return 2

    def number_of_constraints(self) -> int:
        return 0

    def evaluate(self, solution: FloatSolution) -> FloatSolution:
        raw = sum(solution.variables)
        solution.objectives[0] = raw
        solution.objectives[1] = raw
        return solution

    def name(self) -> str:
        return "MaximizeOneObjective"


class TestSampleProblem:
    """Unit tests for sample_problem()."""

    def test_should_default_sample_size_to_200_times_number_of_variables(self):
        """Given no explicit sample_size, samples 200 * D solutions."""
        # Arrange
        problem = ZDT1(number_of_variables=3)

        # Act
        sample = sample_problem(problem, seed=0)

        # Assert
        assert sample.size == DEFAULT_SAMPLE_SIZE_PER_VARIABLE * 3

    def test_should_respect_explicit_sample_size(self):
        """Given an explicit sample_size, samples exactly that many solutions."""
        # Arrange
        problem = ZDT1(number_of_variables=3)

        # Act
        sample = sample_problem(problem, sample_size=17, seed=0)

        # Assert
        assert sample.size == 17

    def test_should_sample_within_problem_bounds(self):
        """Given a problem's bounds, every sampled decision vector respects them."""
        # Arrange
        problem = ZDT1(number_of_variables=4)

        # Act
        sample = sample_problem(problem, sample_size=50, seed=1)

        # Assert
        assert np.all(sample.variables >= problem.lower_bound)
        assert np.all(sample.variables <= problem.upper_bound)

    def test_should_evaluate_each_solution_correctly(self):
        """Given a minimize-only problem, each row's objectives match direct evaluation."""
        # Arrange
        problem = ZDT1(number_of_variables=3)

        # Act
        sample = sample_problem(problem, sample_size=5, seed=2)

        # Assert
        for i, decision_vector in enumerate(sample.variables):
            solution = problem.create_solution()
            solution.variables = list(decision_vector)
            problem.evaluate(solution)
            assert sample.objectives[i] == pytest.approx(solution.objectives)

    def test_should_negate_maximize_objectives(self):
        """Given a MAXIMIZE-direction objective, its column is the negative of the raw value."""
        # Arrange
        problem = _MaximizeOneObjectiveProblem()

        # Act
        sample = sample_problem(problem, sample_size=10, seed=3)

        # Assert
        assert sample.objectives[:, 0] == pytest.approx(-sample.objectives[:, 1])

    def test_should_be_deterministic_for_a_fixed_seed(self):
        """Given the same problem and seed twice, produces identical samples."""
        # Arrange
        problem = ZDT1(number_of_variables=3)

        # Act
        first = sample_problem(problem, sample_size=10, seed=4)
        second = sample_problem(problem, sample_size=10, seed=4)

        # Assert
        np.testing.assert_array_equal(first.variables, second.variables)
        np.testing.assert_array_equal(first.objectives, second.objectives)

    def test_should_record_problem_name_sampler_and_seed(self):
        """Given a problem, records its name, the "lhs" sampler, and the given seed."""
        # Arrange
        problem = ZDT1(number_of_variables=2)

        # Act
        sample = sample_problem(problem, sample_size=5, seed=42)

        # Assert
        assert sample.problem == "ZDT1"
        assert sample.sampler == "lhs"
        assert sample.seed == 42
