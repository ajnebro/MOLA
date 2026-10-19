"""Build claims.csv, affectation_matrix.csv and costs.csv from the phase 0 data files.

Observed values are read from ``../data`` where they exist; the textual registers below record what each
check showed. Separator is ';' because cells contain commas.
"""

import csv
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
chk = json.loads((DATA / "checks_results.json").read_text())
pilot = json.loads((DATA / "pilot_summary.json").read_text())
morph = json.loads((DATA / "moorphology_run_summary.json").read_text())
meta = pd.read_csv(DATA / "pilot_meta.csv")
abl = pd.read_csv(DATA / "pilot_ablation.csv")

imp = chk["6.1_supported_impact"]
sc = chk["6.4_scaling"]
ov = meta[meta.variant == "raw"].groupby("problem").graph_overlap_raw_vs_bound.mean().round(2).to_dict()
cv = lambda col: abl.groupby("problem")[col].agg(lambda s: s.std(ddof=1) / abs(s.mean()))  # noqa: E731
cv_eq, cv_plus = cv("moorph_eq_as_shipped"), cv("moorph_pluseq_fixed")
m2, m4 = morph["instr:ZDT1:D2"], morph["instr:ZDT1:D4"]

CLAIMS = [
    ("E1", "supported_mask returns all-supported when |points| <= M; false for M >= 3",
     "plan.md; earlier review", "checks.py 6.1 case A + LP verifier; DTLZ2 and RE33 local sets",
     f"A: MOLA {chk['6.1_supported_cases']['A']['mola']} vs LP {chk['6.1_supported_cases']['A']['weak_supported_lp']}; "
     f"shortcut used by {imp['RE33']['local_sets_using_count_le_M_shortcut']:.1%} of RE33 local ND sets, "
     f"{imp['DTLZ2']['local_sets_using_count_le_M_shortcut']:.1%} in DTLZ2 (14 false positives)",
     "REPRODUCIDO", "supp_n; lsupp_avg_neig; lsupp_cor_neig", "Replace with LP test (phase 1)"),
    ("E2", "Points inside a supported face are not marked supported",
     "earlier review", "checks.py 6.1 case B; RE33 global ND set",
     f"B: MOLA {chk['6.1_supported_cases']['B']['mola']} == extreme-supported {chk['6.1_supported_cases']['B']['extreme_supported_lp']}; "
     f"weak {chk['6.1_supported_cases']['B']['weak_supported_lp']}. RE33 supp_n: MOLA {imp['RE33']['supp_n']['mola']:.3f}, "
     f"extreme {imp['RE33']['supp_n']['extreme_lp']:.3f}, weak {imp['RE33']['supp_n']['weak_lp']:.3f} -> ties are NOT negligible in RE33",
     "REPRODUCIDO", "supp_n; lsupp_avg_neig; lsupp_cor_neig", "Decide definition (weak vs extreme) explicitly; document"),
    ("E3", "Facet test misses supported vertices whose normal cone meets the non-positive orthant without any single facet normal <= 0",
     "this session", "checks.py 6.1 case C; DTLZ2 (n=2400) and RE33 local sets",
     f"C: MOLA {chk['6.1_supported_cases']['C']['mola']} vs LP {chk['6.1_supported_cases']['C']['weak_supported_lp']} (point 4 is the unique f3 minimiser). "
     f"DTLZ2 lsupp_avg_neig MOLA {imp['DTLZ2']['lsupp_avg_neig']['mola']:.3f} vs exact {imp['DTLZ2']['lsupp_avg_neig']['weak']:.3f}; "
     f"{imp['DTLZ2']['local_disagreements_by_kind'].get('false_negative_missed_vertex', 0)} local false negatives on hull vertices; DTLZ2 global supp_n unaffected",
     "REPRODUCIDO", "supp_n; lsupp_avg_neig; lsupp_cor_neig", "Replace with LP test (phase 1)"),
    ("E4", "k-NN graph built on raw decision variables",
     "plan.md", "pilot.py: graph overlap raw vs bound-normalised; checks.py 6.4",
     f"overlap {ov}; graph-only change alters {len(sc['graph_only_bound_normalised']['changed'])} features; fdc NOT among them "
     f"(measurement-only change alters {len(sc['measurement_only_bound_normalised']['changed'])} features incl. fdc)",
     "REPRODUCIDO", "34 neighbourhood-dependent features (graph); 15 X-measured features (coordinates)",
     "Versioned geometry profile (raw | bound) in phase 1; default to be decided"),
    ("E5", "dist_x_avg_neig / dist_f_avg_neig are raw while CLAUDE.md says normalised",
     "plan.md", "code reading features/evolvability.py; feature_contract.csv", "confirmed by reading",
     "CONFIRMADO_EN_CODIGO", "dist_x_avg_neig; dist_f_avg_neig; ratios dist_f_dist_x_*", "Resolve the contract (doc or code) in phase 1"),
    ("E6", "Under uniform X scaling some raw-X features scale; the rest are invariant",
     "plan.md", "checks.py 6.4 uniform c=3.7 and per-variable affine map",
     f"uniform: {sc['uniform_scaling']['classification']}; per-variable affine: raw geometry changes "
     f"{len(sc['affine_raw_geometry']['changed'])} features, bound-normalised geometry changes "
     f"{len(sc['affine_bound_normalised_geometry']['changed_vs_unmapped_normalised'])}",
     "REPRODUCIDO", "see observed", "Use as unit-invariance test in phase 1"),
    ("E7", "Java pom depends on a dead snapshot repository; jMetal 7.8 works",
     "plan.md", "mvn test with empty -Dmaven.repo.local, as-is and -Djmetal.version=7.8 (JDK 24, Maven 3.9.11)",
     "as-is: cannot resolve jmetal-core/jmetal-problem 7.6-SNAPSHOT; 7.8: BUILD SUCCESS, 32 tests pass",
     "REPRODUCIDO", "n/a (build)", "Pin jMetal 7.8 from Maven Central in phase 1"),
    ("E8", "No CI", "plan.md", "no .github/workflows", "absent", "CONFIRMADO_EN_CODIGO", "n/a", "Add CI (pytest, ruff, mvn test) in phase 1"),
    ("E9", "Sample accepts non-finite objectives and degenerate bounds",
     "plan.md", "checks.py 6.5",
     f"NaN/inf accepted; {len(chk['6.5_degenerate']['nonfinite_objectives']['nan_features'])} features silently NaN; "
     f"upper == lower bound accepted",
     "REPRODUCIDO", "all (input validation)", "Reject non-finite input; flag undefined features with a cause"),
    ("E10", "moocore.pareto_rank equals the jMetalPy ranking and is much faster",
     "plan.md", "checks.py 6.6: M in {2,3,5}, random/duplicates/ties/integer grid",
     f"identical in {sum(v['identical'] for v in chk['6.6_moocore_pareto_rank'].values())}/{len(chk['6.6_moocore_pareto_rank'])} cases",
     "REPRODUCIDO", "rank_*; nd_n; every ND-subset feature (performance only)", "Swap ranking backend in phase 1"),
    ("E11", "RE34 == Liao2008 and RE37 == Goel2007 in jMetalPy; Vaidyanathan2004 is the 4-objective RE37",
     "this session", "comparison of committed examples/benchmarks CSVs (seed 42)", "51/51 columns identical for both pairs",
     "REPRODUCIDO", "dataset (72 rows are 70 distinct problems)", "Group in splits; catalogue in protocol.md"),
    ("E12", "moorphology audit bugs (rank comparison, '=' accumulator, ND pair filter, d-1 neighbours, F normaliser)",
     "MOLA history 0eda131, 64c88d5", "executed moorphology master 9d57172 on ZDT1 D=2,4",
     f"sup+inf+inc = {m2['sup_inf_inc_sum']} (D=2), {m4['sup_inf_inc_sum']} (D=4) = (d-1)/d; "
     f"distanceXNonDominatedAverage {m2['distanceXNonDominatedAverage']:.1f} > distanceXMaximum {m2['distanceXMaximum']:.2f}",
     "REPRODUCIDO", "sup/inf/inc; dist_x_nd_*; dist_*_avg_neig; lnd; lsupp", "Affectation matrix; inform authors with exact evidence"),
    ("E13", "moorphology local rankings overwrite the global ranks (jMetal 6.1 attribute key)",
     "this session", "RankOverwriteDemo.java (jMetal 6.1) + instrumented moorphology master run",
     f"demo: global ranks [0 1 2 3] -> [0 1 0 1] after a local ranking on the same objects, intact with copies; "
     f"moorphology ZDT1 D=2: global rank max {m2['phase0_rankMaximumBeforeLoop']} ({m2['phase0_numberOfSubFronts']} fronts) -> reported rankMaximum {m2['rankMaximum']}; "
     f"D=4: {m4['phase0_rankMaximumBeforeLoop']} -> {m4['rankMaximum']}",
     "REPRODUCIDO", "rank_max; rank_avg; rank_ent; sup/inf/inc; lnd; lsupp",
     "PENDING: confirm that master 9d57172 is the version behind the thesis/moody numbers"),
    ("E14", "Neighbour-distance instability in thesis Table 4.2 is caused by the '=' accumulator",
     "this session (table42_replica.py, preserved)", "pilot.py ablation on identical X: moorphology '=' vs '+='",
     f"CV '=': {cv_eq.round(2).to_dict()}; CV '+=': {cv_plus.round(3).to_dict()}",
     "REPRODUCIDO", "dist_x_avg_neig; dist_f_avg_neig",
     "Scope: 5 problems; the general claim 'neighbour distances are the most stable features' remains HIPOTESIS"),
    ("E15", "Thesis metric with MOLA features recognises the same problem after resampling",
     "this session (similarity_analysis.py, preserved)", "pilot.py: ratios (a) within/mean-other, (b) within/nearest-other",
     "see pilot_similarity.csv; (a) and (b) reported separately", "REPRODUCIDO", "similarity",
     "Recognition only; not evidence of transfer; not comparable to the thesis 2.175/5.573"),
    ("E16", "Thesis ratio metric undefined/unbounded with signed values and 0/0",
     "plan.md", "checks.py 6.5", f"terms: {chk['6.5_degenerate']['thesis_ratio_term']}",
     "REPRODUCIDO", "dist_x_cor_neig; dist_f_cor_neig (already in the 21); f_cor; fdc", "Typed distance in phase 3"),
    ("E17", "bbob-biobj search region is [-100,100]^d", "plan.md", "cocoex 2.8.2 lower/upper bounds",
     json.dumps({k: pilot["coco_problem"][k] for k in ("id", "name", "lower_bounds", "upper_bounds")}),
     "REPRODUCIDO", "COCO sampling region", "Use declared bounds"),
    ("E18", "MO-ELA normalises X by bounds, F min-max; 4 sample sizes x 20 seeds; kNN k=1; random 80/20; final model picked on test",
     "arXiv 2602.00098 v1", "document reading", "as stated", "DOCUMENTAL", "positioning", "Treat as controls / baseline"),
    ("E19", "VAMOS default real-coded operators are invariant under per-variable positive affine maps (SBX abs. eps 1e-14 aside)",
     "this session (static audit)", "code reading of VAMOS 1.0.0 @0a8bbb0; spot-checked crossover_sbx.py:173-202 and operator_primitives.py:256-278",
     "SBX, PM, DE, clip repair, uniform/LHS init relative to bounds; non-invariant opt-ins: Gaussian, Cauchy, PCX, round repair",
     "CONFIRMADO_EN_CODIGO", "RQ1 premise", "Verify empirically with a cheap paired run in phase 2"),
    ("E20", "moorphology/jMetal 6.1 LHS sample is not reproducible via JMetalRandom.setSeed",
     "this session", "two runs with setSeed(42)", "different samples (e.g. ZDT1 D=2 rankAverage 0.205 vs 0.235)",
     "REPRODUCIDO", "reproducibility of historical numbers", "Cause is HIPOTESIS (LHS uses its own RNG); historical numbers cannot be regenerated bit-exactly"),
    ("E21", "moorphology neighbour correlations differ from the paper definition",
     "this session", "reading moorphology master lines 286-320",
     "per edge: Spearman between the two neighbour-distance VECTORS (HashSet order, length d-1), averaged; paper/MOLA: Spearman over edges of per-solution mean distance",
     "CONFIRMADO_EN_CODIGO", "dist_x_cor_neig; dist_f_cor_neig", "Not comparable across implementations; add to affectation"),
    ("E23", "At M=2, several ZCAT problems are identical on the sample: {3,4}, {5,17}, {7,18,20}, {8,9}, {12,15}",
     "this session", "pairwise comparison of all 72 committed rows (52 columns, rtol 1e-9)",
     "52/52 columns identical within each group; none among the M=3 rows; 20 ZCAT M=2 rows = 14 distinct functions",
     "REPRODUCIDO", "dataset; FEATURE_ANALYSIS Finding 2 ('dist_f_max distinct = 14' equals the number of distinct functions)",
     "Cause HIPOTESIS: complicated_pareto_set=False collapses problems differing only in g; ZCAT absent from installed jmetalpy 1.9.0, not re-run"),
    ("E24", "Minor documentation/code inconsistencies in MOLA",
     "feature_contract.csv (agent, code reading)", "reading characterize.py, global_.py, CLAUDE.md",
     "fdc is NaN for |ND|<=2 (docs say <2); characterize.py:195 calls 30 walks 'the paper's own choice' while CLAUDE.md marks it a MOLA judgment call; docstrings cite an absent 'lnd/lsupp' design decision",
     "CONFIRMADO_EN_CODIGO", "fdc; length_aws; eval_aws; lnd_avg_neig; lsupp_avg_neig", "Fix docs in phase 1"),
    ("E25", "moorphology's global-distance normalisation differs from MOLA's (self-pairs force min=0; divisor n(n+1)/2)",
     "feature_contract.csv (agent)", "formula from moorphology lines 144-179 applied to one ZDT1 D=30 sample",
     "dist_x_avg: moorphology-style 0.644 vs MOLA 0.509 on the same sample; the 'F normaliser from X distances' bug (line 160) is numerically inert",
     "REPRODUCIDO (by the agent, single sample)", "dist_x_avg; dist_f_avg; dist_x_nd_avg", "Thesis and MOLA values of these features are not directly comparable"),
    ("E22", "Runtime is dominated by local_nondominance and the jMetalPy ranking",
     "plan.md", "pilot.py stage timers", "see pilot_meta.csv t_* columns", "REPRODUCIDO", "performance", "moocore ranking; vectorise local_nondominance"),
]


