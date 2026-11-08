"""Check whether VAMOS 1.0.0 gives the same fronts with numba installed (2026-11-07).

VAMOS's SBX crossover (crossover_sbx.py) uses a numba kernel (_get_sbx_single_pair_numba) when
numba can be imported, even with engine="numpy", and falls back to numpy otherwise. It does so only
for a single pair with a variation workspace, that is, in steady-state configurations
(offspring_ratio = 0). Every phase so far ran without numba.

Three commands, run on NicoVM with the campaign's venv and numba in a separate directory:
    pip install --target /tmp/numba_test --no-deps numba llvmlite
    python check_numba_sbx.py run /tmp/probe_stub.npz
    NUMBA_CACHE_DIR=/tmp/numba_cache PYTHONPATH=/tmp/numba_test \
        python check_numba_sbx.py run /tmp/probe_numba.npz
    python check_numba_sbx.py compare /tmp/probe_stub.npz /tmp/probe_numba.npz
    NUMBA_CACHE_DIR=/tmp/numba_cache PYTHONPATH=/tmp/numba_test python check_numba_sbx.py paths
NUMBA_CACHE_DIR matters: the kernel is compiled with cache=True, and without it numba writes its
cache into VAMOS's __pycache__ inside the campaign's venv. The 2026-11-07 run did so; the two files
were inert, because the campaign never imports numba, and were deleted on 2026-11-08.

`run` runs 12 configurations (phase 3's 8 random configurations with SBX, 3 without it, and
NSGA-II's default) on 4 development problems with seeds 5001 and 5002 and 5 000 evaluations, and
saves the final fronts and times. Result on 2026-11-07 (numba 0.68.1, llvmlite 0.50.0, numpy 2.2.6,
Python 3.10.12):
- 80 of 96 fronts were bit-identical (`compare`).
- The 16 that differed are all those of random__22 and random__28, the two steady-state
  configurations, the only ones that reach the numba kernel.
- Total time was 84.9 s without numba and 79.6 s with it. The two steady-state configurations ran
  10-17 % faster with numba; the others ran at the same speed. The warm-up uses the default
  configuration, which never reaches the kernel, so the numba time includes its one compilation,
  in random__22's first run.

`paths` finds the cause (2026-11-08): it calls the operator 2 000 times per case through each path,
with the same parents and seed. The children were bit-identical in every call, but the random
stream was not. When crossover applies and no variable is active (identical parents, or no variable
chosen by prob_var), the numpy path returns before drawing its 2 x n_var SBX and swap numbers, and
the kernel draws them anyway. From then on the two runs use different random numbers. Identical
parents shifted the stream in 1 785 of 2 000 calls, the 90 % in which crossover applies; distinct
parents with 2 variables and prob_var = 0.5 did so in 449 (about 0.9 x 0.5^2).

numba was therefore not installed, and the campaign kept the numpy path. In the VAMOS 1.1.0
development tree, available_variation_kernels() states that the kernels consume the same draws as
numpy; this was not checked here.
"""

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "research" / "phase2" / "scripts"))
sys.path.insert(0, str(REPO / "research" / "phase2b" / "scripts"))

import numpy as np  # noqa: E402

PROBLEMS = ["zdt1", "dtlz2", "cec2009_uf1", "bbob-biobj_f14_i01_d10"]
SEEDS = (5001, 5002)
BUDGET = 5000
CALLS = 2000


def run_all(out: Path) -> None:
    """Run every configuration, problem and seed, and save the fronts and times to `out`."""
    from runs import run

    configs = json.loads(
        (REPO / "research" / "phase3" / "data" / "random_configs.json").read_text()
    )
    chosen = {k: v for k, v in configs.items() if v["crossover"] == "sbx"}
    chosen.update({k: configs[k] for k in ("random__00", "random__01", "random__02")})
    chosen["default"] = None
    # Warm-up for imports. The default configuration never reaches the numba kernel.
    run("zdt1", None, 1000, 1, checkpoints=())
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


def compare(first: Path, second: Path) -> None:
    """Print how many fronts are bit-identical between two `run` outputs, and which differ."""
    a, b = np.load(first), np.load(second)
    assert sorted(a.files) == sorted(b.files)
    differ = [k for k in sorted(a.files) if not np.array_equal(a[k], b[k])]
    print(f"bit-identical: {len(a.files) - len(differ)} of {len(a.files)}")
    print("differing configurations:", sorted({k.split("|")[0] for k in differ}))


def paths() -> None:
    """Call single-pair SBX through the numba kernel and the numpy path, and compare both."""
    from vamos.engine.operators.impl.real import crossover_sbx as sbx
    from vamos.engine.operators.impl.real.utils import VariationWorkspace

    kernel = sbx._get_sbx_single_pair_numba()
    assert kernel is not None, "numba is not importable"
    gen = np.random.default_rng(0)

    def call(use_kernel, parents, seed, prob_var):
        sbx._get_sbx_single_pair_numba = (lambda: kernel) if use_kernel else (lambda: None)
        n_var = parents.shape[2]
        op = sbx.SBXCrossover(
            0.9,
            20.0,
            prob_var,
            lower=np.zeros(n_var),
            upper=np.ones(n_var),
            workspace=VariationWorkspace(),
        )
        rng = np.random.default_rng(seed)
        children = op(parents.copy(), rng)
        return children, rng.random()  # the next draw shows whether the streams stayed aligned

    for label, identical in (("distinct parents", False), ("identical parents", True)):
        for prob_var in (0.5, 1.0):
            for n_var in (2, 10, 30):
                children_differ = stream_differs = 0
                for seed in range(CALLS):
                    parents = gen.random((1, 2, n_var))
                    if identical:
                        parents[0, 1] = parents[0, 0]
                    a, next_a = call(True, parents, seed, prob_var)
                    b, next_b = call(False, parents, seed, prob_var)
                    children_differ += not np.array_equal(a, b)
                    stream_differs += next_a != next_b
                print(
                    f"{label:18s} prob_var={prob_var} n_var={n_var:2d}: children differ "
                    f"{children_differ}/{CALLS}, random stream differs {stream_differs}/{CALLS}"
                )


if __name__ == "__main__":
    command, args = sys.argv[1], [Path(a) for a in sys.argv[2:]]
    {"run": run_all, "compare": compare, "paths": paths}[command](*args)
