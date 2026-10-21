"""Collect phase 3e's tuned configurations: the best final elite of each irace run, as Evolver
command lines.

For every pilot problem, reads RUNS/<problem>/irace.Rdata with irace's `read_logfile` and
`getFinalElites` (Rscript, irace >= 4.4.4 in IRACE_LIB) and writes the elite's active
parameters, in the order of irace/parameters.txt, as the `--name value` line Evolver parses.

Run on NicoVM:  MOLA_PHASE3_RUNS=~/mola-phase3e/irace python collect_3e.py  ->  data/tuned_configs.json
"""

import csv
import io
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))

from common import pilot_problems  # noqa: E402

PHASE3E = HERE.parent
RUNS = Path(os.environ.get("MOLA_PHASE3_RUNS", Path.home() / "mola-phase3e" / "irace"))
R_SCRIPT = """
suppressMessages(library(irace))
r <- read_logfile(commandArgs(TRUE)[1])
e <- getFinalElites(r, n = 1)
e$.experiments <- sum(!is.na(r$experiments))
e$.iterations <- length(r$allElites)
e$.configurations <- ncol(r$experiments)
write.csv(e, stdout(), row.names = FALSE, na = "NA")
"""


def parameter_order() -> list[str]:
    lines = (PHASE3E / "irace" / "parameters.txt").read_text().splitlines()
    return [line.split()[0] for line in lines if line.strip() and not line.lstrip().startswith("#")]


def collect(problem: str, order: list[str]) -> dict:
    env = {**os.environ, "R_LIBS": os.environ.get("IRACE_LIB", str(Path.home() / "R" / "irace-4.5-lib"))}
    out = subprocess.run(["Rscript", "-e", R_SCRIPT, str(RUNS / problem / "irace.Rdata")],
                         check=True, capture_output=True, text=True, env=env)
    row = next(csv.DictReader(io.StringIO(out.stdout)))
    active = [(name, row[name]) for name in order if row.get(name) not in (None, "NA", "")]
    return {"problem": problem, "config": " ".join(f"--{n} {v}" for n, v in active),
            "irace_id": int(row[".ID."]), "experiments": int(row[".experiments"]),
            "iterations": int(row[".iterations"]), "configurations": int(row[".configurations"])}


def main() -> None:
    order = parameter_order()
    tuned = {p: collect(p, order) for p in pilot_problems()}
    out = PHASE3E / "data" / "tuned_configs.json"
    out.write_text(json.dumps(tuned, indent=2) + "\n")
    print(f"{len(tuned)} elites -> {out}")


if __name__ == "__main__":
    main()
