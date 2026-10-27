"""Phase 3c, amendment 1 (preregistration.md section 8): the random-configuration reference.

Phase 3's 37 random configurations of the invariant space (phase3/data/random_configs.json), run
on the 165 bbob-biobj problems (MATRIX/random__NN__<problem>.npz, seeds 5001-5010, 20 000
evaluations). Their HVn uses the matrix's normalization (union of the final fronts of the 64 matrix
configurations), so they do not change any other value.

Reported per split, next to the methods of data/transfer_long.csv:
- the mean and the median over the random configurations;
- the share of random configurations that lose more than 0.10 against the split's oracle donor.

Run locally after analyze_3c.py:  MOLA_PHASE3C_MATRIX=... python research/phase3c/scripts/random_configs_3c.py
Writes data/random_configs_hvn.csv and data/random_configs_summary.json.
"""

import json

import moocore
import numpy as np
import pandas as pd
from analyze_3c import DATA, DEFAULTS, FINAL, GENERALISTS, MATRIX, METHODS, REFERENCE, SEEDS, _hv

HERE_PHASE3 = DATA.parents[1] / "phase3" / "data"


def main() -> None:
    catalogue = json.loads((DATA / "catalogue.json").read_text())
    bounds = json.loads((DATA / "tuning_bounds.json").read_text())
    random_ids = list(json.loads((HERE_PHASE3 / "random_configs.json").read_text()))
    matrix_configs = [f"tuned__f{f:02d}" for f in range(1, 56)] + GENERALISTS + DEFAULTS
    reference = np.full(2, REFERENCE)
    rows = []
    for q in catalogue:
        ideal = np.asarray(bounds[q]["ideal"])
        span = np.asarray(bounds[q]["nadir"]) - ideal
        union = np.vstack(
            [
                np.load(MATRIX / f"{c}__{q}.npz")[f"s{s}_e{FINAL}"]
                for c in matrix_configs
                for s in SEEDS
            ]
        )
        best = _hv(
            (union[moocore.is_nondominated(union, keep_weakly=False)] - ideal) / span, reference
        )
        for c in random_ids:
            fronts = np.load(MATRIX / f"{c}__{q}.npz")
            rows.append(
                {
                    "config": c,
                    "problem": q,
                    "hvn": float(
                        np.mean(
                            [
                                _hv((fronts[f"s{s}_e{FINAL}"] - ideal) / span, reference) / best
                                for s in SEEDS
                            ]
                        )
                    ),
                }
            )
    hvn = pd.DataFrame(rows)
    hvn.to_csv(DATA / "random_configs_hvn.csv", index=False)
    per_problem = hvn.pivot(index="problem", columns="config", values="hvn")

    long = pd.read_csv(DATA / "transfer_long.csv")
    targets = long.groupby(["split", "unit", "target", "function"])[METHODS].mean().reset_index()
    targets["random_space_mean"] = per_problem.mean(axis=1).loc[targets.target].to_numpy()
    targets["random_space_median"] = per_problem.median(axis=1).loc[targets.target].to_numpy()
    losing = per_problem.loc[targets.target].rsub(targets["oracle"].to_numpy(), axis=0) > 0.10
    targets["random_space_share_losing_0.10"] = losing.mean(axis=1).to_numpy()
    columns = [
        "random_space_mean",
        "random_space_median",
        "random_space_share_losing_0.10",
    ] + METHODS
    summary = {
        split: x.groupby("function")[columns].mean().mean().round(4).to_dict()
        for split, x in targets.groupby("split")
    }
    (DATA / "random_configs_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(pd.DataFrame(summary).round(3).to_string())


if __name__ == "__main__":
    main()
