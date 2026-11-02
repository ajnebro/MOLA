"""Phase 5 preparation (D12, C8): verify the 17 reserved problems before they are opened.

Checks only problem definitions; no algorithm is run on a reserved problem, so nothing about any
method's performance on them is learned. For each reserved problem (phase2/reserved_groups.json):
1. VAMOS (the implementation every phase uses): dimension, bounds, objectives on 1 000 random
   points in the bounds (seed 0).
2. jMetal 7.8 (Java, phase 3e's RunWorker): the same, on the same points. For WFG, the split of
   the 24 variables into position (k) and distance (l) parameters is not in the name, so both
   k = 4, l = 20 and k = 2, l = 22 are tried and the matching one is reported.
3. jMetalPy (when the class exists in the installed version): the same, on the first 200 points.
4. Reference fronts: VAMOS's own file and Evolver's (resources/referenceFronts), compared by their
   ideal and nadir and by the mean distance from each point of one to the other (normalised by the
   VAMOS front's range), and against the analytic ideal and nadir where they are known:
   WFG1-9 (f1 in [0, 2], f2 in [0, 4]), ZDT6 (f1 in [0.2808, 1], f2 = 1 - f1^2),
   ZCAT (f1 in [0, 1], f2 in [0, 4]).

Run locally:  python research/phase5/scripts/verify_reserved.py
Writes data/reserved_verification.json.
"""

import json
import sys
from pathlib import Path

import moocore
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))
sys.path.insert(0, str(HERE.parents[1] / "phase3e" / "scripts"))

import common  # noqa: E402
from jworker import JAR, JWorker  # noqa: E402

DATA = HERE.parent / "data"
EVOLVER_FRONTS = Path(JAR).parents[1] / "resources" / "referenceFronts"
POINTS, PY_POINTS = 1000, 200
ANALYTIC = {
    **{f"wfg{i}": ([0.0, 0.0], [2.0, 4.0]) for i in range(1, 10)},
    "zdt6": ([0.2807753191, 0.0], [1.0, 1.0 - 0.2807753191**2]),
    **{f"zcat{i}": ([0.0, 0.0], [1.0, 4.0]) for i in (2, 7, 14, 16, 18, 20)},
}


def jmetal_specs(problem: str, n_var: int) -> list[str]:
    if problem.startswith("wfg"):
        i = problem[3:]
        return [f"WFG{i}(4,20,2)", f"WFG{i}(2,22,2)"]
    if problem == "dtlz7":
        return [f"DTLZ7({n_var},2)"]
    return [problem.upper()]


def front_file(problem: str) -> str:
    if problem == "zdt6":
        return "ZDT6.csv"
    return f"{problem.upper()}.2D.csv"


def jmetalpy_problem(problem: str, n_var: int, wfg_k: int | None):
    try:
        import jmetal.problem as jp
    except ImportError:
        return None
    try:
        if problem == "zdt6":
            return jp.ZDT6(number_of_variables=n_var)
        if problem == "dtlz7":
            return jp.DTLZ7(number_of_variables=n_var, number_of_objectives=2)
        if problem.startswith("wfg") and wfg_k is not None:
            cls = getattr(jp, problem.upper())
            return cls(k=wfg_k, l=n_var - wfg_k, number_of_objectives=2)
        if problem.startswith("zcat"):
            cls = getattr(jp, problem.upper(), None)
            return cls(number_of_variables=n_var, number_of_objectives=2) if cls else None
    except (AttributeError, TypeError):
        return None
    return None


def evaluate_jmetalpy(problem_obj, x):
    out = []
    for row in x:
        solution = problem_obj.create_solution()
        solution.variables = list(map(float, row))
        problem_obj.evaluate(solution)
        out.append(solution.objectives[:2])
    return np.asarray(out, float)


def nondominated(front):
    return front[moocore.is_nondominated(front, keep_weakly=False)]


def mean_distance(a, b, span):
    a, b = a / span, b / span
    return float(np.mean(np.min(np.linalg.norm(a[:, None] - b[None], axis=2), axis=1)))


