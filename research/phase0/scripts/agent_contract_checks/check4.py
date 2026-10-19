import warnings; warnings.filterwarnings("ignore")
import numpy as np
from collections import Counter
from scipy.optimize import linprog
from scipy.spatial import ConvexHull
from jmetal.problem.multiobjective import re as RE
from mola.adapters.jmetalpy import sample_problem
from mola.distance import build_neighbourhood
from mola.ranking import rank_solutions
from mola.hull import supported_mask

def supported_exact(F, tol=1e-9):
    n, m = F.shape; out = np.zeros(n, bool)
    if n == 1: return np.ones(1, bool)
    for i in range(n):
        A = F[i] - np.delete(F, i, axis=0)
        out[i] = linprog(np.zeros(m), A_ub=A, b_ub=np.full(len(A), tol), A_eq=np.ones((1, m)), b_eq=[1], bounds=[(0, None)] * m).status == 0
    return out

s = sample_problem(RE.RE33(), seed=42)
F, nb = s.objectives, build_neighbourhood(s.variables, s.number_of_variables)
M = F.shape[1]
lp_only, mola_only = Counter(), Counter()
example = None
for i in range(len(F)):
    idx = np.concatenate(([i], nb.indices[i])); nd = np.flatnonzero(rank_solutions(F[idx]).rank == 0)
    sub = F[idx[nd]]
    a, b = supported_mask(sub), supported_exact(sub)
    lp_only[len(sub)] += int((b & ~a).sum()); mola_only[len(sub)] += int((a & ~b).sum())
    if example is None and (b & ~a).any() and len(sub) > M:
        example = sub
print("M", M, "LP-only (missed by MOLA) by local |ND|:", dict(lp_only))
print("MOLA-only (shortcut overcount) by local |ND|:", dict(mola_only))
if example is not None:
    h = ConvexHull(example)
    print("example local ND set:\n", example)
    print("facet normals:\n", np.round(h.equations[:, :-1], 3))
    print("mask", supported_mask(example), "lp", supported_exact(example))
