"""Builds research/phase0/feature_contract.csv (semicolon-separated)."""
import csv
import sys

OUT = sys.argv[1]
LSUPP_NOTE = sys.argv[2] if len(sys.argv) > 2 else ""

COLS = ["feature", "class", "thesis21", "moorphology_name", "mola_function", "definition_mola_code",
        "inputs", "uses_neighbour_graph", "measurement_coords", "normalization", "denominator",
        "expected_range", "can_be_negative", "undefined_when", "uniform_X_scaling", "doc_vs_code",
        "moorphology_vs_mola", "provenance"]

G, MM, EV, RU = "mola.features.global_.", "mola.features.multimodality.", "mola.features.evolvability.", "mola.features.ruggedness."
NONE = "none found"
NOTM = "not in moorphology"
RUG_PROV = "Paper 4.1.4 ('Spearman correlation coefficient over each pair of neighbours'); CLAUDE.md Ruggedness per-measure correlation procedure"
RUG_UNDEF = "Constant per-solution measure (zero variance) gives NaN propagated from spearmanr (mola/ruggedness.py:36)."
RUG_DEN = "n*k directed edges (one Spearman), k=min(D,n-1)"

rows = []
def r(**kw):
    missing = [c for c in COLS if c not in kw]
    assert not missing, (kw.get("feature"), missing)
    rows.append(kw)

# ---------------- Global (14) ----------------
r(feature="f_cor", **{"class": "global"}, thesis21="no", moorphology_name="", mola_function=G + "f_cor",
  definition_mola_code="Mean over the C(M,2) objective-column pairs of the signed Spearman correlation between the two columns over all n solutions (one Spearman when M=2).",
  inputs="F", uses_neighbour_graph="no", measurement_coords="none (ranks of raw F)", normalization="none",
  denominator="C(M,2) objective pairs (mean)", expected_range="[-1,1]", can_be_negative="yes",
  undefined_when="A constant objective column gives a NaN pair that np.mean propagates; M=1 gives the mean of an empty list (NaN).",
  uniform_X_scaling="invariant", doc_vs_code=NONE, moorphology_vs_mola=NOTM,
  provenance="Paper 4.1.1/Table 1 f_cor (Spearman); signed mean of pairs for M>2 is a MOLA judgment call (CLAUDE.md f_cor)")

r(feature="dist_x_avg", **{"class": "global"}, thesis21="shared", moorphology_name="distanceXAverage", mola_function=G + "dist_x_avg",
  definition_mola_code="Mean Euclidean X distance over all n(n-1)/2 unordered pairs i<j, max-min normalized with the min and max X distance of those same pairs.",
  inputs="X, normalizer_X", uses_neighbour_graph="no", measurement_coords="raw X", normalization="whole-sample X pairwise range",
  denominator="n(n-1)/2 pairs", expected_range="[0,1]", can_be_negative="no",
  undefined_when="n<2 raises ValueError (distance.py:78); zero range (all pairwise distances equal, e.g. n=2) returns 0.0 (normalization.py:44).",
  uniform_X_scaling="invariant", doc_vs_code=NONE,
  moorphology_vs_mola="Loop j>=i (java:145) adds n zero self-pairs: divisor n(n+1)/2 (java:171) and DIST_X_MIN forced to 0 (java:156), so value = mean*(n-1)/(n+1)/max (formula on the same ZDT1 D=30 sample: 0.644 vs MOLA 0.509).",
  provenance="Paper Table 1 dist_x_avg; max-min rule from CLAUDE.md Normalization reference and thesis ch.4")

r(feature="dist_x_max", **{"class": "global"}, thesis21="shared", moorphology_name="distanceXMaximum", mola_function=G + "dist_x_max",
  definition_mola_code="Maximum Euclidean X distance over all unordered pairs i<j, reported raw.",
  inputs="X", uses_neighbour_graph="no", measurement_coords="raw X", normalization="none",
  denominator="none (max over n(n-1)/2 pairs)", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="n<2 raises ValueError (distance.py:78).",
  uniform_X_scaling="scales by c", doc_vs_code=NONE,
  moorphology_vs_mola="Equivalent: raw max (java:155); the self-pairs from java:145 cannot change a max.",
  provenance="Paper Table 1 dist_x_max; raw per CLAUDE.md *_MAX rule and the thesis ch.4 exception")

r(feature="dist_f_avg", **{"class": "global"}, thesis21="shared", moorphology_name="distanceFAverage", mola_function=G + "dist_f_avg",
  definition_mola_code="Mean Euclidean F distance over all n(n-1)/2 unordered pairs i<j, max-min normalized with the min and max F distance of those same pairs.",
  inputs="F, normalizer_F", uses_neighbour_graph="no", measurement_coords="raw F", normalization="whole-sample F pairwise range",
  denominator="n(n-1)/2 pairs", expected_range="[0,1]", can_be_negative="no",
  undefined_when="n<2 raises ValueError; zero F range returns 0.0 (normalization.py:44).",
  uniform_X_scaling="invariant", doc_vs_code=NONE,
  moorphology_vs_mola="Audit's DIST_F_MIN-from-X bug (java:160) is numerically inert: self-pairs (java:145) force both minima to 0; moorphology = mean_F*(n-1)/(n+1)/max_F (java:172,179).",
  provenance="Paper Table 1 dist_f_avg; CLAUDE.md Normalization reference")

