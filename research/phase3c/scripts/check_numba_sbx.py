"""Check whether VAMOS 1.0.0 gives the same fronts with numba installed (2026-11-07).

VAMOS's SBX crossover (crossover_sbx.py, _get_sbx_single_pair_numba) uses a numba kernel when numba
can be imported, even with engine="numpy", and falls back to numpy otherwise. Every phase so far ran
without numba. This script runs 12 configurations (phase 3's 8 random configurations with SBX, 3
without it, and NSGA-II's default) on 4 development problems with seeds 5001 and 5002 and 5 000
evaluations, and saves the final fronts. Run it twice, with and without numba on the path, and
compare the two files.

Run on NicoVM (numba in a separate directory, the campaign's venv untouched):
    pip install --target /tmp/numba_test --no-deps numba llvmlite
    python check_numba_sbx.py /tmp/probe_stub.npz
    PYTHONPATH=/tmp/numba_test python check_numba_sbx.py /tmp/probe_numba.npz

Result on 2026-11-07 (numba 0.68.1, llvmlite 0.50.0, numpy 2.2.6, Python 3.10.12):
- 80 of 96 fronts were bit-identical.
- The 16 that differed are all those of random__22 and random__28, the two steady-state
  configurations (offspring_ratio = 0), which are the only ones that reach the numba kernel.
- Total time was 84.9 s without numba and 79.6 s with it. The two steady-state configurations ran
  10-17 % faster with numba; the others ran at the same speed.
numba was therefore not installed, and the campaign kept the numpy path.
"""

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "research" / "phase2" / "scripts"))
sys.path.insert(0, str(REPO / "research" / "phase2b" / "scripts"))

import numpy as np  # noqa: E402
from runs import run  # noqa: E402

PROBLEMS = ["zdt1", "dtlz2", "cec2009_uf1", "bbob-biobj_f14_i01_d10"]
SEEDS = (5001, 5002)
BUDGET = 5000


def main(out: Path) -> None:
    """Run every configuration, problem and seed, and save the fronts and times to `out`."""
    configs = json.loads(
        (REPO / "research" / "phase3" / "data" / "random_configs.json").read_text()
    )
    chosen = {k: v for k, v in configs.items() if v["crossover"] == "sbx"}
    chosen.update({k: configs[k] for k in ("random__00", "random__01", "random__02")})
    chosen["default"] = None
    run("zdt1", None, 1000, 1, checkpoints=())  # warm-up: numba compiles its kernel here
    arrays, seconds = {}, {}
    for cid, assignment in chosen.items():
        for problem in PROBLEMS:
            for seed in SEEDS:
                start = time.perf_counter()
                front = run(problem, assignment, BUDGET, seed, checkpoints=())["fronts"][BUDGET]
                seconds[f"{cid}|{problem}|{seed}"] = time.perf_counter() - start
                arrays[f"{cid}|{problem}|{seed}"] = front
    numba_loaded = sys.modules.get("numba") is not None
    np.savez(out, **arrays)
    out.with_suffix(".json").write_text(
        json.dumps({"numba": numba_loaded, "seconds": seconds}, indent=1)
    )
    print(f"numba loaded: {numba_loaded}, runs: {len(arrays)}, s: {sum(seconds.values()):.1f}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
