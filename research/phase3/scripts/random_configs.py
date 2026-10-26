"""Phase 3, post hoc reference (not pre-registered; requested by the user on 2026-10-26):
configurations drawn at random from the same invariant NSGA-II space that irace searched.

Question. The `random` donor of analyze_transfer.py picks among the irace-tuned c*_P, each of them
good on at least one problem. How good is a configuration drawn at random from the space itself?

Protocol, fixed before running:
- N_CONFIGS = 37 configurations drawn with `runs.invariant_nsgaii_space().sample(rng)`,
  rng = numpy.random.default_rng(SEED). That is VAMOS's sampler: uniform over each parameter, on a
  log scale where the space says so, with conditional parameters drawn only when active. It is the
  space written to irace's parameters.txt.
- Each runs on the 37 development problems with the matrix's evaluation seeds (5001-5010) and
  20 000 evaluations, VAMOS 1.0.0 (0a8bbb0), numpy engine. Fronts are kept at 5 000, 10 000 and
  20 000 evaluations.
- HVn uses the matrix's normalization: true-front bounds, reference 1.1, divided by the HV of the
  union of the 40 matrix configurations' final fronts. The random configurations do not enter the
  union, so values stay comparable with phase 3 (and can exceed 1).
- Summary per target: the mean and the median over the random configurations (the expected and the
  typical random configuration). They are set against the random tuned donor, the SBS, default
  NSGA-II and the oracle donor of the LOGO split, and against losses to that oracle.

Subcommands:
  sample    (local)   -> data/random_configs.json
  evaluate  (NicoVM)  -> RANDOM_RAW/fronts/random__<k>__<problem>.npz (resumable)
  analyze   (local)   -> data/random_configs_hvn.csv, random_configs_by_target.csv,
                         random_configs_summary.json
"""

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))

PHASE3 = HERE.parent
DATA = PHASE3 / "data"
N_CONFIGS, SEED = 37, 20261026
SEEDS = tuple(range(5001, 5011))
BUDGET = 20_000
RANDOM_RAW = Path(os.environ.get("MOLA_RANDOM_RAW", Path.home() / "mola-phase3" / "random_configs"))
WORKERS = int(os.environ.get("PHASE2_WORKERS", 31))


def sample() -> None:
    from runs import invariant_nsgaii_space

    space = invariant_nsgaii_space()
    rng = np.random.default_rng(SEED)
    configs = {f"random__{k:02d}": space.sample(rng) for k in range(N_CONFIGS)}
    clean = {
        k: {p: (v.item() if hasattr(v, "item") else v) for p, v in c.items()}
        for k, c in configs.items()
    }
    (DATA / "random_configs.json").write_text(json.dumps(clean, indent=2) + "\n")
    print(f"{len(clean)} configurations -> {DATA / 'random_configs.json'}")


def _evaluate(config_id: str, assignment: dict, problem: str) -> list[dict]:
    from runs import CHECKPOINTS, run

    arrays, rows = {}, []
    for seed in SEEDS:
        result = run(problem, assignment, BUDGET, seed)
        for checkpoint in CHECKPOINTS:
            arrays[f"s{seed}_e{checkpoint}"] = result["fronts"][checkpoint]
        rows.append(
            {
                "config": config_id,
                "problem": problem,
                "seed": seed,
                "seconds": result["seconds"],
                "evaluations": result["evaluations"],
            }
        )
    np.savez_compressed(RANDOM_RAW / "fronts" / f"{config_id}__{problem}.npz", **arrays)
    return rows


