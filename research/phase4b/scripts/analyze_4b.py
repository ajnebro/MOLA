"""Phase 4b pre-registered analysis (preregistration.md): the tier-2 threshold t2 (D13).

Per problem and arm (cold: phase 3's irace run from default NSGA-II; warm: this phase's run from
the warm start), the anytime quality HVn(n) is a step function of the experiments n:
- before the first iteration ends, the initial configuration (cold: default NSGA-II; warm: the
  warm start c*_donor), both already in phase 3's matrix;
- from the end of iteration i on, the best elite of iteration i (evaluate_4b.py).
HVn uses phase 3's matrix normalization (union of its 40 configurations' final fronts).

- target(Q) = HVn of the cold arm's final elite - 0.005;
- N_arm(Q) = the fewest experiments after which the arm's HVn(n) >= target (20 000 and censored
  when never reached);
- saving S(Q) = N_cold - N_warm;
- t2 = the largest d_units (warm_start_tasks.json) at which a decreasing isotonic regression of S
  on d_units is still >= 2 000 experiments (0 if nowhere; the largest observed d if everywhere);
- validation: leave one formulation group out over the 24 problems (t2 refitted without the group;
  the held-out problems are predicted worth warm-starting when d <= t2), with the accuracy against
  S >= 2 000 and the experiments a tiered policy would spend against always-cold and always-warm;
- uncertainty: a bootstrap over problems (2 000 resamples, seed 20261102), 95 % interval of t2.
Also the quality of both arms at n in {1 000, 2 000, 5 000, 10 000, 20 000}.

Run locally:
    MOLA_PHASE3_MATRIX=... MOLA_PHASE4B_RAW=... python research/phase4b/scripts/analyze_4b.py
Writes data/tier2_per_problem.csv and data/tier2_summary.json (MOLA_PHASE4B_OUT overrides).
"""

import json
import os
import sys
from pathlib import Path

import moocore
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase3" / "scripts"))

import analyze_transfer as at  # noqa: E402

DATA = HERE.parent / "data"
OUT = Path(os.environ.get("MOLA_PHASE4B_OUT", DATA))
RAW = Path(os.environ.get("MOLA_PHASE4B_RAW", r"C:\tmp\mola-phase4b\matrix"))
TOLERANCE, MIN_SAVING, BUDGET = 0.005, 2_000, 20_000
CHECKPOINTS = (1_000, 2_000, 5_000, 10_000, 20_000)
BOOTSTRAP, SEED = 2_000, 20261102


def elite_hvn(problems, elites: pd.DataFrame) -> dict:
    """(elite_key, problem) -> mean HVn over the seeds, with phase 3's matrix normalization."""
    bounds = json.loads((at.DATA_DIR / "tuning_bounds.json").read_text())
    matrix_configs = [f"tuned__{p}" for p in problems] + list(at.DEFAULTS)
    out = {}
    for problem, keys in elites.groupby("problem")["elite_key"]:
        ideal = np.asarray(bounds[problem]["ideal"])
        span = np.asarray(bounds[problem]["nadir"]) - ideal
        reference = np.full(len(ideal), at.REFERENCE)

        def hv(front, ideal=ideal, span=span, reference=reference):
            scaled = (front - ideal) / span
            scaled = scaled[np.all(scaled < reference, axis=1)]
            return float(moocore.hypervolume(scaled, ref=reference)) if len(scaled) else 0.0

        union = np.vstack(
            [
                np.load(at.MATRIX / f"{c}__{problem}.npz")[f"s{s}_e{at.FINAL}"]
                for c in matrix_configs
                for s in at.SEEDS
            ]
        )
        best = hv(union[moocore.is_nondominated(union, keep_weakly=False)])
        for key in set(keys):
            fronts = np.load(RAW / "fronts" / f"{key}__{problem}.npz")
            out[(key, problem)] = float(
                np.mean([hv(fronts[f"s{s}_e{BUDGET}"]) / best for s in at.SEEDS])
            )
    return out


def threshold(d: np.ndarray, saving: np.ndarray) -> float:
    if len(d) < 2:
        return 0.0
    fitted = IsotonicRegression(increasing=False).fit(d, saving).predict(d)
    ok = d[fitted >= MIN_SAVING]
    return float(ok.max()) if len(ok) else 0.0


