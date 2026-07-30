package org.uma.mola.adapter.jmetal;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import org.uma.jmetal.problem.doubleproblem.DoubleProblem;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;

/**
 * Latin-Hypercube-samples and evaluates a jMetal {@link DoubleProblem} in-process -- the Java
 * counterpart of MOLA's Python {@code mola.adapters.jmetalpy.sample_problem}. jMetal (Java) has no
 * per-objective MAXIMIZE/MINIMIZE convention (confirmed absent from {@code Problem} and every
 * built-in problem in {@code jmetal-problem}): every problem's {@code evaluate()} is assumed to
 * already write minimization-form objectives, so unlike the Python adapter, no negation step is
 * needed here.
 */
public final class ProblemSampler {

  private ProblemSampler() {}

  /**
   * Samples and evaluates {@code problem}.
   *
   * @param problem the problem to sample
   * @param sampleSize number of solutions to draw
   * @param seed seed for the Latin Hypercube sampler, or {@code null} for a non-reproducible run
   * @return {@code sampleSize} evaluated solutions
   */
  public static List<DoubleSolution> sample(DoubleProblem problem, int sampleSize, Long seed) {
    Random random = seed != null ? new Random(seed) : new Random();
    double[][] points = LatinHypercubeSampler.sample(sampleSize, problem.variableBounds(), random);

    List<DoubleSolution> solutions = new ArrayList<>(sampleSize);
    for (double[] point : points) {
      solutions.add(evaluateAt(problem, point));
    }
    return solutions;
  }

  private static DoubleSolution evaluateAt(DoubleProblem problem, double[] point) {
    DoubleSolution solution = problem.createSolution();
    for (int variableIndex = 0; variableIndex < point.length; variableIndex++) {
      solution.variables().set(variableIndex, point[variableIndex]);
    }
    return problem.evaluate(solution);
  }
}
