"""Collect arm B's tuned configurations: the best final elite of each irace run.

For every pilot problem, reads RUNS/<problem>/irace.Rdata with irace's own `read_logfile` and
`getFinalElites` (Rscript, irace >= 4.4.4 in IRACE_LIB), drops irace's metadata columns and the
parameters irace marks inactive (NA), and converts each value to its VAMOS type.

Run on NicoVM:  MOLA_PHASE2B_RUNS=... python research/phase2b/scripts/collect_irace.py
Writes data/tuned_irace.json in the format of phase 2's tuned_configs.json.
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
sys.path.insert(0, str(HERE))

from common import pilot_problems  # noqa: E402
from irace_runner import parse_assignment  # noqa: E402

RUNS = Path(os.environ.get("MOLA_PHASE2B_RUNS", Path.home() / "mola-phase2b" / "raw_B" / "irace"))
R_SCRIPT = """
suppressMessages(library(irace))
r <- read_logfile(commandArgs(TRUE)[1])
e <- getFinalElites(r, n = 1)
e$.experiments <- sum(!is.na(r$experiments))  # instances x configurations, NA = not run
e$.iterations <- length(r$allElites)
e$.configurations <- ncol(r$experiments)
write.csv(e, stdout(), row.names = FALSE, na = "NA")
"""


def collect(problem: str) -> dict:
    out = subprocess.run(["Rscript", "-e", R_SCRIPT, str(RUNS / problem / "irace.Rdata")],
                         check=True, capture_output=True, text=True,
                         env={**os.environ, "R_LIBS": os.environ.get("IRACE_LIB", str(Path.home() / "R" / "irace-4.5-lib"))})
    row = next(csv.DictReader(io.StringIO(out.stdout)))
    arguments = []
    for name, value in row.items():
        if name.startswith(".") or value in ("NA", ""):
            continue
        arguments += [f"--{name}", value]
    return {"problem": problem, "config": parse_assignment(arguments), "irace_id": int(row[".ID."]),
            "experiments": int(row[".experiments"]), "iterations": int(row[".iterations"]),
            "configurations": int(row[".configurations"])}


def main() -> None:
    tuned = {p: collect(p) for p in pilot_problems()}
    out = HERE.parent / "data" / "tuned_irace.json"
    out.write_text(json.dumps(tuned, indent=2) + "\n")
    print(f"{len(tuned)} elites -> {out}")


if __name__ == "__main__":
    main()
