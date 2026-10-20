"""Phase 2, stage C: run every portfolio configuration on every pilot problem.

Configurations: the 37 tuned c*_P (data/tuned_configs.json), NSGA-II's textbook default, and
VAMOS's MOEA/D and SMS-EMOA defaults (population 100) as untuned comparators. Each runs on each of
the 37 pilot problems with evaluation seeds 2001-2005 and 20 000 evaluations, keeping the
non-dominated front of the population at 5 000, 10 000 and 20 000 evaluations.

Fronts go to RAW/fronts/<config>__<problem>.npz (one file per pair, so the stage resumes where it
stopped); run times to data/evaluation_runs.csv.

Run:  python research/phase2/scripts/evaluate_pilot.py
"""

import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from common import DATA, RAW, pilot_problems
from runs import CHECKPOINTS, run

BUDGET = 20_000
EVALUATION_SEEDS = (2001, 2002, 2003, 2004, 2005)
WORKERS = int(os.environ.get("PHASE2_WORKERS", 8))
FRONTS = RAW / "fronts"


def portfolio() -> dict[str, tuple[str, dict | None]]:
    """config id -> (algorithm, NSGA-II assignment or None for that algorithm's defaults)."""
    tuned = json.loads(Path(os.environ.get("PHASE2_TUNED", DATA / "tuned_configs.json")).read_text())
    configs = {f"tuned__{p}": ("nsgaii", tuned[p]["config"]) for p in pilot_problems()}
    if os.environ.get("PHASE2_WITH_DEFAULTS", "1") == "0":  # phase 2b arms reuse the defaults
        return configs
    configs["default__nsgaii"] = ("nsgaii", None)
    configs["default__moead"] = ("moead", None)
    configs["default__smsemoa"] = ("smsemoa", None)
    return configs


def _evaluate(config_id: str, algorithm: str, assignment, problem: str) -> list[dict]:
    path = FRONTS / f"{config_id}__{problem}.npz"
    arrays, rows = {}, []
    for seed in EVALUATION_SEEDS:
        result = run(problem, assignment, BUDGET, seed, algorithm=algorithm)
        for checkpoint in CHECKPOINTS:
            arrays[f"s{seed}_e{checkpoint}"] = result["fronts"][checkpoint]
        rows.append({"config": config_id, "problem": problem, "seed": seed,
                     "seconds": result["seconds"], "evaluations": result["evaluations"]})
    np.savez_compressed(path, **arrays)
    return rows


def main() -> None:
    FRONTS.mkdir(parents=True, exist_ok=True)
    configs = portfolio()
    runs_csv = Path(os.environ.get("PHASE2_RUNS", DATA / "evaluation_runs.csv"))
    done = pd.read_csv(runs_csv) if runs_csv.exists() else pd.DataFrame()
    pending = [(cid, alg, a, p) for cid, (alg, a) in configs.items() for p in pilot_problems()
               if not (FRONTS / f"{cid}__{p}.npz").exists()]
    print(f"{len(pending)} config-problem pairs pending", flush=True)
    start, rows = time.perf_counter(), []
    for i, batch in enumerate(Parallel(n_jobs=WORKERS, return_as="generator_unordered")(
            delayed(_evaluate)(*task) for task in pending)):
        rows += batch
        if i % 50 == 0 or i == len(pending) - 1:
            pd.concat([done, pd.DataFrame(rows)]).to_csv(runs_csv, index=False)
            print(f"{i + 1}/{len(pending)} pairs, {time.perf_counter() - start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
