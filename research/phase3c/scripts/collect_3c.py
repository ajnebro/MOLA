"""Collect phase 3c's tuned configurations: the best final elite of every irace task.

Tasks: f01-f55 (c*_P per instance-1 problem) and the generalists gen_all, gen_g1-gen_g5. Reuses
phase 2b's collector (irace's read_logfile and getFinalElites through Rscript).

Run on NicoVM:  MOLA_PHASE3C_RUNS=~/mola-phase3c/irace python collect_3c.py  ->  data/tuned_configs.json
"""

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = Path(os.environ.get("MOLA_PHASE3C_RUNS", Path.home() / "mola-phase3c" / "irace"))
os.environ["MOLA_PHASE2B_RUNS"] = str(RUNS)
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))
sys.path.insert(0, str(HERE.parents[1] / "phase2b" / "scripts"))

from collect_irace import collect  # noqa: E402

TASKS = [f"f{f:02d}" for f in range(1, 56)] + ["gen_all"] + [f"gen_g{g}" for g in range(1, 6)]


def main() -> None:
    tuned = {task: collect(task) for task in TASKS if (RUNS / task / "DONE").exists()}
    missing = [t for t in TASKS if t not in tuned]
    out = HERE.parent / "data" / "tuned_configs.json"
    out.write_text(json.dumps(tuned, indent=2) + "\n")
    print(f"{len(tuned)} elites -> {out}; missing: {missing}")


if __name__ == "__main__":
    main()
