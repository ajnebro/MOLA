import warnings; warnings.filterwarnings("ignore")
import numpy as np, moocore
from jmetal.problem.multiobjective import re as re_mod
from mola.adapters.jmetalpy import sample_problem
from mola.distance import build_neighbourhood
from mola.ranking import rank_solutions
from mola.characterize import characterize
from mola.sample import Sample

names = [n for n in dir(re_mod) if n.startswith("RE") and n[2:].isdigit() and n != "RE91"]
print(f"{'problem':7s} {'D':>3s} {'xrange ratio':>13s} {'frange ratio':>13s} {'kNN overlap':>12s} {'rank==moocore':>13s}")
for name in sorted(names, key=lambda s: int(s[2:])):
    p = getattr(re_mod, name)()
    s = sample_problem(p, seed=42)
    X, F = s.variables, s.objectives
    lo, hi = s.lower_bounds, s.upper_bounds
    xr = (hi - lo); fr = F.max(0) - F.min(0)
    Xn = (X - lo) / xr
    k = s.number_of_variables
    a = build_neighbourhood(X, k).indices; b = build_neighbourhood(Xn, k).indices
    overlap = np.mean([len(set(a[i]) & set(b[i])) / k for i in range(len(X))])
    same = np.array_equal(rank_solutions(F).rank, np.asarray(moocore.pareto_rank(F)))
    print(f"{name:7s} {k:3d} {xr.max()/xr.min():13.1f} {fr.max()/fr.min():13.2e} {overlap:12.2f} {str(same):>13s}")
