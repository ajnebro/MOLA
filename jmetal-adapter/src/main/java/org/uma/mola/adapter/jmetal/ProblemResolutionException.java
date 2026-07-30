package org.uma.mola.adapter.jmetal;

/** Thrown when a problem class name cannot be resolved to an instantiated jMetal DoubleProblem. */
public class ProblemResolutionException extends RuntimeException {

  public ProblemResolutionException(String message) {
    super(message);
  }
}
