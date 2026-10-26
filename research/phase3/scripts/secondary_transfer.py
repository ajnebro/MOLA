"""Phase 3, secondary analyses of preregistration.md section 7 (descriptive), after G3.

From data/transfer_long.csv (written by analyze_transfer.py):
- regret against the oracle donor and loss against the SBS, per method and split;
- the exploratory comparisons of section 7: knn_selector, loss_predictor and thesis_1nn (and
  landscape_1nn) against metadata_1nn and against the SBS, LOGO, one-sided Wilcoxon over groups,
  without multiplicity correction;
- per-group LOGO table: every method, the landscape donor and its distance rank in the sample;
- leakage: gain of landscape_1nn over the SBS by split (random minus LOGO, random minus LOFO);
- how often landscape_1nn picks the oracle donor, and how often it is at least as good as the SBS.

Run locally:  python research/phase3/scripts/secondary_transfer.py
Writes data/g3_secondary.json and data/g3_groups.csv. MOLA_TRANSFER_DIR as in analyze_transfer.py.
"""

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("MOLA_TRANSFER_DIR", HERE.parent)) / "data"
METHODS = [
    "sbs",
    "metadata_1nn",
    "random",
    "thesis_1nn",
    "landscape_1nn",
    "loss_predictor",
    "knn_selector",
    "landscape_1nn_raw_objectives",
    "oracle",
    "self",
    "default",
]
EXPLORATORY = [
    "landscape_1nn",
    "knn_selector",
    "loss_predictor",
    "thesis_1nn",
    "landscape_1nn_raw_objectives",
]
TIE = 1e-9


def _one_sided(a: pd.Series, b: pd.Series) -> dict:
    difference = a - b
    p = (
        float(wilcoxon(a, b, alternative="greater", zero_method="wilcox").pvalue)
        if (difference.abs() > TIE).any()
        else 1.0
    )
    return {
        "mean": float(difference.mean()),
        "median": float(difference.median()),
        "wins": int((difference > TIE).sum()),
        "losses": int((difference < -TIE).sum()),
        "ties": int((difference.abs() <= TIE).sum()),
        "p_greater": p,
    }


def main() -> None:
    long = pd.read_csv(DATA_DIR / "transfer_long.csv")
    per_target = long.groupby(["split", "unit", "target", "group"])[METHODS].mean().reset_index()
    logo_target = per_target[per_target.split == "LOGO"]
    logo = logo_target.groupby("group")[METHODS].mean()

    regret = {
        s: (
            per_target[per_target.split == s][METHODS]
            .rsub(per_target[per_target.split == s]["oracle"], axis=0)
            .mean()
            .round(4)
            .drop(["oracle"])
            .to_dict()
        )
        for s in ("LOGO", "LOFO", "random")
    }
    vs_sbs = {
        s: (
            per_target[per_target.split == s][METHODS]
            .sub(per_target[per_target.split == s]["sbs"], axis=0)
            .mean()
            .round(4)
            .drop(["sbs"])
            .to_dict()
        )
        for s in ("LOGO", "LOFO", "random")
    }
    comparisons = {
        m: {
            "vs_metadata_1nn": _one_sided(logo[m], logo["metadata_1nn"]),
            "vs_sbs": _one_sided(logo[m], logo["sbs"]),
        }
        for m in EXPLORATORY
    }

    gain = {
        s: float(
            (
                per_target[per_target.split == s]["landscape_1nn"]
                - per_target[per_target.split == s]["sbs"]
            ).mean()
        )
        for s in ("LOGO", "LOFO", "random")
    }

    logo_long = long[long.split == "LOGO"]
    picks_oracle = float(
        np.isclose(logo_long["landscape_1nn"], logo_long["oracle"], atol=TIE).mean()
    )
    at_least_sbs = float((logo_long["landscape_1nn"] >= logo_long["sbs"] - TIE).mean())
    donors = logo_long.groupby("target").landscape_donor.agg(
        lambda s: ", ".join(f"{d} ({n})" for d, n in s.value_counts().items())
    )

    table = logo.copy()
    table["landscape_minus_metadata"] = table["landscape_1nn"] - table["metadata_1nn"]
    table["landscape_minus_sbs"] = table["landscape_1nn"] - table["sbs"]
    table["oracle_minus_sbs"] = table["oracle"] - table["sbs"]
    members = logo_target.groupby("group").target.agg(lambda s: " ".join(sorted(s)))
    table["targets"] = members
    table["landscape_donors"] = [
        ", ".join(donors[t] for t in members[g].split()) for g in table.index
    ]
    table.sort_values("landscape_minus_metadata").round(4).to_csv(DATA_DIR / "g3_groups.csv")

    result = {
        "note": "Descriptive analyses of preregistration.md section 7; the exploratory p-values are not corrected for multiplicity.",
        "regret_vs_oracle_mean_over_targets": regret,
        "difference_vs_sbs_mean_over_targets": vs_sbs,
        "logo_exploratory_comparisons_over_groups": comparisons,
        "leakage_gain_landscape_vs_sbs": {
            **gain,
            "random_minus_logo": gain["random"] - gain["LOGO"],
            "random_minus_lofo": gain["random"] - gain["LOFO"],
        },
        "logo_landscape_picks_oracle_donor_share": picks_oracle,
        "logo_landscape_at_least_sbs_share": at_least_sbs,
        "largest_landscape_losses_vs_metadata": table.sort_values("landscape_minus_metadata")
        .head(5)[["landscape_1nn", "metadata_1nn", "sbs", "oracle", "landscape_donors"]]
        .round(4)
        .to_dict("index"),
        "largest_landscape_wins_vs_metadata": table.sort_values("landscape_minus_metadata")
        .tail(5)[["landscape_1nn", "metadata_1nn", "sbs", "oracle", "landscape_donors"]]
        .round(4)
        .to_dict("index"),
    }
    (DATA_DIR / "g3_secondary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
