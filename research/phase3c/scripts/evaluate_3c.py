"""Phase 3c performance matrix: every configuration on every one of the 165 bbob-biobj problems.

Configurations:
- tuned__fNN: the 55 c*_P (P = bbob-biobj_fNN_i01_d10);
- gen__all and gen__g1-gen__g5: the generalists;
- default__nsgaii and default__moead: VAMOS 1.0.0 defaults;
- default__ibea: run separately with the repaired VAMOS (c4569f25) ahead on PYTHONPATH and
  PHASE3C_CONFIGS=ibea, as in phase 3.

Seeds 5001-5010 and 20 000 evaluations, with fronts kept at 5 000, 10 000 and 20 000 evaluations.
Output: RAW/fronts/<config>__<problem>.npz, resumable, with run times in RAW/evaluation_runs.csv.
PHASE3C_CONFIGS filters the kinds (comma list of tuned, gen, nsgaii, moead, ibea).

Run on NicoVM:  MOLA_PHASE3C_RAW=~/mola-phase3c/matrix PHASE2_WORKERS=31 python evaluate_3c.py
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
RAW = Path(os.environ.get("MOLA_PHASE3C_RAW", Path.home() / "mola-phase3c" / "matrix"))
SEEDS = tuple(range(5001, 5011))
BUDGET = 20_000
WORKERS = int(os.environ.get("PHASE2_WORKERS", 31))
KINDS = set(os.environ.get("PHASE3C_CONFIGS", "tuned,gen,nsgaii,moead").split(","))


def configurations() -> dict[str, tuple[str, dict | None]]:
    """Config id -> (algorithm, NSGA-II assignment or None for that algorithm's defaults)."""
    tuned = json.loads((DATA / "tuned_configs.json").read_text())
    configs = {}
    for task, entry in tuned.items():
        if task.startswith("f") and "tuned" in KINDS:
            configs[f"tuned__{task}"] = ("nsgaii", entry["config"])
        elif task.startswith("gen_") and "gen" in KINDS:
            configs[f"gen__{task[len('gen_') :]}"] = ("nsgaii", entry["config"])
    for algorithm in ("nsgaii", "moead", "ibea"):
        if algorithm in KINDS:
            configs[f"default__{algorithm}"] = (algorithm, None)
    return configs


def _evaluate(config_id: str, algorithm: str, assignment, problem: str) -> list[dict]:
    from runs import CHECKPOINTS, run

    arrays, rows = {}, []
    for seed in SEEDS:
        result = run(problem, assignment, BUDGET, seed, algorithm=algorithm)
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
    from joblib import Parallel, delayed

    (RAW / "fronts").mkdir(parents=True, exist_ok=True)
    problems = list(json.loads((DATA / "catalogue.json").read_text()))
    configs = configurations()
    pending = [
        (c, alg, a, p)
        for c, (alg, a) in configs.items()
        for p in problems
        if not (RAW / "fronts" / f"{c}__{p}.npz").exists()
    ]
    print(f"{len(configs)} configurations, {len(pending)} config-problem pairs pending", flush=True)
    runs_csv = RAW / f"evaluation_runs_{'_'.join(sorted(KINDS))}.csv"
    done = pd.read_csv(runs_csv) if runs_csv.exists() else pd.DataFrame()
    start, rows = time.perf_counter(), []
    for i, batch in enumerate(
        Parallel(n_jobs=WORKERS, return_as="generator_unordered")(
            delayed(_evaluate)(*task) for task in pending
        )
    ):
        rows += batch
        if i % 100 == 0 or i == len(pending) - 1:
            pd.concat([done, pd.DataFrame(rows)]).to_csv(runs_csv, index=False)
            print(f"{i + 1}/{len(pending)} pairs, {time.perf_counter() - start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