def main() -> None:
    from vamos.foundation.problem.resolver import resolve_reference_front_path

    reserved = json.loads((HERE.parents[1] / "phase2" / "reserved_groups.json").read_text())[
        "reserved_problems"
    ]
    rng = np.random.default_rng(0)
    report = {}
    with JWorker() as worker:
        for p in reserved:
            vamos = common.instantiate(p)
            lower, upper = common.bounds(vamos)
            n_var = len(lower)
            x = lower + rng.random((POINTS, n_var)) * (upper - lower)
            f_vamos = common.evaluate(vamos, x)
            scale = np.maximum(np.abs(f_vamos).max(axis=0), 1e-12)
            entry = {
                "n_var": n_var,
                "lower": [float(lower.min()), float(lower.max())],
                "upper": [float(upper.min()), float(upper.max())],
                "jmetal": {},
            }
            wfg_k = None
            for spec in jmetal_specs(p, n_var):
                try:
                    n, m, j_lower, j_upper = worker.info(spec)
                    f_jmetal = worker.evaluate(spec, x, m)
                except Exception as error:  # noqa: BLE001 - report and continue
                    entry["jmetal"][spec] = {"error": str(error)[:200]}
                    continue
                same_bounds = bool(
                    n == n_var and np.allclose(j_lower, lower) and np.allclose(j_upper, upper)
                )
                diff = float(np.max(np.abs(f_jmetal - f_vamos) / scale))
                entry["jmetal"][spec] = {
                    "same_dimension_and_bounds": same_bounds,
                    "max_relative_objective_difference": diff,
                }
                if p.startswith("wfg") and diff < 1e-2:
                    wfg_k = int(spec.split("(")[1].split(",")[0])
            py = jmetalpy_problem(p, n_var, wfg_k)
            if py is not None:
                try:
                    f_py = evaluate_jmetalpy(py, x[:PY_POINTS])
                    entry["jmetalpy_max_relative_objective_difference"] = float(
                        np.max(np.abs(f_py - f_vamos[:PY_POINTS]) / scale)
                    )
                except Exception as error:  # noqa: BLE001
                    entry["jmetalpy_error"] = str(error)[:200]
            else:
                entry["jmetalpy"] = "not available in the installed version"

            fronts = {}
            try:
                fronts["vamos"] = nondominated(
                    np.loadtxt(resolve_reference_front_path(p, None, n_obj=2), delimiter=",")
                )
            except Exception as error:  # noqa: BLE001
                entry["vamos_front_error"] = str(error)[:200]
            path = EVOLVER_FRONTS / front_file(p)
            if path.exists():
                fronts["evolver"] = nondominated(
                    np.loadtxt(path.read_text().replace(",", " ").splitlines())
                )
            for k in list(fronts):
                if fronts[k].shape[1] != 2:
                    entry[f"{k}_front_not_biobjective"] = int(fronts[k].shape[1])
                    del fronts[k]
            entry["fronts"] = {
                k: {
                    "points": int(len(f)),
                    "ideal": f.min(axis=0).round(6).tolist(),
                    "nadir": f.max(axis=0).round(6).tolist(),
                }
                for k, f in fronts.items()
            }
            if "vamos" in fronts and "evolver" in fronts:
                span = np.maximum(fronts["vamos"].max(axis=0) - fronts["vamos"].min(axis=0), 1e-12)
                entry["front_distance_vamos_to_evolver"] = mean_distance(
                    fronts["vamos"], fronts["evolver"], span
                )
                entry["front_distance_evolver_to_vamos"] = mean_distance(
                    fronts["evolver"], fronts["vamos"], span
                )
            if p in ANALYTIC and "vamos" in fronts:
                ideal, nadir = (np.asarray(v) for v in ANALYTIC[p])
                span = nadir - ideal
                entry["analytic"] = {"ideal": ideal.tolist(), "nadir": nadir.round(6).tolist()}
                entry["vamos_front_vs_analytic_max_gap"] = float(
                    np.max(
                        np.abs(
                            np.r_[
                                fronts["vamos"].min(axis=0) - ideal,
                                fronts["vamos"].max(axis=0) - nadir,
                            ]
                        )
                        / np.r_[span, span]
                    )
                )
            report[p] = entry
            print(
                p,
                n_var,
                {
                    k: round(v.get("max_relative_objective_difference", -1), 12)
                    for k, v in entry["jmetal"].items()
                },
                entry.get("jmetalpy_max_relative_objective_difference", entry.get("jmetalpy")),
                entry.get("vamos_front_vs_analytic_max_gap"),
                flush=True,
            )
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "reserved_verification.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
