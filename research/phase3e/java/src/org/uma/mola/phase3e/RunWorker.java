package org.uma.mola.phase3e;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import org.uma.evolver.algorithm.nsgaii.DoubleNSGAII;
import org.uma.evolver.cli.ProblemRegistry;
import org.uma.evolver.cli.ProblemSpec;
import org.uma.evolver.parameter.factory.DoubleParameterFactory;
import org.uma.evolver.parameter.yaml.YAMLParameterSpace;
import org.uma.jmetal.component.algorithm.EvolutionaryAlgorithm;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.problem.doubleproblem.DoubleProblem;
import org.uma.jmetal.problem.doubleproblem.impl.AbstractDoubleProblem;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.bounds.Bounds;
import org.uma.jmetal.util.pseudorandom.JMetalRandom;

/**
 * A long-lived, single-threaded jMetal/Evolver worker for MOLA's phase 3 replication.
 *
 * <p>It reads one request per line from standard input and writes one reply per line. Requests
 * are served strictly one after another, so jMetal's process-global {@link JMetalRandom} is never
 * shared between two runs, and a run seeded with {@code s} is reproducible. A dispatcher runs
 * several of these processes in parallel.
 *
 * <p>Requests (tab-separated; a problem spec is {@code NAME} or {@code NAME(a,b,...)}, optionally
 * followed by {@code |xscale=a1,a2,...} and/or {@code |fscale=b1,b2,...}):
 *
 * <ul>
 *   <li>{@code INFO <spec>} replies {@code OK <n> <m> <lower csv> <upper csv>};
 *   <li>{@code EVAL <spec> <rows> <x csv>} replies {@code OK <f csv>} (row-major);
 *   <li>{@code RUN <spec> <seed> <maxEvaluations> <configuration>} runs NSGA-II from Evolver's
 *       {@code NSGAIIDouble.yaml} space with population 100 and replies {@code OK <rows> <f csv>}
 *       with the objective vectors of the algorithm's result, unfiltered.
 * </ul>
 *
 * <p>Errors reply {@code ERR <message>}. Scaled specs wrap the problem so that variable i is
 * expressed in units multiplied by a_i (bounds and points scaled, the original evaluated at x/a)
 * and objective j is multiplied by b_j.
 */
public final class RunWorker {

  private static final String SPACE = "NSGAIIDouble.yaml";
  private static final int POPULATION_SIZE = 100;

  private RunWorker() {}

  public static void main(String[] args) throws Exception {
    Locale.setDefault(Locale.ROOT);
    var in = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
    var out = new PrintStream(System.out, false, StandardCharsets.UTF_8);
    String line;
    while ((line = in.readLine()) != null) {
      if (line.isBlank()) {
        continue;
      }
      String reply;
      try {
        reply = "OK\t" + handle(line.split("\t", -1));
      } catch (Exception | Error e) {
        reply = "ERR\t" + (e.getClass().getSimpleName() + ": " + e.getMessage()).replace('\n', ' ');
      }
      out.println(reply);
      out.flush();
    }
  }

  private static String handle(String[] parts) {
    return switch (parts[0]) {
      case "INFO" -> info(problem(parts[1]));
      case "EVAL" -> evaluate(problem(parts[1]), Integer.parseInt(parts[2]), parts[3]);
      case "RUN" ->
          run(problem(parts[1]), Long.parseLong(parts[2]), Integer.parseInt(parts[3]), parts[4]);
      default -> throw new IllegalArgumentException("unknown request " + parts[0]);
    };
  }

  private static String info(DoubleProblem problem) {
    var lower = new StringBuilder();
    var upper = new StringBuilder();
    for (Bounds<Double> b : problem.variableBounds()) {
      lower.append(lower.isEmpty() ? "" : ",").append(b.getLowerBound());
      upper.append(upper.isEmpty() ? "" : ",").append(b.getUpperBound());
    }
    return problem.numberOfVariables() + "\t" + problem.numberOfObjectives() + "\t" + lower + "\t"
        + upper;
  }

  private static String evaluate(DoubleProblem problem, int rows, String csv) {
    String[] values = csv.split(",");
    int n = problem.numberOfVariables();
    if (values.length != rows * n) {
      throw new IllegalArgumentException("expected " + rows * n + " values, got " + values.length);
    }
    var objectives = new StringBuilder();
    for (int r = 0; r < rows; r++) {
      DoubleSolution solution = problem.createSolution();
      for (int i = 0; i < n; i++) {
        solution.variables().set(i, Double.parseDouble(values[r * n + i]));
      }
      problem.evaluate(solution);
      appendObjectives(objectives, solution);
    }
    return objectives.toString();
  }

