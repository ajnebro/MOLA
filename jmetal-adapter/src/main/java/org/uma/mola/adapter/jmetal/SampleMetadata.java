package org.uma.mola.adapter.jmetal;

import java.util.List;

/**
 * Provenance and dimensions of one interchange sample -- mirrors the sidecar JSON keys MOLA's
 * Python core reads via {@code mola.sample.read_sample} exactly (see the repository root
 * CLAUDE.md, "Interchange schema"): {@code problem, number_of_variables, number_of_objectives,
 * lower_bounds, upper_bounds, sample_size, sampler, seed}.
 */
public record SampleMetadata(
    String problemName,
    int numberOfVariables,
    int numberOfObjectives,
    List<Double> lowerBounds,
    List<Double> upperBounds,
    int sampleSize,
    String sampler,
    Long seed) {

  /** Validates consistency and defensively copies the bound lists. */
  public SampleMetadata {
    if (problemName == null || problemName.isBlank()) {
      throw new IllegalArgumentException("problemName cannot be blank");
    }
    if (lowerBounds.size() != numberOfVariables || upperBounds.size() != numberOfVariables) {
      throw new IllegalArgumentException(
          "lowerBounds/upperBounds must have size numberOfVariables=" + numberOfVariables);
    }
    lowerBounds = List.copyOf(lowerBounds);
    upperBounds = List.copyOf(upperBounds);
  }
}
