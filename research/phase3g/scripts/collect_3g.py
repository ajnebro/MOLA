"""Collect phase 3g's generalists: the best final elite of every irace task.

Tasks (data/generalist_tasks.json): gen_lofo_dtlz, gen_lofo_lz09uf, gen_lofo_rerwa, gen_lofo_zcat,
gen_lofo_zdt and gen_all. Reuses phase 2b's collector (irace's read_logfile and getFinalElites
through Rscript).

Run on NicoVM:
    MOLA_PHASE3G_RUNS=~/mola-phase3g/irace python collect_3g.py  ->  data/tuned_configs.json
"""

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = Path(os.environ.get("MOLA_PHASE3G_RUNS", Path.home() / "mola-phase3g" / "irace"))
os.environ["MOLA_PHASE2B_RUNS"] = str(RUNS)
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))
sys.path.insert(0, str(HERE.parents[1] / "phase2b" / "scripts"))

from collect_irace import collect  # noqa: E402

TASKS = list(json.loads((HERE.parent / "data" / "generalist_tasks.json").read_text()))


def main() -> None:
    tuned = {task: collect(task) for task in TASKS if (RUNS / task / "DONE").exists()}
    missing = [t for t in TASKS if t not in tuned]
    out = HERE.parent / "data" / "tuned_configs.json"
    out.write_text(json.dumps(tuned, indent=2) + "\n")
    print(f"{len(tuned)} elites -> {out}; missing: {missing}")


if __name__ == "__main__":
    main()
