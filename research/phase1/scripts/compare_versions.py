"""How much MOLA 0.3.0's values differ from 0.2.0's on the same samples.

Samples a few problems once, writes them as interchange files, and characterizes each file with
MOLA 0.2.0 (commit 58bc0ca, extracted with `git archive` and run in a subprocess) and with this
checkout under both geometries. `raw` isolates the definition fixes (supported test, normalized
neighbour distances); `bound` adds the geometry change.

Run from the repository root:  python research/phase1/scripts/compare_versions.py
Writes research/phase1/data/version_comparison.json and version_comparison.csv.
"""

import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from jmetal.problem import DTLZ2, ZDT1
from jmetal.problem.multiobjective import re as re_suite

import mola
from mola.adapters.jmetalpy import sample_problem
from mola.characterize import characterize
from mola.sample import read_sample, write_sample

ROOT = Path(__file__).resolve().parents[3]
DATA = Path(__file__).resolve().parents[1] / "data"
OLD_COMMIT = "58bc0ca"
PROBLEMS = [("ZDT1", lambda: ZDT1(number_of_variables=5)), ("DTLZ2", DTLZ2),
            ("RE25", re_suite.RE25), ("RE33", re_suite.RE33), ("RE41", re_suite.RE41),
            ("RE61", re_suite.RE61)]
SEED = 42

OLD_RUNNER = """
import json, sys
import mola
from mola.characterize import characterize
from mola.sample import read_sample
assert mola.__version__ == "0.2.0", mola.__file__
out = {}
for path in sys.argv[1:]:
    out[path] = {k: float(v) for k, v in characterize(read_sample(path)).items()}
print(json.dumps(out))
"""


def _extract_old_source(target: Path) -> Path:
    archive = subprocess.run(["git", "-C", str(ROOT), "archive", OLD_COMMIT, "src"],
                             check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(target, filter="data")
    return target / "src"


def _differs(a: float, b: float) -> bool:
    if np.isnan(a) and np.isnan(b):
        return False
    return not np.isclose(a, b, rtol=1e-9, atol=1e-12)


def main() -> None:
    evaluations = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        paths = []
        for name, factory in PROBLEMS:
            problem = factory()
            n = 200 * problem.number_of_variables()
            evaluations[name] = n
            path = tmp_path / f"{name}.csv"
            write_sample(sample_problem(problem, sample_size=n, seed=SEED), path)
            paths.append(path)

        old_src = _extract_old_source(tmp_path / "mola-0.2.0")
        env = {"PYTHONPATH": str(old_src), "PATH": "", "SYSTEMROOT": str(Path("C:/Windows"))}
        completed = subprocess.run([sys.executable, "-W", "ignore", "-c", OLD_RUNNER, *map(str, paths)],
                                   check=True, capture_output=True, text=True, env=env)
        old = json.loads(completed.stdout)

        rows, summary = [], {}
        for (name, _), path in zip(PROBLEMS, paths, strict=True):
            sample = read_sample(path)
            before = old[str(path)]
            new = {g: characterize(sample, geometry=g) for g in ("raw", "bound")}
            features = [k for k in before if k not in ("sample_size", "num_obj", "num_var")]
            summary[name] = {
                "M": sample.number_of_objectives, "D": sample.number_of_variables,
                "bounds_homogeneous": bool(np.allclose(sample.lower_bounds, sample.lower_bounds[0])
                                           and np.allclose(sample.upper_bounds, sample.upper_bounds[0])),
                **{f"changed_{g}": [k for k in features if _differs(before[k], new[g][k])]
                   for g in new},
            }
            for k in features:
                rows.append({"problem": name, "feature": k, "v0.2.0": before[k],
                             "v0.3.0_raw": new["raw"][k], "v0.3.0_bound": new["bound"][k]})

    DATA.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(DATA / "version_comparison.csv", index=False)
    result = {"old_commit": OLD_COMMIT, "new_version": mola.__version__, "seed": SEED,
              "evaluations": evaluations, "total_evaluations": sum(evaluations.values()),
              "problems": summary}
    (DATA / "version_comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    for name, info in summary.items():
        print(name, "raw:", len(info["changed_raw"]), "bound:", len(info["changed_bound"]),
              sorted(info["changed_raw"]))


if __name__ == "__main__":
    main()
