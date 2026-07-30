package org.uma.mola.adapter.jmetal;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Collectors;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;

/**
 * Writes an interchange sample -- a CSV file plus a sidecar metadata JSON -- matching the schema
 * MOLA's Python core reads via {@code mola.sample.read_sample} (repository root CLAUDE.md,
 * "Interchange schema"): CSV columns {@code problem, sample_id, x_1..x_D, f_1..f_M}; JSON keys
 * {@code schema_version, problem, number_of_variables, number_of_objectives, lower_bounds,
 * upper_bounds, sample_size, sampler, seed}.
 */
public final class InterchangeSampleWriter {

  private static final int SCHEMA_VERSION = 1;

  private InterchangeSampleWriter() {}

  /**
   * Writes {@code solutions} and their provenance to {@code csvPath} and its sidecar JSON.
   *
   * @throws UncheckedIOException if either file cannot be written
   */
  public static void write(Path csvPath, SampleMetadata metadata, List<DoubleSolution> solutions) {
    try {
      Files.writeString(csvPath, csvContent(metadata, solutions));
      Files.writeString(metadataPathFor(csvPath), jsonContent(metadata));
    } catch (IOException e) {
      throw new UncheckedIOException("could not write interchange sample to " + csvPath, e);
    }
  }

  /** Returns the sidecar metadata path matching a sample CSV path: the same path, `.json`. */
  public static Path metadataPathFor(Path csvPath) {
    String fileName = csvPath.getFileName().toString();
    int lastDot = fileName.lastIndexOf('.');
    String baseName = lastDot >= 0 ? fileName.substring(0, lastDot) : fileName;
    return csvPath.resolveSibling(baseName + ".json");
  }

  private static String csvContent(SampleMetadata metadata, List<DoubleSolution> solutions) {
    StringBuilder csv = new StringBuilder(csvHeader(metadata)).append('\n');
    for (int index = 0; index < solutions.size(); index++) {
      csv.append(csvRow(metadata.problemName(), index, solutions.get(index))).append('\n');
    }
    return csv.toString();
  }

  private static String csvHeader(SampleMetadata metadata) {
    StringBuilder header = new StringBuilder("problem,sample_id");
    for (int i = 1; i <= metadata.numberOfVariables(); i++) {
      header.append(",x_").append(i);
    }
    for (int i = 1; i <= metadata.numberOfObjectives(); i++) {
      header.append(",f_").append(i);
    }
    return header.toString();
  }

  private static String csvRow(String problemName, int sampleId, DoubleSolution solution) {
    StringBuilder row = new StringBuilder();
    row.append(problemName).append(',').append(sampleId);
    for (Double variable : solution.variables()) {
      row.append(',').append(variable);
    }
    for (double objective : solution.objectives()) {
      row.append(',').append(objective);
    }
    return row.toString();
  }

  private static String jsonContent(SampleMetadata metadata) {
    String seedJson = metadata.seed() == null ? "null" : String.valueOf(metadata.seed());
    return """
        {
          "schema_version": %d,
          "problem": "%s",
          "number_of_variables": %d,
          "number_of_objectives": %d,
          "lower_bounds": %s,
          "upper_bounds": %s,
          "sample_size": %d,
          "sampler": "%s",
          "seed": %s
        }
        """
        .formatted(
            SCHEMA_VERSION,
            metadata.problemName(),
            metadata.numberOfVariables(),
            metadata.numberOfObjectives(),
            jsonArray(metadata.lowerBounds()),
            jsonArray(metadata.upperBounds()),
            metadata.sampleSize(),
            metadata.sampler(),
            seedJson);
  }

  private static String jsonArray(List<Double> values) {
    return values.stream().map(String::valueOf).collect(Collectors.joining(", ", "[", "]"));
  }
}
