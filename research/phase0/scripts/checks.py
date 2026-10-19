"""Phase 0 minimal correctness checks (plan.md section 9, items 6.1-6.6).

Each check records what was run and what was observed; nothing here changes MOLA. Known defects that
reproduce are reported as results, not hidden. Writes ``research/phase0/data/checks_results.json``.

Run from the repository root:  python research/phase0/scripts/checks.py
"""

import json
import sys
import time
import warnings
from pathlib import Path

import moocore
import numpy as np
from scipy.optimize import linprog

from mola.characterize import characterize
from mola.distance import build_neighbourhood
from mola.dominance import neighbourhood_dominance
from mola.hull import supported_mask
from mola.ranking import rank_solutions
from mola.sample import Sample

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import (  # noqa: E402
    EVALUATIONS,
    sample_jmetalpy,
    thesis_ratio_terms,
)

RESULTS: dict = {}


# --------------------------------------------------------------------------------------------
# 6.1 Supported points
# --------------------------------------------------------------------------------------------
def supported_weak(objectives: np.ndarray, tol: float = 1e-9) -> np.ndarray:
    """Point i is supported iff some w >= 0 with sum(w) = 1 makes it a minimiser of w.f (ties allowed)."""
    count, m = objectives.shape
    out = np.zeros(count, dtype=bool)
    for i in range(count):
        a_ub = objectives[i] - np.delete(objectives, i, axis=0)
        res = linprog(np.zeros(m), A_ub=a_ub, b_ub=np.full(len(a_ub), tol),
                      A_eq=np.ones((1, m)), b_eq=[1.0], bounds=[(0, None)] * m)
        out[i] = res.status == 0
    return out


def supported_extreme(objectives: np.ndarray, tol: float = 1e-9) -> np.ndarray:
    """Point i is extreme-supported iff some w makes it the *unique* minimiser (strict margin t > 0)."""
    count, m = objectives.shape
    out = np.zeros(count, dtype=bool)
    for i in range(count):
        diff = np.delete(objectives, i, axis=0) - objectives[i]  # need w.diff_j >= t for all j
        a_ub = np.hstack([-diff, np.ones((len(diff), 1))])        # -w.diff_j + t <= 0
        res = linprog(np.r_[np.zeros(m), -1.0], A_ub=a_ub, b_ub=np.zeros(len(diff)),
                      A_eq=np.r_[np.ones(m), 0.0][None, :], b_eq=[1.0],
                      bounds=[(0, None)] * m + [(None, 1.0)])
        out[i] = res.status == 0 and -res.fun > tol
    return out


CASES = {
    "A": np.array([[0, 1, 1], [1, 0, 0], [0.6, 0.6, 0.6]], float),
    "B": np.array([[0, 2], [0.5, 1.5], [2, 0], [1.5, 1]], float),
    "C": np.array([[0.4, 0.5, 0.3], [0.9, 0.2, 0.8], [0.5, 0.3, 0.7], [0.8, 0.9, 0.1]], float),
}


def check_supported_cases() -> None:
    out = {}
    for name, pts in CASES.items():
        nd = bool((rank_solutions(pts).rank == 0).all())
        out[name] = {"points": pts.tolist(), "mutually_nondominated": nd,
                     "mola": supported_mask(pts).tolist(),
                     "weak_supported_lp": supported_weak(pts).tolist(),
                     "extreme_supported_lp": supported_extreme(pts).tolist()}
    RESULTS["6.1_supported_cases"] = out


def _classify_miss(sub: np.ndarray, local_index: int) -> str:
    from scipy.spatial import ConvexHull, QhullError
    if len(sub) <= sub.shape[1]:
        return "shortcut_count_le_M"
    try:
        hull = ConvexHull(sub)
    except QhullError:
        return "qhull_fallback"
    return "missed_vertex" if local_index in hull.vertices else "missed_non_vertex"


