"""Phase 4b (tier 2, D13): the warm starts of irace for the 24 non-saturated development problems.

For every problem Q outside the easy stratum (phase3/data/strata.csv), with the LOGO training set
of phase 3 (every development problem outside Q's formulation group):
- for each of Q's 5 samples, knn_selector's choice: the training configuration c*_P with the best
  mean HVn over the 3 training problems nearest to the sample (policy.scaled, robust z, Euclidean);
- the warm start is the configuration chosen by most samples (ties: the best mean HVn over the
  union of the samples' 3 nearest problems);
- d_units: the median over the 5 samples of the distance to the nearest training mean, in noise
  units (policy.distance_and_s1);
- the irace seed is 8300 + the problem's index in common.pilot_problems() (phase 3 used 8000 +).
The initial configurations of the warm run are the warm start and default NSGA-II, written in
irace's configurations-file format (data/initial/<problem>.txt).

Uses only phase 3's training matrix (the configurations' HVn on training problems), never Q's own
tuning. Run locally:  MOLA_PHASE3_MATRIX=... python research/phase4b/scripts/make_warm_starts.py
Writes data/warm_start_tasks.json and data/initial/*.txt.
"""

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase3" / "scripts"))
sys.path.insert(0, str(HERE.parents[1] / "phase4" / "scripts"))

import analyze_transfer as at  # noqa: E402
from policy import distance_and_s1, scaled  # noqa: E402

DATA = HERE.parent / "data"
PHASE3_IRACE = HERE.parents[1] / "phase3" / "irace"
SEED_BASE, K = 8300, 3


def irace_line(config: dict, header: list[str]) -> str:
    def text(v):
        if isinstance(v, float) and v.is_integer() and v not in (0.0, 1.0):
            return str(int(v))
        return str(v)

    return " ".join(text(config[p]) if p in config else "NA" for p in header)


def main() -> None:
    problems = at.pilot_problems()
    group, _ = at.groups_and_families(problems)
    samples = pd.read_csv(at.PRIMARY_FEATURES)
    ctx = at.Context(
        problems,
        samples,
        pd.read_csv(at.RAW_OBJECTIVE_FEATURES),
        at.metadata(problems),
        at.hvn_matrix(problems),
    )
    strata = pd.read_csv(at.DATA_DIR / "strata.csv").set_index("target")["stratum"]
    tuned = json.loads((at.DATA_DIR / "tuned_configs.json").read_text())
    default_lines = (PHASE3_IRACE / "default.txt").read_text().splitlines()
    header = default_lines[0].split()

    tasks = {}
    (DATA / "initial").mkdir(parents=True, exist_ok=True)
    for q, problem in enumerate(problems):
        if strata[problem] == "easy":
            continue
        train = np.array([i for i, p in enumerate(problems) if group[p] != group[problem]])
        within = ctx.score[np.ix_(train, train)]  # within[a, b]: c*_{train[a]} on train[b]
        picks, near_union, distances = [], set(), []
        for row in np.flatnonzero(ctx.sample_problem == q):
            _, _, means, query = scaled(ctx.sample_values, ctx.sample_problem, train, row)
            nearest = np.argsort(np.linalg.norm(means - query, axis=1), kind="stable")[:K]
            picks.append(int(np.argmax(within[:, nearest].mean(axis=1))))
            near_union.update(nearest.tolist())
            distances.append(
                distance_and_s1(ctx.sample_values, ctx.sample_problem, train, row)["d_units"]
            )
        counts = Counter(picks)
        top = max(counts.values())
        tied = [c for c, n in counts.items() if n == top]
        union = sorted(near_union)
        chosen = max(tied, key=lambda c: within[c, union].mean())
        donor = problems[train[chosen]]
        config = tuned[donor]["config"]
        (DATA / "initial" / f"{problem}.txt").write_text(
            "\n".join([default_lines[0], irace_line(config, header), default_lines[1]]) + "\n",
            newline="\n",  # irace reads these on Linux: no CRLF
        )
        tasks[problem] = {
            "seed": SEED_BASE + q,
            "stratum": strata[problem],
            "warm_donor": donor,
            "votes": int(top),
            "d_units_median": round(float(np.median(distances)), 4),
            "warm_config": config,
        }
    (DATA / "warm_start_tasks.json").write_text(json.dumps(tasks, indent=2) + "\n")
    print(len(tasks), "problems")
    for p, v in tasks.items():
        print(
            f"{p:14s} {v['stratum']:12s} donor={v['warm_donor']:14s} votes={v['votes']} "
            f"d={v['d_units_median']:.2f}"
        )


if __name__ == "__main__":
    main()