def evaluate() -> None:
    import pandas as pd
    from common import pilot_problems
    from joblib import Parallel, delayed

    (RANDOM_RAW / "fronts").mkdir(parents=True, exist_ok=True)
    configs = json.loads((DATA / "random_configs.json").read_text())
    pending = [
        (c, a, p)
        for c, a in configs.items()
        for p in pilot_problems()
        if not (RANDOM_RAW / "fronts" / f"{c}__{p}.npz").exists()
    ]
    print(f"{len(pending)} config-problem pairs pending", flush=True)
    runs_csv = RANDOM_RAW / "evaluation_runs.csv"
    done = pd.read_csv(runs_csv) if runs_csv.exists() else pd.DataFrame()
    start, rows = time.perf_counter(), []
    for i, batch in enumerate(
        Parallel(n_jobs=WORKERS, return_as="generator_unordered")(
            delayed(_evaluate)(*task) for task in pending
        )
    ):
        rows += batch
        if i % 50 == 0 or i == len(pending) - 1:
            pd.concat([done, pd.DataFrame(rows)]).to_csv(runs_csv, index=False)
            print(f"{i + 1}/{len(pending)} pairs, {time.perf_counter() - start:.0f}s", flush=True)


def analyze() -> None:
    import analyze_transfer as at
    import moocore
    import pandas as pd

    problems = at.pilot_problems()
    bounds = json.loads((DATA / "tuning_bounds.json").read_text())
    matrix_configs = [f"tuned__{p}" for p in problems] + list(at.DEFAULTS)
    configs = json.loads((DATA / "random_configs.json").read_text())
    reference = np.full(2, at.REFERENCE)
    rows = []
    for problem in problems:
        ideal = np.asarray(bounds[problem]["ideal"])
        span = np.asarray(bounds[problem]["nadir"]) - ideal

        def hv(front, ideal=ideal, span=span):
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
        for c in configs:
            fronts = np.load(RANDOM_RAW / "fronts" / f"{c}__{problem}.npz")
            rows.append(
                {
                    "config": c,
                    "problem": problem,
                    "hvn": float(np.mean([hv(fronts[f"s{s}_e{BUDGET}"]) / best for s in SEEDS])),
                }
            )
    hvn = pd.DataFrame(rows)
    hvn.to_csv(DATA / "random_configs_hvn.csv", index=False)

    long = pd.read_csv(DATA / "transfer_long.csv")
    logo = (
        long[long.split == "LOGO"]
        .groupby("target")[["random", "sbs", "default", "oracle", "landscape_1nn"]]
        .mean()
    )
    space = hvn.groupby("problem").hvn.agg(["mean", "median", "min", "max"])
    space.columns = [f"space_{c}" for c in space.columns]
    table = logo.join(space)
    loss = pd.DataFrame(
        {
            "random_space_config": table["oracle"] - table["space_mean"],
            "random_tuned_donor": table["oracle"] - table["random"],
            "landscape_1nn": table["oracle"] - table["landscape_1nn"],
            "default": table["oracle"] - table["default"],
            "sbs": table["oracle"] - table["sbs"],
        }
    )
    per_config = hvn.pivot(index="problem", columns="config", values="hvn")
    per_config_loss = per_config.rsub(table["oracle"], axis=0)
    summary = {
        "note": "Post hoc, not pre-registered. Mean over the 37 targets; LOGO references.",
        "mean_hvn": {
            "random_space_config_mean": float(table.space_mean.mean()),
            "random_space_config_median": float(table.space_median.mean()),
            "random_tuned_donor": float(table.random.mean()),
            "default_nsgaii": float(table.default.mean()),
            "sbs": float(table.sbs.mean()),
            "landscape_1nn": float(table.landscape_1nn.mean()),
            "oracle": float(table.oracle.mean()),
        },
        "mean_loss_vs_oracle": loss.mean().round(4).to_dict(),
        "share_of_random_space_configs_losing_more_than_0.10": float(
            (per_config_loss > 0.10).to_numpy().mean()
        ),
        "best_random_space_config_mean_hvn": float(per_config.mean().max()),
        "random_space_configs_beating_default_on_average": int(
            (per_config.mean() > table["default"].mean()).sum()
        ),
        "targets_where_random_space_mean_beats_random_tuned_donor": int(
            (table.space_mean > table.random).sum()
        ),
    }
    table.round(4).to_csv(DATA / "random_configs_by_target.csv")
    (DATA / "random_configs_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(table.round(3).sort_values("oracle").to_string())


if __name__ == "__main__":
    {"sample": sample, "evaluate": evaluate, "analyze": analyze}[sys.argv[1]]()
