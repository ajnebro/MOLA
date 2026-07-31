"""Internal critical analysis of the 49-feature set, over the committed benchmark CSVs.

Every number quoted in `FEATURE_ANALYSIS.md` is produced by this script, so the analysis stays
reproducible and re-checkable when the underlying data changes. This is also the first concrete
instance of the "benchmark diversity and redundancy" use case (`USE_CASES.md` §2.2).

The analysis is *internal*: it takes the paper's feature set as given and asks how it behaves when
applied outside the setting it was designed for (bi-objective MO-ICOPs on a shared variable space).
It is not a critique of the paper's own results.

Run directly, from the repository root:

    python examples/benchmarks/analyze_feature_set.py
"""

import glob
import re
from pathlib import Path

import numpy as np
import pandas as pd

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_DIR = REPOSITORY_ROOT / "examples" / "benchmarks"
ORCHESTRATOR = REPOSITORY_ROOT / "src" / "mola" / "characterize.py"
METADATA_COLUMNS = ["problem", "suite", "sample_size", "num_obj", "num_var"]

# Features computed purely from the decision-variable sample: no objective value ever enters them.
VARIABLE_SPACE_ONLY = ["dist_x_avg", "dist_x_max", "dist_x_avg_neig", "dist_x_cor_neig"]


def load_benchmark_features() -> pd.DataFrame:
    """Concatenate every committed benchmark CSV, tagging each row with its suite."""
    frames = []
    for path in sorted(glob.glob(str(BENCHMARK_DIR / "*_features.csv"))):
        frame = pd.read_csv(path)
        frame["suite"] = Path(path).name.replace("_features.csv", "")
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def feature_columns(data: pd.DataFrame) -> list[str]:
    """The 49 landscape-feature column names, excluding metadata."""
    return [column for column in data.columns if column not in METADATA_COLUMNS]


def report_neighbourhood_dependence() -> None:
    """Count how many features derive from the k=D neighbourhood graph, read from the source."""
    source = ORCHESTRATOR.read_text()
    entries = re.findall(r'"(\w+)": features\.\w+\((.*?)\),\n', source, re.S)
    derived = [
        name
        for name, arguments in entries
        if any(key in arguments for key in ("neighbourhood=", "dominance=", "local=", "walks="))
    ]
    free = [name for name, _ in entries if name not in derived]
    print(f"neighbourhood-derived features: {len(derived)} of {len(entries)}")
    print(f"neighbourhood-free features   : {len(free)}")
    print(f"  {free}")
    print("  note: hv_avg_neig carries a _neig suffix but takes no neighbourhood argument.")


def report_algebraic_redundancy(data: pd.DataFrame) -> None:
    """Check the features that Table 1 defines as ratios of other features."""
    reconstructions = {
        "dist_f_dist_x_avg_neig": data.dist_f_avg_neig / data.dist_x_avg_neig,
        "diff_f_dist_x_avg_neig": data.diff_f_avg_neig / data.dist_x_avg_neig,
        "nd_per_plo": data.nd_n / data.plo_n,
    }
    for name, reconstructed in reconstructions.items():
        error = np.nanmax(np.abs(data[name] - reconstructed))
        print(f"  {name:24s} max |actual - reconstructed| = {error:.3e}")


def report_correlation_redundancy(data: pd.DataFrame, threshold: float = 0.95) -> None:
    """List feature pairs whose absolute Spearman correlation exceeds `threshold`."""
    features = feature_columns(data)
    correlation = data[features].corr(method="spearman").abs()
    pairs = [
        (a, b, correlation.loc[a, b])
        for index, a in enumerate(features)
        for b in features[index + 1 :]
        if correlation.loc[a, b] > threshold
    ]
    pairs.sort(key=lambda pair: -pair[2])
    total = len(features) * (len(features) - 1) // 2
    print(f"  {len(pairs)} of {total} pairs above |rho| = {threshold}")
    for a, b, value in pairs[:8]:
        print(f"    {value:.4f}  {a:24s} ~ {b}")


def report_effective_dimensionality(data: pd.DataFrame) -> None:
    """Report how many principal components span the feature set's variance."""
    complete = data[feature_columns(data)].dropna(axis=1)
    standardized = (complete - complete.mean()) / complete.std().replace(0, 1)
    standardized = standardized.dropna(axis=1)
    values = standardized.to_numpy()
    _, singular_values, _ = np.linalg.svd(values - values.mean(axis=0), full_matrices=False)
    explained = np.cumsum(singular_values**2 / (singular_values**2).sum())
    print(f"  {standardized.shape[1]} usable feature columns")
    for count in (1, 2, 3, 5, 10):
        print(
            f"    first {count:2d} PCs explain {explained[count - 1] * 100:5.1f}% of the variance"
        )


