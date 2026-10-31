"""Phase 3g: run the irace generalists on phase 3's 37 development problems.

Configurations: data/tuned_configs.json (collect_3g.py), as gen__<task without "gen_"> (gen__all,
gen__lofo_dtlz, ...). Each runs with the matrix's evaluation seeds (5001-5010) and 20 000
evaluations, VAMOS 1.0.0 (0a8bbb0), numpy engine, with fronts kept at 5 000, 10 000 and 20 000
evaluations, as in phase 3's matrix.

Output: RAW/fronts/<config>__<problem>.npz, resumable, with run times in RAW/evaluation_runs.csv.

Run on NicoVM:  MOLA_PHASE3G_RAW=~/mola-phase3g/matrix PHASE2_WORKERS=31 python evaluate_3g.py
"""

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))

DATA = HERE.parent / "data"
RAW = Path(os.environ.get("MOLA_PHASE3G_RAW", Path.home() / "mola-phase3g" / "matrix"))
SEEDS = tuple(range(5001, 5011))
BUDGET = 20_000
WORKERS = int(os.environ.get("PHASE2_WORKERS", 31))


def configurations() -> dict[str, dict]:
    tuned = json.loads((DATA / "tuned_configs.json").read_text())
    return {f"gen__{task[len('gen_') :]}": entry["config"] for task, entry in tuned.items()}


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
    np.savez_compressed(RAW / "fronts" / f"{config_id}__{problem}.npz", **arrays)
    return rows


def main() -> None:
    import pandas as pd
    from common import pilot_problems
    from joblib import Parallel, delayed

    (RAW / "fronts").mkdir(parents=True, exist_ok=True)
    configs = configurations()
    pending = [
        (c, a, p)
        for c, a in configs.items()
        for p in pilot_problems()
        if not (RAW / "fronts" / f"{c}__{p}.npz").exists()
    ]
    print(f"{len(configs)} configurations, {len(pending)} config-problem pairs pending", flush=True)
    runs_csv = RAW / "evaluation_runs.csv"
    done = pd.read_csv(runs_csv) if runs_csv.exists() else pd.DataFrame()
    start, rows = time.perf_counter(), []
    for i, batch in enumerate(
        Parallel(n_jobs=WORKERS, return_as="generator_unordered")(
            delayed(_evaluate)(*task) for task in pending
        )
    ):
        rows += batch
        if i % 20 == 0 or i == len(pending) - 1:
            pd.concat([done, pd.DataFrame(rows)]).to_csv(runs_csv, index=False)
            print(f"{i + 1}/{len(pending)} pairs, {time.perf_counter() - start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
