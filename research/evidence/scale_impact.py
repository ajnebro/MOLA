import warnings; warnings.filterwarnings("ignore")
import dataclasses, numpy as np
from jmetal.problem.multiobjective import re as re_mod
from mola.adapters.jmetalpy import sample_problem
from mola.characterize import characterize

feats = ["sup_avg_neig","inc_avg_neig","plo_n","slo_n","lnd_avg_neig","fdc","dist_f_cor_neig","hv_cor_neig"]
for name in ["RE25","RE33","RE42"]:
    s = sample_problem(getattr(re_mod, name)(), seed=42)
    lo, hi = s.lower_bounds, s.upper_bounds
    sx = dataclasses.replace(s, variables=(s.variables-lo)/(hi-lo), lower_bounds=np.zeros_like(lo), upper_bounds=np.ones_like(hi))
    a, b = characterize(s), characterize(sx)
    print(name, "  ".join(f"{f}: {a[f]:.3f}->{b[f]:.3f}" for f in feats))
