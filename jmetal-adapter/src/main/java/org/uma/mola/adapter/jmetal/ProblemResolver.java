package org.uma.mola.adapter.jmetal;

import java.lang.reflect.InvocationTargetException;
import org.uma.jmetal.problem.doubleproblem.DoubleProblem;

/**
 * Looks up and instantiates a jMetal {@link DoubleProblem} by its fully-qualified class name,
 * e.g. {@code org.uma.jmetal.problem.multiobjective.zdt.ZDT1}. Java has no equivalent of Python's
 * flat, enumerable module namespace (the mechanism the Python adapter's own resolver uses), so
 * reflection over the fully-qualified name is the natural fit here instead.
 */
public final class ProblemResolver {

  private ProblemResolver() {}

  /**
   * Resolves and instantiates a problem.
   *
   * @param className fully-qualified name of a class implementing {@link DoubleProblem}
   * @param numberOfVariables passed as the sole constructor argument if given (matching problems
   *     such as ZDT1, whose constructor is {@code ZDT1(Integer numberOfVariables)}); problems
   *     that don't accept it (e.g. ZDT4, most RE/RWA problems) must be resolved without it
   * @return the instantiated problem
   * @throws ProblemResolutionException if the class can't be found, isn't a DoubleProblem, or
   *     can't be instantiated with the given arguments
   */
  public static DoubleProblem resolve(String className, Integer numberOfVariables) {
    Class<?> problemClass = loadClass(className);
    if (!DoubleProblem.class.isAssignableFrom(problemClass)) {
      throw new ProblemResolutionException(
          "'"
              + className
              + "' is not a jMetal DoubleProblem. MOLA's Java adapter only characterizes"
              + " continuous problems.");
    }
    return numberOfVariables != null
        ? instantiateWithVariables(problemClass, numberOfVariables)
        : instantiateDefault(problemClass);
  }

  private static Class<?> loadClass(String className) {
    try {
      return Class.forName(className);
    } catch (ClassNotFoundException e) {
      throw new ProblemResolutionException("class not found: '" + className + "'");
    }
  }

  private static DoubleProblem instantiateDefault(Class<?> problemClass) {
    try {
      return (DoubleProblem) problemClass.getDeclaredConstructor().newInstance();
    } catch (ReflectiveOperationException | ClassCastException e) {
      throw new ProblemResolutionException(
          "could not instantiate '"
              + problemClass.getName()
              + "' with no arguments: "
              + rootCauseMessage(e));
    }
  }

  private static DoubleProblem instantiateWithVariables(
      Class<?> problemClass, int numberOfVariables) {
    try {
      return (DoubleProblem)
          problemClass.getDeclaredConstructor(Integer.class).newInstance(numberOfVariables);
    } catch (ReflectiveOperationException | ClassCastException e) {
      throw new ProblemResolutionException(
          "could not instantiate '"
              + problemClass.getName()
              + "' with --variables "
              + numberOfVariables
              + ": "
              + rootCauseMessage(e));
    }
  }

  private static String rootCauseMessage(Throwable e) {
    Throwable cause = e instanceof InvocationTargetException ite ? ite.getTargetException() : e;
    return cause.getMessage() != null ? cause.getMessage() : cause.toString();
  }
}
