"""One optimization run in VAMOS 1.0.0 (numpy engine), with anytime snapshots of the front.

A configuration is either None (NSGA-II's textbook default: population 100, SBX 1.0/20,
polynomial mutation 1/n/20, binary tournament) or an assignment from VAMOS's NSGA-II tuning space
(`build_nsgaii_config_space`, without the external-archive parameters, as the VAMOS CLI does).
"""

import time

import numpy as np

import common  # noqa: F401  (pins the thread pools before numpy-heavy imports)
from common import instantiate

CHECKPOINTS = (5_000, 10_000, 20_000)
DEFAULT_POP_SIZE = 100
_ARCHIVE_PARAMETERS = {"use_external_archive", "archive_unbounded", "archive_prune_policy"}


def nsgaii_space():
    """VAMOS's NSGA-II tuning space minus the external-archive controls (as `vamos tune` does)."""
    from vamos.engine.tuning import ParamSpace, build_nsgaii_config_space

    space = build_nsgaii_config_space().to_param_space()
    return ParamSpace(
        params={k: v for k, v in space.params.items() if k not in _ARCHIVE_PARAMETERS},
        conditions=[c for c in space.conditions if c.param_name not in _ARCHIVE_PARAMETERS
                    and not any(f"cfg['{a}']" in c.expr for a in _ARCHIVE_PARAMETERS)],
    )


NON_INVARIANT_CHOICES = {
    "crossover": {"pcx", "undx"},
    "mutation": {"gaussian", "cauchy"},
    "repair": {"round"},
    "initializer": {"halton"},
}
"""Operators that broke bit-identical invariance to per-variable power-of-two unit changes in
data/invariance.csv (phase 2, task 2). PCX and UNDX use directions mixing variables, the gaussian
and Cauchy mutations use an absolute scale, `round` rounds to integers, and the Halton initializer
differed on ZDT1."""


def invariant_nsgaii_space():
    """The pilot's configuration space: `nsgaii_space()` without NON_INVARIANT_CHOICES.

    Conditional parameters that can only be active under a removed choice are dropped as well.
    """
    from vamos.engine.tuning import Categorical, ParamSpace

    space = nsgaii_space()
    params = dict(space.params)
    for name, removed in NON_INVARIANT_CHOICES.items():
        params[name] = Categorical(name, [c for c in params[name].choices if c not in removed])
    removed_conditions = [f"cfg['{name}'] == '{choice}'"
                          for name, choices in NON_INVARIANT_CHOICES.items() for choice in choices]
    orphaned = {c.param_name for c in space.conditions if c.expr in removed_conditions}
    return ParamSpace(
        params={k: v for k, v in params.items() if k not in orphaned},
        conditions=[c for c in space.conditions if c.param_name not in orphaned],
    )


def _pareto(points: np.ndarray) -> np.ndarray:
    from vamos.foundation.quality_indicators.pareto import pareto_filter

    return np.asarray(pareto_filter(np.asarray(points, dtype=float)), dtype=float)


class _Snapshots:
    """live_viz recorder: the population's non-dominated front at each evaluation checkpoint."""

    def __init__(self, checkpoints):
        self.pending = sorted(checkpoints)
        self.fronts: dict[int, np.ndarray] = {}

    def on_start(self, ctx=None):
        pass

    def on_generation(self, generation, F=None, X=None, stats=None):
        evaluations = (stats or {}).get("evals")
        if evaluations is None or F is None:
            return
        while self.pending and evaluations >= self.pending[0]:
            self.fronts[self.pending.pop(0)] = _pareto(F)

    def on_end(self, final_F=None, final_stats=None):
        pass


def run(problem_name: str, assignment: dict | None, budget: int, seed: int,
        checkpoints=CHECKPOINTS, algorithm: str = "nsgaii") -> dict:
    """Run one configuration and return its fronts per checkpoint, time and evaluations.

    `assignment=None` runs `algorithm` (nsgaii, moead or smsemoa) with VAMOS defaults and
    population 100; otherwise the assignment is an NSGA-II configuration.
    """
    from vamos import optimize
    from vamos.engine.tuning import config_from_assignment

    problem = instantiate(problem_name)
    recorder = _Snapshots([c for c in checkpoints if c < budget])
    start = time.perf_counter()
    if assignment is None:
        result = optimize(problem, algorithm=algorithm, max_evaluations=budget,
                          pop_size=DEFAULT_POP_SIZE, seed=seed, engine="numpy", live_viz=recorder)
    else:
        config = config_from_assignment("nsgaii", dict(assignment))
        result = optimize(problem, algorithm="nsgaii", algorithm_config=config,
                          max_evaluations=budget, seed=seed, engine="numpy", live_viz=recorder)
    seconds = time.perf_counter() - start
    fronts = dict(recorder.fronts)
    fronts[budget] = _pareto(result.data["population"]["F"])
    return {"fronts": fronts, "seconds": seconds,
            "evaluations": int(result.data.get("evaluations", budget))}
