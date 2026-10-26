"""Phase 2: descriptive follow-ups to the pre-registered G2 analysis (not part of the gate).

From data/hvn.csv and data/g2_gaps.csv:
- which donor is the leave-group-out SBS and which is the oracle donor for each target, using all
  5 evaluation seeds (no cross-fitting: identities only, not gap estimates);
- the gap of the untuned MOEA/D and SMS-EMOA defaults against the SBS, i.e. what adding those
  algorithms would bring, with the same 10-split cross-fitting as the gate;
- the uncertainty of the gate's verdict: a bootstrap over formulation groups (10 000 resamples)
  of the fraction of groups with a gap >= 0.01;
- the share of each group gap explained by the oracle donor coming from the LZ09/UF family when
  the target is in it (the relatives flagged by stage A).

Run:  python research/phase2/scripts/secondary_g2.py   ->  data/g2_secondary.json, g2_donors.csv
"""

import json
from itertools import combinations

import numpy as np
import pandas as pd

from analyze_g2 import FINAL, OUT, X_THRESHOLD
from common import PHASE, pilot_problems
from evaluate_pilot import EVALUATION_SEEDS, default_algorithms


def main() -> None:
    problems = pilot_problems()
    catalogue = pd.read_csv(PHASE / "catalogue.csv").set_index("problem")
    group_of, family_of = catalogue["group"].to_dict(), catalogue["family"].to_dict()
    others = [a for a in default_algorithms() if a != "nsgaii"]  # moead, smsemoa (ibea since D9)
    hvn = pd.read_csv(OUT / "hvn.csv")
    hvn = hvn[hvn.evaluations == FINAL]
    mean = hvn.groupby(["config", "problem"]).hvn.mean().unstack()
    table = hvn.pivot_table(index=["config", "problem"], columns="seed", values="hvn")

    rows = []
    for target in problems:
        donors = [f"tuned__{p}" for p in problems if group_of[p] != group_of[target]]
        training = [p for p in problems if group_of[p] != group_of[target]]
        sbs = mean.loc[donors, training].mean(axis=1).idxmax()
        oracle = mean.loc[donors, target].idxmax()
        comparators = {}
        for name in [f"default__{a}" for a in others] + ["default__nsgaii"]:
            split = []
            for selection in combinations(EVALUATION_SEEDS, 3):
                sel = list(selection)
                assessment = [s for s in EVALUATION_SEEDS if s not in selection]
                generalist = {d: table.loc[[(d, p) for p in training], sel].to_numpy().mean() for d in donors}
                chosen = max(generalist, key=generalist.get)
                split.append(table.loc[(name, target), assessment].mean()
                             - table.loc[(chosen, target), assessment].mean())
            comparators[f"gap_{name}_vs_sbs"] = float(np.mean(split))
        rows.append({"problem": target, "group": group_of[target], "family": family_of[target],
                     "sbs": sbs, "oracle_donor": oracle,
                     "oracle_donor_family": family_of[oracle.split("__", 1)[1]],
                     "hvn_sbs": mean.loc[sbs, target], "hvn_oracle": mean.loc[oracle, target],
                     "hvn_self_tuned": mean.loc[f"tuned__{target}", target], **comparators})
    donors_frame = pd.DataFrame(rows)
    donors_frame.to_csv(OUT / "g2_donors.csv", index=False)

    gaps = pd.read_csv(OUT / "g2_gaps.csv")
    gaps = gaps[gaps.evaluations == FINAL].groupby("group").gap_oracle_donor_vs_sbs.mean()
    rng = np.random.default_rng(20261020)
    values = gaps.to_numpy()
    boot = np.array([(rng.choice(values, size=values.size) >= X_THRESHOLD).mean() for _ in range(10_000)])
    in_family = donors_frame[(donors_frame.family == "LZ09/UF") & (donors_frame.oracle_donor_family == "LZ09/UF")]

    summary = {
        "sbs_counts": donors_frame.sbs.value_counts().to_dict(),
        "oracle_donor_counts": donors_frame.oracle_donor.value_counts().head(10).to_dict(),
        "lz09_uf_targets_with_lz09_uf_oracle_donor": f"{len(in_family)} of {int((donors_frame.family == 'LZ09/UF').sum())}",
        "fraction_bootstrap_over_groups": {"p05": float(np.quantile(boot, 0.05)),
                                           "p50": float(np.quantile(boot, 0.5)),
                                           "p95": float(np.quantile(boot, 0.95)),
                                           "share_at_or_above_0.25": float((boot >= 0.25).mean())},
        **{f"mean_gap_{a}_default_vs_sbs": float(donors_frame[f"gap_default__{a}_vs_sbs"].mean()) for a in others},
        **{f"problems_where_{a}_default_beats_sbs_by_0.01": donors_frame.loc[
            donors_frame[f"gap_default__{a}_vs_sbs"] >= X_THRESHOLD, "problem"].tolist() for a in others},
        "mean_hvn_over_problems": mean.mean(axis=1).sort_values(ascending=False).head(5).round(4).to_dict(),
        "mean_hvn_defaults": mean.loc[[f"default__{a}" for a in default_algorithms()]].mean(axis=1).round(4).to_dict(),
    }
    (OUT / "g2_secondary.json").write_text(json.dumps(summary, indent=2, default=float) + "\n")
    print(json.dumps(summary, indent=2, default=float))
    print(donors_frame[["problem", "sbs", "oracle_donor", "hvn_sbs", "hvn_oracle", "hvn_self_tuned"]]
          .sort_values("hvn_oracle", ascending=False).round(3).head(14).to_string(index=False))


if __name__ == "__main__":
    main()
