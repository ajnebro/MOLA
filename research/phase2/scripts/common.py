"""Shared helpers for the phase 2 pilot: problems, VAMOS-based sampling for MOLA, paths.

Every objective evaluation, for characterization and for optimization alike, goes through the
VAMOS implementation of each problem (decision D3: generate and evaluate in the same framework).
Thread pools are pinned to one thread before numpy is imported, so that timings and parallel
workers do not oversubscribe the machine.
"""

import os

for _variable in (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ.setdefault(_variable, "1")

import importlib.util  # noqa: E402
import sys  # noqa: E402

# VAMOS 1.0.0 imports numba inside its SBX crossover on every call (crossover_sbx.py,
# _get_sbx_single_pair_numba). Without numba installed, each failed import searches the whole of
# sys.path: one search per generation, about 0.007 ms per sys.path entry on NicoVM. In the 3c
# campaign instantiate() below also added an entry per experiment, so after days a server worker
# searched ~16 000 entries (~100 ms) per generation (2026-11-07/08). A None entry makes the import
# fail at once; VAMOS then takes the same numpy fallback, so results are bit-identical (checked on
# bbob-biobj f14).
if importlib.util.find_spec("numba") is None:
    sys.modules["numba"] = None

import json  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
from scipy.stats import qmc  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
PHASE = REPO / "research" / "phase2"
DATA = PHASE / "data"
RAW = Path(os.environ.get("MOLA_PHASE2_RAW", r"C:\tmp\mola-phase2\raw"))
"""Bulky per-run outputs (fronts, checkpoints) live outside the repository."""

N_OBJ = 2

# Bi-objective, continuous, box-constrained VAMOS problems (catalogue.csv adds their groups).
SUITES: dict[str, list[str]] = {
    "ZDT": ["zdt1", "zdt2", "zdt3", "zdt4", "zdt6"],
    "DTLZ": [f"dtlz{i}" for i in range(1, 8)],
    "LZ09": [f"lz09_f{i}" for i in (1, 2, 3, 4, 5, 7, 8, 9)],
    "UF": [f"cec2009_uf{i}" for i in range(1, 8)],
    "WFG": [f"wfg{i}" for i in range(1, 10)],
    "ZCAT": [f"zcat{i}" for i in range(1, 21)],
    "RE": ["re21", "re24"],
    "RWA": ["rwa1"],
}
EXCLUDED = {
    "zdt5": "binary encoding",
    "re22": "mixed encoding",
    "re23": "mixed encoding",
    "re25": "mixed encoding",
}


def instantiate(name: str):
    """A VAMOS problem instance by registry name, with two objectives where that is a parameter.

    COCO bbob-biobj ids ("bbob-biobj_f20_i01_d10", phase 3c) are wrapped over [-5, 5]^D.
    """
    if name.startswith("bbob-biobj_"):
        import sys

        # Once only: this runs on every experiment, and until 2026-11-08 it added one sys.path
        # entry each time, so a long-lived server worker's every failed import grew slower.
        scripts = str(REPO / "research" / "phase3c" / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        from coco_problems import make_problem

        return make_problem(name)
    from vamos.foundation.problem.registry import make_problem_selection

    if name.startswith(("dtlz", "wfg", "zcat")):
        return make_problem_selection(name, n_obj=N_OBJ).instantiate()
    return make_problem_selection(name).instantiate()


def bounds(problem) -> tuple[np.ndarray, np.ndarray]:
    lower = np.broadcast_to(np.asarray(problem.xl, dtype=float), (problem.n_var,)).copy()
    upper = np.broadcast_to(np.asarray(problem.xu, dtype=float), (problem.n_var,)).copy()
    return lower, upper


def evaluate(problem, variables: np.ndarray) -> np.ndarray:
    """Objective vectors of a batch, through the problem's own VAMOS evaluate()."""
    out = {"F": np.full((variables.shape[0], problem.n_obj), np.nan)}
    problem.evaluate(np.ascontiguousarray(variables, dtype=float), out)
    return np.asarray(out["F"], dtype=float)


def sample_problem(name: str, seed: int, sample_size: int | None = None):
    """LHS sample of a VAMOS problem as a MOLA Sample (n = 200 * D by default), and its eval time.

    MOLA is imported here, not at module level, so the optimization scripts also run where MOLA
    is not installed (NicoVM, phase 2b).

    Same design as MOLA's jMetalPy adapter: scipy's scrambled Latin Hypercube, scaled to the
    problem's declared bounds.
    """
    from mola.sample import Sample

    problem = instantiate(name)
    lower, upper = bounds(problem)
    n = sample_size or 200 * problem.n_var
    unit = qmc.LatinHypercube(d=problem.n_var, scramble=True, seed=seed).random(n)
    variables = qmc.scale(unit, lower, upper)
    start = time.perf_counter()
    objectives = evaluate(problem, variables)
    seconds = time.perf_counter() - start
    sample = Sample(
        problem=name,
        variables=variables,
        objectives=objectives,
        lower_bounds=lower,
        upper_bounds=upper,
        sampler="lhs",
        seed=seed,
    )
    return sample, seconds


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=float) + "\n")


def pilot_problems() -> list[str]:
    """Development problems for the pilot, one representative per set of exact duplicates."""
    import pandas as pd

    catalogue = pd.read_csv(PHASE / "catalogue.csv")
    duplicates = json.loads((DATA / "duplicates.json").read_text())["objective_identical_pairs"]
    redundant = {b for a, b in duplicates}  # keep the first-listed member of each pair
    development = catalogue.loc[catalogue.role == "development", "problem"].tolist()
    return [name for name in development if name not in redundant]
