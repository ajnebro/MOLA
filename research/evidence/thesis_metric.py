import numpy as np
# Thesis Table 4.1 / Listing B.5 features available in MOLA (the two dist_*_max_neig are not paper features).
THESIS = ["dist_x_avg","dist_x_max","dist_f_avg","dist_f_max","nd_n","dist_x_nd_avg","dist_x_nd_max",
          "rank_avg","rank_max","rank_ent","sup_avg_neig","inf_avg_neig","inc_avg_neig","lnd_avg_neig",
          "lsupp_avg_neig","dist_x_avg_neig","dist_f_avg_neig","dist_x_cor_neig","dist_f_cor_neig"]

def ratio_terms(a, b):
    """Equation 4.1 / Listing B.5 term by term: |1 - min/max| (min/max taken by value, as in the SPARQL)."""
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(b < a, b / a, a / b)
    return np.abs(1 - r)