r(feature="dist_f_max", **{"class": "global"}, thesis21="shared", moorphology_name="distanceFMaximum", mola_function=G + "dist_f_max",
  definition_mola_code="Maximum Euclidean F distance over all unordered pairs i<j, reported raw.",
  inputs="F", uses_neighbour_graph="no", measurement_coords="raw F", normalization="none",
  denominator="none (max over n(n-1)/2 pairs)", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="n<2 raises ValueError (distance.py:78).",
  uniform_X_scaling="invariant", doc_vs_code=NONE,
  moorphology_vs_mola="Equivalent: raw max (java:159).",
  provenance="Paper Table 1 dist_f_max; raw per CLAUDE.md *_MAX rule and the thesis ch.4 exception")

r(feature="nd_n", **{"class": "global"}, thesis21="shared", moorphology_name="proportionOfNonDominated", mola_function=G + "nd_n",
  definition_mola_code="Size of front 0 of jMetalPy FastNonDominatedRanking (Pareto dominance, minimization) divided by n.",
  inputs="ranking", uses_neighbour_graph="no", measurement_coords="none", normalization="none",
  denominator="n", expected_range="(0,1]", can_be_negative="no",
  undefined_when="none (a non-empty sample always has a front 0); identical F vectors are mutually non-dominated.",
  uniform_X_scaling="invariant", doc_vs_code=NONE,
  moorphology_vs_mola="Equivalent: getSubFront(0).size()/numSamples (java:325); stored subfront lists are not affected by the rank-attribute overwrite.",
  provenance="Paper 4.1.1/Table 1 nd_n")

r(feature="supp_n", **{"class": "global"}, thesis21="no", moorphology_name="", mola_function=G + "supp_n",
  definition_mola_code="Fraction of ND solutions that are vertices of a ConvexHull facet of the ND objective vectors whose outward normal is <=1e-9 in every component.",
  inputs="F, ranking", uses_neighbour_graph="no", measurement_coords="raw F (hull geometry)", normalization="none",
  denominator="|ND|", expected_range="[0,1]", can_be_negative="no",
  undefined_when="|ND|<=M skips the hull and returns 1.0 (hull.py:36); QhullError (degenerate ND set) also returns 1.0 (hull.py:41).",
  uniform_X_scaling="invariant",
  doc_vs_code="CLAUDE.md's facet 'iff' and '|ND|<=M supported by construction' are inexact for M>=3: (0,10,10),(10,0,10),(6,6,10.1) is masked all-supported though point 3 is not (verified); global sets of ZDT1/DTLZ1/DTLZ2 matched an LP check.",
  moorphology_vs_mola=NOTM,
  provenance="Paper 4.1.1 ('proportion of supported points therein', Ehrgott [10]); both 1.0 fallbacks are MOLA judgment calls (CLAUDE.md supp_n)")

r(feature="hv", **{"class": "global"}, thesis21="no", moorphology_name="", mola_function=G + "hv",
  definition_mola_code="moocore.hypervolume of the ND objective vectors against ref = element-wise max of F over the whole sample (no padding).",
  inputs="F, ranking, ref", uses_neighbour_graph="no", measurement_coords="raw F (volume in F units^M)", normalization="none",
  denominator="none", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="none; ND points attaining ref_m in some objective add zero volume.",
  uniform_X_scaling="invariant", doc_vs_code=NONE, moorphology_vs_mola=NOTM,
  provenance="Paper 4.1.1/Table 1 hv; reference point is a MOLA judgment call (CLAUDE.md hv and shared reference point)")

r(feature="dist_x_nd_avg", **{"class": "global"}, thesis21="shared", moorphology_name="distanceXNonDominatedAverage", mola_function=G + "dist_x_nd_avg",
  definition_mola_code="Mean Euclidean X distance over the C(|ND|,2) pairs of ND solutions, max-min normalized with the whole-sample X pairwise min and max.",
  inputs="X, ranking, normalizer_X", uses_neighbour_graph="no", measurement_coords="raw X", normalization="whole-sample X pairwise range",
  denominator="C(|ND|,2) pairs", expected_range="[0,1]", can_be_negative="no",
  undefined_when="|ND|<2 returns NaN (explicit guard, global_.py:142); zero whole-sample range returns 0.0.",
  uniform_X_scaling="invariant", doc_vs_code=NONE,
  moorphology_vs_mola="ND filter tests i twice (java:163), so it sums pairs (i in ND, any j>=i incl. self) and divides by |ND| not the pair count (java:173), then /max (java:180): can be >>1.",
  provenance="Paper Table 1 dist_x_nd_avg; CLAUDE.md Normalization reference")

r(feature="dist_x_nd_max", **{"class": "global"}, thesis21="shared", moorphology_name="distanceXNonDominatedMaximum", mola_function=G + "dist_x_nd_max",
  definition_mola_code="Maximum Euclidean X distance over the C(|ND|,2) pairs of ND solutions, reported raw.",
  inputs="X, ranking", uses_neighbour_graph="no", measurement_coords="raw X", normalization="none",
  denominator="none (max over C(|ND|,2) pairs)", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="|ND|<2 returns NaN (explicit guard, global_.py:164).",
  uniform_X_scaling="scales by c", doc_vs_code=NONE,
  moorphology_vs_mola="Max over pairs with only i in ND (java:163-165), so it is >= MOLA's and often equals dist_x_max; both raw (java:186) although the thesis text implies normalized.",
  provenance="Paper Table 1 dist_x_nd_max; raw per CLAUDE.md *_MAX rule")

