"""Phase 3 amendment check: is VAMOS invariant to per-objective changes of units?

Each problem is wrapped so that objective m is multiplied by a_m = 2^k_m (k_m drawn from -4..4).
Multiplying by a power of two is exact, so an algorithm that only uses Pareto dominance and
range-normalized crowding must produce bit-identical decision vectors on the original and the
scaled problem with the same seed, and objective vectors that differ exactly by a.

Tested as in phase 2's invariance.py: NSGA-II, MOEA/D and SMS-EMOA with VAMOS defaults, and every
categorical choice of the invariant NSGA-II space one at a time from the textbook baseline, on
ZDT1 and UF1 (D = 30), seeds 1 and 2, 5 000 evaluations.

Run locally:  python research/phase3/scripts/objective_invariance.py  ->  data/objective_invariance.csv

Environment: MOLA_INVARIANCE_DEFAULTS (untuned algorithms, default "moead,smsemoa"; "ibea" since
D9), MOLA_INVARIANCE_NSGAII=0 to skip the NSGA-II variants, MOLA_INVARIANCE_OUT for the CSV.
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))

import common  # noqa: E402, F401
from common import bounds, evaluate, instantiate  # noqa: E402
from invariance import BUDGET, PROBLEMS, SEEDS, _run, _variants  # noqa: E402
from runs import invariant_nsgaii_space  # noqa: E402

PHASE3 = HERE.parent


def _scaled_objectives(name: str, factors: np.ndarray):
    from vamos import Problem

    base = instantiate(name)
    lower, upper = bounds(base)

    class Scaled(Problem):
        def __init__(self):
            self.n_var, self.n_obj = base.n_var, base.n_obj
            self.xl, self.xu = lower, upper
            self.encoding = "real"

        def objectives(self, X):
            return evaluate(base, np.asarray(X)) * factors

    return base, Scaled()


def main() -> None:
    rng = np.random.default_rng(19)
    variants = [(label, a, "nsgaii") for label, a in _variants(invariant_nsgaii_space(), rng)]
    if os.environ.get("MOLA_INVARIANCE_NSGAII", "1") == "0":
        variants = []
    variants += [(f"{a}_default", None, a) for a in os.environ.get("MOLA_INVARIANCE_DEFAULTS", "moead,smsemoa").split(",")]
    rows = []
    for problem_name in PROBLEMS:
        factors = 2.0 ** np.random.default_rng(11).integers(-4, 5, 2)
        base, scaled = _scaled_objectives(problem_name, factors)
        for label, assignment, algorithm in variants:
            for seed in SEEDS:
                f0, x0 = _run(base, assignment, algorithm, seed)
                f1, x1 = _run(scaled, assignment, algorithm, seed)
                same_shape = f0.shape == f1.shape
                rows.append({"problem": problem_name, "variant": label, "seed": seed,
                             "factors": factors.tolist(),
                             "identical_X": bool(same_shape and np.array_equal(x0, x1)),
                             "identical_F_over_a": bool(same_shape and np.array_equal(f0, f1 / factors))})
    frame = pd.DataFrame(rows)
    out = Path(os.environ.get("MOLA_INVARIANCE_OUT", PHASE3 / "data" / "objective_invariance.csv"))
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    summary = frame.groupby("variant").identical_X.agg(lambda s: "all" if s.all() else ("none" if not s.any() else "some"))
    print(summary.to_string())
    print("budget", BUDGET)


if __name__ == "__main__":
    main()
