package org.uma.mola.adapter.jmetal;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;
import java.util.stream.IntStream;
import org.uma.jmetal.util.bounds.Bounds;

/**
 * Latin Hypercube sampling with a random offset within each stratum (i.e. "scrambled" -- the same
 * design MOLA's Python core uses via {@code scipy.stats.qmc.LatinHypercube(scramble=True)}; see
 * the repository root CLAUDE.md, Design decisions: "Sampling strategy"). Bit-for-bit matching
 * across the two implementations is not the goal, only a statistically equivalent design.
 */
public final class LatinHypercubeSampler {

  private LatinHypercubeSampler() {}

  /**
   * Draws a Latin Hypercube sample scaled to the given per-variable bounds.
   *
   * @param sampleSize number of points to draw; must be positive
   * @param bounds per-variable (lower, upper) bounds; its size fixes the sample's dimensionality
   * @param random source of randomness for both the per-dimension stratum permutation and the
   *     within-stratum offset
   * @return an array of shape {@code [sampleSize][bounds.size()]}
   * @throws IllegalArgumentException if sampleSize is not positive
   */
  public static double[][] sample(int sampleSize, List<Bounds<Double>> bounds, Random random) {
    if (sampleSize <= 0) {
      throw new IllegalArgumentException("sampleSize must be positive, got " + sampleSize);
    }

    int numberOfVariables = bounds.size();
    double[][] points = new double[sampleSize][numberOfVariables];
    for (int variableIndex = 0; variableIndex < numberOfVariables; variableIndex++) {
      fillColumn(points, variableIndex, bounds.get(variableIndex), random);
    }
    return points;
  }

  private static void fillColumn(
      double[][] points, int variableIndex, Bounds<Double> bounds, Random random) {
    int sampleSize = points.length;
    List<Integer> strata = shuffledStrata(sampleSize, random);
    double lowerBound = bounds.getLowerBound();
    double upperBound = bounds.getUpperBound();

    for (int sampleIndex = 0; sampleIndex < sampleSize; sampleIndex++) {
      double unitValue = (strata.get(sampleIndex) + random.nextDouble()) / sampleSize;
      points[sampleIndex][variableIndex] = lowerBound + unitValue * (upperBound - lowerBound);
    }
  }

  private static List<Integer> shuffledStrata(int sampleSize, Random random) {
    List<Integer> strata = new ArrayList<>(IntStream.range(0, sampleSize).boxed().toList());
    Collections.shuffle(strata, random);
    return strata;
  }
}