def check_supported_impact(problems=("DTLZ2", "RE33")) -> None:
    out = {}
    for name in problems:
        sample, evals, secs = sample_jmetalpy(name, seed=42)
        F, X = sample.objectives, sample.variables
        nb = build_neighbourhood(X, sample.number_of_variables)
        m = sample.number_of_objectives
        nd_global = F[rank_solutions(F).rank == 0]
        g_mola, g_weak, g_ext = (supported_mask(nd_global), supported_weak(nd_global), supported_extreme(nd_global))
        counts = {"mola": 0, "weak": 0, "extreme": 0}
        kinds: dict[str, int] = {}
        shortcut = 0
        for i in range(len(F)):
            idx = np.concatenate(([i], nb.indices[i]))
            nd_pos = np.flatnonzero(rank_solutions(F[idx]).rank == 0)
            sub = F[idx[nd_pos]]
            shortcut += len(sub) <= m
            a, w, e = supported_mask(sub), supported_weak(sub), supported_extreme(sub)
            not_self = nd_pos != 0
            counts["mola"] += int(a[not_self].sum())
            counts["weak"] += int(w[not_self].sum())
            counts["extreme"] += int(e[not_self].sum())
            for p in np.flatnonzero(a != w):
                kind = ("false_positive_" if a[p] else "false_negative_") + _classify_miss(sub, p)
                kinds[kind] = kinds.get(kind, 0) + 1
        denom = len(F) * nb.size
        out[name] = {
            "n": len(F), "M": m, "k": nb.size, "evaluations": evals, "sampling_seconds": secs,
            "global_nd": len(nd_global),
            "supp_n": {"mola": float(g_mola.mean()), "weak_lp": float(g_weak.mean()), "extreme_lp": float(g_ext.mean())},
            "lsupp_avg_neig": {k: v / denom for k, v in counts.items()},
            "local_sets_using_count_le_M_shortcut": shortcut / len(F),
            "local_disagreements_by_kind": kinds,
        }
    RESULTS["6.1_supported_impact"] = out


# --------------------------------------------------------------------------------------------
# 6.2 Rankings: MOLA isolation (the jMetal 6.1 side effect is checked by the Java harness)
# --------------------------------------------------------------------------------------------
def check_mola_ranking_isolation() -> None:
    rng = np.random.default_rng(0)
    F = rng.random((60, 2))
    before = rank_solutions(F).rank.copy()
    for i in range(0, 60, 7):  # local rankings on overlapping subsets, as local_nondominance does
        rank_solutions(F[i:i + 5])
    after = rank_solutions(F).rank
    RESULTS["6.2_mola_ranking_isolation"] = {"global_rank_unchanged_after_local_rankings": bool(np.array_equal(before, after)),
                                             "fronts": int(after.max()) + 1}


