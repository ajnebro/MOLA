"""Phase 0 limited pilot (plan.md section 9, item 7). Budget: <= 25 000 evaluations in total for phase 0.

Samples (evaluations): COCO bbob-biobj_f02_i02_d02, n=400 x 5 seeds (2 000); RE25, RE33, RE42 with
heterogeneous bounds and RE36 with homogeneous bounds, n=200*D x 3 seeds (10 200). Each sample's X/F
matrices are kept and reused for every variant:

* geometry ``raw``: MOLA as is (neighbour graph and all measurements on raw X);
* geometry ``bound``: X mapped to [0,1]^D by the declared bounds for graph and measurements;
* ablation of moorphology's neighbour-distance accumulator (``=`` as shipped vs ``+=``), on the same X.

Recognition ratios between resamples are reported separately as (a) within / mean-to-others and
(b) within / nearest-other. They measure recognition, not transfer. Outputs go to ``../data/pilot_*``.
"""

import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

from mola import characterize as ch
from mola.distance import build_neighbourhood
from mola.dominance import local_nondominance, neighbourhood_dominance
from mola.hypervolume import reference_point
from mola.multimodality import adaptive_walks, single_objective_local_optima
from mola.normalization import build_normalizers
from mola.ranking import rank_solutions
from mola.sample import Sample

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
sys.path.insert(0, str(HERE))
from common import EVALUATIONS, THESIS19, sample_coco, sample_jmetalpy, thesis_ratio_terms  # noqa: E402

PLAN = [("COCO", "dimensions:2 function_indices:2 instance_indices:2", [1, 2, 3, 4, 5])] + \
       [(name, None, [1, 2, 3]) for name in ("RE25", "RE33", "RE42", "RE36")]


def timed_features(Xg: np.ndarray, Xm: np.ndarray, F: np.ndarray, seed: int, k: int) -> tuple[dict, dict, object]:
    """All 49 features with stage timings; graph built on Xg, X measurements taken on Xm."""
    t, times = time.perf_counter(), {}
    def lap(name):
        nonlocal t
        now = time.perf_counter(); times[name] = now - t; t = now
    nb = build_neighbourhood(Xg, k); lap("neighbourhood")
    ranking = rank_solutions(F); lap("ranking_jmetalpy")
    dom = neighbourhood_dominance(F, nb); lap("pairwise_dominance")
    local = local_nondominance(F, nb); lap("local_nondominance")
    norms = build_normalizers(Xm, F); lap("normalizers")
    ref = reference_point(F); walks = adaptive_walks(F, nb, seed=seed); lap("ref_and_walks")
    sub = ch._Substrate(neighbourhood=nb, ranking=ranking, dominance=dom, local=local, normalizers=norms, ref=ref, walks=walks)
    feats = {}
    for group in (ch._global_features, ch._multimodality_features, ch._evolvability_features, ch._ruggedness_features):
        feats.update(group(Xm, F, sub)); lap(group.__name__.strip("_"))
    return feats, times, (nb, ranking, dom)


def undefined_causes(feats: dict, F: np.ndarray, nb, ranking, dom) -> dict:
    nd = len(ranking.nondominated)
    plo = int((dom.dominating == 0).sum())
    slo_per_obj = single_objective_local_optima(F, nb).sum(axis=0).tolist()
    causes = {}
    for k, v in feats.items():
        if not (isinstance(v, float) and np.isnan(v)):
            continue
        if k in ("dist_x_nd_avg", "dist_x_nd_max", "fdc"):
            causes[k] = f"|ND|={nd} < 2"
        elif k.startswith("plo_dist"):
            causes[k] = f"|PLO|={plo} < 2"
        elif k.startswith("slo_dist"):
            causes[k] = f"local optima per objective={slo_per_obj}, all < 2"
        elif k.endswith("_cor_neig") or k == "f_cor":
            causes[k] = "Spearman undefined: constant measure"
        else:
            causes[k] = "unclassified"
    return causes


def moorphology_neigh_dist_x_avg(X: np.ndarray, d: int, accumulate: bool) -> float:
    """Faithful re-implementation of moorphology's neighbourDistanceXAverage (master 9d57172, lines 136-278).

    getNeighbours spends one of its d picks on the self point (distance 0) -> d-1 neighbours; the per-sample
    mean is assigned with '=' (accumulate=False, as shipped) or accumulated with '+=' (accumulate=True);
    the result is divided by n and normalised with DIST_X_MIN = 0 (the pair loop includes j = i).
    """
    D = cdist(X, X)
    n = len(X)
    total = 0.0
    for i in range(n):  # HashMap<Integer,...> over keys 0..n-1 iterates in ascending order
        row = D[i].copy(); neighbours = []
        for _ in range(d):
            j = int(np.argmin(row))
            if j != i:
                neighbours.append(j)
            row[j] = np.inf
        mean = D[i, neighbours].mean() if neighbours else np.nan
        total = total + mean if accumulate else mean
    avg = total / n
    dmin, dmax = 0.0, D.max()
    return (avg - dmin) / (dmax - dmin)


