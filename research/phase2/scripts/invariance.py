"""Phase 2, task 2: is VAMOS invariant to per-variable changes of units? (E19, premise of RQ1)

Each problem is wrapped so that variable i is expressed in units scaled by a_i = 2^k_i
(k_i drawn from -4..4, b = 0): bounds become a_i * [xl_i, xu_i] and the objectives are evaluated at
x / a. Multiplying by a power of two is exact in floating point, so a bound-relative algorithm
must produce **bit-identical** objective vectors on the original and on the scaled problem with
the same seed, and decision vectors that differ exactly by the factor a.

Tested: NSGA-II, MOEA/D and SMS-EMOA with VAMOS defaults, and every categorical choice of the
NSGA-II tuning space (crossover, mutation, repair, initializer, selection, offspring ratio), one
at a time from a fixed baseline, on ZDT1 (D = 30) and UF1 (D = 30), seeds 1 and 2, 5 000
evaluations.

Run:  python research/phase2/scripts/invariance.py   ->  data/invariance.csv
"""

import numpy as np
import pandas as pd

import common  # noqa: F401
from common import DATA, bounds, evaluate, instantiate
from runs import nsgaii_space

BUDGET = 5_000
SEEDS = (1, 2)
PROBLEMS = ("zdt1", "cec2009_uf1")
BASELINE = {"pop_size": 100, "offspring_ratio": 1.0, "selection": "tournament", "selection_size": 2,
            "initializer": "random", "crossover": "sbx", "crossover_prob": 0.9, "crossover_eta": 20.0,
            "mutation": "polynomial", "mutation_prob_factor": 1.0, "mutation_eta": 20.0,
            "repair": "clip"}


def _scaled_problem(name: str, factors: np.ndarray):
    from vamos import Problem

    base = instantiate(name)
    lower, upper = bounds(base)

    class Scaled(Problem):
        def __init__(self):
            self.n_var, self.n_obj = base.n_var, base.n_obj
            self.xl, self.xu = lower * factors, upper * factors
            self.encoding = "real"

        def objectives(self, X):
            return evaluate(base, np.asarray(X) / factors)

    return base, Scaled()


def _variants(space, rng):
    """(label, assignment) pairs: the baseline with one categorical parameter changed."""
    yield "nsgaii_baseline", dict(BASELINE)
    for parameter in ("crossover", "mutation", "repair", "initializer", "selection", "offspring_ratio"):
        for choice in space.params[parameter].choices:
            if choice == BASELINE[parameter]:
                continue
            config = dict(BASELINE)
            config[parameter] = choice
            for name, param in space.params.items():
                if name not in config and space.is_active(name, config):
                    config[name] = param.sample(rng)
            config = {k: v for k, v in config.items() if k not in space.params or space.is_active(k, config)}
            yield f"{parameter}={choice}", config


def _run(problem, assignment, algorithm, seed):
    from vamos import optimize
    from vamos.engine.tuning import config_from_assignment

    if assignment is None:
        result = optimize(problem, algorithm=algorithm, max_evaluations=BUDGET, pop_size=100,
                          seed=seed, engine="numpy")
    else:
        result = optimize(problem, algorithm="nsgaii",
                          algorithm_config=config_from_assignment("nsgaii", assignment),
                          max_evaluations=BUDGET, seed=seed, engine="numpy")
    population = result.data["population"]
    return np.asarray(population["F"], float), np.asarray(population["X"], float)


def main() -> None:
    rng = np.random.default_rng(19)
    space = nsgaii_space()
    variants = [(label, a, "nsgaii") for label, a in _variants(space, rng)]
    variants += [("moead_default", None, "moead"), ("smsemoa_default", None, "smsemoa")]
    rows = []
    for problem_name in PROBLEMS:
        n_var = instantiate(problem_name).n_var
        factors = 2.0 ** np.random.default_rng(7).integers(-4, 5, n_var)
        base, scaled = _scaled_problem(problem_name, factors)
        for label, assignment, algorithm in variants:
            for seed in SEEDS:
                row = {"problem": problem_name, "variant": label, "seed": seed}
                try:
                    f0, x0 = _run(base, assignment, algorithm, seed)
                    f1, x1 = _run(scaled, assignment, algorithm, seed)
                    row.update(identical_F=bool(f0.shape == f1.shape and np.array_equal(f0, f1)),
                               identical_X_over_a=bool(x0.shape == x1.shape and np.array_equal(x0, x1 / factors)),
                               max_abs_F_difference=float(np.max(np.abs(f0 - f1))) if f0.shape == f1.shape else np.inf)
                except Exception as error:  # noqa: BLE001 - recorded, not hidden
                    row.update(identical_F=None, identical_X_over_a=None, error=f"{type(error).__name__}: {error}"[:200])
                rows.append(row)
                print(row, flush=True)
    frame = pd.DataFrame(rows)
    DATA.mkdir(parents=True, exist_ok=True)
    frame.to_csv(DATA / "invariance.csv", index=False)
    summary = frame.groupby("variant").identical_F.agg(lambda s: "all" if s.all() else ("none" if not s.any() else "some"))
    print(summary.to_string())


if __name__ == "__main__":
    main()
