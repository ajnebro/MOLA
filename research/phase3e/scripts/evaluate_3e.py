"""Phase 3e performance matrix: every tuned configuration (and Evolver's default NSGA-II) on every
development problem, in jMetal, with the evaluation seeds of phase 3 (5001-5010).

Each run: NSGA-II from Evolver's NSGAIIDouble.yaml, population 100, 20 000 evaluations (Evolver
checks termination once per generation, so a run can overshoot by up to one offspring batch), on
the problem's jMetal implementation. The non-dominated front of the result is kept, as
MATRIX/<config>__<problem>.npz with keys s<seed>_e20000, the layout phase 3's analysis reads.

WORKERS threads each own one RunWorker JVM; pairs already on disk are skipped (resumable).

Run on NicoVM:  MOLA_PHASE3E_MATRIX=~/mola-phase3e/matrix/fronts python evaluate_3e.py
"""

import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import moocore
import numpy as np

from catalogue_3e import SPECS
from jworker import DEFAULT, PHASE3E, JWorker, command_line

import common

SEEDS = tuple(range(5001, 5011))
BUDGET = 20_000
WORKERS = int(os.environ.get("PHASE3E_WORKERS", 31))
MATRIX = Path(os.environ.get("MOLA_PHASE3E_MATRIX", Path.home() / "mola-phase3e" / "matrix" / "fronts"))
_local = threading.local()


def _worker() -> JWorker:
    if not hasattr(_local, "worker"):
        _local.worker = JWorker()
    return _local.worker


def _evaluate(config_id: str, config: str, problem: str) -> str:
    worker = _worker()
    n_obj = 2
    arrays = {}
    for seed in SEEDS:
        front = worker.run(SPECS[problem], seed, BUDGET, config, n_obj)
        arrays[f"s{seed}_e{BUDGET}"] = front[moocore.is_nondominated(front, keep_weakly=False)]
    np.savez_compressed(MATRIX / f"{config_id}__{problem}.npz", **arrays)
    return f"{config_id}__{problem}"


def main() -> None:
    MATRIX.mkdir(parents=True, exist_ok=True)
    tuned = json.loads((PHASE3E / "data" / "tuned_configs.json").read_text())
    problems = common.pilot_problems()
    configs = {f"tuned__{p}": tuned[p]["config"] for p in problems}
    configs["default__nsgaii"] = command_line(DEFAULT)
    pending = [(c, line, p) for c, line in configs.items() for p in problems
               if not (MATRIX / f"{c}__{p}.npz").exists()]
    print(f"{len(pending)} config-problem pairs pending", flush=True)
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(_evaluate, *task) for task in pending]
        for i, future in enumerate(as_completed(futures)):
            future.result()
            if i % 100 == 0 or i == len(futures) - 1:
                print(f"{i + 1}/{len(futures)} pairs, {time.perf_counter() - start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
