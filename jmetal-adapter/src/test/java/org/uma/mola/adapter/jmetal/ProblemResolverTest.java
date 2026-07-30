package org.uma.mola.adapter.jmetal;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.function.Executable;
import org.uma.jmetal.problem.doubleproblem.DoubleProblem;

@DisplayName("Unit tests for class ProblemResolver")
class ProblemResolverTest {

  private static final String ZDT1_CLASS_NAME = "org.uma.jmetal.problem.multiobjective.zdt.ZDT1";
  private static final String RE21_CLASS_NAME = "org.uma.jmetal.problem.multiobjective.re.RE21";

  @Nested
  @DisplayName("When resolving a valid problem class name")
  class ResolvingAValidProblemClassName {

    @Test
    @DisplayName("given a variables count, when resolved, then it is passed to the constructor")
    void givenAVariablesCount_whenResolved_thenItIsPassedToTheConstructor() {
      // Arrange & Act
      DoubleProblem problem = ProblemResolver.resolve(ZDT1_CLASS_NAME, 7);

      // Assert
      assertEquals(7, problem.numberOfVariables());
    }

    @Test
    @DisplayName("given no variables count, when resolved, then the no-arg constructor is used")
    void givenNoVariablesCount_whenResolved_thenTheNoArgConstructorIsUsed() {
      // Arrange & Act
      DoubleProblem problem = ProblemResolver.resolve(ZDT1_CLASS_NAME, null);

      // Assert: ZDT1() delegates to ZDT1(30).
      assertEquals(30, problem.numberOfVariables());
    }

    @Test
    @DisplayName("given a fixed-dimension problem, when resolved without --variables, then it works")
    void givenAFixedDimensionProblem_whenResolvedWithoutVariables_thenItWorks() {
      // Arrange & Act
      DoubleProblem problem = ProblemResolver.resolve(RE21_CLASS_NAME, null);

      // Assert
      assertEquals("RE21", problem.name());
    }
  }

  @Nested
  @DisplayName("When resolving an invalid problem class name")
  class ResolvingAnInvalidProblemClassName {

    @Test
    @DisplayName("given an unknown class name, when resolved, then throw ProblemResolutionException")
    void givenAnUnknownClassName_whenResolved_thenProblemResolutionExceptionIsThrown() {
      // Arrange
      Executable executable = () -> ProblemResolver.resolve("not.a.real.Class", null);

      // Act & Assert
      assertThrows(ProblemResolutionException.class, executable);
    }

    @Test
    @DisplayName("given a class that is not a DoubleProblem, when resolved, then throw")
    void givenAClassThatIsNotADoubleProblem_whenResolved_thenProblemResolutionExceptionIsThrown() {
      // Arrange
      Executable executable = () -> ProblemResolver.resolve("java.lang.String", null);

      // Act & Assert
      assertThrows(ProblemResolutionException.class, executable);
    }

    @Test
    @DisplayName("given a fixed-dimension problem with --variables, when resolved, then throw")
    void givenAFixedDimensionProblemWithVariables_whenResolved_thenProblemResolutionExceptionIsThrown() {
      // Arrange
      Executable executable = () -> ProblemResolver.resolve(RE21_CLASS_NAME, 5);

      // Act & Assert
      assertThrows(ProblemResolutionException.class, executable);
    }
  }
}
