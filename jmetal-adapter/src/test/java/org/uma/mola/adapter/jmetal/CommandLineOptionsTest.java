package org.uma.mola.adapter.jmetal;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.function.Executable;

@DisplayName("Unit tests for class CommandLineOptions")
class CommandLineOptionsTest {

  @Nested
  @DisplayName("When parsing valid arguments")
  class ParsingValidArguments {

    @Test
    @DisplayName("given no flags, when parsed, then every option is null")
    void givenNoFlags_whenParsed_thenEveryOptionIsNull() {
      // Arrange
      String[] args = {"ZDT1", "output.csv"};

      // Act
      CommandLineOptions options = CommandLineOptions.parse(args, 2);

      // Assert
      assertNull(options.variables());
      assertNull(options.sampleSize());
      assertNull(options.seed());
    }

    @Test
    @DisplayName("given all three flags, when parsed, then every option is set")
    void givenAllThreeFlags_whenParsed_thenEveryOptionIsSet() {
      // Arrange
      String[] args = {
        "ZDT1", "output.csv", "--variables", "5", "--sample-size", "1000", "--seed", "42"
      };

      // Act
      CommandLineOptions options = CommandLineOptions.parse(args, 2);

      // Assert
      assertEquals(5, options.variables());
      assertEquals(1000, options.sampleSize());
      assertEquals(42L, options.seed());
    }
  }

  @Nested
  @DisplayName("When parsing invalid arguments")
  class ParsingInvalidArguments {

    @Test
    @DisplayName("given an unknown flag, when parsed, then throw IllegalArgumentException")
    void givenAnUnknownFlag_whenParsed_thenIllegalArgumentExceptionIsThrown() {
      // Arrange
      String[] args = {"ZDT1", "output.csv", "--unknown", "1"};
      Executable executable = () -> CommandLineOptions.parse(args, 2);

      // Act & Assert
      assertThrows(IllegalArgumentException.class, executable);
    }

    @Test
    @DisplayName("given a flag with a missing value, when parsed, then throw")
    void givenAFlagWithAMissingValue_whenParsed_thenIllegalArgumentExceptionIsThrown() {
      // Arrange
      String[] args = {"ZDT1", "output.csv", "--seed"};
      Executable executable = () -> CommandLineOptions.parse(args, 2);

      // Act & Assert
      assertThrows(IllegalArgumentException.class, executable);
    }

    @Test
    @DisplayName("given a non-numeric value, when parsed, then throw IllegalArgumentException")
    void givenANonNumericValue_whenParsed_thenIllegalArgumentExceptionIsThrown() {
      // Arrange
      String[] args = {"ZDT1", "output.csv", "--seed", "not-a-number"};
      Executable executable = () -> CommandLineOptions.parse(args, 2);

      // Act & Assert
      assertThrows(IllegalArgumentException.class, executable);
    }
  }
}