def write(path: Path, header: list[str], rows: list) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        w.writerow(header)
        w.writerows(rows)


write(ROOT / "claims.csv", ["id", "description", "source", "check_run", "observed", "status", "affected_features", "action"], CLAIMS)

# Affectation: thesis/moody numbers come from moorphology; MOLA CSVs from MOLA 58bc0ca.
M = "moorphology"
AFF = {
    "dist_x_avg": ("DIFFERENT DEFINITION: self-pairs force min=0, divisor n(n+1)/2 (E25; e.g. 0.644 vs MOLA 0.509); audit called it reliable", "same as thesis (moorphology)", "unaffected by bugs; raw-geometry choice (E4) on heterogeneous bounds"),
    "dist_x_max": ("reliable", "same", "raw (by design); scales with units (E6)"),
    "dist_f_avg": ("DIFFERENT DEFINITION as dist_x_avg (E25); the F-normaliser bug is numerically inert", "same", "unaffected"),
    "dist_f_max": ("reliable", "same", "raw (by design)"),
    "nd_n": ("reliable (getSubFront read before overwrite)", "same", "unaffected"),
    "dist_x_nd_avg": ("AFFECTED: pair filter checks i twice; divided by |ND| (E12)", "same", "raw-geometry choice (E4)"),
    "dist_x_nd_max": ("AFFECTED: pair filter (E12)", "same", "raw (by design); raw-geometry choice"),
    "rank_avg": ("AFFECTED: ranks overwritten by local rankings (E13)", "same", "unaffected"),
    "rank_max": ("AFFECTED (E13)", "same", "unaffected"),
    "rank_ent": ("AFFECTED (E13)", "same", "unaffected"),
    "sup_avg_neig": ("AFFECTED: global-rank comparison, overwritten ranks, d-1 neighbours over d (E12, E13)", "same", "raw-geometry choice (graph)"),
    "inf_avg_neig": ("AFFECTED (E12, E13)", "same", "raw-geometry choice (graph)"),
    "inc_avg_neig": ("AFFECTED (E12, E13)", "same", "raw-geometry choice (graph)"),
    "lnd_avg_neig": ("AFFECTED: local vs overwritten global ranks (E12, E13)", "same", "raw-geometry choice (graph)"),
    "lsupp_avg_neig": ("AFFECTED: not a convex-hull test (E12)", "same", "AFFECTED for M>=3 (E1, E3); raw-geometry choice"),
    "dist_x_avg_neig": ("AFFECTED: '=' accumulator (E12, E14)", "same", "raw, contradicts CLAUDE.md (E5)"),
    "dist_f_avg_neig": ("AFFECTED: '=' accumulator (E12, E14)", "same", "raw, contradicts CLAUDE.md (E5)"),
    "dist_x_cor_neig": ("AFFECTED: different definition, arbitrary vector order (E21)", "same", "raw-geometry choice (graph)"),
    "dist_f_cor_neig": ("AFFECTED: different definition (E21)", "same", "raw-geometry choice (graph)"),
    "dist_x_max_neig": ("thesis-only; d-1 neighbours; max of per-sample mean (not a paper feature)", "same", "not computed by MOLA"),
    "dist_f_max_neig": ("thesis-only; d-1 neighbours (not a paper feature)", "same", "not computed by MOLA"),
}
supp_related = {"supp_n": "AFFECTED for M>=3 (E1-E3)", "lsupp_cor_neig": "AFFECTED for M>=3 (E1, E3); raw-geometry choice"}
rows = [[f, "shared" if f not in ("dist_x_max_neig", "dist_f_max_neig") else "thesis_only", *v,
         "E12/E13 evidence by executing moorphology master; link to thesis version pending" if v[0].startswith("AFFECTED") else ""]
        for f, v in AFF.items()]
