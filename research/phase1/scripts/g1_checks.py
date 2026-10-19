"""Gate G1 checks for phase 1 (research/phase0/protocol.md, section 7).

1. Concordance of MOLA 0.3.0's supported test with an independent exact verifier, globally and on
   every local front, on DTLZ2 and RE33 (the phase 0 problems) plus RE21, RE41, RE61 and
   Ahmad2017, so that all three methods of `mola.hull` (chain, dominated hull, linear programs)
   are exercised.
2. Invariance of all 49 features under the per-variable affine map of phase 0 section 6.4, with
   the `bound` geometry, on the three heterogeneous-bound pilot problems.

The verifier is written here, independently of `mola.hull`: it solves the *primal* program
"maximize t subject to w >= t, sum(w) = 1 and w . (p_i - p_j) <= 0 for every j", and calls p_i
supported iff t* > 1e-9 (strictly positive weights, ties allowed). `mola.hull` instead uses the
dual characterization (no dominating convex combination) or geometry. Local fronts are found by
brute-force pairwise dominance, not by moocore.

Run from the repository root:  python research/phase1/scripts/g1_checks.py
Writes research/phase1/data/g1_results.json.
"""

import json
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
from jmetal.problem import DTLZ2
from jmetal.problem.multiobjective import re as re_suite
from jmetal.problem.multiobjective import rwa
from scipy.optimize import linprog

import mola
from mola.adapters.jmetalpy import sample_problem
from mola.characterize import characterize_report
from mola.distance import build_neighbourhood
from mola.dominance import local_nondominance
from mola.geometry import Geometry, decision_space
from mola.hull import supported_mask
from mola.ranking import rank_solutions

OUT = Path(__file__).resolve().parents[1] / "data" / "g1_results.json"
EVALUATIONS: dict[str, int] = {}
TOLERANCE = 1e-9


def _sample(name: str, factory, seed: int):
    problem = factory()
    n = 200 * problem.number_of_variables()
    EVALUATIONS[f"{name}/seed{seed}"] = n
    return sample_problem(problem, sample_size=n, seed=seed)


def verifier_supported(objectives: np.ndarray) -> np.ndarray:
    """Independent primal LP: max t s.t. w >= t, sum w = 1, w.(p_i - p_j) <= 0 for all j."""
    count, m = objectives.shape
    lower, span = objectives.min(axis=0), np.ptp(objectives, axis=0)
    scaled = (objectives - lower) / np.where(span == 0, 1.0, span)
    out = np.zeros(count, dtype=bool)
    for i in range(count):
        diffs = scaled[i] - scaled  # rows j: p_i - p_j ; w . diff <= 0
        a_ub = np.vstack([np.hstack([diffs, np.zeros((count, 1))]),
                          np.hstack([-np.eye(m), np.ones((m, 1))])])  # t - w_m <= 0
        b_ub = np.zeros(count + m)
        res = linprog(np.r_[np.zeros(m), -1.0], A_ub=a_ub, b_ub=b_ub,
                      A_eq=np.r_[np.ones(m), 0.0][None, :], b_eq=[1.0],
                      bounds=[(0, None)] * m + [(None, 1.0)], method="highs")
        out[i] = res.status == 0 and -res.fun > TOLERANCE
    return out


def brute_force_nondominated(points: np.ndarray) -> np.ndarray:
    leq = (points[:, None, :] <= points[None, :, :]).all(axis=2)
    lt = (points[:, None, :] < points[None, :, :]).any(axis=2)
    dominated_by = leq & lt  # [a, b]: a dominates b
    return ~dominated_by.any(axis=0)