def main() -> None:
    problems = at.pilot_problems()
    group, _ = at.groups_and_families(problems)
    tasks = json.loads((DATA / "warm_start_tasks.json").read_text())
    hvn = at.hvn_matrix(problems)
    elites = pd.read_csv(RAW / "anytime_elites.csv")
    values = elite_hvn(problems, elites)

    rows = []
    for problem, task in tasks.items():
        curves = {}
        for arm in ("cold", "warm"):
            start = (
                hvn[("default__nsgaii", problem)]
                if arm == "cold"
                else hvn[(f"tuned__{task['warm_donor']}", problem)]
            )
            steps = [(0, float(np.mean(start)))]
            x = elites[(elites.problem == problem) & (elites.arm == arm)].sort_values("iteration")
            steps += [(int(r.experiments), values[(r.elite_key, problem)]) for r in x.itertuples()]
            curves[arm] = steps
        target = curves["cold"][-1][1] - TOLERANCE

        def first_reach(steps, target=target):
            for n, value in steps:
                if value >= target:
                    return n, False
            return BUDGET, True

        def at_n(steps, n):
            return [v for m, v in steps if m <= n][-1]

        n_cold, censored_cold = first_reach(curves["cold"])
        n_warm, censored_warm = first_reach(curves["warm"])
        rows.append(
            {
                "problem": problem,
                "group": group[problem],
                "stratum": task["stratum"],
                "d_units": task["d_units_median"],
                "warm_donor": task["warm_donor"],
                "target": target,
                "n_cold": n_cold,
                "n_warm": n_warm,
                "censored_cold": censored_cold,
                "censored_warm": censored_warm,
                "saving": n_cold - n_warm,
                **{f"cold_{n}": at_n(curves["cold"], n) for n in CHECKPOINTS},
                **{f"warm_{n}": at_n(curves["warm"], n) for n in CHECKPOINTS},
            }
        )
    table = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    table.round(5).to_csv(OUT / "tier2_per_problem.csv", index=False)

    d, saving = table["d_units"].to_numpy(), table["saving"].to_numpy(float)
    t2 = threshold(d, saving)
    predictions = []
    for g in sorted(table["group"].unique()):
        inside = (table["group"] == g).to_numpy()
        t2_out = threshold(d[~inside], saving[~inside])
        for _, r in table[inside].iterrows():
            warm = r["d_units"] <= t2_out
            predictions.append(
                {
                    "problem": r["problem"],
                    "t2_without_group": t2_out,
                    "predicted_warm": bool(warm),
                    "actual_worth": bool(r["saving"] >= MIN_SAVING),
                    "spent_policy": r["n_warm"] if warm else r["n_cold"],
                }
            )
    validation = pd.DataFrame(predictions)
    rng = np.random.default_rng(SEED)
    boot = [
        threshold(d[i], saving[i])
        for i in (rng.integers(0, len(d), len(d)) for _ in range(BOOTSTRAP))
    ]
    summary = {
        "note": "Pre-registered, descriptive (no gate). Experiments are irace experiments.",
        "problems": int(len(table)),
        "t2_units": round(t2, 3),
        "t2_at_largest_observed_d": bool(t2 == d.max()),
        "t2_bootstrap_95": [
            round(float(np.percentile(boot, 2.5)), 3),
            round(float(np.percentile(boot, 97.5)), 3),
        ],
        "saving": {
            "median": float(np.median(saving)),
            "share_ge_2000": round(float((saving >= MIN_SAVING).mean()), 3),
            "censored_warm": int(table["censored_warm"].sum()),
        },
        "validation_logo": {
            "accuracy": round(
                float((validation.predicted_warm == validation.actual_worth).mean()), 3
            ),
            "experiments_policy": int(validation.spent_policy.sum()),
            "experiments_always_cold": int(table["n_cold"].sum()),
            "experiments_always_warm": int(table["n_warm"].sum()),
        },
        "mean_hvn_at": {
            str(n): {
                "cold": round(float(table[f"cold_{n}"].mean()), 4),
                "warm": round(float(table[f"warm_{n}"].mean()), 4),
            }
            for n in CHECKPOINTS
        },
    }
    (OUT / "tier2_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