  @SuppressWarnings("unchecked")
  private static String run(DoubleProblem problem, long seed, int maxEvaluations, String config) {
    var space = new YAMLParameterSpace(SPACE, new DoubleParameterFactory());
    var nsgaii = new DoubleNSGAII((Problem<DoubleSolution>) (Problem<?>) problem, POPULATION_SIZE,
        maxEvaluations, space);
    nsgaii.parse(config.trim().split("\\s+"));
    JMetalRandom.getInstance().setSeed(seed);
    EvolutionaryAlgorithm<DoubleSolution> algorithm = nsgaii.build();
    algorithm.run();
    List<DoubleSolution> result = algorithm.result();
    var objectives = new StringBuilder();
    for (DoubleSolution solution : result) {
      appendObjectives(objectives, solution);
    }
    return result.size() + "\t" + objectives;
  }

  private static void appendObjectives(StringBuilder builder, DoubleSolution solution) {
    for (double f : solution.objectives()) {
      builder.append(builder.isEmpty() ? "" : ",").append(f);
    }
  }

  // ---------------------------------------------------------------------------------- problems

  static DoubleProblem problem(String spec) {
    String[] pieces = spec.split("\\|");
    DoubleProblem base = (DoubleProblem) ProblemRegistry.resolve(problemSpec(pieces[0]));
    double[] xscale = null;
    double[] fscale = null;
    for (int i = 1; i < pieces.length; i++) {
      if (pieces[i].startsWith("xscale=")) {
        xscale = doubles(pieces[i].substring(7));
      } else if (pieces[i].startsWith("fscale=")) {
        fscale = doubles(pieces[i].substring(7));
      } else {
        throw new IllegalArgumentException("unknown spec option " + pieces[i]);
      }
    }
    return xscale == null && fscale == null ? base : new Scaled(base, xscale, fscale);
  }

  private static ProblemSpec problemSpec(String text) {
    int open = text.indexOf('(');
    if (open < 0) {
      return new ProblemSpec(text);
    }
    List<Object> args = new ArrayList<>();
    for (String token : text.substring(open + 1, text.length() - 1).split(",")) {
      String t = token.trim();
      if (t.equals("true") || t.equals("false")) {
        args.add(Boolean.parseBoolean(t));
      } else if (t.contains(".") || t.contains("e") || t.contains("E")) {
        args.add(Double.parseDouble(t));
      } else {
        args.add(Integer.parseInt(t));
      }
    }
    return new ProblemSpec(text.substring(0, open), args);
  }

  private static double[] doubles(String csv) {
    String[] tokens = csv.split(",");
    double[] values = new double[tokens.length];
    for (int i = 0; i < tokens.length; i++) {
      values[i] = Double.parseDouble(tokens[i]);
    }
    return values;
  }

  /** A problem in other units: variables scaled by a (bounds too), objectives scaled by b. */
  static final class Scaled extends AbstractDoubleProblem {
    private final DoubleProblem base;
    private final double[] xscale;
    private final double[] fscale;

    Scaled(DoubleProblem base, double[] xscale, double[] fscale) {
      this.base = base;
      this.xscale = xscale;
      this.fscale = fscale;
      numberOfObjectives(base.numberOfObjectives());
      numberOfConstraints(base.numberOfConstraints());
      name(base.name() + "-scaled");
      List<Double> lower = new ArrayList<>();
      List<Double> upper = new ArrayList<>();
      List<Bounds<Double>> bounds = base.variableBounds();
      for (int i = 0; i < bounds.size(); i++) {
        double a = xscale == null ? 1.0 : xscale[i];
        lower.add(bounds.get(i).getLowerBound() * a);
        upper.add(bounds.get(i).getUpperBound() * a);
      }
      variableBounds(lower, upper);
    }

    @Override
    public DoubleSolution evaluate(DoubleSolution solution) {
      // A copy, not base.createSolution(): creating a solution draws from jMetal's global random
      // generator and would shift the run's random stream.
      DoubleSolution inner = (DoubleSolution) solution.copy();
      for (int i = 0; i < solution.variables().size(); i++) {
        double a = xscale == null ? 1.0 : xscale[i];
        inner.variables().set(i, solution.variables().get(i) / a);
      }
      base.evaluate(inner);
      for (int j = 0; j < solution.objectives().length; j++) {
        double b = fscale == null ? 1.0 : fscale[j];
        solution.objectives()[j] = inner.objectives()[j] * b;
      }
      for (int c = 0; c < solution.constraints().length; c++) {
        solution.constraints()[c] = inner.constraints()[c];
      }
      return solution;
    }
  }
}
