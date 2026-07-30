package org.uma.mola.adapter.jmetal;

import java.io.UncheckedIOException;
import java.nio.file.Path;
import java.util.List;
import org.uma.jmetal.problem.doubleproblem.DoubleProblem;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.bounds.Bounds;

/**
 * Command-line entry point: Latin-Hypercube-samples and evaluates a jMetal {@link DoubleProblem},
 * writing an interchange sample file (CSV + sidecar metadata JSON) MOLA's Python core can
 * characterize. No feature computation happens here -- see the repository root CLAUDE.md, "Java
 * adapter location".
 */
public final class Main {

  private static final int DEFAULT_SAMPLE_SIZE_PER_VARIABLE = 200;

  private static final String USAGE =
      """
      Usage: mola-jmetal-adapter <problemClassName> <output.csv> [options]

        <problemClassName>   Fully-qualified class name of a jMetal DoubleProblem,
                              e.g. org.uma.jmetal.problem.multiobjective.zdt.ZDT1
        <output.csv>         Destination CSV path (a sidecar .json is written alongside it)

      Options:
        --variables N        Number of decision variables, for problems whose constructor
                              accepts it (passed as `new ProblemClass(Integer)`)
        --sample-size N      Number of solutions to Latin-Hypercube-sample (default: 200 * D)
        --seed N             Seed for the Latin Hypercube sampler

      Example:
        mola-jmetal-adapter org.uma.jmetal.problem.multiobjective.zdt.ZDT1 sample.csv \\
            --variables 5 --sample-size 1000 --seed 42
      """;

  private Main() {}

  public static void main(String[] args) {
    System.exit(run(args));
  }

  /**
   * Runs the adapter and returns a process exit code, without calling {@link System#exit}, so
   * tests can invoke it directly.
   */
  static int run(String[] args) {
    if (args.length == 0) {
      System.err.println(USAGE);
      return 1;
    }
    if ("--help".equals(args[0])) {
      System.out.println(USAGE);
      return 0;
    }
    if (args.length < 2) {
      System.err.println("Error: expected <problemClassName> and <output.csv>.\n\n" + USAGE);
      return 1;
    }
    try {
      return sampleAndWrite(args[0], Path.of(args[1]), CommandLineOptions.parse(args, 2));
    } catch (ProblemResolutionException | IllegalArgumentException | UncheckedIOException e) {
      System.err.println("Error: " + e.getMessage());
      return 1;
    }
  }

  private static int sampleAndWrite(
      String problemClassName, Path output, CommandLineOptions options) {
    DoubleProblem problem = ProblemResolver.resolve(problemClassName, options.variables());
    int sampleSize =
        options.sampleSize() != null
            ? options.sampleSize()
            : DEFAULT_SAMPLE_SIZE_PER_VARIABLE * problem.numberOfVariables();

    List<DoubleSolution> solutions = ProblemSampler.sample(problem, sampleSize, options.seed());
    SampleMetadata metadata = metadataFor(problem, sampleSize, options.seed());
    InterchangeSampleWriter.write(output, metadata, solutions);

    System.out.println(
        "Wrote "
            + sampleSize
            + " solutions to "
            + output
            + " and "
            + InterchangeSampleWriter.metadataPathFor(output));
    return 0;
  }

  private static SampleMetadata metadataFor(DoubleProblem problem, int sampleSize, Long seed) {
    List<Bounds<Double>> bounds = problem.variableBounds();
    return new SampleMetadata(
        problem.name(),
        problem.numberOfVariables(),
        problem.numberOfObjectives(),
        bounds.stream().map(Bounds::getLowerBound).toList(),
        bounds.stream().map(Bounds::getUpperBound).toList(),
        sampleSize,
        "lhs",
        seed);
  }
}
