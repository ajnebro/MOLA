"""Phase 3, descriptive analyses adopted from the external review (D12: C9, C10, C11; 2026-11-02).

C9  Unseen family or hard problem? Under LOFO the left-out family and the hard stratum are
    collinear (6 of the 7 hard problems are LZ09/UF). For every target, the LOFO penalty is
    HVn under LOGO minus HVn under LOFO (same target, same method); it is reported by stratum and by
    family. A penalty inside the easy and intermediate strata is a family effect, not difficulty.
    Also LOFO by fold.
C10 Tuning noise floor: the targets whose own c*_Q is more than 0.01 below the best donor, i.e.
    where one irace run left value on the table.
C11 RQ7 Mantel tests again (landscape distance against behaviour and mutual transfer loss):
    without the easy stratum, and with the permutations restricted to within families
    (9 999 permutations, seed 20261102).

Run locally:  MOLA_PHASE3_MATRIX=... python research/phase3/scripts/review_descriptives.py
Writes data/review_descriptives.json.
"""

import json

import analyze_transfer as at
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

METHODS = ["sbs", "knn_selector", "landscape_1nn", "metadata_1nn", "default", "oracle"]
PERMUTATIONS, SEED = 9999, 20261102


def mantel(a, b, pairs, rng, blocks=None):
    i, j = pairs
    observed = spearmanr(a[i, j], b[i, j]).statistic
    n, count = len(a), 0
    for _ in range(PERMUTATIONS):
        if blocks is None:
            p = rng.permutation(n)
        else:
            p = np.arange(n)
            for members in blocks:
                p[members] = rng.permutation(members)
        count += spearmanr(a[i, j], b[p][:, p][i, j]).statistic >= observed
    return {
        "rho": round(float(observed), 3),
        "p": round((count + 1) / (PERMUTATIONS + 1), 4),
        "pairs": int(len(i)),
    }


def main() -> None:
    problems = at.pilot_problems()
    _, family = at.groups_and_families(problems)
    strata = pd.read_csv(at.DATA_DIR / "strata.csv").set_index("target")["stratum"]
    long = pd.read_csv(at.DATA_DIR / "transfer_long.csv")
    per_target = long.groupby(["split", "target"])[METHODS + ["self"]].mean()
    result = {"note": "Descriptive (D12: C9, C10, C11)."}

    # C9
    logo, lofo = per_target.loc["LOGO"], per_target.loc["LOFO"]
    penalty = (logo[METHODS] - lofo[METHODS]).assign(
        stratum=strata.reindex(logo.index), family=pd.Series(family).reindex(logo.index)
    )
    result["c9_lofo_penalty_by_stratum"] = (
        penalty.groupby("stratum")[["knn_selector", "landscape_1nn", "sbs"]]
        .mean()
        .round(4)
        .assign(targets=penalty.groupby("stratum").size())
        .to_dict("index")
    )
    result["c9_lofo_penalty_by_family"] = (
        penalty.groupby("family")[["knn_selector", "landscape_1nn", "sbs"]]
        .mean()
        .round(4)
        .assign(targets=penalty.groupby("family").size())
        .to_dict("index")
    )
    result["c9_strata_by_family"] = pd.crosstab(
        pd.Series(family).reindex(logo.index), strata.reindex(logo.index)
    ).to_dict("index")
    lofo_rows = long[long.split == "LOFO"]
    result["c9_lofo_by_fold"] = lofo_rows.groupby("unit")[METHODS].mean().round(4).to_dict("index")

    # C10
    floor = logo[logo["self"] + 0.01 < logo["oracle"]][["self", "oracle"]]
    result["c10_tuning_noise_floor"] = {
        "targets": int(len(floor)),
        "cases": floor.assign(gap=floor["oracle"] - floor["self"]).round(4).to_dict("index"),
    }

    # C11
    samples = pd.read_csv(at.PRIMARY_FEATURES)
    ctx = at.Context(
        problems,
        samples,
        pd.read_csv(at.RAW_OBJECTIVE_FEATURES),
        at.metadata(problems),
        at.hvn_matrix(problems),
    )
    values = ctx.means[:, np.isfinite(ctx.means).all(axis=0)]
    q75, median, q25 = np.percentile(values, [75, 50, 25], axis=0)
    keep = (q75 - q25) > 0
    z = (values[:, keep] - median[keep]) / (q75 - q25)[keep]
    landscape = np.linalg.norm(z[:, None] - z[None], axis=2)
    S = ctx.score
    behaviour = 1 - spearmanr(S, axis=1).statistic
    loss = np.diag(S)[None, :] - S
    mutual = (loss + loss.T) / 2
    n = len(problems)
    upper = np.triu_indices(n, k=1)
    hard_or_mid = np.array([strata[p] != "easy" for p in problems])
    keep_pairs = hard_or_mid[upper[0]] & hard_or_mid[upper[1]]
    non_easy = (upper[0][keep_pairs], upper[1][keep_pairs])
    families = sorted(set(family.values()))
    blocks = [np.array([k for k, p in enumerate(problems) if family[p] == f]) for f in families]
    rng = np.random.default_rng(SEED)
    result["c11_mantel_landscape"] = {
        name: {
            "non_easy_pairs": mantel(landscape, d, non_easy, rng),
            "within_family_permutations": mantel(landscape, d, upper, rng, blocks),
        }
        for name, d in [("behaviour", behaviour), ("mutual_transfer_loss", mutual)]
    }
    (at.DATA_DIR / "review_descriptives.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
