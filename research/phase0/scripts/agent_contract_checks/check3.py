import warnings; warnings.filterwarnings("ignore")
import numpy as np
from scipy.optimize import linprog
import jmetal.problem as P
from mola.adapters.jmetalpy import sample_problem
from mola.ranking import rank_solutions
from mola.hull import supported_mask

def supported_exact(F, tol=1e-9):
    n, m = F.shape; out = np.zeros(n, bool)
    if n == 1: return np.ones(1, bool)
    for i in range(n):
        A = F[i] - np.delete(F, i, axis=0)
        out[i] = linprog(np.zeros(m), A_ub=A, b_ub=np.full(len(A), tol), A_eq=np.ones((1, m)), b_eq=[1], bounds=[(0, None)] * m).status == 0
    return out

for prob in (P.ZDT1(number_of_variables=5), P.DTLZ2(number_of_variables=6), P.DTLZ1(number_of_variables=6)):
    s = sample_problem(prob, seed=7)
    F = s.objectives[rank_solutions(s.objectives).fronts[0]]
    a, b = supported_mask(F), supported_exact(F)
    print(f"{s.problem} M={F.shape[1]} |ND|={len(F)} supp_n MOLA={a.mean():.3f} LP-exact={b.mean():.3f}  MOLA-only={int((a&~b).sum())} LP-only={int((b&~a).sum())}")
