import sys, numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1]); from thesis_metric import THESIS, ratio_terms
df = pd.read_csv(sys.argv[2]); labels = df["problem"].to_numpy()
ALL = [c for c in df.columns if c not in ("problem","seed","sample_size","num_obj","num_var")]
n = len(df)

def ratio_dist(X):
    D = np.zeros((n, n)); C = np.zeros((n, n, X.shape[1]))
    for i in range(n):
        for j in range(n):
            t = ratio_terms(X[i], X[j]); t = np.nan_to_num(t, nan=0.0); C[i, j] = t; D[i, j] = t.sum()
    return D, C

def zeuclid(X):
    Z = (X - X.mean(0)) / np.where(X.std(0) > 0, X.std(0), 1)
    return np.linalg.norm(Z[:, None] - Z[None], axis=2)

def report(name, D):
    np.fill_diagonal(D, np.inf); nn = D.argmin(1); acc = (labels[nn] == labels).mean()
    np.fill_diagonal(D, np.nan)
    same = np.array([[labels[i] == labels[j] for j in range(n)] for i in range(n)])
    within = np.nanmean(np.where(same, D, np.nan)); between = np.nanmean(np.where(~same, D, np.nan))
    # per sample: is every same-problem sample closer than every other-problem sample?
    sep = np.mean([np.nanmax(np.where(same[i], D[i], np.nan)) < np.nanmin(np.where(~same[i], D[i], np.nan)) for i in range(n)])
    print(f"{name:34s} 1-NN same problem: {acc:5.0%}   within/between mean: {within:6.2f}/{between:6.2f} = {within/between:.2f}   fully separated: {sep:4.0%}")
    return nn

X = df[THESIS].to_numpy(float)
D, C = ratio_dist(X)
nn = report("thesis ratio metric, 19 features", D.copy())
report("z-score Euclidean, same 19", zeuclid(X))
report("z-score Euclidean, all 49", zeuclid(df[ALL].to_numpy(float)))
noX = [c for c in THESIS if not c.startswith("dist_x")]
report("thesis ratio, without dist_x_* (14)", ratio_dist(df[noX].to_numpy(float))[0])
print("\nmisidentified by the thesis metric (sample -> nearest):")
for i in range(n):
    if labels[nn[i]] != labels[i]: print(f"  {labels[i]} seed {df.seed[i]} -> {labels[nn[i]]} seed {df.seed[nn[i]]}")
same = np.array([[labels[i] == labels[j] and i != j for j in range(n)] for i in range(n)])
noise = C[same].mean(0)
print("\nshare of the resampling-noise distance (same problem, different seed) per feature:")
for f, v in sorted(zip(THESIS, noise / noise.sum()), key=lambda t: -t[1])[:6]: print(f"  {f:18s} {v:5.1%}")
