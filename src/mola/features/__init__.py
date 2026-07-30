"""Landscape feature functions, one module per paper class (Table 1).

Re-exports every implemented feature under `mola.features`, so callers don't need to know which
class module a given feature lives in — `from mola.features import dist_x_avg, sup_avg_neig` reads
the same regardless of how many classes are behind it.
"""

from mola.features.evolvability import inc_avg_neig, inf_avg_neig, sup_avg_neig
from mola.features.global_ import (
    dist_f_max,
    dist_x_avg,
    dist_x_max,
    nd_n,
    rank_avg,
    rank_ent,
    rank_max,
)
from mola.features.multimodality import nd_per_plo, plo_dist_avg, plo_dist_max, plo_n

__all__ = [
    "dist_f_max",
    "dist_x_avg",
    "dist_x_max",
    "inc_avg_neig",
    "inf_avg_neig",
    "nd_n",
    "nd_per_plo",
    "plo_dist_avg",
    "plo_dist_max",
    "plo_n",
    "rank_avg",
    "rank_ent",
    "rank_max",
    "sup_avg_neig",
]
