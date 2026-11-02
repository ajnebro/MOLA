"""Phase 3r on NicoVM: collect the re-tuned elites and run them on the 37 development problems.

Collects the best final elite of each re-tuning (phase 2b's collector) into data/tuned_configs.json,
then runs each one as retuned__<problem> on every development problem with the matrix's seeds
(5001-5010) and 20 000 evaluations, keeping fronts at 5 000, 10 000 and 20 000 evaluations, as in
phase 3's matrix. Output: RAW/fronts/retuned__<tuned problem>__<problem>.npz (resumable).

Run on NicoVM:
    MOLA_PHASE3R_RUNS=~/mola-phase3r/irace MOLA_PHASE3R_RAW=~/mola-phase3r/matrix \
        PHASE2_WORKERS=31 python evaluate_3r.py
"""

import json
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = Path(os.environ.get("MOLA_PHASE3R_RUNS", Path.home() / "mola-phase3r" / "irace"))
os.environ["MOLA_PHASE2B_RUNS"] = str(RUNS)
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))
sys.path.insert(0, str(HERE.parents[1] / "phase2b" / "scripts"))

DATA = HERE.parent / "data"
RAW = Path(os.environ.get("MOLA_PHASE3R_RAW", Path.home() / "mola-phase3r" / "matrix"))
SEEDS = tuple(range(5001, 5011))
BUDGET = 20_000
WORKERS = int(os.environ.get("PHASE2_WORKERS", 31))


def _evaluate(config_id: str, assignment: dict, problem: str) -> None:
    from runs import CHECKPOINTS, run

    arrays = {}
    for seed in SEEDS:
        result = run(problem, assignment, BUDGET, seed)
        for checkpoint in CHECKPOINTS:
            arrays[f"s{seed}_e{checkpoint}"] = result["fronts"][checkpoint]
    np.savez_compressed(RAW / "fronts" / f"{config_id}__{problem}.npz", **arrays)


def main() -> None:
    from collect_irace import collect
    from common import pilot_problems
    from joblib import Parallel, delayed

    tasks = json.loads((DATA / "retune_tasks.json").read_text())
    tuned = {p: collect(p) for p in tasks}
    (DATA / "tuned_configs.json").write_text(json.dumps(tuned, indent=2) + "\n")
    (RAW / "fronts").mkdir(parents=True, exist_ok=True)
    pending = [
        (f"retuned__{p}", tuned[p]["config"], q)
        for p in tasks
        for q in pilot_problems()
        if not (RAW / "fronts" / f"retuned__{p}__{q}.npz").exists()
    ]
    print(f"{len(tuned)} elites, {len(pending)} config-problem pairs pending", flush=True)
    Parallel(n_jobs=WORKERS)(delayed(_evaluate)(*task) for task in pending)
    print("done", flush=True)


if __name__ == "__main__":
    main()
