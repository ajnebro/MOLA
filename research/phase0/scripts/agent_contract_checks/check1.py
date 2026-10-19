import warnings; warnings.filterwarnings("ignore")
import dataclasses, numpy as np
from scipy.stats import spearmanr
from mola.hull import supported_mask
from mola.ranking import rank_solutions
from mola.characterize import characterize
from mola.adapters.jmetalpy import sample_problem
import jmetal.problem as P

for n in (0, 1, 2):
    try:
        print("spearman len", n, spearmanr(np.arange(n, dtype=float), np.arange(n, dtype=float)[::-1]).statistic)
    except Exception as e:
        print("spearman len", n, "raises", type(e).__name__, e)

F = np.array([[0, 10, 10], [10, 0, 10], [6, 6, 10.1]], float)
print("ranks", rank_solutions(F).rank, "mask", supported_mask(F))

# python float / 0.0
try:
    print(float(np.float64(1.0).mean()) / float(0.0))
except Exception as e:
    print("float div:", type(e).__name__)

for prob in (P.ZDT1(number_of_variables=5), P.DTLZ2(number_of_variables=6)):
    s = sample_problem(prob, seed=7)
    c = 3.0
    sx = dataclasses.replace(s, variables=s.variables * c, lower_bounds=s.lower_bounds * c, upper_bounds=s.upper_bounds * c)
    a, b = characterize(s), characterize(sx)
    print(s.problem, "n", s.size, "D", s.number_of_variables, "M", s.number_of_objectives)
    for key in a:
        va, vb = a[key], b[key]
        if np.isnan(va) and np.isnan(vb): tag = "both NaN"
        elif np.isclose(va, vb, rtol=1e-9, atol=1e-12): tag = "invariant"
        elif np.isclose(vb, c * va, rtol=1e-9): tag = "x c"
        elif np.isclose(vb, va / c, rtol=1e-9): tag = "x 1/c"
        else: tag = f"OTHER {va} -> {vb}"
        print(f"  {key:24s} {va: .6g}  {tag}")
