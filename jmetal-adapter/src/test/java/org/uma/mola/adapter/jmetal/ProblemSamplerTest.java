package org.uma.mola.adapter.jmetal;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.uma.jmetal.problem.doubleproblem.DoubleProblem;
import org.uma.jmetal.problem.multiobjective.zdt.ZDT1;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;

@DisplayName("Unit tests for class ProblemSampler")
class ProblemSamplerTest {

  private DoubleProblem problem;

  @BeforeEach
  void setUp() {
    problem = new ZDT1(3);
  }

  @Nested
  @DisplayName("When sampling a problem")
  class SamplingAProblem {

    @Test
    @DisplayName("given a sample size, when sampling, then that many solutions are returned")
    void givenASampleSize_whenSampling_thenThatManySolutionsAreReturned() {
      // Arrange & Act
      List<DoubleSolution> solutions = ProblemSampler.sample(problem, 15, 1L);

      // Assert
      assertEquals(15, solutions.size());
    }

    @Test
    @DisplayName("given a sampled solution, when evaluated, then it matches direct evaluation")
    void givenASampledSolution_whenEvaluated_thenItMatchesDirectEvaluation() {
      // Arrange & Act
      List<DoubleSolution> solutions = ProblemSampler.sample(problem, 5, 2L);

      // Assert
      for (DoubleSolution solution : solutions) {
        DoubleSolution reevaluated = problem.createSolution();
        for (int i = 0; i < solution.variables().size(); i++) {
          reevaluated.variables().set(i, solution.variables().get(i));
        }
        problem.evaluate(reevaluated);
        assertEquals(solution.objectives()[0], reevaluated.objectives()[0], 1e-12);
        assertEquals(solution.objectives()[1], reevaluated.objectives()[1], 1e-12);
      }
    }

    @Test
    @DisplayName("given problem bounds, when sampling, then every variable respects them")
    void givenProblemBounds_whenSampling_thenEveryVariableRespectsThem() {
      // Arrange & Act
      List<DoubleSolution> solutions = ProblemSampler.sample(problem, 20, 3L);

      // Assert
      for (DoubleSolution solution : solutions) {
        for (int i = 0; i < solution.variables().size(); i++) {
          double lower = problem.variableBounds().get(i).getLowerBound();
          double upper = problem.variableBounds().get(i).getUpperBound();
          double value = solution.variables().get(i);
          assertTrue(value >= lower && value <= upper);
        }
      }
    }

    @Test
    @DisplayName("given the same seed twice, when sampling, then the results are identical")
    void givenTheSameSeedTwice_whenSampling_thenTheResultsAreIdentical() {
      // Arrange & Act
      List<DoubleSolution> first = ProblemSampler.sample(problem, 10, 7L);
      List<DoubleSolution> second = ProblemSampler.sample(problem, 10, 7L);

      // Assert
      for (int i = 0; i < first.size(); i++) {
        assertEquals(first.get(i).variables(), second.get(i).variables());
      }
    }

    @Test
    @DisplayName("given a null seed, when sampling twice, then no exception is thrown")
    void givenANullSeed_whenSamplingTwice_thenNoExceptionIsThrown() {
      // Arrange & Act & Assert
      ProblemSampler.sample(problem, 5, null);
      ProblemSampler.sample(problem, 5, null);
    }
  }
}
