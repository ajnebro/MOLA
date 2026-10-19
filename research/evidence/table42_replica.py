import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, cocoex
from scipy.stats import qmc, shapiro
from mola.sample import Sample
from mola.characterize import characterize
prob = next(iter(cocoex.Suite("bbob-biobj", "", "dimensions:2 function_indices:2 instance_indices:2")))
lo, hi = np.full(2, -100.0), np.full(2, 100.0)
rows = []
for seed in range(100):
    X = qmc.scale(qmc.LatinHypercube(d=2, scramble=True, seed=seed).random(400), lo, hi)
    F = np.array([prob(x) for x in X])
    rows.append(characterize(Sample("bbob-biobj_f02_i02_d02", X, F, lo, hi, "lhs", seed)))
df = pd.DataFrame(rows); print("samples with |ND|<2 (ND-subset features undefined):", int(df.dist_x_nd_avg.isna().sum()), "of 100")
thesis = {"sup_avg_neig": (0.25605, 0.00892, "Yes"), "inf_avg_neig": (0.15698, 0.00924, "Yes"),
          "inc_avg_neig": (0.08697, 0.00954, "Yes"), "nd_n": (0.00995, 0.00395, "No"),
          "dist_x_avg_neig": (4.7941e-05, 2.0107e-05, "No"), "dist_f_avg_neig": (8.4385e-05, 8.7613e-05, "No"),
          "dist_x_nd_avg": (61.211, 19.368, "Yes"), "dist_x_nd_max": (171.61, 24.835, "No"),
          "rank_avg": (0.38233, 0.01836, "Yes"), "rank_ent": (0.95865, 0.01253, "Yes")}
print(f"{'feature':16s} {'thesis mean±sd':>22s} {'gauss':>5s} | {'MOLA mean±sd':>22s} {'CV':>6s} {'SW p':>7s}")
for f, (m, s, g) in thesis.items():
    v = df[f].dropna().to_numpy(); p = shapiro(v).pvalue
    print(f"{f:16s} {m:10.4g} ± {s:<9.3g} {g:>5s} | {v.mean():10.4g} ± {v.std(ddof=1):<9.3g} {v.std(ddof=1)/abs(v.mean()):6.1%} {p:7.3f}")
tot = df.sup_avg_neig + df.inf_avg_neig + df.inc_avg_neig
print(f"\nsup+inf+inc  thesis: {0.25605+0.15698+0.08697:.3f}   MOLA: {tot.mean():.3f}")
print(f"|ND| per sample (nd_n*400): mean {df.nd_n.mean()*400:.1f}, values {sorted(set((df.nd_n*400).round().astype(int)))}")
print(f"dist_x_max in MOLA: {df.dist_x_max.mean():.1f} (thesis 270.28)   rank_max values: {sorted(set(df.rank_max))}")
