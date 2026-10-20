"""Phase 3 amendment: the stage A characterizations again, with objectives scaled per sample.

Same 37 development problems and LHS seeds (1001-1005) as phase2/data/pilot_features.csv, hence
the same samples (VAMOS evaluation is deterministic), characterized by MOLA with geometry `bound`,
k = D and objective scaling `sample` (each objective min-max scaled over its sample).

Run locally:  python research/phase3/scripts/characterize_sample_scaled.py
Writes data/features_sample_scaled.csv with the columns of pilot_features.csv.
"""

import json
import sys
import time
from pathlib import Path

import pandas as pd
from joblib import Parallel, delayed

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))

from characterize_pilot import LHS_SEEDS, WORKERS  # noqa: E402
from common import pilot_problems, sample_problem  # noqa: E402

PHASE3 = HERE.parent


def _characterize(problem: str, seed: int) -> dict:
    from mola.characterize import characterize_report
    from mola.ranking import rank_solutions

    sample, evaluation_seconds = sample_problem(problem, seed=seed)
    start = time.perf_counter()
    report = characterize_report(sample, objective_scaling="sample")
    return {
        "problem": problem, "seed": seed, "n": sample.size, "D": sample.number_of_variables,
        "M": sample.number_of_objectives, "geometry": report.provenance.geometry,
        "k": report.provenance.neighbours, "nd_count": int(rank_solutions(sample.objectives).nondominated.size),
        "evaluation_seconds": evaluation_seconds,
        "characterization_seconds": time.perf_counter() - start,
        "undefined": json.dumps(report.causes),
        "objective_scaling": report.provenance.objective_scaling,
        "mola_version": report.provenance.mola_version, **report.features,
    }


def main() -> None:
    rows = Parallel(n_jobs=WORKERS)(delayed(_characterize)(p, s) for p in pilot_problems() for s in LHS_SEEDS)
    frame = pd.DataFrame(rows)
    (PHASE3 / "data").mkdir(parents=True, exist_ok=True)
    frame.to_csv(PHASE3 / "data" / "features_sample_scaled.csv", index=False)
    print(f"{len(frame)} characterizations; objective scaling {frame.objective_scaling.unique()}")


if __name__ == "__main__":
    main()
