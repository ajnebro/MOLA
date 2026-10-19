import sys, glob, numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1]); from thesis_metric import THESIS, ratio_terms
df = pd.concat([pd.read_csv(f) for f in glob.glob(sys.argv[2] + "/*_features.csv")], ignore_index=True)
X = df[THESIS].to_numpy(float)
print("problems:", len(df))
print("feature values == 0 :", {c: int((df[c] == 0).sum()) for c in THESIS if (df[c] == 0).any()})
print("feature values < 0  :", {c: int((df[c] < 0).sum()) for c in THESIS if (df[c] < 0).any()})
print("feature values NaN  :", {c: int(df[c].isna().sum()) for c in THESIS if df[c].isna().any()})
n = len(df); nan_pairs = 0; gt1 = 0; total = 0
for i in range(n):
    for j in range(i + 1, n):
        t = ratio_terms(X[i], X[j]); total += 1
        nan_pairs += np.isnan(t).any() or np.isinf(t).any()
        gt1 += (t[np.isfinite(t)] > 1).any()
print(f"pairs: {total}  pairs with NaN/inf distance: {nan_pairs}  pairs with a term > 1 (sign flip): {gt1}")