r(feature="fdc", **{"class": "global"}, thesis21="no", moorphology_name="", mola_function=G + "fdc",
  definition_mola_code="Spearman correlation between the pdist X distances and the pdist F distances over the C(|ND|,2) pairs of ND solutions.",
  inputs="X, F, ranking", uses_neighbour_graph="no", measurement_coords="raw X and raw F (pairwise)", normalization="none (rank-based)",
  denominator="C(|ND|,2) pairs", expected_range="[-1,1]", can_be_negative="yes",
  undefined_when="|ND|<=2 (0 or 1 pair) or a constant distance vector gives NaN propagated from spearmanr (verified on length-0/1 input).",
  uniform_X_scaling="invariant",
  doc_vs_code="CLAUDE.md fdc (and global_.py:234) say NaN only when |ND|<2; |ND|=2 (one pair) also yields NaN.",
  moorphology_vs_mola=NOTM,
  provenance="Paper 4.1.1 ('fitness-distance-correlation in [18]'); CLAUDE.md fdc")

r(feature="rank_avg", **{"class": "global"}, thesis21="shared", moorphology_name="rankAverage", mola_function=G + "rank_avg",
  definition_mola_code="Mean over all n solutions of the zero-based global non-dominated-sorting rank (front index).",
  inputs="ranking", uses_neighbour_graph="no", measurement_coords="none", normalization="none",
  denominator="n", expected_range="[0,n-1]", can_be_negative="no",
  undefined_when="none", uniform_X_scaling="invariant", doc_vs_code=NONE,
  moorphology_vs_mola="Same formula, but java:324 reads ranks after the loop and local rankings (java:243-244) share the attribute key, so it averages each solution's last local rank (<=d-1); old audit wrongly called it reliable.",
  provenance="Paper Table 1 rank_avg; zero-based rank is MOLA's convention (global_.py:172)")

r(feature="rank_max", **{"class": "global"}, thesis21="shared", moorphology_name="rankMaximum", mola_function=G + "rank_max",
  definition_mola_code="Maximum zero-based global non-dominated-sorting rank, i.e. number of fronts minus 1.",
  inputs="ranking", uses_neighbour_graph="no", measurement_coords="none", normalization="none",
  denominator="none (max)", expected_range="integer in [0,n-1]", can_be_negative="no",
  undefined_when="none", uniform_X_scaling="invariant", doc_vs_code=NONE,
  moorphology_vs_mola="Same rank overwrite (java:324,326): reports the max of last local ranks, bounded by d-1 (local groups have d members); old audit wrongly called it reliable.",
  provenance="Paper Table 1 rank_max; zero-based rank is MOLA's convention (global_.py:187)")

r(feature="rank_ent", **{"class": "global"}, thesis21="shared", moorphology_name="rankEntropy", mola_function=G + "rank_ent",
  definition_mola_code="Base-2 Shannon entropy of the global front-size proportions |front_r|/n (scipy.stats.entropy).",
  inputs="ranking", uses_neighbour_graph="no", measurement_coords="none", normalization="none",
  denominator="n (front-size proportions)", expected_range="[0,log2(n)]", can_be_negative="no",
  undefined_when="none (0 when all solutions share one front)", uniform_X_scaling="invariant", doc_vs_code=NONE,
  moorphology_vs_mola="Same base-2 formula (java:384-403) but computed over the overwritten local ranks (java:324,328).",
  provenance="Paper Table 1 rank_ent; base 2 is a MOLA judgment call (CLAUDE.md), same base as java:399")

# ---------------- Multimodality (9) ----------------
r(feature="slo_n", **{"class": "multimodality"}, thesis21="no", moorphology_name="", mola_function=MM + "slo_n",
  definition_mola_code="Mean of the n x M mask where i is a local optimum for objective m iff no k-NN neighbour has strictly smaller f_m (= mean over m of |S_m|/n).",
  inputs="F, neighbourhood", uses_neighbour_graph="yes", measurement_coords="none (raw F comparisons)", normalization="none",
  denominator="n*M", expected_range="(0,1]", can_be_negative="no",
  undefined_when="none (each objective's sample minimiser is an SLO, so >=1/n); ties do not break optimality.",
  uniform_X_scaling="invariant", doc_vs_code=NONE, moorphology_vs_mola=NOTM,
  provenance="Paper 4.1.2/Table 1 ('proportion... per objective'); CLAUDE.md Multimodality")