feats = pd.read_csv(DATA / "pilot_features.csv").columns
graph_dep = set(chk["6.4_scaling"]["graph_only_bound_normalised"]["changed"])
for f in [c for c in feats if c not in ("problem", "seed", "variant", "D", "M", "n") and c not in AFF]:
    mola = supp_related.get(f, "raw-geometry choice (graph)" if f in graph_dep else "unaffected by known bugs")
    rows.append([f, "mola_only", "n/a (not in thesis)", "n/a", mola, ""])
write(ROOT / "affectation_matrix.csv", ["feature", "scope", "thesis_numbers", "moody_kg_zenodo", "mola_committed_csvs", "note"], rows)

COSTS = [
    ("pytest (152 tests)", 0, 18.8, "src+tests at 58bc0ca"),
    ("ruff check", 0, 1.0, "all checks passed"),
    ("mvn test as-is, empty repo", 0, 9, "fails resolving 7.6-SNAPSHOT"),
    ("mvn test jMetal 7.8, empty repo", 0, 63, "32 tests pass; includes downloads"),
    ("checks.py", sum(chk["evaluations_used"].values()), round(chk["wall_seconds"], 1), json.dumps(chk["evaluations_used"])),
    ("moorphology Java runs (orig + instrumented)", 2 * (400 + 800), 3.7, "ZDT1 D=2 (n=400), D=4 (n=800)"),
    ("pilot.py", pilot["evaluations_total"] - sum(chk["evaluations_used"].values()) - 2400, round(pilot["wall_seconds"], 1), "COCO 5x400; RE25/33/42/36 3 x 200D"),
    ("VAMOS static audit (agent)", 0, 404, "reading only"),
    ("feature-contract agent verification scripts", 14_000, None,
     "ZDT1 D5 x3 (3000), ZDT1 D30 (6000), DTLZ2 D6 x2 (2400), DTLZ1 D6 (1200), RE33 (800), DTLZ2 n600 (600); "
     "cap not passed to the agent -> phase total exceeds the 25 000 cap"),
]
write(ROOT / "costs.csv", ["step", "evaluations", "wall_seconds", "notes"], COSTS)
print(f"claims {len(CLAIMS)}; affectation rows {len(rows)}; total evaluations {pilot['evaluations_total']}")
