"""Phase 2, task 1: VAMOS run-time micro-benchmark on the 37 pilot problems (decision D2).

For every pilot problem, at 20 000 evaluations and seed 1:
- NSGA-II with its textbook default (population 100), with the anytime recorder attached;
- 8 configurations drawn from VAMOS's NSGA-II tuning space (the same 8 draws for every problem);
- MOEA/D and SMS-EMOA with VAMOS defaults (population 100), to price a more diverse portfolio.
Plus one MOLA characterization (n = 200 * D, seed 1, bound geometry) per problem.

Runs execute in WORKERS parallel single-threaded processes, so times include some contention;
they size the study, they are not a performance comparison.

Run:  python research/phase2/scripts/microbench.py   ->  data/microbench.csv
"""

import time

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from common import DATA, instantiate, pilot_problems, sample_problem
from runs import nsgaii_space, run

BUDGET = 20_000
SEED = 1
WORKERS = 8
SAMPLED_CONFIGS = 8


def _nsgaii_task(problem, label, assignment):
    result = run(problem, assignment, BUDGET, SEED)
    return {"problem": problem, "task": label, "seconds": result["seconds"],
            "evaluations": result["evaluations"], "front_size": len(result["fronts"][BUDGET])}


def _other_algorithm_task(problem, algorithm):
    import common  # noqa: F401
    from vamos import optimize

    start = time.perf_counter()
    result = optimize(instantiate(problem), algorithm=algorithm, max_evaluations=BUDGET,
                      pop_size=100, seed=SEED, engine="numpy")
    return {"problem": problem, "task": algorithm, "seconds": time.perf_counter() - start,
            "evaluations": int(result.data.get("evaluations", BUDGET)), "front_size": -1}


def _characterization_task(problem):
    from mola.characterize import characterize_report

    sample, evaluation_seconds = sample_problem(problem, seed=SEED)
    start = time.perf_counter()
    characterize_report(sample)
    return {"problem": problem, "task": "mola", "seconds": time.perf_counter() - start,
            "evaluations": sample.size, "front_size": -1, "evaluation_seconds": evaluation_seconds}


def main() -> None:
    problems = pilot_problems()
    rng = np.random.default_rng(2026)
    space = nsgaii_space()
    sampled = [space.sample(rng) for _ in range(SAMPLED_CONFIGS)]
    tasks = []
    for problem in problems:
        tasks.append(delayed(_nsgaii_task)(problem, "nsgaii_default", None))
        tasks += [delayed(_nsgaii_task)(problem, f"nsgaii_sample{i}", a) for i, a in enumerate(sampled)]
        tasks += [delayed(_other_algorithm_task)(problem, alg) for alg in ("moead", "smsemoa")]
        tasks.append(delayed(_characterization_task)(problem))
    start = time.perf_counter()
    rows = Parallel(n_jobs=WORKERS, verbose=0)(tasks)
    frame = pd.DataFrame(rows)
    DATA.mkdir(parents=True, exist_ok=True)
    frame.to_csv(DATA / "microbench.csv", index=False)
    pd.DataFrame(sampled).to_csv(DATA / "microbench_sampled_configs.csv", index=False)
    print(f"wall {time.perf_counter() - start:.0f}s")
    frame["kind"] = frame.task.str.replace(r"\d+$", "", regex=True)
    print(frame.groupby("kind").seconds.describe().round(2))


if __name__ == "__main__":
    main()