r(feature="slo_dist_avg", **{"class": "multimodality"}, thesis21="no", moorphology_name="", mola_function=MM + "slo_dist_avg",
  definition_mola_code="For each objective m with |S_m|>=2, the X-normalized mean pairwise X distance among S_m, then nanmean over those objectives.",
  inputs="X, F, neighbourhood, normalizer_X", uses_neighbour_graph="yes", measurement_coords="raw X", normalization="whole-sample X pairwise range",
  denominator="C(|S_m|,2) pairs per objective, then #objectives with |S_m|>=2", expected_range="[0,1]", can_be_negative="no",
  undefined_when="NaN if every objective has |S_m|<2 (nanmean of all-NaN); zero range gives 0.0.",
  uniform_X_scaling="invariant", doc_vs_code=NONE, moorphology_vs_mola=NOTM,
  provenance="Paper Table 1 slo_dist_avg; per-objective-then-mean is a MOLA judgment call (CLAUDE.md Multimodality)")

r(feature="slo_dist_max", **{"class": "multimodality"}, thesis21="no", moorphology_name="", mola_function=MM + "slo_dist_max",
  definition_mola_code="For each objective m with |S_m|>=2, the raw max pairwise X distance among S_m, then nanmean over those objectives (a mean of maxima).",
  inputs="X, F, neighbourhood", uses_neighbour_graph="yes", measurement_coords="raw X", normalization="none",
  denominator="#objectives with |S_m|>=2", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="NaN if every objective has |S_m|<2 (nanmean of all-NaN).",
  uniform_X_scaling="scales by c", doc_vs_code="none found (CLAUDE.md documents the mean of per-objective maxima)", moorphology_vs_mola=NOTM,
  provenance="Paper Table 1 slo_dist_max; per-objective-then-mean is a MOLA judgment call (CLAUDE.md Multimodality)")

r(feature="plo_n", **{"class": "multimodality"}, thesis21="no", moorphology_name="", mola_function=MM + "plo_n",
  definition_mola_code="Fraction of solutions with zero k-NN neighbours that Pareto-dominate them (jMetalPy dominance_test).",
  inputs="dominance", uses_neighbour_graph="yes", measurement_coords="none", normalization="none",
  denominator="n", expected_range="(0,1]", can_be_negative="no",
  undefined_when="none (every ND solution is a PLO, so >=nd_n>0)",
  uniform_X_scaling="invariant", doc_vs_code=NONE, moorphology_vs_mola=NOTM,
  provenance="Paper 4.1.2 (PLO = no dominating neighbour); CLAUDE.md Multimodality")

r(feature="plo_dist_avg", **{"class": "multimodality"}, thesis21="no", moorphology_name="", mola_function=MM + "plo_dist_avg",
  definition_mola_code="Mean Euclidean X distance over the C(|PLO|,2) pairs of PLO solutions, max-min normalized with the whole-sample X pairwise range.",
  inputs="X, dominance, normalizer_X", uses_neighbour_graph="yes", measurement_coords="raw X", normalization="whole-sample X pairwise range",
  denominator="C(|PLO|,2) pairs", expected_range="[0,1]", can_be_negative="no",
  undefined_when="|PLO|<2 returns NaN (explicit guard, features/multimodality.py:54); zero range gives 0.0.",
  uniform_X_scaling="invariant", doc_vs_code=NONE, moorphology_vs_mola=NOTM,
  provenance="Paper Table 1 plo_dist_avg; CLAUDE.md Normalization reference")

r(feature="plo_dist_max", **{"class": "multimodality"}, thesis21="no", moorphology_name="", mola_function=MM + "plo_dist_max",
  definition_mola_code="Maximum Euclidean X distance over the C(|PLO|,2) pairs of PLO solutions, reported raw.",
  inputs="X, dominance", uses_neighbour_graph="yes", measurement_coords="raw X", normalization="none",
  denominator="none (max over C(|PLO|,2) pairs)", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="|PLO|<2 returns NaN (explicit guard, features/multimodality.py:75).",
  uniform_X_scaling="scales by c", doc_vs_code=NONE, moorphology_vs_mola=NOTM,
  provenance="Paper Table 1 plo_dist_max; raw per CLAUDE.md *_MAX rule")

r(feature="nd_per_plo", **{"class": "multimodality"}, thesis21="no", moorphology_name="", mola_function=MM + "nd_per_plo",
  definition_mola_code="nd_n divided by plo_n, i.e. |ND|/|PLO|.",
  inputs="ranking, dominance", uses_neighbour_graph="yes", measurement_coords="none", normalization="none",
  denominator="|PLO|", expected_range="(0,1] (ND is a subset of PLO)", can_be_negative="no",
  undefined_when="none (plo_n>0 always)",
  uniform_X_scaling="invariant", doc_vs_code=NONE, moorphology_vs_mola=NOTM,
  provenance="Paper Table 1 parenthetical nd_n/plo_n; CLAUDE.md Multimodality")

r(feature="length_aws", **{"class": "multimodality"}, thesis21="no", moorphology_name="", mola_function=MM + "length_aws",
  definition_mola_code="Mean over min(30,n) distinct starts drawn by default_rng(sample.seed) of the number of moves to the closest dominating k-NN neighbour until none dominates.",
  inputs="walks (F, neighbourhood, seed)", uses_neighbour_graph="yes", measurement_coords="none", normalization="none",
  denominator="number of walks, min(30,n)", expected_range="[0,inf) (mean of integer lengths)", can_be_negative="no",
  undefined_when="none; seed=None makes the start draw non-reproducible.",
  uniform_X_scaling="invariant (same graph and seed)",
  doc_vs_code="characterize.py:195 calls 30 walks 'the paper's own choice', but CLAUDE.md says the paper does not specify the number (MOLA judgment call).",
  moorphology_vs_mola=NOTM,
  provenance="Paper 4.1.2 adaptive walk; min(30,n) uniform starts with the run seed is a MOLA judgment call (CLAUDE.md Multimodality)")

