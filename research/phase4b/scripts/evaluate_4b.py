"""Phase 4b on NicoVM: the anytime elites of the cold and warm irace runs, and their evaluation.

For every problem in data/warm_start_tasks.json and each arm:
- cold: phase 3's run (~/mola-phase3/irace/<problem>/irace.Rdata), started from default NSGA-II;
- warm: this phase's run (MOLA_PHASE4B_RUNS/<problem>/irace.Rdata), started from the warm start;
it reads, with irace's read_logfile, the best elite of every iteration and the experiments used up
to the end of that iteration (state$experiment_log). Every distinct elite is run with the matrix's
seeds (5001-5010) and 20 000 evaluations, VAMOS 1.0.0, numpy engine (phase 2's runs.run).

Outputs (MOLA_PHASE4B_RAW, default ~/mola-phase4b/matrix):
  anytime_elites.csv           problem, arm, iteration, experiments, elite_key, config (json)
  fronts/<elite_key>__<problem>.npz   final fronts per seed (resumable)

Run on NicoVM:  MOLA_PHASE4B_RAW=~/mola-phase4b/matrix PHASE2_WORKERS=31 python evaluate_4b.py
"""

import csv
import hashlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))
sys.path.insert(0, str(HERE.parents[1] / "phase2b" / "scripts"))

DATA = HERE.parent / "data"
RAW = Path(os.environ.get("MOLA_PHASE4B_RAW", Path.home() / "mola-phase4b" / "matrix"))
COLD = Path(os.environ.get("MOLA_PHASE3_RUNS", Path.home() / "mola-phase3" / "irace"))
WARM = Path(os.environ.get("MOLA_PHASE4B_RUNS", Path.home() / "mola-phase4b" / "irace"))
SEEDS = tuple(range(5001, 5011))
BUDGET = 20_000
WORKERS = int(os.environ.get("PHASE2_WORKERS", 31))
R_SCRIPT = """
suppressMessages(library(irace))
r <- read_logfile(commandArgs(TRUE)[1])
log <- r$state$experiment_log
out <- NULL
for (i in seq_along(r$allElites)) {
  id <- r$allElites[[i]][1]
  conf <- r$allConfigurations[r$allConfigurations$.ID. == id, , drop = FALSE]
  conf$.iteration <- i
  conf$.experiments <- sum(log$iteration <= i)
  out <- rbind(out, conf)
}
write.csv(out, stdout(), row.names = FALSE, na = "NA")
"""


def iteration_elites(rdata: Path) -> list[dict]:
    from irace_runner import parse_assignment

    out = subprocess.run(
        ["Rscript", "-e", R_SCRIPT, str(rdata)],
        check=True,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "R_LIBS": os.environ.get("IRACE_LIB", str(Path.home() / "R" / "irace-4.5-lib")),
        },
    )
    elites = []
    for row in csv.DictReader(io.StringIO(out.stdout)):
        arguments = []
        for name, value in row.items():
            if name.startswith(".") or value in ("NA", ""):
                continue
            arguments += [f"--{name}", value]
        elites.append(
            {
                "iteration": int(row[".iteration"]),
                "experiments": int(row[".experiments"]),
                "config": parse_assignment(arguments),
            }
        )
    return elites


def key_of(config: dict) -> str:
    return "elite__" + hashlib.sha1(json.dumps(config, sort_keys=True).encode()).hexdigest()[:12]


def _evaluate(key: str, config: dict, problem: str) -> None:
    from runs import run

    arrays = {}
    for seed in SEEDS:
        result = run(problem, config, BUDGET, seed)
        arrays[f"s{seed}_e{BUDGET}"] = result["fronts"][BUDGET]
    np.savez_compressed(RAW / "fronts" / f"{key}__{problem}.npz", **arrays)


def main() -> None:
    from joblib import Parallel, delayed

    (RAW / "fronts").mkdir(parents=True, exist_ok=True)
    tasks = json.loads((DATA / "warm_start_tasks.json").read_text())
    rows, pending = [], {}
    for problem in tasks:
        for arm, runs in (("cold", COLD), ("warm", WARM)):
            for elite in iteration_elites(runs / problem / "irace.Rdata"):
                key = key_of(elite["config"])
                rows.append(
                    {
                        "problem": problem,
                        "arm": arm,
                        "iteration": elite["iteration"],
                        "experiments": elite["experiments"],
                        "elite_key": key,
                        "config": json.dumps(elite["config"], sort_keys=True),
                    }
                )
                if not (RAW / "fronts" / f"{key}__{problem}.npz").exists():
                    pending[(key, problem)] = elite["config"]
    with (RAW / "anytime_elites.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} iteration elites, {len(pending)} elite-problem pairs to run", flush=True)
    Parallel(n_jobs=WORKERS)(
        delayed(_evaluate)(key, config, problem) for (key, problem), config in pending.items()
    )
    print("done", flush=True)


if __name__ == "__main__":
    main()
