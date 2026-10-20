"""Phase 2b analysis: arms C (phase 2 F-Race), A (F-Race, reference-front bounds), B (irace).

Inputs (fetched from NicoVM): ARMS_DIR/<arm>/fronts/<config>__<problem>.npz for the arm's 37 tuned
configurations plus the three untuned defaults (evaluated once, in arm C, and copied to A and B),
and the arms' tuned-configuration files.

1. G2 per arm: phase 2's pre-registered rule (`analyze_g2.gaps`, seed cross-fitting) on the arm's
   own portfolio and normalization (union of the arm's final fronts).
2. Each c*_P on its own problem P under a common normalization: the union of the final fronts of
   all three arms on P. Paired Wilcoxon signed-rank tests B vs A (tuner) and A vs C (normalization).
3. The SBS of each arm, the number of distinct operator combinations, and the tuning runs used.

Run locally:  python research/phase2b/scripts/analyze_arms.py   ->  data/arms_*.csv, arms_result.json
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))

import moocore  # noqa: E402

from analyze_g2 import FINAL, X_THRESHOLD, Y_FRACTION, gaps  # noqa: E402
from common import DATA as PHASE2_DATA  # noqa: E402
from common import PHASE as PHASE2  # noqa: E402
from common import pilot_problems  # noqa: E402
from evaluate_pilot import EVALUATION_SEEDS  # noqa: E402
from runs import CHECKPOINTS  # noqa: E402
from tune_pilot import REFERENCE  # noqa: E402

PHASE2B = HERE.parent
ARMS_DIR = Path(os.environ.get("MOLA_PHASE2B_ARMS", r"C:\tmp\mola-phase2b"))
ARMS = {"C": PHASE2_DATA / "tuned_configs.json",
        "A": PHASE2B / "data" / "tuned_frace_refnorm.json",
        "B": PHASE2B / "data" / "tuned_irace.json"}
DEFAULTS = ("default__nsgaii", "default__moead", "default__smsemoa")
OPERATORS = ("crossover", "mutation", "repair", "initializer", "selection")


def _front(arm: str, config: str, problem: str, seed: int, evaluations: int) -> np.ndarray:
    return np.load(ARMS_DIR / arm / "fronts" / f"{config}__{problem}.npz")[f"s{seed}_e{evaluations}"]


def _hv(points: np.ndarray, reference: np.ndarray) -> float:
    points = points[np.all(points < reference, axis=1)]
    return float(moocore.hypervolume(points, ref=reference)) if len(points) else 0.0


def _normalizer(fronts: list[np.ndarray]):
    union = np.vstack(fronts)
    union = union[moocore.is_nondominated(union, keep_weakly=True)]
    ideal, nadir = union.min(axis=0), union.max(axis=0)
    span = np.where(nadir > ideal, nadir - ideal, 1.0)
    reference = np.full(union.shape[1], REFERENCE)
    best = _hv((union - ideal) / span, reference)
    return lambda front: _hv((front - ideal) / span, reference) / best


def arm_hvn(arm: str) -> pd.DataFrame:
    """Phase 2's HVn table for one arm: normalization from the arm's own portfolio."""
    configs = [f"tuned__{p}" for p in pilot_problems()] + list(DEFAULTS)
    rows = []
    for problem in pilot_problems():
        score = _normalizer([_front(arm, c, problem, s, FINAL) for c in configs for s in EVALUATION_SEEDS])
        for c in configs:
            for s in EVALUATION_SEEDS:
                rows.append({"config": c, "problem": problem, "seed": s, "evaluations": FINAL,
                             "hvn": score(_front(arm, c, problem, s, FINAL))})
    return pd.DataFrame(rows)


def self_tuned_common() -> pd.DataFrame:
    """HVn of each arm's c*_P on P, normalized by the union of all arms' final fronts on P."""
    configs = [f"tuned__{p}" for p in pilot_problems()] + list(DEFAULTS)
    rows = []
    for problem in pilot_problems():
        fronts = [_front(a, c, problem, s, FINAL) for a in ARMS for c in configs for s in EVALUATION_SEEDS]
        score = _normalizer(fronts)
        row = {"problem": problem}
        for arm in ARMS:
            row[arm] = float(np.mean([score(_front(arm, f"tuned__{problem}", problem, s, FINAL))
                                      for s in EVALUATION_SEEDS]))
        row["default__nsgaii"] = float(np.mean([score(_front("C", "default__nsgaii", problem, s, FINAL))
                                               for s in EVALUATION_SEEDS]))
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    group_of = pd.read_csv(PHASE2 / "catalogue.csv").set_index("problem")["group"].to_dict()
    result, per_arm = {}, []
    for arm, tuned_file in ARMS.items():
        hvn = arm_hvn(arm)
        arm_gaps = gaps(hvn, group_of, FINAL)
        arm_gaps["arm"] = arm
        per_arm.append(arm_gaps)
        per_group = arm_gaps.groupby("group").gap_oracle_donor_vs_sbs.mean()
        mean = hvn.groupby(["config", "problem"]).hvn.mean().unstack()
        tuned = json.loads(Path(tuned_file).read_text())
        combos = {tuple(tuned[p]["config"].get(k) for k in OPERATORS) for p in pilot_problems()}
        result[arm] = {
            "g2_fraction": float((per_group >= X_THRESHOLD).mean()),
            "g2_groups_meeting": int((per_group >= X_THRESHOLD).sum()),
            "g2_passes": bool((per_group >= X_THRESHOLD).mean() >= Y_FRACTION),
            "g2_fraction_at": {str(x): float((per_group >= x).mean()) for x in (0.005, 0.01, 0.02, 0.05)},
            "best_generalist": mean.loc[[f"tuned__{p}" for p in pilot_problems()]].mean(axis=1).idxmax(),
            "best_generalist_mean_hvn": float(mean.loc[[f"tuned__{p}" for p in pilot_problems()]].mean(axis=1).max()),
            "distinct_operator_combinations": len(combos),
            "default_selected": sum(tuned[p]["config"].get("crossover") == "sbx" and tuned[p]["config"].get("pop_size") == 100
                                    and tuned[p]["config"].get("mutation") == "polynomial" for p in pilot_problems()),
            "tuning_runs": int(sum(v.get("experiments", 0) for v in tuned.values())),
        }
    pd.concat(per_arm).to_csv(PHASE2B / "data" / "arms_gaps.csv", index=False)

    common = self_tuned_common()
    common.to_csv(PHASE2B / "data" / "arms_self_tuned.csv", index=False)
    for a, b in (("B", "A"), ("A", "C"), ("B", "C")):
        difference = common[a] - common[b]
        result[f"self_tuned_{a}_minus_{b}"] = {
            "mean": float(difference.mean()), "median": float(difference.median()),
            "wins": int((difference > 1e-6).sum()), "losses": int((difference < -1e-6).sum()),
            "wilcoxon_p": float(wilcoxon(common[a], common[b]).pvalue),
        }
    (PHASE2B / "data" / "arms_result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print(common.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
