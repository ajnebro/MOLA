"""Build the phase 2 problem catalogue: duplicates, formulation groups and the reserved test split.

1. Exact duplicates (protocol.md section 1, E23): two problems with the same dimension and bounds
   are duplicates when they return the same objective vectors on the same 2 000 random points
   (relative tolerance 1e-12). MOLA's 49 features on one LHS sample (seed 0) are compared as well.
2. Formulation groups: duplicates share a group; DTLZ4 joins DTLZ2 (a biased variant by
   construction); every other problem is its own group.
3. Reserved final-test groups, drawn **before** any tuning or method design (plan.md section 5):
   the whole WFG suite (suite excluded), plus a seeded draw of 25 % of the formulation groups
   (at least one) of ZDT, DTLZ and ZCAT (formulation excluded). LZ09 and UF stay in development as
   one family, because their exact correspondence is unverified and splitting them could leak;
   RE and RWA were inspected in phase 0 and are development only.

Run from the repository root:  python research/phase2/scripts/catalogue.py
Writes research/phase2/catalogue.csv, reserved_groups.json and data/duplicates.json; the seed-0
features go to the raw directory and are not used for any method decision.
"""

import hashlib
import json
from itertools import combinations

import numpy as np
import pandas as pd

from common import DATA, EXCLUDED, PHASE, RAW, SUITES, bounds, evaluate, instantiate, sample_problem
from mola.characterize import characterize_report

RESERVATION_SEED = 20261020
RESERVED_FRACTION = 0.25
FAMILY = {"ZDT": "ZDT", "DTLZ": "DTLZ", "LZ09": "LZ09/UF", "UF": "LZ09/UF", "WFG": "WFG",
          "ZCAT": "ZCAT", "RE": "RE/RWA", "RWA": "RE/RWA"}


def main() -> None:
    names = [name for suite in SUITES.values() for name in suite]
    suite_of = {name: suite for suite, members in SUITES.items() for name in members}
    problems = {name: instantiate(name) for name in names}

    # 1a. Objective-level duplicates among problems with identical dimension and bounds.
    rng = np.random.default_rng(0)
    probe = {}
    identical = []
    for a, b in combinations(names, 2):
        pa, pb = problems[a], problems[b]
        if pa.n_var != pb.n_var:
            continue
        (la, ua), (lb, ub) = bounds(pa), bounds(pb)
        if not (np.array_equal(la, lb) and np.array_equal(ua, ub)):
            continue
        key = (pa.n_var, la.tobytes(), ua.tobytes())
        if key not in probe:
            probe[key] = la + rng.random((2000, pa.n_var)) * (ua - la)
        fa, fb = evaluate(pa, probe[key]), evaluate(pb, probe[key])
        if np.allclose(fa, fb, rtol=1e-12, atol=1e-12):
            identical.append((a, b))

    # 1b. Feature-level comparison (seed 0, bound geometry, k = D).
    features, meta = {}, []
    for name in names:
        sample, seconds = sample_problem(name, seed=0)
        report = characterize_report(sample)
        features[name] = report.features
        meta.append({"problem": name, "n": sample.size, "D": sample.number_of_variables,
                     "evaluation_seconds": seconds})
    RAW.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(features).T.to_csv(RAW / "catalogue_features_seed0.csv")
    feature_identical = []
    for a, b in combinations(names, 2):
        va, vb = np.array(list(features[a].values())), np.array(list(features[b].values()))
        both_nan = np.isnan(va) & np.isnan(vb)
        if np.all(both_nan | np.isclose(va, vb, rtol=1e-9, atol=1e-12)):
            feature_identical.append((a, b))

    # 2. Formulation groups (union-find over duplicate pairs plus the DTLZ2/DTLZ4 variant).
    parent = {name: name for name in names}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in [*identical, ("dtlz2", "dtlz4")]:
        parent[find(b)] = find(a)
    group_of = {name: find(name) for name in names}

    # 3. Reserved final-test groups.
    draw = np.random.default_rng(RESERVATION_SEED)
    reserved = {group_of[name] for name in SUITES["WFG"]}
    for suite in ("ZDT", "DTLZ", "ZCAT"):
        groups = sorted({group_of[name] for name in SUITES[suite]},
                        key=lambda g: names.index(g))
        count = max(1, round(RESERVED_FRACTION * len(groups)))
        reserved.update(draw.choice(groups, size=count, replace=False).tolist())

    rows = []
    for name in names:
        problem = problems[name]
        lower, upper = bounds(problem)
        rows.append({
            "problem": name, "suite": suite_of[name], "family": FAMILY[suite_of[name]],
            "group": group_of[name], "n_var": problem.n_var, "n_obj": problem.n_obj,
            "lower_min": lower.min(), "upper_max": upper.max(),
            "homogeneous_bounds": bool(np.ptp(lower) == 0 and np.ptp(upper) == 0),
            "role": "test" if group_of[name] in reserved else "development",
        })
    catalogue = pd.DataFrame(rows)
    catalogue.to_csv(PHASE / "catalogue.csv", index=False)

    test = sorted(catalogue.loc[catalogue.role == "test", "problem"])
    groups = sorted(reserved)
    digest = hashlib.sha256(json.dumps({"groups": groups, "problems": test}).encode()).hexdigest()
    (PHASE / "reserved_groups.json").write_text(json.dumps({
        "reservation_seed": RESERVATION_SEED, "fraction": RESERVED_FRACTION,
        "rule": "whole WFG suite + seeded 25% (>= 1) of ZDT, DTLZ, ZCAT groups; LZ09/UF, RE, RWA development",
        "reserved_groups": groups, "reserved_problems": test, "sha256": digest,
    }, indent=2) + "\n")
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "duplicates.json").write_text(json.dumps({
        "objective_identical_pairs": identical, "feature_identical_pairs_seed0": feature_identical,
        "excluded": EXCLUDED, "sampling": meta,
    }, indent=2, default=float) + "\n")

    print("objective-identical:", identical)
    print("feature-identical:", feature_identical)
    print(catalogue.groupby(["family", "role"]).size())
    print("reserved:", test, digest)


if __name__ == "__main__":
    main()
