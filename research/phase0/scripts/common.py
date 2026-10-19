"""Shared helpers for the phase 0 scripts: problem sampling with evaluation accounting, the thesis metric.

Every objective evaluation made by a phase 0 script goes through ``sample_jmetalpy`` or ``sample_coco``
so that the 25 000-evaluation cap of plan.md can be enforced and reported.
"""

import time
from collections import Counter

import numpy as np
from scipy.stats import qmc

from mola.adapters.jmetalpy import sample_problem
from mola.sample import Sample

EVALUATION_CAP = 25_000
EVALUATIONS: Counter = Counter()

# The 19 thesis (Table 4.1) features that MOLA also computes; the two dist_*_max_neig are thesis-only.
THESIS19 = ["dist_x_avg", "dist_x_max", "dist_f_avg", "dist_f_max", "nd_n", "dist_x_nd_avg", "dist_x_nd_max",
            "rank_avg", "rank_max", "rank_ent", "sup_avg_neig", "inf_avg_neig", "inc_avg_neig", "lnd_avg_neig",
            "lsupp_avg_neig", "dist_x_avg_neig", "dist_f_avg_neig", "dist_x_cor_neig", "dist_f_cor_neig"]


def _charge(label: str, count: int) -> None:
    if sum(EVALUATIONS.values()) + count > EVALUATION_CAP:
        raise RuntimeError(f"evaluation cap {EVALUATION_CAP} would be exceeded by {label} (+{count})")
    EVALUATIONS[label] += count


def resolve_jmetalpy(name: str):
    import jmetal.problem as flat
    from jmetal.problem.multiobjective import re as re_suite
    for module in (flat, re_suite):
        if hasattr(module, name):
            return getattr(module, name)()
    raise KeyError(name)


def sample_jmetalpy(name: str, seed: int, sample_size: int | None = None) -> tuple[Sample, int, float]:
    """LHS-sample a jMetalPy problem through MOLA's own adapter; returns (sample, evaluations, seconds)."""
    problem = resolve_jmetalpy(name)
    n = sample_size or 200 * problem.number_of_variables()
    _charge(name, n)
    t = time.perf_counter()
    sample = sample_problem(problem, sample_size=n, seed=seed)
    return sample, n, time.perf_counter() - t


def sample_coco(suite_options: str, seed: int, n: int) -> tuple[Sample, int, float, dict]:
    """LHS-sample a COCO bbob-biobj problem over the bounds COCO itself declares."""
    import cocoex
    problem = next(iter(cocoex.Suite("bbob-biobj", "", suite_options)))
    lo, hi = np.asarray(problem.lower_bounds, float), np.asarray(problem.upper_bounds, float)
    _charge(problem.id, n)
    t = time.perf_counter()
    X = qmc.scale(qmc.LatinHypercube(d=problem.dimension, scramble=True, seed=seed).random(n), lo, hi)
    F = np.array([problem(x) for x in X])
    secs = time.perf_counter() - t
    info = {"id": problem.id, "name": problem.name, "dimension": problem.dimension,
            "objectives": problem.number_of_objectives, "lower_bounds": lo.tolist(), "upper_bounds": hi.tolist(),
            "cocoex_version": cocoex.__version__,
            "f_at_origin": [float(v) for v in problem(np.zeros(problem.dimension))]}
    return Sample(problem.id, X, F, lo, hi, "lhs", seed), n, secs, info


def thesis_ratio_terms(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Eq. 4.1 / Listing B.5 of the thesis, term by term: |1 - (smaller/larger)| with min/max by value."""
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(b < a, b / a, a / b)
    return np.abs(1 - r)
