"""Phase 3c characterization: MOLA features of the 165 bbob-biobj problems.

Five independent Latin hypercube samples per problem (seeds 1001-1005), n = 200 * D = 2000 over
the search box [-5, 5]^10, evaluated with cocoex. MOLA 0.4.0 with geometry `bound`, k = D,
objective scaling `sample` (primary) and `raw` (secondary), as in phase 3.

Run locally:  python research/phase3c/scripts/characterize_3c.py
Writes data/features_sample_scaled.csv and data/features_raw_objectives.csv, with the columns of
phase 3's tables.
"""

import json
import sys
import time
from pathlib import Path

import pandas as pd
from joblib import Parallel, delayed

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))

from common import sample_problem  # noqa: E402

DATA = HERE.parent / "data"
LHS_SEEDS = (1001, 1002, 1003, 1004, 1005)
WORKERS = 8


def _characterize(problem: str, seed: int) -> list[dict]:
    from mola.characterize import characterize_report
    from mola.ranking import rank_solutions

    sample, evaluation_seconds = sample_problem(problem, seed=seed)
    rows = []
    for scaling in ("sample", "raw"):
        start = time.perf_counter()
        report = characterize_report(sample, objective_scaling=scaling)
        rows.append(
            {
                "problem": problem,
                "seed": seed,
                "n": sample.size,
                "D": sample.number_of_variables,
                "M": sample.number_of_objectives,
                "geometry": report.provenance.geometry,
                "k": report.provenance.neighbours,
                "nd_count": int(rank_solutions(sample.objectives).nondominated.size),
                "evaluation_seconds": evaluation_seconds,
                "characterization_seconds": time.perf_counter() - start,
                "undefined": json.dumps(report.causes),
                "objective_scaling": report.provenance.objective_scaling,
                "mola_version": report.provenance.mola_version,
                **report.features,
            }
        )
    return rows


def main() -> None:
    problems = list(json.loads((DATA / "catalogue.json").read_text()))
    batches = Parallel(n_jobs=WORKERS)(
        delayed(_characterize)(p, s) for p in problems for s in LHS_SEEDS
    )
    frame = pd.DataFrame([row for batch in batches for row in batch])
    frame[frame.objective_scaling == "sample"].to_csv(
        DATA / "features_sample_scaled.csv", index=False
    )
    frame[frame.objective_scaling == "raw"].to_csv(
        DATA / "features_raw_objectives.csv", index=False
    )
    print(f"{len(frame) // 2} characterizations per profile")


if __name__ == "__main__":
    main()
