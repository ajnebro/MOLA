import warnings; warnings.filterwarnings("ignore")
import numpy as np
from scipy.optimize import linprog
import jmetal.problem as P
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

for prob in [RE.RE33(), RE.RE61(), P.DTLZ2()]:
    s = sample_problem(prob, sample_size=600 if prob.number_of_variables() > 6 else None, seed=42)
    F, nb = s.objectives, build_neighbourhood(s.variables, s.number_of_variables)
    M = s.number_of_objectives; shortcut = 0; mola_cnt = exact_cnt = 0
    for i in range(len(F)):
        idx = np.concatenate(([i], nb.indices[i])); nd = np.flatnonzero(rank_solutions(F[idx]).rank == 0)
        sub = F[idx[nd]]; shortcut += len(nd) <= M
        a, b = supported_mask(sub), supported_exact(sub)
        mola_cnt += a[nd != 0].sum(); exact_cnt += b[nd != 0].sum()
    k = nb.size; n = len(F)
    print(f"{s.problem:6s} M={M} n={n} k={k}: local ND sets taking the 'count<=M' shortcut: {shortcut/n:5.1%}   lsupp_avg_neig MOLA {mola_cnt/(n*k):.3f} vs exact {exact_cnt/(n*k):.3f}")
