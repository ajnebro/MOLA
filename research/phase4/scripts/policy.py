"""Phase 4 (RQ4, D12): the two-tier recommend-or-fall-back policy, shared by phases 3 and 3c.

Definitions (preregistration.md, section 3):
- the training samples, the training problem means and the query sample are robust-scaled with
  the training samples only (median and IQR per feature; features undefined in any training
  sample or in the query, or with zero IQR, are dropped), as in analyze_transfer._robust_z;
- d: the Euclidean distance from the query sample to the nearest training problem mean;
- the noise distribution of the fold: for every training problem and each of its samples, the
  distance from that sample to the mean of the problem's other samples (5 |T| values);
- s1 = the share of the noise distribution strictly greater than d;
- pi_alpha: knn_selector when s1 >= alpha, the generalist otherwise.
The noise unit (the median distance between two samples of the same training problem) turns d into
noise units, which is how distances are reported.
"""

import itertools

import numpy as np

ALPHA = 0.05
ALPHAS = (0.01, 0.05, 0.10, 0.25)


def scaled(values, sample_problem, train, row):
    """Training samples, their problems, the training means and the query, robust-scaled."""
    train_rows = np.isin(sample_problem, train)
    query = values[row]
    defined = np.isfinite(values[train_rows]).all(axis=0) & np.isfinite(query)
    q75, median, q25 = np.percentile(values[train_rows][:, defined], [75, 50, 25], axis=0)
    iqr = q75 - q25
    keep = np.flatnonzero(defined)[iqr > 0]
    median, iqr = median[iqr > 0], iqr[iqr > 0]
    samples = (values[train_rows][:, keep] - median) / iqr
    owner = sample_problem[train_rows]
    means = np.vstack([samples[owner == p].mean(axis=0) for p in train])
    return samples, owner, means, (query[keep] - median) / iqr


def noise(samples, owner):
    """Leave-one-sample-out distances, and the noise unit (median same-problem pair distance)."""
    loso, pairs = [], []
    for p in np.unique(owner):
        own = samples[owner == p]
        for j in range(len(own)):
            loso.append(np.linalg.norm(own[j] - np.delete(own, j, axis=0).mean(axis=0)))
        pairs += [np.linalg.norm(a - b) for a, b in itertools.combinations(own, 2)]
    return np.asarray(loso), float(np.median(pairs))


def distance_and_s1(values, sample_problem, train, row):
    """D (raw and in noise units), s1, and the index (into train) of the nearest training mean."""
    samples, owner, means, query = scaled(values, sample_problem, train, row)
    distance = np.linalg.norm(means - query, axis=1)
    nearest = int(np.argmin(distance))
    loso, unit = noise(samples, owner)
    d = float(distance[nearest])
    return {
        "d_units": d / unit,
        "s1": float(np.mean(loso > d)),
        "nearest": nearest,
        "unit": unit,
        "loso_p95_units": float(np.percentile(loso, 95) / unit),
    }


def loss_calibrated_threshold(pseudo, epsilon, beta=0.10):
    """Largest distance t (noise units) meeting the loss target among pseudo-targets with d <= t.

    The target is share(loss <= epsilon) >= 1 - beta. `pseudo` holds (d_units, loss) pairs; returns
    0 when no distance qualifies.
    """
    if len(pseudo) == 0:
        return 0.0
    pseudo = np.asarray(sorted(pseudo))
    ok = np.cumsum(pseudo[:, 1] <= epsilon) / np.arange(1, len(pseudo) + 1)
    qualifying = np.flatnonzero(ok >= 1 - beta)
    return float(pseudo[qualifying[-1], 0]) if len(qualifying) else 0.0
