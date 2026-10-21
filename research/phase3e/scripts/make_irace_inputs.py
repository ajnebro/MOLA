"""Phase 3e irace inputs: Evolver's NSGA-II space without the four non-invariant operators.

1. Evolver generates the irace description of NSGAIIDouble.yaml itself
   (org.uma.evolver.irace.IraceParameterDescriptionGenerator), so names, types and conditions
   are exactly Evolver's.
2. Decision D6 (2026-10-21) removes the operators that broke per-variable unit invariance in
   jMetal 7.8 (data/jmetal_invariance.csv): crossovers PCX, UNDC and Laplace, mutation uniform,
   with their own parameters and every mention in other parameters' conditions.
3. default.txt holds Evolver's default NSGA-II (NSGAIIDoubleDefault.txt) as irace's initial
   candidate, inactive parameters as NA.

Run locally:  python research/phase3e/scripts/make_irace_inputs.py  ->  irace/parameters.txt, default.txt
"""

import re
import subprocess

from jworker import CLASSES, DEFAULT, JAR, JAVA, PHASE3E  # noqa: F401

REMOVED_VALUES = {"crossover": {"PCX", "UNDC", "laplace"}, "mutation": {"uniform"}}
REMOVED_PARAMETERS = {"pcxCrossoverZeta", "pcxCrossoverEta", "undcCrossoverZeta", "undcCrossoverEta",
                      "laplaceCrossoverScale", "uniformMutationPerturbation"}
_VALUES = re.compile(r'\(([^)]*)\)')


def _drop_values(text: str, removed: set[str]) -> str:
    def clean(match: re.Match) -> str:
        values = [v.strip() for v in match.group(1).split(",")]
        kept = [v for v in values if v.strip('"') not in removed]
        return "(" + ", ".join(kept) + ")"

    return _VALUES.sub(clean, text, count=1)


def main() -> None:
    full = subprocess.run([JAVA, "-cp", JAR, "org.uma.evolver.irace.IraceParameterDescriptionGenerator",
                           "NSGAIIDouble.yaml", "Double"], check=True, capture_output=True, text=True).stdout
    lines, names = [], []
    all_removed = set().union(*REMOVED_VALUES.values())
    for line in full.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            lines.append(line)
            continue
        name = line.split()[0]
        if name in REMOVED_PARAMETERS:
            continue
        head, _, condition = line.partition("|")
        if name in REMOVED_VALUES:
            head = _drop_values(head, REMOVED_VALUES[name])
        if condition:
            condition = re.sub(r'c\(([^)]*)\)', lambda m: "c(" + ", ".join(
                v for v in (x.strip() for x in m.group(1).split(",")) if v.strip('"') not in all_removed) + ")",
                condition)
            line = head.rstrip() + " |" + condition
        else:
            line = head.rstrip()
        lines.append(line)
        names.append(name)
    for removed in all_removed:
        if any(f'"{removed}"' in line for line in lines):
            raise ValueError(f"{removed} still appears in the parameter file")
    out = PHASE3E / "irace"
    out.mkdir(parents=True, exist_ok=True)
    (out / "parameters.txt").write_bytes(("\n".join(lines) + "\n").encode())
    default = [DEFAULT.get(n, "NA") for n in names]
    (out / "default.txt").write_bytes((" ".join(names) + "\n" + " ".join(default) + "\n").encode())
    (out / "parameters-evolver-full.txt").write_bytes(full.replace("\r\n", "\n").encode())
    print(f"{len(names)} parameters kept")


if __name__ == "__main__":
    main()
