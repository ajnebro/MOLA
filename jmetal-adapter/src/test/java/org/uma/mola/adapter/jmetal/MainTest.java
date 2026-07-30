package org.uma.mola.adapter.jmetal;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

@DisplayName("Unit tests for class Main")
class MainTest {

  @TempDir private Path tempDir;

  private final PrintStream originalOut = System.out;
  private final PrintStream originalErr = System.err;
  private ByteArrayOutputStream capturedErr;

  @BeforeEach
  void setUp() {
    capturedErr = new ByteArrayOutputStream();
    System.setOut(new PrintStream(new ByteArrayOutputStream()));
    System.setErr(new PrintStream(capturedErr));
  }

  @AfterEach
  void tearDown() {
    System.setOut(originalOut);
    System.setErr(originalErr);
  }

  @Nested
  @DisplayName("When run with valid arguments")
  class RunWithValidArguments {

    @Test
    @DisplayName("given a known problem, when run, then it writes an interchange sample")
    void givenAKnownProblem_whenRun_thenItWritesAnInterchangeSample() {
      // Arrange
      Path output = tempDir.resolve("sample.csv");
      String[] args = {
        "org.uma.jmetal.problem.multiobjective.zdt.ZDT1",
        output.toString(),
        "--variables",
        "3",
        "--sample-size",
        "10",
        "--seed",
        "1"
      };

      // Act
      int exitCode = Main.run(args);

      // Assert
      assertEquals(0, exitCode);
      assertTrue(Files.exists(output));
      assertTrue(Files.exists(InterchangeSampleWriter.metadataPathFor(output)));
    }

    @Test
    @DisplayName("given --help, when run, then it prints usage and returns 0")
    void givenHelp_whenRun_thenItPrintsUsageAndReturns0() {
      // Arrange
      String[] args = {"--help"};

      // Act
      int exitCode = Main.run(args);

      // Assert
      assertEquals(0, exitCode);
    }
  }

  @Nested
  @DisplayName("When run with invalid arguments")
  class RunWithInvalidArguments {

    @Test
    @DisplayName("given no arguments, when run, then it returns a non-zero exit code")
    void givenNoArguments_whenRun_thenItReturnsANonZeroExitCode() {
      // Arrange
      String[] args = {};

      // Act
      int exitCode = Main.run(args);

      // Assert
      assertEquals(1, exitCode);
    }

    @Test
    @DisplayName("given only one positional argument, when run, then it returns a non-zero code")
    void givenOnlyOnePositionalArgument_whenRun_thenItReturnsANonZeroExitCode() {
      // Arrange
      String[] args = {"org.uma.jmetal.problem.multiobjective.zdt.ZDT1"};

      // Act
      int exitCode = Main.run(args);

      // Assert
      assertEquals(1, exitCode);
    }

    @Test
    @DisplayName("given an unknown problem, when run, then it reports a clean error, no stack trace")
    void givenAnUnknownProblem_whenRun_thenItReportsACleanErrorNoStackTrace() {
      // Arrange
      Path output = tempDir.resolve("sample.csv");
      String[] args = {"not.a.real.Class", output.toString()};

      // Act
      int exitCode = Main.run(args);

      // Assert
      assertEquals(1, exitCode);
      assertFalse(Files.exists(output));
      assertFalse(capturedErr.toString().contains("at org.uma.mola"));
    }
  }
}
