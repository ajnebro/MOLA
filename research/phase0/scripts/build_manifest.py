"""Write manifest.json: versions, provenance and SHA-256 of every phase 0 artefact and input."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # research/phase0
REPO = ROOT.parents[1]
env = json.loads((ROOT / "data" / "environment.json").read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree(base: Path) -> dict:
    return {str(p.relative_to(REPO)).replace("\\", "/"): sha(p) for p in sorted(base.rglob("*")) if p.is_file() and p.name != "manifest.json"}


manifest = {
    "phase": "0",
    "mola": {"ref_sha": "58bc0ca69f17c1bee2c078360ec7cfa4995e621b", **env["mola_repo"]},
    "python": env["python"], "packages": env["packages"], "platform": env["platform"],
    "java": {"jdk": "Temurin 24.0.2+12 (JDK 21 listed on PATH is not installed)",
             "maven": "3.9.11 (bundled with IntelliJ IDEA 261.17801.55)"},
    "vamos": {**env["vamos_repo"], "version": "1.0.0", "note": "local fork; static reading only"},
    "moorphology": {"url": "https://gitlab.com/jfaldanam-phd/moorphology", "branch": "master",
                    "sha": "9d571722d8e315f5db2410a73cded9e9b47dcd8f", "committed": "2024-01-10",
                    "dependencies": "jmetal-core/problem/component 6.1, json 20230227, commons-math3 3.6.1"},
    "external_sources": {"MO-ELA": "https://arxiv.org/html/2602.00098v1",
                         "van der Blom & Vermetten": "https://arxiv.org/abs/2605.04954",
                         "COCO": "coco-experiment 2.8.2 (PyPI)"},
    "inputs": {p: sha(REPO / p) for p in ["examples/benchmarks/re_features.csv", "examples/benchmarks/rwa_features.csv",
                                           "examples/benchmarks/dtlz_features.csv", "examples/benchmarks/zcat_2obj_features.csv",
                                           "examples/benchmarks/zcat_3obj_features.csv", "plan.md"]},
    "artefacts": {**tree(ROOT), **tree(REPO / "research" / "evidence")},
}
(ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2))
print(f"manifest: {len(manifest['artefacts'])} artefacts hashed")
