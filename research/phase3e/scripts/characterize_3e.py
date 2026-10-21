"""Phase 3e stage A: characterize the jMetal implementations of the 37 development problems.

Same design as phase 2 and 3: scipy's scrambled LHS with seeds 1001-1005, n = 200 * D, scaled to
each problem's jMetal bounds, evaluated by jMetal through the RunWorker (EVAL). MOLA 0.4.0
characterizes every sample twice, with geometry `bound` and k = D: objective scaling `sample`
(the representation of every landscape method, as in phase 3's amendment 1) and `raw` (for the
secondary landscape_1nn_raw_objectives).

Run locally:  python research/phase3e/scripts/characterize_3e.py
Writes data/features_sample_scaled.csv and data/features_raw_objectives.csv.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import qmc

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))

import common  # noqa: E402
from catalogue_3e import SPECS  # noqa: E402
from jworker import PHASE3E, JWorker  # noqa: E402

LHS_SEEDS = (1001, 1002, 1003, 1004, 1005)


def _characterize(problem, seed, variables, objectives, lower, upper, scaling):
    from mola.characterize import characterize_report
    from mola.sample import Sample

    sample = Sample(problem=problem, variables=variables, objectives=objectives,
                    lower_bounds=lower, upper_bounds=upper, sampler="lhs", seed=seed)
    report = characterize_report(sample, objective_scaling=scaling)
    return {"problem": problem, "seed": seed, "n": sample.size, "D": sample.number_of_variables,
            "M": sample.number_of_objectives, "geometry": report.provenance.geometry,
            "k": report.provenance.neighbours, "undefined": json.dumps(report.causes),
            "objective_scaling": scaling, "mola_version": report.provenance.mola_version,
            **report.features}


def main() -> None:
    samples = []
    with JWorker() as worker:
        for problem in common.pilot_problems():
            spec = SPECS[problem]
            n, m, lower, upper = worker.info(spec)
            for seed in LHS_SEEDS:
                unit = qmc.LatinHypercube(d=n, scramble=True, seed=seed).random(200 * n)
                variables = qmc.scale(unit, lower, upper)
                objectives = worker.evaluate(spec, variables, m)
                samples.append((problem, seed, variables, objectives, lower, upper))
    for scaling, name in (("sample", "features_sample_scaled.csv"), ("raw", "features_raw_objectives.csv")):
        rows = Parallel(n_jobs=8)(delayed(_characterize)(*s, scaling) for s in samples)
        pd.DataFrame(rows).to_csv(PHASE3E / "data" / name, index=False)
        print(name, len(rows))


if __name__ == "__main__":
    main()