r(feature="eval_aws", **{"class": "multimodality"}, thesis21="no", moorphology_name="", mola_function=MM + "eval_aws",
  definition_mola_code="Mean over the same walks of total neighbour inspections (each step scans closest-first until a dominating neighbour; the last step scans all k).",
  inputs="walks (F, neighbourhood, seed)", uses_neighbour_graph="yes", measurement_coords="none", normalization="none",
  denominator="number of walks, min(30,n)", expected_range="[k,inf) (each walk ends with a full k-neighbour scan)", can_be_negative="no",
  undefined_when="none; seed=None makes the start draw non-reproducible.",
  uniform_X_scaling="invariant (same graph and seed)",
  doc_vs_code="Same '30 is the paper's own choice' docstring claim (characterize.py:195); counts lookups, not evaluate() calls (documented).",
  moorphology_vs_mola=NOTM,
  provenance="Paper Table 1 ('calls to the evaluation function'); counted as lookups per CLAUDE.md Multimodality")

# ---------------- Evolvability (13) ----------------
EVDEN = "k=min(D,n-1) per solution, then mean over n"
r(feature="sup_avg_neig", **{"class": "evolvability"}, thesis21="shared", moorphology_name="averageProportionOfDominatingNeighbours", mola_function=EV + "sup_avg_neig",
  definition_mola_code="Mean over i of (number of k-NN neighbours j that Pareto-dominate i, via jMetalPy dominance_test) / k.",
  inputs="dominance, neighbourhood", uses_neighbour_graph="yes", measurement_coords="none", normalization="none",
  denominator=EVDEN, expected_range="[0,1] (sup+inf+inc=1)", can_be_negative="no",
  undefined_when="none", uniform_X_scaling="invariant", doc_vs_code=NONE,
  moorphology_vs_mola="Compares global ranks, not pairwise dominance (java:223-236), with ranks partly overwritten by earlier local rankings (java:244); getNeighbours yields d-1 neighbours (java:368-373) but divides by d (java:255).",
  provenance="Paper 4.1.3 ('proportions of dominating, dominated, and incomparable neighbours'); CLAUDE.md Neighbourhood definition")

r(feature="inf_avg_neig", **{"class": "evolvability"}, thesis21="shared", moorphology_name="averageProportionOfDominatedNeighbours", mola_function=EV + "inf_avg_neig",
  definition_mola_code="Mean over i of (number of k-NN neighbours j that i Pareto-dominates) / k.",
  inputs="dominance, neighbourhood", uses_neighbour_graph="yes", measurement_coords="none", normalization="none",
  denominator=EVDEN, expected_range="[0,1]", can_be_negative="no",
  undefined_when="none", uniform_X_scaling="invariant", doc_vs_code=NONE,
  moorphology_vs_mola="Counts neighbours with a worse global rank (java:233-234), not dominated ones; same rank-overwrite and d-1 neighbours divided by d (java:256).",
  provenance="Paper 4.1.3; CLAUDE.md Neighbourhood definition")

r(feature="inc_avg_neig", **{"class": "evolvability"}, thesis21="shared", moorphology_name="averageProportionOfIncomparableNeighbours", mola_function=EV + "inc_avg_neig",
  definition_mola_code="Mean over i of (number of k-NN neighbours neither dominating nor dominated by i, identical F included) / k.",
  inputs="dominance, neighbourhood", uses_neighbour_graph="yes", measurement_coords="none", normalization="none",
  denominator=EVDEN, expected_range="[0,1]", can_be_negative="no",
  undefined_when="none", uniform_X_scaling="invariant", doc_vs_code=NONE,
  moorphology_vs_mola="Counts neighbours with equal global rank (java:231-232), so cross-front incomparable pairs are misfiled as sup/inf; same rank-overwrite and d-1/d (java:257).",
  provenance="Paper 4.1.3; CLAUDE.md Neighbourhood definition")

r(feature="lnd_avg_neig", **{"class": "evolvability"}, thesis21="shared", moorphology_name="averageProportionOfLocallyNonDominatedNeighbours", mola_function=EV + "lnd_avg_neig",
  definition_mola_code="Mean over i of (number of neighbours j in N(i) in front 0 of a non-dominated sort of the local group {i} U N(i)) / k.",
  inputs="local, neighbourhood", uses_neighbour_graph="yes", measurement_coords="none", normalization="none",
  denominator=EVDEN, expected_range="[0,1]", can_be_negative="no",
  undefined_when="none", uniform_X_scaling="invariant",
  doc_vs_code="Docstrings (evolvability.py:69, dominance.py:14,101) cite a Design decision 'lnd/lsupp' that CLAUDE.md does not contain.",
  moorphology_vs_mola="Counts neighbours whose rank equals the reference's local rank (java:246-250), not local front 0; audit reads java:248 as global, but the shared attribute key returns the local rank just written (java:244); d-1/d (java:258).",
  provenance="Paper Table 1 lnd_avg_neig; local group {i} U N(i) is a MOLA judgment call (dominance.py:96-98)")

