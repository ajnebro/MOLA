"""Phase 2, stage A: characterize the 37 pilot problems with 5 independent LHS samples each.

MOLA 0.3.0, bound geometry, k = D, n = 200 * D, LHS seeds 1001-1005 (the characterization
stream). Every objective evaluation goes through the VAMOS implementation of the problem.

Run:  python research/phase2/scripts/characterize_pilot.py
Writes data/pilot_features.csv (one row per problem and seed: the 49 values, undefined causes,
|ND|, timings and evaluations).
"""

import json
import time

import pandas as pd
from joblib import Parallel, delayed

from common import DATA, pilot_problems, sample_problem

LHS_SEEDS = (1001, 1002, 1003, 1004, 1005)
WORKERS = 8


def _characterize(problem: str, seed: int) -> dict:
    from mola.characterize import characterize_report
    from mola.ranking import rank_solutions

    sample, evaluation_seconds = sample_problem(problem, seed=seed)
    start = time.perf_counter()
    report = characterize_report(sample)
    seconds = time.perf_counter() - start
    return {
        "problem": problem, "seed": seed, "n": sample.size, "D": sample.number_of_variables,
        "M": sample.number_of_objectives, "geometry": report.provenance.geometry,
        "k": report.provenance.neighbours, "nd_count": int(rank_solutions(sample.objectives).nondominated.size),
        "evaluation_seconds": evaluation_seconds, "characterization_seconds": seconds,
        "undefined": json.dumps(report.causes), **report.features,
    }


def main() -> None:
    tasks = [delayed(_characterize)(p, s) for p in pilot_problems() for s in LHS_SEEDS]
    start = time.perf_counter()
    rows = Parallel(n_jobs=WORKERS)(tasks)
    frame = pd.DataFrame(rows)
    DATA.mkdir(parents=True, exist_ok=True)
    frame.to_csv(DATA / "pilot_features.csv", index=False)
    print(f"{len(frame)} characterizations, wall {time.perf_counter() - start:.0f}s, "
          f"evaluations {frame.n.sum()}")


if __name__ == "__main__":
    main()
