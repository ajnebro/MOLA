package org.uma.mola.adapter.jmetal;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;
import java.util.List;
import java.util.Random;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.function.Executable;
import org.uma.jmetal.util.bounds.Bounds;

@DisplayName("Unit tests for class LatinHypercubeSampler")
class LatinHypercubeSamplerTest {

  private List<Bounds<Double>> unitBounds;

  @BeforeEach
  void setUp() {
    unitBounds = List.of(Bounds.create(0.0, 1.0), Bounds.create(0.0, 1.0));
  }

  @Nested
  @DisplayName("When sampling with valid arguments")
  class SamplingWithValidArguments {

    @Test
    @DisplayName("given a sample size and bounds, when sampling, then the shape matches")
    void givenSampleSizeAndBounds_whenSampling_thenShapeMatches() {
      // Arrange
      int sampleSize = 25;

      // Act
      double[][] points = LatinHypercubeSampler.sample(sampleSize, unitBounds, new Random(1));

      // Assert
      assertEquals(sampleSize, points.length);
      Arrays.stream(points).forEach(point -> assertEquals(unitBounds.size(), point.length));
    }

    @Test
    @DisplayName("given non-unit bounds, when sampling, then every value is within bounds")
    void givenNonUnitBounds_whenSampling_thenEveryValueIsWithinBounds() {
      // Arrange
      List<Bounds<Double>> bounds = List.of(Bounds.create(-5.0, 5.0), Bounds.create(10.0, 20.0));

      // Act
      double[][] points = LatinHypercubeSampler.sample(30, bounds, new Random(2));

      // Assert
      for (double[] point : points) {
        assertTrue(point[0] >= -5.0 && point[0] <= 5.0);
        assertTrue(point[1] >= 10.0 && point[1] <= 20.0);
      }
    }

    @Test
    @DisplayName("given a sample, when checking one dimension, then it is a valid stratification")
    void givenASample_whenCheckingOneDimension_thenItIsAValidStratification() {
      // Arrange
      int sampleSize = 50;

      // Act
      double[][] points = LatinHypercubeSampler.sample(sampleSize, unitBounds, new Random(3));
      double[] column = Arrays.stream(points).mapToDouble(point -> point[0]).sorted().toArray();

      // Assert: exactly one point falls in each of the sampleSize equal-width strata.
      for (int stratumIndex = 0; stratumIndex < sampleSize; stratumIndex++) {
        double lower = (double) stratumIndex / sampleSize;
        double upper = (double) (stratumIndex + 1) / sampleSize;
        assertTrue(
            column[stratumIndex] >= lower && column[stratumIndex] <= upper,
            "value " + column[stratumIndex] + " not in stratum [" + lower + ", " + upper + "]");
      }
    }

    @Test
    @DisplayName("given the same seed twice, when sampling, then the results are identical")
    void givenTheSameSeedTwice_whenSampling_thenTheResultsAreIdentical() {
      // Arrange & Act
      double[][] first = LatinHypercubeSampler.sample(20, unitBounds, new Random(42));
      double[][] second = LatinHypercubeSampler.sample(20, unitBounds, new Random(42));

      // Assert
      assertArrayEquals(first, second);
    }
  }

  @Nested
  @DisplayName("When sampling with an invalid sample size")
  class SamplingWithInvalidSampleSize {

    @Test
    @DisplayName("given a zero sample size, when sampling, then throw IllegalArgumentException")
    void givenAZeroSampleSize_whenSampling_thenIllegalArgumentExceptionIsThrown() {
      // Arrange
      Executable executable = () -> LatinHypercubeSampler.sample(0, unitBounds, new Random(1));

      // Act & Assert
      assertThrows(IllegalArgumentException.class, executable);
    }

    @Test
    @DisplayName("given a negative sample size, when sampling, then throw IllegalArgumentException")
    void givenANegativeSampleSize_whenSampling_thenIllegalArgumentExceptionIsThrown() {
      // Arrange
      Executable executable = () -> LatinHypercubeSampler.sample(-3, unitBounds, new Random(1));

      // Act & Assert
      assertThrows(IllegalArgumentException.class, executable);
    }
  }
}
