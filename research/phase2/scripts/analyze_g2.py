"""Phase 2, gate G2: is there room between the single best tuned configuration and the best donor?

Pre-registered in research/phase2/preregistration.md; this script is the rule, committed before the
data it reads existed.

Normalized hypervolume. For each pilot problem Q, the union of the 20 000-evaluation fronts of
every configuration and evaluation seed fixes the ideal and nadir. Fronts are min-max normalized
by them, the reference point is 1.1 in every objective, and HVn(run) = HV(run) / HV(union front),
in [0, 1]. Earlier checkpoints use the same normalization.

Gap, for a target Q and a split of the 5 evaluation seeds into 3 selection seeds and 2 assessment
seeds (all 10 splits, averaged):
- donors(Q): the tuned c*_P of every pilot problem P outside Q's formulation group;
- SBS(Q): the donor with the best mean HVn over all pilot problems outside Q's group (selection
  seeds) -- the generalist a recommender would fall back to;
- VBS(Q): the donor with the best mean HVn on Q itself (selection seeds) -- the oracle donor;
- gap(Q) = mean HVn of VBS(Q) minus mean HVn of SBS(Q), on Q, over the assessment seeds.
The group gap is the mean gap over the group's pilot problems.

G2 passes iff at least Y = 25 % of the formulation groups have a group gap >= X = 0.01.

Run:  python research/phase2/scripts/analyze_g2.py
Writes data/hvn.csv, data/g2_gaps.csv, data/transfer_loss.csv and data/g2_result.json.
"""

import json
from itertools import combinations

import numpy as np
import pandas as pd

from common import DATA, PHASE, pilot_problems
from evaluate_pilot import EVALUATION_SEEDS, FRONTS, portfolio
from runs import CHECKPOINTS
from tune_pilot import REFERENCE

X_THRESHOLD = 0.01
Y_FRACTION = 0.25
FINAL = CHECKPOINTS[-1]


def _hv(points: np.ndarray, reference: np.ndarray) -> float:
    from vamos.foundation.quality_indicators.hypervolume import hypervolume

    points = points[np.all(points < reference, axis=1)]
    return float(hypervolume(points, reference)) if len(points) else 0.0


def hvn_table() -> pd.DataFrame:
    from vamos.foundation.quality_indicators.pareto import pareto_filter

    rows = []
    configs = list(portfolio())
    for problem in pilot_problems():
        fronts = {c: np.load(FRONTS / f"{c}__{problem}.npz") for c in configs}
        union = np.vstack([fronts[c][f"s{s}_e{FINAL}"] for c in configs for s in EVALUATION_SEEDS])
        union = np.asarray(pareto_filter(union), float)
        ideal, nadir = union.min(axis=0), union.max(axis=0)
        span = np.where(nadir > ideal, nadir - ideal, 1.0)
        reference = np.full(union.shape[1], REFERENCE)
        best = _hv((union - ideal) / span, reference)
        for c in configs:
            for s in EVALUATION_SEEDS:
                for e in CHECKPOINTS:
                    front = (fronts[c][f"s{s}_e{e}"] - ideal) / span
                    rows.append({"config": c, "problem": problem, "seed": s, "evaluations": e,
                                 "hvn": _hv(front, reference) / best})
    return pd.DataFrame(rows)


def gaps(hvn: pd.DataFrame, group_of: dict[str, str], evaluations: int = FINAL) -> pd.DataFrame:
    problems = pilot_problems()
    table = hvn[hvn.evaluations == evaluations].pivot_table(
        index=["config", "problem"], columns="seed", values="hvn")
    donors_all = [f"tuned__{p}" for p in problems]
    rows = []
    for target in problems:
        donors = [d for d in donors_all if group_of[d.split("__", 1)[1]] != group_of[target]]
        training = [p for p in problems if group_of[p] != group_of[target]]
        split_gaps, split_self, split_default = [], [], []
        for selection in combinations(EVALUATION_SEEDS, 3):
            assessment = [s for s in EVALUATION_SEEDS if s not in selection]
            sel = list(selection)
            generalist = {d: table.loc[[(d, p) for p in training], sel].to_numpy().mean() for d in donors}
            sbs = max(generalist, key=generalist.get)
            oracle = {d: table.loc[(d, target), sel].mean() for d in donors}
            vbs = max(oracle, key=oracle.get)
            sbs_score = table.loc[(sbs, target), assessment].mean()
            split_gaps.append(table.loc[(vbs, target), assessment].mean() - sbs_score)
            split_self.append(table.loc[(f"tuned__{target}", target), assessment].mean() - sbs_score)
            split_default.append(table.loc[("default__nsgaii", target), assessment].mean() - sbs_score)
        rows.append({"problem": target, "group": group_of[target], "evaluations": evaluations,
                     "gap_oracle_donor_vs_sbs": float(np.mean(split_gaps)),
                     "gap_self_tuned_vs_sbs": float(np.mean(split_self)),
                     "gap_default_vs_sbs": float(np.mean(split_default))})
    return pd.DataFrame(rows)


def main() -> None:
    catalogue = pd.read_csv(PHASE / "catalogue.csv").set_index("problem")
    group_of = catalogue["group"].to_dict()
    hvn = hvn_table()
    hvn.to_csv(DATA / "hvn.csv", index=False)

    per_problem = pd.concat([gaps(hvn, group_of, e) for e in CHECKPOINTS])
    per_problem.to_csv(DATA / "g2_gaps.csv", index=False)
    final = per_problem[per_problem.evaluations == FINAL]
    per_group = final.groupby("group").gap_oracle_donor_vs_sbs.mean()
    fraction = float((per_group >= X_THRESHOLD).mean())

    mean_final = hvn[hvn.evaluations == FINAL].groupby(["config", "problem"]).hvn.mean().unstack()
    own = {p: mean_final.loc[f"tuned__{p}", p] for p in pilot_problems()}
    loss = pd.DataFrame({q: {p: own[q] - mean_final.loc[f"tuned__{p}", q] for p in pilot_problems()}
                         for q in pilot_problems()})  # rows: donor P, columns: target Q
    loss.to_csv(DATA / "transfer_loss.csv")

    result = {
        "rule": f"G2 passes iff >= {Y_FRACTION:.0%} of groups have gap >= {X_THRESHOLD}",
        "groups": int(per_group.size), "groups_meeting_threshold": int((per_group >= X_THRESHOLD).sum()),
        "fraction": fraction, "passes": bool(fraction >= Y_FRACTION),
        "group_gap_quantiles": per_group.quantile([0, 0.25, 0.5, 0.75, 1]).round(4).to_dict(),
        "sensitivity_fraction": {str(x): float((per_group >= x).mean()) for x in (0.005, 0.01, 0.02, 0.05)},
        "by_budget_fraction": {int(e): float((per_problem[per_problem.evaluations == e]
                                              .groupby("group").gap_oracle_donor_vs_sbs.mean() >= X_THRESHOLD).mean())
                               for e in CHECKPOINTS},
    }
    (DATA / "g2_result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
