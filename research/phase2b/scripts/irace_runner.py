"""irace target runner for phase 2b (arm B): one NSGA-II run in VAMOS, cost = -normalized HV.

irace calls `target-runner <configuration id> <instance id> <seed> <instance> --name value ...`;
the instance is the pilot problem's VAMOS name. The run uses 20 000 evaluations and the seed
irace gives; the cost is minus the hypervolume of the final non-dominated population after min-max
normalization by data/tuning_bounds.json, with reference point 1.1 (the same objective as arm A).
The only output is the cost (irace merges stdout and stderr).
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))

from runs import invariant_nsgaii_space, run  # noqa: E402  (imports common first: one thread)

import numpy as np  # noqa: E402

BUDGET = 20_000
REFERENCE = 1.1
BOUNDS = HERE.parent / "data" / "tuning_bounds.json"


def parse_assignment(arguments: list[str]) -> dict:
    """`--name value` pairs -> a VAMOS assignment with each value in its parameter's own type."""
    space = invariant_nsgaii_space()
    raw = {arguments[i].lstrip("-"): arguments[i + 1] for i in range(0, len(arguments), 2)}
    assignment = {}
    for name, text in raw.items():
        spec = space.params[name]
        kind = type(spec).__name__
        if kind == "Int":
            assignment[name] = int(round(float(text)))
        elif kind == "Real":
            assignment[name] = float(text)
        else:
            matches = [choice for choice in spec.choices if str(choice) == text]
            if not matches:
                raise ValueError(f"{name}: {text!r} not among {spec.choices}")
            assignment[name] = matches[0]
    return assignment


def normalized_hv(front: np.ndarray, ideal: np.ndarray, nadir: np.ndarray) -> float:
    from vamos.foundation.quality_indicators.hypervolume import hypervolume

    span = np.where(nadir > ideal, nadir - ideal, 1.0)
    scaled = (np.asarray(front, float) - ideal) / span
    reference = np.full(scaled.shape[1], REFERENCE)
    scaled = scaled[np.all(scaled < reference, axis=1)]
    return float(hypervolume(scaled, reference)) if len(scaled) else 0.0


def main(argv: list[str]) -> None:
    seed, problem = int(argv[2]), argv[3]
    assignment = parse_assignment(argv[4:])
    bounds = json.loads(BOUNDS.read_text())[problem]
    front = run(problem, assignment, BUDGET, seed, checkpoints=())["fronts"][BUDGET]
    hv = normalized_hv(front, np.asarray(bounds["ideal"]), np.asarray(bounds["nadir"]))
    print(f"{0.0 - hv:.12g}" if hv > 0 else "0")


if __name__ == "__main__":
    main(sys.argv[1:])
