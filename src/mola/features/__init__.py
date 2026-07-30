"""Landscape feature functions, one module per paper class (Table 1).

Re-exports every implemented feature under `mola.features`, so callers don't need to know which
class module a given feature lives in — `from mola.features import dist_x_avg, sup_avg_neig` reads
the same regardless of how many classes are behind it.
"""

from mola.features.global_ import (
    dist_f_max,
    dist_x_avg,
    dist_x_max,
    nd_n,
    rank_avg,
    rank_ent,
    rank_max,
)

__all__ = [
    "dist_f_max",
    "dist_x_avg",
    "dist_x_max",
    "nd_n",
    "rank_avg",
    "rank_ent",
    "rank_max",
]
