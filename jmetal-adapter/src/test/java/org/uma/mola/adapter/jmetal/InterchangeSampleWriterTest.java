package org.uma.mola.adapter.jmetal;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.uma.jmetal.problem.doubleproblem.DoubleProblem;
import org.uma.jmetal.problem.multiobjective.zdt.ZDT1;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;

@DisplayName("Unit tests for class InterchangeSampleWriter")
class InterchangeSampleWriterTest {

  @TempDir private Path tempDir;

  private SampleMetadata metadata;
  private List<DoubleSolution> solutions;

  @BeforeEach
  void setUp() {
    DoubleProblem problem = new ZDT1(3);
    solutions = ProblemSampler.sample(problem, 5, 11L);
    metadata =
        new SampleMetadata(
            "ZDT1",
            3,
            2,
            List.of(0.0, 0.0, 0.0),
            List.of(1.0, 1.0, 1.0),
            5,
            "lhs",
            11L);
  }

  @Nested
  @DisplayName("When writing a sample")
  class WritingASample {

    @Test
    @DisplayName("given a sample, when written, then the CSV has the expected header")
    void givenASample_whenWritten_thenTheCsvHasTheExpectedHeader() throws IOException {
      // Arrange
      Path csvPath = tempDir.resolve("sample.csv");

      // Act
      InterchangeSampleWriter.write(csvPath, metadata, solutions);

      // Assert
      List<String> lines = Files.readAllLines(csvPath);
      assertEquals("problem,sample_id,x_1,x_2,x_3,f_1,f_2", lines.get(0));
    }

    @Test
    @DisplayName("given a sample, when written, then the CSV has one row per solution")
    void givenASample_whenWritten_thenTheCsvHasOneRowPerSolution() throws IOException {
      // Arrange
      Path csvPath = tempDir.resolve("sample.csv");

      // Act
      InterchangeSampleWriter.write(csvPath, metadata, solutions);

      // Assert
      List<String> lines = Files.readAllLines(csvPath);
      assertEquals(solutions.size() + 1, lines.size());
      assertTrue(lines.get(1).startsWith("ZDT1,0,"));
    }

    @Test
    @DisplayName("given a sample, when written, then the sidecar JSON has the expected keys")
    void givenASample_whenWritten_thenTheSidecarJsonHasTheExpectedKeys() throws IOException {
      // Arrange
      Path csvPath = tempDir.resolve("sample.csv");

      // Act
      InterchangeSampleWriter.write(csvPath, metadata, solutions);

      // Assert
      String json = Files.readString(InterchangeSampleWriter.metadataPathFor(csvPath));
      assertTrue(json.contains("\"schema_version\": 1"));
      assertTrue(json.contains("\"problem\": \"ZDT1\""));
      assertTrue(json.contains("\"number_of_variables\": 3"));
      assertTrue(json.contains("\"number_of_objectives\": 2"));
      assertTrue(json.contains("\"sample_size\": 5"));
      assertTrue(json.contains("\"sampler\": \"lhs\""));
      assertTrue(json.contains("\"seed\": 11"));
    }

    @Test
    @DisplayName("given a null seed, when written, then the sidecar JSON has a JSON null")
    void givenANullSeed_whenWritten_thenTheSidecarJsonHasAJsonNull() throws IOException {
      // Arrange
      Path csvPath = tempDir.resolve("sample.csv");
      SampleMetadata metadataWithoutSeed =
          new SampleMetadata(
              "ZDT1", 3, 2, List.of(0.0, 0.0, 0.0), List.of(1.0, 1.0, 1.0), 5, "lhs", null);

      // Act
      InterchangeSampleWriter.write(csvPath, metadataWithoutSeed, solutions);

      // Assert
      String json = Files.readString(InterchangeSampleWriter.metadataPathFor(csvPath));
      assertTrue(json.contains("\"seed\": null"));
    }
  }

  @Nested
  @DisplayName("When computing the sidecar metadata path")
  class ComputingTheMetadataPath {

    @Test
    @DisplayName("given a CSV path, when computed, then it swaps the suffix for .json")
    void givenACsvPath_whenComputed_thenItSwapsTheSuffixForJson() {
      // Arrange
      Path csvPath = tempDir.resolve("sample.csv");

      // Act
      Path metadataPath = InterchangeSampleWriter.metadataPathFor(csvPath);

      // Assert
      assertEquals(tempDir.resolve("sample.json"), metadataPath);
    }
  }
}
