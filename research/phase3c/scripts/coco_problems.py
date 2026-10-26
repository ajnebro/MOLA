"""COCO bbob-biobj problems as VAMOS problems, for phase 3c.

A problem name is the COCO id, e.g. "bbob-biobj_f20_i01_d10" (function 20, instance 1, D = 10).
- **Search box:** [-5, 5]^D, the region of interest of the bbob suites, where the optima of both
  single-objective components lie. COCO declares [-100, 100]^D for bbob-biobj; most of that box is
  far from the Pareto set, and a Latin hypercube of 200 * D points over it would describe the far
  region instead of the front (decision recorded in the phase 3c pre-registration).
- **True ideal and nadir:** COCO's own normalization.
  - The ideal is (f1(x1*), f2(x2*)), from the optima x1* and x2* of the two bbob components, which
    cocoex writes with `Problem._best_parameter("print")`.
  - The nadir is COCO's `largest_fvalues_of_interest`.
  - The nadir implied by the optima, (f1(x2*), f2(x1*)), must agree with it; it does for all 165
    problems of phase 3c (checked). A component's instance is an instance id, so its bbob problem is
    built with suite_instance "instances: N"; an index into the default list gave wrong optima.
"""

import os
import re
import tempfile
from functools import cache

import numpy as np

BOX = 5.0
_NAME = re.compile(r"^bbob-biobj_f(\d+)_i(\d+)_d(\d+)$")
_COMPONENT = re.compile(r"^bbob_f(\d+)_i(\d+)_d(\d+)$")


def parse(name: str) -> tuple[int, int, int]:
    match = _NAME.match(name)
    if not match:
        raise ValueError(f"not a bbob-biobj problem id: {name}")
    function, instance, dimension = (int(g) for g in match.groups())
    return function, instance, dimension


def _coco_problem(name: str):
    import cocoex

    function, instance, dimension = parse(name)
    options = f"dimensions:{dimension} function_indices:{function}"
    suite = cocoex.Suite("bbob-biobj", f"instances: {instance}", options)
    problem = suite.get_problem(0)
    if problem.id != name:
        raise ValueError(f"cocoex returned {problem.id} for {name}")
    return suite, problem


def _component_optimum(component_id: str) -> np.ndarray:
    """x* of a single-objective bbob problem such as 'bbob_f020_i02_d10'."""
    import cocoex

    match = _COMPONENT.match(component_id)
    if not match:
        raise ValueError(f"not a bbob problem id: {component_id}")
    function, instance, dimension = (int(g) for g in match.groups())
    # The component's instance is an instance id, not an index into the suite's default list.
    suite = cocoex.Suite(
        "bbob", f"instances: {instance}", f"dimensions:{dimension} function_indices:{function}"
    )
    problem = suite.get_problem(0)
    if problem.id != component_id:
        raise ValueError(f"cocoex returned {problem.id} for {component_id}")
    with tempfile.TemporaryDirectory() as folder:
        previous = os.getcwd()
        os.chdir(folder)
        try:
            problem._best_parameter("print")
            return np.loadtxt("._bbob_problem_best_parameter.txt")
        finally:
            os.chdir(previous)


@cache
def true_bounds(name: str) -> dict:
    """Ideal and nadir points of the true Pareto front (COCO's normalization)."""
    _, problem = _coco_problem(name)
    first, second = problem.name.split("__")
    x1, x2 = _component_optimum(first), _component_optimum(second)
    f_x1, f_x2 = np.asarray(problem(x1)), np.asarray(problem(x2))
    ideal = np.array([f_x1[0], f_x2[1]])
    from_optima = np.array([f_x2[0], f_x1[1]])
    nadir = np.asarray(problem.largest_fvalues_of_interest, dtype=float)
    if np.any(ideal >= nadir):
        raise ValueError(f"{name}: ideal {ideal} not below nadir {nadir}")
    if not np.allclose(from_optima, nadir, rtol=1e-9, atol=1e-6):
        raise ValueError(f"{name}: nadir from the optima {from_optima} differs from COCO's {nadir}")
    return {
        "ideal": ideal.tolist(),
        "nadir": nadir.tolist(),
        "nadir_from_optima": from_optima.tolist(),
        "nadir_relative_difference": float(np.max(np.abs(from_optima - nadir) / (nadir - ideal))),
        "optima_inside_box": bool(np.all(np.abs(x1) <= BOX) and np.all(np.abs(x2) <= BOX)),
        "components": [first, second],
    }


def make_problem(name: str):
    """A VAMOS problem over [-5, 5]^D that evaluates the COCO problem point by point."""
    from vamos import Problem

    suite, coco = _coco_problem(name)
    dimension = coco.dimension

    class CocoBiobj(Problem):
        def __init__(self):
            self.n_var, self.n_obj = dimension, 2
            self.xl, self.xu = np.full(dimension, -BOX), np.full(dimension, BOX)
            self.encoding = "real"
            self._suite, self._coco = suite, coco  # the suite owns the C problem; keep both alive

        def objectives(self, X):
            return np.array([self._coco(x) for x in np.asarray(X, dtype=float)], dtype=float)

    return CocoBiobj()
