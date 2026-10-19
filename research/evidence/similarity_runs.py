"""Characterize ZDT/DTLZ with several seeds using MOLA; save the feature rows."""
import sys, time, warnings; warnings.filterwarnings("ignore")
import pandas as pd
import jmetal.problem as P
from mola.adapters.jmetalpy import sample_problem
from mola.characterize import characterize

out = sys.argv[1]
names = ["ZDT1", "ZDT2", "ZDT3", "ZDT4", "ZDT6"] + [f"DTLZ{i}" for i in range(1, 8)]
rows = []
for name in names:
    for seed in (1, 2, 3):
        t = time.perf_counter()
        s = sample_problem(getattr(P, name)(), seed=seed)
        rows.append({"problem": name, "seed": seed, **characterize(s)})
        print(f"{name} seed={seed} D={s.number_of_variables} {time.perf_counter()-t:.1f}s", flush=True)
pd.DataFrame(rows).to_csv(out, index=False)
