"""Python client of the Java RunWorker (phase 3e: the Evolver/jMetal replication of phase 3).

A JWorker owns one RunWorker JVM and sends it one request at a time over its standard input, so
each JVM serves runs strictly in sequence and jMetal's global random generator is never shared.
Parallelism comes from running several JWorkers.

Environment: MOLA_EVOLVER_JAR (Evolver 2.5 fat jar), MOLA_PHASE3E_CLASSES (compiled RunWorker),
JAVA (the java executable).
"""

import os
import subprocess
from pathlib import Path

import numpy as np

JAR = os.environ.get("MOLA_EVOLVER_JAR", r"C:\tmp\evolver-2.5\target\Evolver-2.5-jar-with-dependencies.jar")
CLASSES = os.environ.get("MOLA_PHASE3E_CLASSES", r"C:\tmp\phase3e\classes")
JAVA = os.environ.get("JAVA", r"C:\Program Files\Eclipse Adoptium\jdk-24.0.2.12-hotspot\bin\java.exe")

# Evolver's default NSGA-II configuration (src/main/resources/defaultConfigurations/
# NSGAIIDoubleDefault.txt), the textbook setting of the NSGAIIDouble.yaml space.
DEFAULT = {"algorithmResult": "population", "createInitialSolutions": "default",
           "variation": "crossoverAndMutationVariation", "offspringPopulationSize": "100",
           "crossover": "SBX", "crossoverProbability": "0.9", "crossoverRepairStrategy": "bounds",
           "sbxDistributionIndex": "20.0", "mutation": "polynomial",
           "mutationProbabilityFactor": "1.0", "mutationRepairStrategy": "bounds",
           "polynomialMutationDistributionIndex": "20.0", "selection": "tournament",
           "selectionTournamentSize": "2"}


def command_line(config: dict[str, str]) -> str:
    return " ".join(f"--{k} {v}" for k, v in config.items())


class JWorker:
    """One RunWorker process; not thread-safe (one request at a time)."""

    def __init__(self) -> None:
        classpath = os.pathsep.join([JAR, CLASSES])
        self.process = subprocess.Popen([JAVA, "-cp", classpath, "org.uma.mola.phase3e.RunWorker"],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                                        bufsize=1, encoding="utf-8")

    def _ask(self, *fields) -> list[str]:
        self.process.stdin.write("\t".join(str(f) for f in fields) + "\n")
        self.process.stdin.flush()
        reply = self.process.stdout.readline().rstrip("\n").split("\t")
        if not reply or reply[0] != "OK":
            raise RuntimeError(f"RunWorker: {' '.join(reply)} (request {fields[0]} {fields[1]})")
        return reply[1:]

    def info(self, spec: str) -> tuple[int, int, np.ndarray, np.ndarray]:
        n, m, lower, upper = self._ask("INFO", spec)
        return int(n), int(m), np.array(lower.split(","), float), np.array(upper.split(","), float)

    def evaluate(self, spec: str, variables: np.ndarray, n_obj: int) -> np.ndarray:
        values = ",".join(repr(float(v)) for v in np.asarray(variables, float).ravel())
        (objectives,) = self._ask("EVAL", spec, len(variables), values)
        return np.array(objectives.split(","), float).reshape(len(variables), n_obj)

    def run(self, spec: str, seed: int, max_evaluations: int, config: str, n_obj: int) -> np.ndarray:
        rows, objectives = self._ask("RUN", spec, seed, max_evaluations, config)
        return np.array(objectives.split(","), float).reshape(int(rows), n_obj)

    def close(self) -> None:
        self.process.stdin.close()
        self.process.wait(timeout=30)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


PHASE3E = Path(__file__).resolve().parents[1]
