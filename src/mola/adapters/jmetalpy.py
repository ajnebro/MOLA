"""jMetalPy adapter: sample and evaluate a FloatProblem in-process, emit a Sample.

Owns evaluation, per the interchange contract (CLAUDE.md, "Design principle"): imports and
evaluates a jMetalPy problem directly, then hands the core the same structured `Sample` a
file-based adapter would produce -- the core never sees the problem object. Latin Hypercube
sampling with `n = 200 * D` and `scramble=True` (CLAUDE.md, Design decisions: "Sampling
strategy") -- matching the paper's own `lhs::randomLHS` convention rather than scipy's
`scramble=False` default, which centers points in their strata instead of placing them uniformly.
"""

import numpy as np
from jmetal.core.problem import FloatProblem
from scipy.stats import qmc

from mola.sample import Sample

DEFAULT_SAMPLE_SIZE_PER_VARIABLE = 200
"""The paper's own sampling rate: `n = 200 * D` (Design decisions, "Sampling strategy")."""


def sample_problem(
    problem: FloatProblem, *, sample_size: int | None = None, seed: int | None = None
) -> Sample:
    """Latin-Hypercube-sample, evaluate, and package a jMetalPy FloatProblem into a Sample.

    Args:
        problem: The jMetalPy problem to sample. Objectives whose `obj_directions[i]` is
            `Problem.MAXIMIZE` are negated so the returned objectives are in minimization form
            (CLAUDE.md, Design decisions: "Optimization sense"). A problem that does not set
            `obj_directions` (only concrete subclasses are expected to) is assumed all-minimize.
        sample_size: Number of solutions to sample. Defaults to `DEFAULT_SAMPLE_SIZE_PER_VARIABLE
            * problem.number_of_variables()`.
        seed: Seed for the Latin Hypercube sampler, recorded on the returned `Sample`.

    Returns:
        A `Sample` holding the evaluated decision and (minimization-form) objective vectors.
    """
    number_of_variables = problem.number_of_variables()
    number_of_objectives = problem.number_of_objectives()
    size = (
        sample_size
        if sample_size is not None
        else DEFAULT_SAMPLE_SIZE_PER_VARIABLE * number_of_variables
    )

    lower_bound = np.asarray(problem.lower_bound, dtype=float)
    upper_bound = np.asarray(problem.upper_bound, dtype=float)

    unit_sample = qmc.LatinHypercube(d=number_of_variables, scramble=True, seed=seed).random(n=size)
    variables = qmc.scale(unit_sample, lower_bound, upper_bound)

    directions = getattr(problem, "obj_directions", [FloatProblem.MINIMIZE] * number_of_objectives)
    sign = np.array([-1.0 if d == FloatProblem.MAXIMIZE else 1.0 for d in directions])

    objectives = np.empty((size, number_of_objectives))
    for i, decision_vector in enumerate(variables):
        solution = problem.create_solution()
        solution.variables = list(decision_vector)
        problem.evaluate(solution)
        objectives[i] = np.asarray(solution.objectives) * sign

    return Sample(
        problem=problem.name(),
        variables=variables,
        objectives=objectives,
        lower_bounds=lower_bound,
        upper_bounds=upper_bound,
        sampler="lhs",
        seed=seed,
    )
