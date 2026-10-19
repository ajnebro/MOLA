import warnings; warnings.filterwarnings("ignore")
import numpy as np
from mola.adapters.jmetalpy import sample_problem
from mola.distance import pairwise_distance_stats
import jmetal.problem as P
for d in (5, 30):
    s = sample_problem(P.ZDT1(number_of_variables=d), seed=1)
    n = s.size
    for name, pts in (("X", s.variables), ("F", s.objectives)):
        st = pairwise_distance_stats(pts)
        mola = (st.mean - st.minimum) / (st.maximum - st.minimum)
        moor = st.mean * (n - 1) / (n + 1) / st.maximum   # j>=i loop: min=0, divisor n(n+1)/2
        print(f"ZDT1 D={d} n={n} {name}: min/max={st.minimum/st.maximum:.3f}  MOLA={mola:.4f}  moorphology-style={moor:.4f}")