def concordance(name: str, factory, seed: int = 42) -> dict:
    sample = _sample(name, factory, seed)
    variables = decision_space(sample, Geometry.BOUND)
    objectives = sample.objectives
    neighbourhood = build_neighbourhood(variables, sample.number_of_variables)

    t0 = time.perf_counter()
    nd = objectives[rank_solutions(objectives).rank == 0]
    mola_global = supported_mask(nd)
    t_mola_global = time.perf_counter() - t0
    t0 = time.perf_counter()
    verifier_global = verifier_supported(nd)
    t_verifier_global = time.perf_counter() - t0

    t0 = time.perf_counter()
    local = local_nondominance(objectives, neighbourhood)
    t_mola_local = time.perf_counter() - t0
    t0 = time.perf_counter()
    expected_lnd = np.zeros(len(objectives), dtype=int)
    expected_lsupp = np.zeros(len(objectives), dtype=int)
    for i in range(len(objectives)):
        group = np.concatenate(([i], neighbourhood.indices[i]))
        front = np.flatnonzero(brute_force_nondominated(objectives[group]))
        expected_lnd[i] = np.count_nonzero(front != 0)
        supported = verifier_supported(objectives[group[front]])
        expected_lsupp[i] = np.count_nonzero(supported[front != 0])
    t_verifier_local = time.perf_counter() - t0

    method = {2: "chain"}.get(objectives.shape[1], "dominated hull" if objectives.shape[1] <= 4 else "linear programs")
    denominator = len(objectives) * neighbourhood.size
    return {
        "problem": name, "seed": seed, "n": len(objectives), "M": objectives.shape[1],
        "D": sample.number_of_variables, "geometry": "bound", "k": neighbourhood.size,
        "mola_method": method, "global_nd": len(nd),
        "supp_n": {"mola": float(mola_global.mean()), "verifier": float(verifier_global.mean())},
        "global_disagreements": int(np.count_nonzero(mola_global != verifier_global)),
        "lsupp_avg_neig": {"mola": float(local.locally_supported.sum() / denominator),
                           "verifier": float(expected_lsupp.sum() / denominator)},
        "lnd_disagreeing_groups": int(np.count_nonzero(local.locally_nondominated != expected_lnd)),
        "lsupp_disagreeing_groups": int(np.count_nonzero(local.locally_supported != expected_lsupp)),
        "seconds": {"mola_global": t_mola_global, "verifier_global": t_verifier_global,
                    "mola_local": t_mola_local, "verifier_local": t_verifier_local},
    }


def affine_invariance(name: str, factory, seed: int = 7) -> dict:
    """Phase 0 section 6.4's map: a ~ U(0.1, 50), b ~ U(-10, 10) per variable (rng seed 3)."""
    sample = _sample(name, factory, seed)
    rng = np.random.default_rng(3)
    a = rng.uniform(0.1, 50.0, sample.number_of_variables)
    b = rng.uniform(-10.0, 10.0, sample.number_of_variables)
    mapped = replace(sample, variables=a * sample.variables + b,
                     lower_bounds=a * sample.lower_bounds + b, upper_bounds=a * sample.upper_bounds + b)
    out = {"problem": name, "seed": seed, "D": sample.number_of_variables}
    for geometry in ("bound", "raw"):
        before = characterize_report(sample, geometry=geometry).features
        after = characterize_report(mapped, geometry=geometry).features
        changed = [key for key in before
                   if not (np.isnan(before[key]) and np.isnan(after[key]))
                   and not np.isclose(before[key], after[key], rtol=1e-6, atol=1e-12)]
        max_rel = max((abs(after[k] - before[k]) / max(abs(before[k]), 1e-300)
                       for k in before if np.isfinite(before[k]) and np.isfinite(after[k])), default=0.0)
        out[geometry] = {"changed": changed, "number_changed": len(changed),
                         "max_relative_difference": float(max_rel)}
    return out


def main() -> None:
    results = {"mola_version": mola.__version__, "tolerance": TOLERANCE,
               "concordance": [], "affine_invariance": []}
    for name, factory in [("RE21", re_suite.RE21), ("DTLZ2", DTLZ2), ("RE33", re_suite.RE33),
                          ("RE41", re_suite.RE41), ("RE61", re_suite.RE61),
                          ("Ahmad2017", rwa.Ahmad2017)]:
        results["concordance"].append(concordance(name, factory))
        print(json.dumps(results["concordance"][-1]))
    for name, factory in [("RE25", re_suite.RE25), ("RE33", re_suite.RE33), ("RE42", re_suite.RE42)]:
        results["affine_invariance"].append(affine_invariance(name, factory))
        print(json.dumps(results["affine_invariance"][-1]))
    results["evaluations"] = EVALUATIONS
    results["total_evaluations"] = sum(EVALUATIONS.values())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2) + "\n")
    print("total evaluations", results["total_evaluations"])


if __name__ == "__main__":
    main()
