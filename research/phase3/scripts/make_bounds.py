"""Phase 3 tuning bounds: the ideal and nadir of each development problem's true Pareto front.

The tuning objective (normalized HV, reference point 1.1) must not be stretched by "dominance
resistant" extreme points, which the union of evaluated fronts contains (in UF5, (0.002, 2.52) is
non-dominated only through a marginally smaller f1). Bounds therefore come from the true front:
- analytic for the bi-objective DTLZ (f1 + f2 = 0.5 for DTLZ1, a unit quarter circle for DTLZ2,
  3, 4 and 6) and LZ09 (f1 in [0, 1], f2 = 1 - sqrt(f1) or 1 - f1^2), whose VAMOS files are
  three-objective or missing;
- VAMOS's own reference front otherwise (ZDT, UF, ZCAT, RE21, RE24, RWA1), accepted only if it
  agrees with the union of every front evaluated in phases 2 and 2b (no evaluated point may
  dominate the reference front's ideal by more than 1 % of its range).
The union of evaluated fronts is still saved, as data/evaluated_fronts.npz.

Run locally:  python research/phase3/scripts/make_bounds.py   ->  data/tuning_bounds.json
"""

import json
import os
import sys
from pathlib import Path

import moocore
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))

from common import DATA as PHASE2_DATA  # noqa: E402
from common import pilot_problems  # noqa: E402

PHASE3 = HERE.parent
ARMS = Path(os.environ.get("MOLA_PHASE2B_ARMS", r"C:\tmp\mola-phase2b"))
ANALYTIC = {"dtlz1": ([0.0, 0.0], [0.5, 0.5]),
            **{p: ([0.0, 0.0], [1.0, 1.0]) for p in ("dtlz2", "dtlz3", "dtlz4", "dtlz6")},
            **{f"lz09_f{i}": ([0.0, 0.0], [1.0, 1.0]) for i in (1, 2, 3, 4, 5, 7, 8, 9)},
            # VAMOS's UF6 file starts at f1 = 0.25 and misses the isolated point (0, 1) of the
            # true front {0} U [1/4, 1/2] U [3/4, 1] (f2 = 1 - f1).
            "cec2009_uf6": ([0.0, 0.0], [1.0, 1.0])}


def evaluated_front(problem: str, phase2_fronts) -> np.ndarray:
    parts = [phase2_fronts[problem]]
    for arm in ("A", "B", "C"):
        for path in (ARMS / arm / "fronts").glob(f"*__{problem}.npz"):
            with np.load(path) as data:
                parts += [data[key] for key in data.files if key.endswith("_e20000")]
    union = np.vstack(parts)
    return union[moocore.is_nondominated(union, keep_weakly=False)]


def true_front_bounds(problem: str) -> tuple[list[float], list[float], str]:
    if problem in ANALYTIC:
        ideal, nadir = ANALYTIC[problem]
        return ideal, nadir, "analytic"
    from vamos.foundation.problem.resolver import resolve_reference_front_path

    front = np.loadtxt(resolve_reference_front_path(problem, None, n_obj=2), delimiter=",")
    front = front[moocore.is_nondominated(front, keep_weakly=False)]
    return front.min(axis=0).tolist(), front.max(axis=0).tolist(), "vamos reference front"


def main() -> None:
    phase2 = np.load(PHASE2_DATA / "reference_fronts.npz")
    bounds, evaluated = {}, {}
    for problem in pilot_problems():
        union = evaluated_front(problem, phase2)
        evaluated[problem] = union
        ideal, nadir, source = true_front_bounds(problem)
        span = np.asarray(nadir) - np.asarray(ideal)
        overshoot = float(np.max((np.asarray(ideal) - union.min(axis=0)) / span))
        if overshoot > 0.01:
            raise ValueError(f"{problem}: evaluated points beat the {source} ideal by {overshoot:.1%}")
        bounds[problem] = {"ideal": ideal, "nadir": nadir, "source": source,
                           "evaluated_ideal": union.min(axis=0).tolist(),
                           "evaluated_nadir": union.max(axis=0).tolist()}
        print(f"{problem:12s} {source:22s} ideal {np.round(ideal, 4)} nadir {np.round(nadir, 4)}"
              f" | evaluated nadir {np.round(union.max(axis=0), 3)}")
    (PHASE3 / "data").mkdir(parents=True, exist_ok=True)
    np.savez_compressed(PHASE3 / "data" / "evaluated_fronts.npz", **evaluated)
    (PHASE3 / "data" / "tuning_bounds.json").write_text(json.dumps(bounds, indent=2) + "\n")


if __name__ == "__main__":
    main()