# --------------------------------------------------------------------------------------------
# 6.3 Neighbourhoods and dominance
# --------------------------------------------------------------------------------------------
def check_neighbourhood() -> None:
    out = {}
    X = np.array([[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
    nb = build_neighbourhood(X, 2)
    out["duplicates_self_excluded_by_index"] = bool(all(i not in nb.indices[i] for i in range(len(X))))
    out["duplicates_neighbours"] = nb.indices.tolist()
    small = build_neighbourhood(np.random.default_rng(1).random((4, 3)), 10)
    out["requested_k_10_with_n_4_effective_k"] = small.size
    rng = np.random.default_rng(2)
    Xr, Fr = rng.random((300, 4)), rng.random((300, 3))
    nbr = build_neighbourhood(Xr, 4)
    dom = neighbourhood_dominance(Fr, nbr)
    totals = (dom.dominating + dom.dominated + dom.incomparable) / nbr.size
    out["sup_inf_inc_sum_min_max"] = [float(totals.min()), float(totals.max())]
    # Pairwise dominance vs global-rank comparison (moorphology's sup/inf/inc logic)
    F = np.array([[0.0, 3.0], [1.0, 1.0], [2.0, 2.0]])  # (2,2) is dominated by (1,1) -> rank 1
    ranks = rank_solutions(F).rank
    y, x = F[0], F[2]
    pairwise_incomparable = not (np.all(y <= x) and np.any(y < x)) and not (np.all(x <= y) and np.any(x < y))
    out["pairwise_vs_global_rank_example"] = {
        "y": y.tolist(), "x": x.tolist(), "global_ranks": [int(ranks[0]), int(ranks[2])],
        "pairwise_incomparable": bool(pairwise_incomparable),
        "rank_comparison_says": "y dominates x" if ranks[0] < ranks[2] else "not dominating"}
    RESULTS["6.3_neighbourhood_dominance"] = out


# --------------------------------------------------------------------------------------------
# 6.4 Scaling
# --------------------------------------------------------------------------------------------
def _features_with(Xg: np.ndarray, Xm: np.ndarray, F: np.ndarray, base: Sample) -> dict:
    """All 49 features with the neighbour graph built on Xg and every X measurement taken on Xm."""
    from mola import characterize as ch
    from mola.dominance import local_nondominance
    from mola.hypervolume import reference_point
    from mola.multimodality import adaptive_walks
    from mola.normalization import build_normalizers
    nb = build_neighbourhood(Xg, base.number_of_variables)
    sub = ch._Substrate(neighbourhood=nb, ranking=rank_solutions(F), dominance=neighbourhood_dominance(F, nb),
                        local=local_nondominance(F, nb), normalizers=build_normalizers(Xm, F),
                        ref=reference_point(F), walks=adaptive_walks(F, nb, seed=base.seed))
    return {**ch._global_features(Xm, F, sub), **ch._multimodality_features(Xm, F, sub),
            **ch._evolvability_features(Xm, F, sub), **ch._ruggedness_features(Xm, F, sub)}


def _compare(a: dict, b: dict, rtol: float = 1e-9) -> dict:
    changed, ratio = [], {}
    for k in a:
        x, y = a[k], b[k]
        if np.isnan(x) and np.isnan(y):
            continue
        if not np.isclose(x, y, rtol=rtol, atol=1e-12):
            changed.append(k)
            if x != 0:
                ratio[k] = y / x
    return {"changed": changed, "ratio_new_over_old": ratio}


def check_scaling(problem="RE25", seed=7) -> None:
    sample, evals, _ = sample_jmetalpy(problem, seed=seed)
    X, F, lo, hi = sample.variables, sample.objectives, sample.lower_bounds, sample.upper_bounds
    Xn = (X - lo) / (hi - lo)
    raw = _features_with(X, X, F, sample)
    out = {"problem": problem, "evaluations": evals, "D": sample.number_of_variables}
    # (a) graph only: neighbours from bound-normalised X, all measurements on raw X
    out["graph_only_bound_normalised"] = _compare(raw, _features_with(Xn, X, F, sample))
    # (b) measurement only: neighbours from raw X, measurements on bound-normalised X
    out["measurement_only_bound_normalised"] = _compare(raw, _features_with(X, Xn, F, sample))
    # (c) uniform scaling X -> c X (graph is invariant by construction)
    c = 3.7
    uni = _compare(raw, _features_with(c * X, c * X, F, sample))
    out["uniform_scaling_c"] = c
    out["uniform_scaling"] = {"changed": uni["changed"],
                              "classification": {k: ("scales_by_c" if np.isclose(r, c) else "scales_by_1/c" if np.isclose(r, 1 / c) else f"other({r:.4g})")
                                                 for k, r in uni["ratio_new_over_old"].items()}}
    # (d) per-variable positive affine map with transformed bounds: raw vs bound-normalised geometry
    rng = np.random.default_rng(3)
    a, b = rng.uniform(0.1, 50.0, X.shape[1]), rng.uniform(-10, 10, X.shape[1])
    Xa, loa, hia = a * X + b, a * lo + b, a * hi + b
    Xan = (Xa - loa) / (hia - loa)
    out["affine_map"] = {"a": a.tolist(), "b": b.tolist()}
    out["affine_raw_geometry"] = {"changed": _compare(raw, _features_with(Xa, Xa, F, sample))["changed"]}
    norm = _features_with(Xn, Xn, F, sample)
    out["affine_bound_normalised_geometry"] = {"changed_vs_unmapped_normalised": _compare(norm, _features_with(Xan, Xan, F, sample), rtol=1e-6)["changed"],
                                               "max_abs_X_difference": float(np.abs(Xan - Xn).max())}
    RESULTS["6.4_scaling"] = out


# --------------------------------------------------------------------------------------------
# 6.5 Degenerate inputs and the thesis distance
# --------------------------------------------------------------------------------------------
def check_degenerate() -> None:
    out = {}
    X = np.random.default_rng(4).random((40, 2))
    F = np.column_stack([X[:, 0], 1 - X[:, 0] + X[:, 1]])
    F_bad = F.copy(); F_bad[3, 0] = np.nan; F_bad[5, 1] = np.inf
    try:
        s = Sample("nonfinite", X, F_bad, np.zeros(2), np.ones(2), "test")
        feats = characterize(s)
        out["nonfinite_objectives"] = {"accepted_by_Sample": True,
                                       "nan_features": sorted(k for k, v in feats.items() if isinstance(v, float) and np.isnan(v)),
                                       "n_features_finite": sum(np.isfinite(v) for v in feats.values())}
    except Exception as exc:  # noqa: BLE001
        out["nonfinite_objectives"] = {"accepted_by_Sample": False, "error": repr(exc)}
    try:
        Sample("degenerate_bounds", X, F, np.zeros(2), np.array([1.0, 0.0]), "test")
        out["degenerate_bounds_upper_eq_lower"] = "accepted (no check); bound normalisation would divide by zero"
    except Exception as exc:  # noqa: BLE001
        out["degenerate_bounds_upper_eq_lower"] = f"rejected: {exc!r}"
    # One solution dominating all others -> |ND| = 1
    F1 = F + 1.0; F1[0] = [0.0, 0.0]
    feats1 = characterize(Sample("single_nd", X, F1, np.zeros(2), np.ones(2), "test", seed=1))
    out["single_nondominated_point_nan_features"] = sorted(k for k, v in feats1.items() if isinstance(v, float) and np.isnan(v))
    out["single_nondominated_point_supp_n"] = feats1["supp_n"]
    # Thesis ratio distance (Eq. 4.1 / Listing B.5) on signed and zero values
    pairs = {"(-0.8,-0.2)": (-0.8, -0.2), "(-0.9,0.1)": (-0.9, 0.1), "(-0.2,0)": (-0.2, 0.0), "(0,0)": (0.0, 0.0), "(0.01,0.02)": (0.01, 0.02)}
    out["thesis_ratio_term"] = {k: float(thesis_ratio_terms(np.array([a]), np.array([b]))[0]) for k, (a, b) in pairs.items()}
    RESULTS["6.5_degenerate"] = out


# --------------------------------------------------------------------------------------------
# 6.6 moocore.pareto_rank vs jMetalPy ranking
# --------------------------------------------------------------------------------------------
def check_moocore_rank() -> None:
    out = {}
    rng = np.random.default_rng(5)
    for m in (2, 3, 5):
        for kind in ("random", "with_duplicates", "with_ties", "integer_grid"):
            F = rng.random((300, m))
            if kind == "with_duplicates":
                F[150:] = F[:150]
            elif kind == "with_ties":
                F[:, 0] = np.round(F[:, 0], 1)
            elif kind == "integer_grid":
                F = rng.integers(0, 5, (300, m)).astype(float)
            a = rank_solutions(F).rank
            b = np.asarray(moocore.pareto_rank(F))
            t0 = time.perf_counter(); rank_solutions(F); t1 = time.perf_counter(); moocore.pareto_rank(F); t2 = time.perf_counter()
            out[f"M{m}_{kind}"] = {"identical": bool(np.array_equal(a, b)), "jmetalpy_s": t1 - t0, "moocore_s": t2 - t1}
    RESULTS["6.6_moocore_pareto_rank"] = out


if __name__ == "__main__":
    start = time.perf_counter()
    for fn in (check_supported_cases, check_mola_ranking_isolation, check_neighbourhood, check_degenerate,
               check_moocore_rank, check_scaling, check_supported_impact):
        t = time.perf_counter(); fn(); print(f"{fn.__name__:32s} {time.perf_counter() - t:6.1f}s", flush=True)
    RESULTS["evaluations_used"] = dict(EVALUATIONS)
    RESULTS["wall_seconds"] = time.perf_counter() - start
    path = HERE.parent / "data" / "checks_results.json"
    path.write_text(json.dumps(RESULTS, indent=2, default=float))
    print(f"wrote {path}")