r(feature="lsupp_avg_neig", **{"class": "evolvability"}, thesis21="shared", moorphology_name="averageProportionOfSupportedLocallyNonDominatedNeighbours", mola_function=EV + "lsupp_avg_neig",
  definition_mola_code="Mean over i of (number of locally ND neighbours j on a minimizing ConvexHull facet of the local ND set, via hull.supported_mask) / k.",
  inputs="local, neighbourhood", uses_neighbour_graph="yes", measurement_coords="raw F (hull geometry)", normalization="none",
  denominator=EVDEN + " (not local |ND|)", expected_range="[0,1], <= lnd_avg_neig", can_be_negative="no",
  undefined_when="Local ND sets with <=M points skip the hull (all supported, hull.py:36); QhullError also marks all supported.",
  uniform_X_scaling="invariant",
  doc_vs_code="For M>=3 the facet test (hull.py:44) misses supported points (e.g. a local f3-minimiser) and the |ND|<=M shortcut over-marks: LP-exact vs MOLA RE33 0.788/0.771, DTLZ2 0.408/0.379 (lsupp_impact.py); docstring cites absent 'lnd/lsupp' decision.",
  moorphology_vs_mola="No hull test: counts neighbours ranked worse than the reference's local rank (java:251-252); d-1/d (java:259); JSON key 'Supported' (java:283) vs thesis 'Suported'.",
  provenance="Paper Table 1 lsupp_avg_neig; hull test and denominator k are MOLA judgment calls (evolvability.py:87-98)")

r(feature="dist_x_avg_neig", **{"class": "evolvability"}, thesis21="shared", moorphology_name="neighbourDistanceXAverage", mola_function=EV + "dist_x_avg_neig",
  definition_mola_code="Mean over all n*k directed edges (i, j in N(i)) of the raw Euclidean X distance.",
  inputs="X, neighbourhood", uses_neighbour_graph="yes", measurement_coords="raw X", normalization="none",
  denominator="n*k edges", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="none", uniform_X_scaling="scales by c",
  doc_vs_code="CLAUDE.md (Normalization reference, Feature set) says NEIGH_DIST_X_AVG is max-min normalized by (DIST_X_MIN, DIST_X_MAX); code returns the raw mean (evolvability.py:117, no normalizer at characterize.py:117-119).",
  moorphology_vs_mola="'=' not '+=' (java:217) makes it the last-iterated solution's mean / n (java:262), then /max with min 0 (java:272), so ~0; d-1 neighbours; thesis and moorphology normalize, MOLA does not.",
  provenance="Paper Table 1 dist_x_avg_neig; CLAUDE.md Normalization reference (not followed by the code)")

r(feature="dist_f_avg_neig", **{"class": "evolvability"}, thesis21="shared", moorphology_name="neighbourDistanceFAverage", mola_function=EV + "dist_f_avg_neig",
  definition_mola_code="Mean over all n*k directed edges (neighbours defined in X) of the raw Euclidean F distance.",
  inputs="F, neighbourhood", uses_neighbour_graph="yes", measurement_coords="raw F", normalization="none",
  denominator="n*k edges", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="none", uniform_X_scaling="invariant",
  doc_vs_code="CLAUDE.md says NEIGH_DIST_F_AVG is max-min normalized by (DIST_F_MIN, DIST_F_MAX); code returns the raw mean (evolvability.py:131, characterize.py:120-122).",
  moorphology_vs_mola="'=' not '+=' (java:219), /n (java:263), then /DIST_F_MAX with min 0 (java:273), so ~0; d-1 neighbours; thesis and moorphology normalize, MOLA does not.",
  provenance="Paper Table 1 dist_f_avg_neig; CLAUDE.md Normalization reference (not followed by the code)")

r(feature="dist_f_dist_x_avg_neig", **{"class": "evolvability"}, thesis21="no", moorphology_name="", mola_function=EV + "dist_f_dist_x_avg_neig",
  definition_mola_code="dist_f_avg_neig divided by dist_x_avg_neig (ratio of the two sample-wide raw means, not a mean of per-solution ratios).",
  inputs="F, X, neighbourhood", uses_neighbour_graph="yes", measurement_coords="raw F over raw X", normalization="none",
  denominator="dist_x_avg_neig", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="dist_x_avg_neig==0 raises ZeroDivisionError (Python float division, evolvability.py:147), not NaN.",
  uniform_X_scaling="scales by 1/c",
  doc_vs_code="Inherits the dist_*_avg_neig raw-vs-normalized discrepancy (ratio of raw means).",
  moorphology_vs_mola=NOTM,
  provenance="Paper Table 1 parenthetical formula; CLAUDE.md Evolvability's missing six")

r(feature="diff_f_avg_neig", **{"class": "evolvability"}, thesis21="no", moorphology_name="", mola_function=EV + "diff_f_avg_neig",
  definition_mola_code="Mean over all n*k directed edges of the mean over objectives of |f_m(i)-f_m(j)|.",
  inputs="F, neighbourhood", uses_neighbour_graph="yes", measurement_coords="raw F (per-objective absolute difference)", normalization="none",
  denominator="n*k edges and M objectives", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="none", uniform_X_scaling="invariant", doc_vs_code=NONE, moorphology_vs_mola=NOTM,
  provenance="Paper Table 1 ('average difference per objective with neighbours'); unsigned mean over objectives is a MOLA judgment call (CLAUDE.md)")