def main() -> None:
    rows, meta, ablation, coco_info = [], [], [], None
    # Phase-wide cap: count what the checks and the Java moorphology runs already spent.
    prior = json.loads((DATA / "checks_results.json").read_text())["evaluations_used"]
    EVALUATIONS.update({f"prior_checks_{k}": v for k, v in prior.items()})
    EVALUATIONS["prior_moorphology_java_ZDT1_D2_D4_x2"] = 2 * (400 + 800)
    start = time.perf_counter()
    for name, opts, seeds in PLAN:
        for seed in seeds:
            if name == "COCO":
                s, evals, eval_secs, coco_info = sample_coco(opts, seed=seed, n=400)
            else:
                s, evals, eval_secs = sample_jmetalpy(name, seed=seed)
            X, F, lo, hi = s.variables, s.objectives, s.lower_bounds, s.upper_bounds
            Xn = (X - lo) / (hi - lo)
            k = s.number_of_variables
            per_variant = {}
            for variant, (Xg, Xm) in {"raw": (X, X), "bound": (Xn, Xn)}.items():
                feats, times, (nb, ranking, dom) = timed_features(Xg, Xm, F, seed, k)
                per_variant[variant] = nb
                rows.append({"problem": s.problem, "seed": seed, "variant": variant, "D": k, "M": s.number_of_objectives,
                             "n": s.size, **feats})
                meta.append({"problem": s.problem, "seed": seed, "variant": variant, "evaluations": evals if variant == "raw" else 0,
                             "evaluation_seconds": eval_secs if variant == "raw" else 0.0, "nd_count": len(ranking.nondominated),
                             "effective_k": nb.size, "undefined": json.dumps(undefined_causes(feats, F, nb, ranking, dom)),
                             **{f"t_{kk}": vv for kk, vv in times.items()}})
            overlap = np.mean([len(set(a) & set(b)) / k for a, b in zip(per_variant["raw"].indices, per_variant["bound"].indices)])
            meta[-2]["graph_overlap_raw_vs_bound"] = meta[-1]["graph_overlap_raw_vs_bound"] = float(overlap)
            ablation.append({"problem": s.problem, "seed": seed,
                             "moorph_eq_as_shipped": moorphology_neigh_dist_x_avg(X, k, accumulate=False),
                             "moorph_pluseq_fixed": moorphology_neigh_dist_x_avg(X, k, accumulate=True),
                             "mola_dist_x_avg_neig_raw": rows[-2]["dist_x_avg_neig"]})
            print(f"{s.problem:24s} seed={seed} n={s.size:5d} |ND|={meta[-1]['nd_count']:4d} overlap={overlap:.2f} "
                  f"char={sum(v for kk, v in meta[-2].items() if kk.startswith('t_')):.1f}s", flush=True)
    feats = pd.DataFrame(rows); feats.to_csv(DATA / "pilot_features.csv", index=False)
    pd.DataFrame(meta).to_csv(DATA / "pilot_meta.csv", index=False)
    pd.DataFrame(ablation).to_csv(DATA / "pilot_ablation.csv", index=False)

    # Recognition between resamples with the thesis ratio metric over the 19 shared features
    sim = []
    for variant in ("raw", "bound"):
        sub = feats[feats.variant == variant].reset_index(drop=True)
        V = sub[THESIS19].to_numpy(float); labels = sub.problem.to_numpy()
        Dm = np.array([[np.nansum(thesis_ratio_terms(V[i], V[j])) for j in range(len(V))] for i in range(len(V))])
        for p in np.unique(labels):
            idx = np.flatnonzero(labels == p); other = np.flatnonzero(labels != p)
            within = np.mean([Dm[i, j] for i in idx for j in idx if i != j])
            sim.append({"variant": variant, "problem": p, "within_mean": within,
                        "a_within_over_mean_other": within / Dm[np.ix_(idx, other)].mean(),
                        "b_within_over_nearest_other": within / Dm[np.ix_(idx, other)].min(),
                        "nan_terms_skipped": int(np.isnan(np.array([thesis_ratio_terms(V[i], V[j]) for i in idx for j in other])).sum())})
    pd.DataFrame(sim).to_csv(DATA / "pilot_similarity.csv", index=False)
    summary = {"evaluations": dict(EVALUATIONS), "evaluations_total": int(sum(EVALUATIONS.values())),
               "wall_seconds": time.perf_counter() - start, "coco_problem": coco_info}
    (DATA / "pilot_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
