"""Phase 2, stage B: tune one NSGA-II configuration c*_P per pilot problem (decision D2).

Calibration: NSGA-II default, 20 000 evaluations, seeds 4001-4005; the union of the final fronts
fixes each problem's ideal and nadir for the tuning objective (data/calibration.json).

Tuning: VAMOS 1.0.0 RacingTuner (decision D3) over VAMOS's NSGA-II space without the archive
controls, on the problem alone, with blocks = seeds 3001-3025, 20 000 evaluations per run,
elitist restarts, the textbook default as an initial configuration, and MAX_EXPERIMENTS runs per
problem. The score is the hypervolume of the final non-dominated population after min-max
normalization by the calibration ideal and nadir, with reference point 1.1 in every objective
(points beyond it contribute nothing).

Problems run in parallel (WORKERS processes, racing itself sequential). Results are written per
problem as they finish, so an interrupted run resumes where it stopped.

Run:  python research/phase2/scripts/tune_pilot.py
Writes data/calibration.json, data/tuned_configs.json and the tuning histories in the raw dir.
"""

import json
import time
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed

from common import DATA, RAW, pilot_problems
from runs import invariant_nsgaii_space, run

BUDGET = 20_000
CALIBRATION_SEEDS = (4001, 4002, 4003, 4004, 4005)
TUNING_SEEDS = tuple(range(3001, 3021))
MAX_EXPERIMENTS = 400
INITIAL_CONFIGS = 60
WORKERS = 8
REFERENCE = 1.1
BASELINE = {"pop_size": 100, "offspring_ratio": 1.0, "selection": "tournament", "selection_size": 2,
            "initializer": "random", "crossover": "sbx", "crossover_prob": 1.0, "crossover_eta": 20.0,
            "mutation": "polynomial", "mutation_prob_factor": 1.0, "mutation_eta": 20.0,
            "repair": "clip"}
CALIBRATION = DATA / "calibration.json"
TUNED = DATA / "tuned_configs.json"

_bounds_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}


def normalized_hv(front: np.ndarray, ideal: np.ndarray, nadir: np.ndarray) -> float:
    """HV of a front min-max normalized by (ideal, nadir), reference point REFERENCE."""
    from vamos.foundation.quality_indicators.hypervolume import hypervolume

    span = np.where(nadir > ideal, nadir - ideal, 1.0)
    scaled = (np.asarray(front, float) - ideal) / span
    reference = np.full(scaled.shape[1], REFERENCE)
    scaled = scaled[np.all(scaled < reference, axis=1)]
    return float(hypervolume(scaled, reference)) if len(scaled) else 0.0


def _calibrate(problem: str) -> dict:
    fronts = [run(problem, None, BUDGET, seed)["fronts"][BUDGET] for seed in CALIBRATION_SEEDS]
    union = np.vstack(fronts)
    return {"ideal": union.min(axis=0).tolist(), "nadir": union.max(axis=0).tolist()}


def tuning_score(config, ctx) -> float:
    """Racing objective: normalized HV of one run (module level so joblib can pickle it)."""
    problem = ctx.instance.name
    if problem not in _bounds_cache:
        entry = json.loads(CALIBRATION.read_text())[problem]
        _bounds_cache[problem] = (np.asarray(entry["ideal"]), np.asarray(entry["nadir"]))
    ideal, nadir = _bounds_cache[problem]
    front = run(problem, dict(config), ctx.budget, ctx.seed, checkpoints=())["fronts"][ctx.budget]
    return normalized_hv(front, ideal, nadir)


def _tune(problem: str) -> dict:
    import common  # noqa: F401
    from vamos.engine.tuning import Instance, RacingTuner, Scenario, TuningTask

    from common import instantiate

    task = TuningTask(name=f"nsgaii_{problem}", param_space=invariant_nsgaii_space(),
                      instances=[Instance(problem, instantiate(problem).n_var)],
                      seeds=list(TUNING_SEEDS), budget_per_run=BUDGET, maximize=True,
                      aggregator=np.mean)
    scenario = Scenario(max_experiments=MAX_EXPERIMENTS, n_jobs=1, verbose=False,
                        use_elitist_restarts=False,
                        use_multi_fidelity=False)
    seed = 7000 + pilot_problems().index(problem)
    start = time.perf_counter()
    best, history = RacingTuner(task, scenario, seed=seed, max_initial_configs=INITIAL_CONFIGS,
                                initial_configs=[dict(BASELINE)]).run(tuning_score, verbose=False)
    seconds = time.perf_counter() - start
    raw = RAW / "tuning"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / f"{problem}.json").write_text(json.dumps(
        [{"config": dict(t.config), "score": getattr(t, "score", None),
          "details": getattr(t, "details", None)} for t in history], default=str))
    return {"problem": problem, "config": {k: (v.item() if hasattr(v, "item") else v) for k, v in best.items()},
            "experiments": len(history), "seconds": seconds, "racing_seed": seed}


def main() -> None:
    problems = pilot_problems()
    calibration = json.loads(CALIBRATION.read_text()) if CALIBRATION.exists() else {}
    missing = [p for p in problems if p not in calibration]
    if missing:
        results = Parallel(n_jobs=WORKERS)(delayed(_calibrate)(p) for p in missing)
        calibration.update(dict(zip(missing, results, strict=True)))
        CALIBRATION.write_text(json.dumps(calibration, indent=2) + "\n")

    tuned = json.loads(TUNED.read_text()) if TUNED.exists() else {}
    pending = [p for p in problems if p not in tuned]
    start = time.perf_counter()
    for result in Parallel(n_jobs=WORKERS, return_as="generator_unordered")(
            delayed(_tune)(p) for p in pending):
        tuned[result["problem"]] = result
        Path(TUNED).write_text(json.dumps(tuned, indent=2, default=str) + "\n")
        print(f"{result['problem']}: {result['experiments']} runs, {result['seconds']:.0f}s", flush=True)
    print(f"tuning wall {time.perf_counter() - start:.0f}s")


if __name__ == "__main__":
    main()