r(feature="diff_f_dist_x_avg_neig", **{"class": "evolvability"}, thesis21="no", moorphology_name="", mola_function=EV + "diff_f_dist_x_avg_neig",
  definition_mola_code="diff_f_avg_neig divided by dist_x_avg_neig (ratio of sample-wide raw means).",
  inputs="F, X, neighbourhood", uses_neighbour_graph="yes", measurement_coords="raw F over raw X", normalization="none",
  denominator="dist_x_avg_neig", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="dist_x_avg_neig==0 raises ZeroDivisionError (evolvability.py:182), not NaN.",
  uniform_X_scaling="scales by 1/c",
  doc_vs_code="Inherits the dist_x_avg_neig raw-vs-normalized discrepancy.",
  moorphology_vs_mola=NOTM,
  provenance="Paper Table 1 parenthetical formula; CLAUDE.md Evolvability's missing six")

r(feature="hv_avg_neig", **{"class": "evolvability"}, thesis21="no", moorphology_name="", mola_function=EV + "hv_avg_neig",
  definition_mola_code="Mean over all n solutions of the singleton box hypervolume prod_m max(0, ref_m - f_m(i)), ref = whole-sample max; no neighbourhood is used.",
  inputs="F, ref", uses_neighbour_graph="no", measurement_coords="raw F (volume)", normalization="none",
  denominator="n", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="none (solutions attaining ref_m in any objective score 0)", uniform_X_scaling="invariant",
  doc_vs_code="none found (CLAUDE.md notes the _neig suffix is misleading, FEATURE_ANALYSIS Finding 5)", moorphology_vs_mola=NOTM,
  provenance="Paper Table 1 ('average (single) solution's hypervolume'); singleton box HV is a MOLA judgment call (CLAUDE.md)")

r(feature="hvd_avg_neig", **{"class": "evolvability"}, thesis21="no", moorphology_name="", mola_function=EV + "hvd_avg_neig",
  definition_mola_code="Mean over all n*k directed edges of |hv(i)-hv(j)| using the singleton hypervolumes.",
  inputs="F, neighbourhood, ref", uses_neighbour_graph="yes", measurement_coords="raw F (volume)", normalization="none",
  denominator="n*k edges", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="none", uniform_X_scaling="invariant", doc_vs_code=NONE, moorphology_vs_mola=NOTM,
  provenance="Paper Table 1 hvd_avg_neig; unsigned difference is a MOLA judgment call (CLAUDE.md)")

r(feature="nhv_avg_neig", **{"class": "evolvability"}, thesis21="no", moorphology_name="", mola_function=EV + "nhv_avg_neig",
  definition_mola_code="Mean over i of moocore.hypervolume of the k neighbours' objective vectors (i excluded) against the shared ref.",
  inputs="F, neighbourhood, ref", uses_neighbour_graph="yes", measurement_coords="raw F (volume)", normalization="none",
  denominator="n", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="none", uniform_X_scaling="invariant",
  doc_vs_code="Matrix Notes cite mola.features.nhv_avg_neig (re-export), not the evolvability module; cosmetic.", moorphology_vs_mola=NOTM,
  provenance="Paper Table 1 ('hypervolume from the whole neighbourhood'); excluding i is a MOLA judgment call (CLAUDE.md)")

# ---------------- Ruggedness (13) ----------------
def rug(feature, measure, inputs, coords, thesis="no", mname="", moor=NOTM, doc=NONE, undef=RUG_UNDEF, prov=RUG_PROV):
    r(feature=feature, **{"class": "ruggedness"}, thesis21=thesis, moorphology_name=mname, mola_function=RU + feature,
      definition_mola_code=f"Spearman over all n*k directed edges (i, j in N(i)) of (m(i), m(j)), where m(i) = {measure}.",
      inputs=inputs, uses_neighbour_graph="yes", measurement_coords=coords, normalization="none (rank-based)",
      denominator=RUG_DEN, expected_range="[-1,1]", can_be_negative="yes", undefined_when=undef,
      uniform_X_scaling="invariant", doc_vs_code=doc, moorphology_vs_mola=moor, provenance=prov)

rug("dist_x_cor_neig", "mean raw X distance from i to its k neighbours", "X, neighbourhood", "raw X", thesis="shared",
    mname="neighboursCorrelationOfAverageDistanceX",
    moor="Different statistic: mean over edges of a per-edge Spearman between the endpoints' neighbour-distance vectors, paired by HashSet order (java:291-318); '||' guard (java:301); NaN when d=2 (all edges skipped, 0/0).")
rug("dist_f_cor_neig", "mean raw F distance from i to its k neighbours", "F, neighbourhood", "raw F", thesis="shared",
    mname="neighboursCorrelationOfAverageDistanceF",
    moor="Same per-edge Spearman of HashSet-paired F-distance vectors averaged over edges (java:308-319); same '||' guard and d=2 NaN.")
