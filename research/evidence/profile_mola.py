import time
import numpy as np
from jmetal.problem import ZDT1
from mola.adapters.jmetalpy import sample_problem
from mola.distance import build_neighbourhood
from mola.ranking import rank_solutions
from mola.dominance import neighbourhood_dominance, local_nondominance
from mola.normalization import build_normalizers
from mola.hypervolume import reference_point, neighbourhood_hypervolume
from mola.multimodality import adaptive_walks
from mola.characterize import characterize

for d in (10, 30):
    t = time.perf_counter(); s = sample_problem(ZDT1(d), seed=1); print(f"D={d} n={s.size} sample {time.perf_counter()-t:.1f}s")
    X, F = s.variables, s.objectives
    def tm(name, f):
        t = time.perf_counter(); r = f(); print(f"  {name:26s} {time.perf_counter()-t:6.2f}s"); return r
    nb = tm("build_neighbourhood", lambda: build_neighbourhood(X, d))
    tm("rank_solutions (jMetalPy)", lambda: rank_solutions(F))
    tm("neighbourhood_dominance", lambda: neighbourhood_dominance(F, nb))
    tm("local_nondominance", lambda: local_nondominance(F, nb))
    tm("build_normalizers", lambda: build_normalizers(X, F))
    ref = reference_point(F)
    tm("neighbourhood_hypervolume", lambda: neighbourhood_hypervolume(F, nb, ref))
    tm("adaptive_walks", lambda: adaptive_walks(F, nb, seed=1))
    tm("characterize TOTAL", lambda: characterize(s))
    import moocore
    tm("moocore.pareto_rank", lambda: moocore.pareto_rank(F))
