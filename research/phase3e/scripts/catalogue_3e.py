"""Phase 3e catalogue: the 37 development problems in their jMetal 7.8 implementations.

For every pilot problem (phase 2 names, VAMOS registry), its jMetal spec (SPECS) is checked:
1. dimension and bounds agree with VAMOS's;
2. objective values on 1 000 shared random points, jMetal against VAMOS (an implementation
   difference is reported, not corrected: each replication uses its own framework's problem);
3. exact duplicates among the jMetal implementations (same dimension and bounds, same objective
   values on shared points);
4. true-front bounds for the tuning objective: analytic where phase 3 used them (bi-objective
   DTLZ, LZ09, UF6), otherwise Evolver's reference front (resources/referenceFronts), accepted
   only if no point of 5 runs of Evolver's default NSGA-II (20 000 evaluations, seeds 9001-9005)
   beats its ideal by more than 1 % of its range.

Run locally:  python research/phase3e/scripts/catalogue_3e.py  ->  data/catalogue_3e.json,
data/tuning_bounds.json
"""

import json
import sys
from itertools import combinations
from pathlib import Path

import moocore
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))
sys.path.insert(0, str(HERE.parents[1] / "phase3" / "scripts"))

import common  # noqa: E402
from jworker import DEFAULT, JAR, PHASE3E, JWorker, command_line  # noqa: E402
from make_bounds import ANALYTIC  # noqa: E402

EVOLVER_FRONTS = Path(JAR).parents[1] / "resources" / "referenceFronts"
SPECS = {
    **{f"zdt{i}": f"ZDT{i}" for i in (1, 2, 3, 4)},
    "dtlz1": "DTLZ1(6,2)", **{f"dtlz{i}": f"DTLZ{i}(11,2)" for i in (2, 3, 4, 6)},
    **{f"lz09_f{i}": f"LZ09F{i}" for i in (1, 2, 3, 4, 5, 7, 8, 9)},
    **{f"cec2009_uf{i}": f"UF{i}" for i in range(1, 8)},
    **{f"zcat{i}": f"ZCAT{i}" for i in (1, 3, 5, 6, 8, 10, 11, 12, 13, 19)},
    "re21": "RE21", "re24": "RE24", "rwa1": "RWA1",
}
FRONT_FILES = {**{f"zdt{i}": f"ZDT{i}.csv" for i in (1, 2, 3, 4)},
               **{f"cec2009_uf{i}": f"UF{i}.csv" for i in (1, 2, 3, 4, 5, 7)},
               **{f"zcat{i}": f"ZCAT{i}.2D.csv" for i in (1, 3, 5, 6, 8, 10, 11, 12, 13, 19)},
               "re21": "RE21.csv", "re24": "RE24.csv", "rwa1": "RWA1.csv"}


def _load_front(name: str) -> np.ndarray:
    path = EVOLVER_FRONTS / name
    text = path.read_text().replace(",", " ")
    front = np.loadtxt(text.splitlines())
    return front[moocore.is_nondominated(front, keep_weakly=False)]


def main() -> None:
    problems = common.pilot_problems()
    rng = np.random.default_rng(0)
    report, bounds_out, probes = {}, {}, {}
    with JWorker() as worker:
        for p in problems:
            spec = SPECS[p]
            n, m, lower, upper = worker.info(spec)
            vamos = common.instantiate(p)
            v_lower, v_upper = common.bounds(vamos)
            x = lower + rng.random((1000, n)) * (upper - lower)
            f_jmetal = worker.evaluate(spec, x, m)
            f_vamos = common.evaluate(vamos, x)
            scale = np.maximum(np.abs(f_vamos).max(axis=0), 1e-12)
            mismatch = float(np.max(np.abs(f_jmetal - f_vamos) / scale))
            probes[p] = (n, lower.tobytes(), upper.tobytes(), f_jmetal, x)
            entry = {"spec": spec, "n_var": n, "n_obj": m,
                     "same_dimension_and_bounds_as_vamos": bool(n == vamos.n_var and np.allclose(lower, v_lower) and np.allclose(upper, v_upper)),
                     "max_relative_objective_difference_vs_vamos": mismatch}

            runs = [worker.run(spec, s, 20_000, command_line(DEFAULT), m) for s in range(9001, 9006)]
            evaluated = np.vstack(runs)
            evaluated = evaluated[moocore.is_nondominated(evaluated, keep_weakly=False)]
            if p in ANALYTIC:
                ideal, nadir = (np.asarray(v, float) for v in ANALYTIC[p])
                source = "analytic"
            else:
                front = _load_front(FRONT_FILES[p])
                ideal, nadir, source = front.min(axis=0), front.max(axis=0), f"evolver {FRONT_FILES[p]}"
            overshoot = float(np.max((ideal - evaluated.min(axis=0)) / (nadir - ideal)))
            entry.update(bounds_source=source, ideal=ideal.tolist(), nadir=nadir.tolist(),
                         default_runs_beat_ideal_by=overshoot)
            if overshoot > 0.01:
                entry["bounds_rejected"] = True
            bounds_out[p] = {"ideal": ideal.tolist(), "nadir": nadir.tolist(), "source": source}
            report[p] = entry
            print(p, spec, n, entry["same_dimension_and_bounds_as_vamos"], f"{mismatch:.2e}", source, f"{overshoot:+.3f}", flush=True)

    duplicates = []
    for a, b in combinations(problems, 2):
        na, la, ua, fa, xa = probes[a]
        nb, lb, ub, fb, _ = probes[b]
        if na == nb and la == lb and ua == ub:
            with JWorker() as worker:
                fb_on_a = worker.evaluate(SPECS[b], xa, fa.shape[1])
            if np.allclose(fa, fb_on_a, rtol=1e-12, atol=1e-12):
                duplicates.append((a, b))
    (PHASE3E / "data").mkdir(parents=True, exist_ok=True)
    (PHASE3E / "data" / "catalogue_3e.json").write_text(json.dumps(
        {"problems": report, "jmetal_duplicates": duplicates}, indent=2) + "\n")
    (PHASE3E / "data" / "tuning_bounds.json").write_text(json.dumps(bounds_out, indent=2) + "\n")
    print("duplicates:", duplicates)
    rejected = [p for p, e in report.items() if e.get("bounds_rejected")]
    print("bounds rejected:", rejected)


if __name__ == "__main__":
    main()