rug("sup_cor_neig", "dominating-neighbour count / k", "dominance, neighbourhood", "none",
    undef=RUG_UNDEF + " Heavy ties (values in {0,1/k,...,1}) use average ranks.")
rug("inf_cor_neig", "dominated-neighbour count / k", "dominance, neighbourhood", "none",
    undef=RUG_UNDEF + " Heavy ties use average ranks.")
rug("inc_cor_neig", "incomparable-neighbour count / k", "dominance, neighbourhood", "none",
    undef=RUG_UNDEF + " Heavy ties use average ranks.")
rug("lnd_cor_neig", "locally non-dominated neighbour count / k", "local, neighbourhood", "none",
    undef=RUG_UNDEF + " Heavy ties use average ranks.")
rug("lsupp_cor_neig", "locally supported neighbour count / k", "local, neighbourhood", "raw F (hull geometry)",
    doc="Inherits the inexact M>=3 supported test (facet test misses, |ND|<=M shortcut over-marks), see lsupp_avg_neig.",
    undef=RUG_UNDEF + " Hull fallbacks as in lsupp_avg_neig.")
rug("dist_f_dist_x_cor_neig", "mean F distance to neighbours / mean X distance to neighbours (per-solution ratio)", "F, X, neighbourhood", "raw F over raw X",
    undef="Constant measure gives NaN; a solution whose neighbours all coincide in X gives inf or NaN (numpy, no error) and NaN propagates.",
    prov=RUG_PROV + "; ratio-then-correlate is a MOLA judgment call (features/ruggedness.py:140-142)")
rug("diff_f_cor_neig", "mean over neighbours of the mean over objectives of |f_m(i)-f_m(j)|", "F, neighbourhood", "raw F (per-objective absolute difference)")
rug("diff_f_dist_x_cor_neig", "diff_f measure / mean X distance to neighbours (per-solution ratio)", "F, X, neighbourhood", "raw F over raw X",
    undef="Constant measure gives NaN; zero per-solution X distance gives inf or NaN (numpy, no error) and NaN propagates.",
    prov=RUG_PROV + "; ratio-then-correlate is a MOLA judgment call (features/ruggedness.py:179-180)")
rug("hv_cor_neig", "singleton box hypervolume of i against the shared ref", "F, ref, neighbourhood", "raw F (volume)")
rug("hvd_cor_neig", "mean over neighbours of |hv(i)-hv(j)|", "F, neighbourhood, ref", "raw F (volume)")
rug("nhv_cor_neig", "moocore hypervolume of the k neighbours (i excluded)", "F, neighbourhood, ref", "raw F (volume)",
    doc="Matrix Notes cite mola.features.nhv_cor_neig (re-export), not the ruggedness module; cosmetic.")

# ---------------- Thesis-only (2) ----------------
r(feature="dist_x_max_neig", **{"class": "evolvability"}, thesis21="thesis_only", moorphology_name="neighbourDistanceXMaximum", mola_function="",
  definition_mola_code="Not computed by MOLA; moorphology: max over solutions of the mean raw X distance to their d-1 neighbours (java:218).",
  inputs="X, neighbourhood", uses_neighbour_graph="yes", measurement_coords="raw X", normalization="none (reported raw, java:275)",
  denominator="d-1 neighbours (mean), then max over n", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="none", uniform_X_scaling="scales by c",
  doc_vs_code="Not in MOLA (CLAUDE.md: not a paper feature); thesis text says normalized but java:275 reports raw.",
  moorphology_vs_mola="Not in MOLA and must not be added; old audit called it correct, but it averages over d-1 neighbours (off-by-one, java:368-373).",
  provenance="Thesis Table 4.1 (moorphology); absent from paper Table 1, a moorphology invention by analogy (pre-64c88d5 CLAUDE.md)")

r(feature="dist_f_max_neig", **{"class": "evolvability"}, thesis21="thesis_only", moorphology_name="neighbourDistanceFMaximum", mola_function="",
  definition_mola_code="Not computed by MOLA; moorphology: max over solutions of the mean raw F distance to their d-1 X-space neighbours (java:220).",
  inputs="F, neighbourhood", uses_neighbour_graph="yes", measurement_coords="raw F", normalization="none (reported raw, java:277)",
  denominator="d-1 neighbours (mean), then max over n", expected_range="[0,inf)", can_be_negative="no",
  undefined_when="none", uniform_X_scaling="invariant",
  doc_vs_code="Not in MOLA (CLAUDE.md: not a paper feature); thesis text says normalized but java:277 reports raw.",
  moorphology_vs_mola="Not in MOLA and must not be added; old audit called it correct, but it averages over d-1 neighbours (off-by-one, java:368-373).",
  provenance="Thesis Table 4.1 (moorphology); absent from paper Table 1, a moorphology invention by analogy (pre-64c88d5 CLAUDE.md)")

assert len(rows) == 51, len(rows)
assert len({x["feature"] for x in rows}) == 51
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
    w.writeheader()
    w.writerows(rows)
print("rows", len(rows))
print("VERIFY cells", [(x["feature"], c) for x in rows for c in COLS if str(x[c]).startswith("VERIFY")])
print("cells needing quotes", sum(1 for x in rows for c in COLS if ";" in str(x[c])))