def report_variable_space_only_features(data: pd.DataFrame) -> None:
    """Show that X-only features are constant across problems sharing a sampling design."""
    zcat = data[data.suite == "zcat_2obj"]
    dimension = int(zcat.num_var.iloc[0])
    # ZCAT bounds are [-0.5*i, +0.5*i] for i = 1..D, so the box diagonal is sqrt(sum i^2).
    diagonal = np.sqrt(sum(i**2 for i in range(1, dimension + 1)))
    print(f"  across the {len(zcat)} ZCAT problems at M=2, D={dimension}:")
    for column in VARIABLE_SPACE_ONLY:
        distinct = zcat[column].nunique()
        print(f"    {column:20s} distinct = {distinct}  ({zcat[column].iloc[0]:.6f})")
    contrast = zcat.dist_f_max.nunique()
    print(f"    {'dist_f_max':20s} distinct = {contrast}  (objective-space contrast)")
    print(f"  box diagonal (analytic) = {diagonal:.4f}, dist_x_max = {zcat.dist_x_max.iloc[0]:.4f}")
    print(f"  ratio = {zcat.dist_x_max.iloc[0] / diagonal:.4f}")


def report_dimension_coupling(data: pd.DataFrame) -> None:
    """Measure how strongly each feature tracks D or M on its own."""
    rows = []
    for column in feature_columns(data):
        subset = data[[column, "num_var", "num_obj"]].dropna()
        if subset[column].nunique() < 3:
            continue
        against_d = abs(subset[column].corr(subset.num_var, method="spearman"))
        against_m = abs(subset[column].corr(subset.num_obj, method="spearman"))
        rows.append((column, against_d, against_m))
    rows.sort(key=lambda row: -max(row[1], row[2]))
    strong = sum(1 for _, against_d, against_m in rows if max(against_d, against_m) > 0.5)
    print(f"  {strong} of {len(rows)} features reach |rho| > 0.5 against D or M alone")
    for column, against_d, against_m in rows[:5]:
        print(f"    {column:24s} |rho| vs D = {against_d:.3f}   |rho| vs M = {against_m:.3f}")


def report_walk_degeneracy(data: pd.DataFrame) -> None:
    """Report the range actually covered by the adaptive-walk and local-optima features."""
    for column in ("length_aws", "eval_aws", "slo_n", "plo_n"):
        values = data[column]
        print(
            f"  {column:12s} min={values.min():7.3f}  median={values.median():7.3f}  "
            f"max={values.max():7.3f}"
        )
    lengths = data.length_aws
    zero, below_one = (lengths == 0).sum(), (lengths < 1).sum()
    print(f"  length_aws is exactly 0 for {zero} problems, below 1 for {below_one}")


def report_missing_values(data: pd.DataFrame) -> None:
    """Identify features that are undefined for some problems, and why."""
    for column in feature_columns(data):
        missing = data[column].isna().sum()
        if missing:
            affected = data.loc[data[column].isna(), "problem"].tolist()
            print(f"  {column:24s} undefined for {missing} problem(s): {affected}")


def main() -> None:
    """Run every analysis block over the committed benchmark CSVs."""
    data = load_benchmark_features()
    suites, features = data.suite.nunique(), len(feature_columns(data))
    print(f"{len(data)} problems from {suites} suites, {features} features\n")

    blocks = [
        (
            "1. Neighbourhood dependence (read from the orchestrator source)",
            lambda: report_neighbourhood_dependence(),
        ),
        ("2. Exact algebraic redundancy", lambda: report_algebraic_redundancy(data)),
        ("3. Correlation redundancy", lambda: report_correlation_redundancy(data)),
        ("4. Effective dimensionality", lambda: report_effective_dimensionality(data)),
        ("5. Variable-space-only features", lambda: report_variable_space_only_features(data)),
        ("6. Coupling to problem dimensions", lambda: report_dimension_coupling(data)),
        ("7. Adaptive-walk and local-optima range", lambda: report_walk_degeneracy(data)),
        ("8. Undefined values", lambda: report_missing_values(data)),
    ]
    for title, block in blocks:
        print(f"=== {title} ===")
        block()
        print()


if __name__ == "__main__":
    main()
