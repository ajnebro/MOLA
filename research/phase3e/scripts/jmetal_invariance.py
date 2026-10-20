"""Phase 3e: which operators of Evolver's NSGA-II space are invariant to changes of units?

The same check as phase 2 (variables, VAMOS) and phase 3 (objectives, VAMOS), now for jMetal 7.8
through Evolver 2.5: each variant runs with the same seed on a problem and on the same problem in
other units, with every variable i scaled by a_i = 2^k_i (bounds too) or every objective j by
b_j = 2^k_j. Powers of two keep the rescaling exact, so a unit-invariant configuration gives
bit-identical objective vectors (divided by b for the objective test).

Variants: Evolver's default NSGA-II, then every categorical choice of NSGAIIDouble.yaml one at a
time (with mid-range values for its sub-parameters). Problems: ZDT1 and UF1 (D = 30), seeds 1 and
2, 5 000 evaluations.

Run locally:  python research/phase3e/scripts/jmetal_invariance.py  ->  data/jmetal_invariance.csv
"""

import numpy as np
import pandas as pd

from jworker import DEFAULT, PHASE3E, JWorker, command_line

PROBLEMS = {"ZDT1": "ZDT1", "UF1": "UF1(30)"}
SEEDS = (1, 2)
BUDGET = 5_000
CHOICES = {
    ("algorithmResult", "externalArchive"): [
        {"populationSizeWithArchive": "100", "archiveType": a} | ({"knnDistanceArchiveK": "3"} if a == "knnDistanceArchive" else {})
        for a in ("crowdingDistanceArchive", "unboundedArchive", "spatialSpreadDeviationArchive",
                  "knnDistanceArchive", "angleArchive")],
    ("createInitialSolutions", "latinHypercubeSampling"): [{}],
    ("createInitialSolutions", "scatterSearch"): [{}],
    ("createInitialSolutions", "sobol"): [{}],
    ("createInitialSolutions", "cauchy"): [{}],
    ("createInitialSolutions", "oppositionBased"): [{}],
    ("offspringPopulationSize", "1"): [{}],
    ("offspringPopulationSize", "400"): [{}],
    ("crossover", "blxAlpha"): [{"blxAlphaCrossoverAlpha": "0.5"}],
    ("crossover", "wholeArithmetic"): [{}],
    ("crossover", "blxAlphaBeta"): [{"blxAlphaBetaCrossoverBeta": "0.5", "blxAlphaBetaCrossoverAlpha": "0.5"}],
    ("crossover", "arithmetic"): [{}],
    ("crossover", "laplace"): [{"laplaceCrossoverScale": "0.3"}],
    ("crossover", "fuzzyRecombination"): [{"fuzzyRecombinationCrossoverAlpha": "0.5"}],
    ("crossover", "PCX"): [{"pcxCrossoverZeta": "0.1", "pcxCrossoverEta": "0.1"}],
    ("crossover", "UNDC"): [{"undcCrossoverZeta": "0.5", "undcCrossoverEta": "0.35"}],
    ("crossover", "SDX"): [{"sdxCrossoverF": "0.5"}],
    ("crossoverRepairStrategy", "random"): [{}],
    ("crossoverRepairStrategy", "round"): [{}],
    ("mutation", "uniform"): [{"uniformMutationPerturbation": "0.5"}],
    ("mutation", "linkedPolynomial"): [{"linkedPolynomialMutationDistributionIndex": "20.0"}],
    ("mutation", "nonUniform"): [{"nonUniformMutationPerturbation": "0.5"}],
    ("mutation", "levyFlight"): [{"levyFlightMutationBeta": "1.5", "levyFlightMutationStepSize": "0.1"}],
    ("mutation", "powerLaw"): [{"powerLawMutationDelta": "1.0"}],
    ("mutationRepairStrategy", "random"): [{}],
    ("mutationRepairStrategy", "round"): [{}],
    ("selection", "random"): [{}],
    ("selection", "boltzmann"): [{"boltzmannTemperature": "10.0"}],
    ("selection", "ranking"): [{}],
    ("selection", "stochasticUniversalSampling"): [{}],
}
_DROP = {"crossover": ("sbxDistributionIndex",), "mutation": ("polynomialMutationDistributionIndex",),
         "selection": ("selectionTournamentSize",)}


def variants():
    yield "default", dict(DEFAULT)
    for (name, value), extras in CHOICES.items():
        for extra in extras:
            config = {k: v for k, v in DEFAULT.items() if k not in _DROP.get(name, ())}
            config[name] = value
            if name == "algorithmResult":
                # externalArchive's sub-parameters go right after it, in the YAML's order
                config = {"algorithmResult": value, **extra,
                          **{k: v for k, v in config.items() if k != "algorithmResult"}}
            else:
                config.update(extra)
            label = f"{name}={value}" + (f"[{extra['archiveType']}]" if "archiveType" in extra else "")
            yield label, config


def main() -> None:
    rows = []
    with JWorker() as worker:
        for problem, spec in PROBLEMS.items():
            n, m, _, _ = worker.info(spec)
            xs = 2.0 ** np.random.default_rng(7).integers(-4, 5, n)
            fs = 2.0 ** np.random.default_rng(11).integers(-4, 5, m)
            x_spec = spec + "|xscale=" + ",".join(repr(float(a)) for a in xs)
            f_spec = spec + "|fscale=" + ",".join(repr(float(b)) for b in fs)
            for label, config in variants():
                line = command_line(config)
                for seed in SEEDS:
                    row = {"problem": problem, "variant": label, "seed": seed}
                    try:
                        base = worker.run(spec, seed, BUDGET, line, m)
                        in_x = worker.run(x_spec, seed, BUDGET, line, m)
                        in_f = worker.run(f_spec, seed, BUDGET, line, m)
                        row["variable_units_invariant"] = bool(base.shape == in_x.shape and np.array_equal(base, in_x))
                        row["objective_units_invariant"] = bool(base.shape == in_f.shape and np.array_equal(base, in_f / fs))
                    except RuntimeError as error:
                        row["error"] = str(error)[:200]
                    rows.append(row)
    frame = pd.DataFrame(rows)
    (PHASE3E / "data").mkdir(parents=True, exist_ok=True)
    frame.to_csv(PHASE3E / "data" / "jmetal_invariance.csv", index=False)
    summary = frame.groupby("variant")[["variable_units_invariant", "objective_units_invariant"]].agg(
        lambda s: "all" if s.all() else ("none" if not s.any() else "some"))
    print(summary.to_string())
    if "error" in frame:
        print(frame.dropna(subset=["error"])[["variant", "error"]].drop_duplicates().to_string())


if __name__ == "__main__":
    main()
