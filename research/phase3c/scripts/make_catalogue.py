"""Phase 3c catalogue: the 165 bbob-biobj problems (55 functions x instances 1-3, D = 10).

For every problem: function, instance, its two bbob components and their bbob function groups,
and COCO's true ideal and nadir (coco_problems.true_bounds). Writes data/catalogue.json and
data/tuning_bounds.json (the normalization of the tuning objective and of HVn, as in phase 3).

bbob function groups of the ten components used by bbob-biobj:
  1 separable {f1, f2}; 2 moderate conditioning {f6, f8}; 3 ill-conditioned {f13, f14};
  4 multimodal with adequate global structure {f15, f17}; 5 multimodal with weak structure {f20, f21}.

Run locally:  python research/phase3c/scripts/make_catalogue.py
"""

import json
from pathlib import Path

import coco_problems as cp

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
DIMENSION = 10
FUNCTIONS = range(1, 56)
INSTANCES = (1, 2, 3)
BBOB_GROUP = {1: 1, 2: 1, 6: 2, 8: 2, 13: 3, 14: 3, 15: 4, 17: 4, 20: 5, 21: 5}


def name(function: int, instance: int) -> str:
    return f"bbob-biobj_f{function:02d}_i{instance:02d}_d{DIMENSION:02d}"


def main() -> None:
    catalogue, bounds = {}, {}
    for function in FUNCTIONS:
        for instance in INSTANCES:
            problem = name(function, instance)
            true = cp.true_bounds(problem)
            components = [int(c.split("_f")[1][:3]) for c in true["components"]]
            catalogue[problem] = {
                "function": function,
                "instance": instance,
                "components": components,
                "groups": sorted({BBOB_GROUP[c] for c in components}),
                "component_ids": true["components"],
            }
            bounds[problem] = {
                "ideal": true["ideal"],
                "nadir": true["nadir"],
                "source": "COCO (cocoex 2.8.2)",
            }
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "catalogue.json").write_text(json.dumps(catalogue, indent=1) + "\n")
    (DATA / "tuning_bounds.json").write_text(json.dumps(bounds, indent=1) + "\n")
    print(f"{len(catalogue)} problems")


if __name__ == "__main__":
    main()
