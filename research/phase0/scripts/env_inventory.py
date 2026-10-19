"""Record the effective environment of phase 0 (versions, paths, git state) as JSON."""
import importlib.metadata as md, json, platform, subprocess, sys
from pathlib import Path

def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as exc:  # noqa: BLE001 - inventory must never abort
        return f"ERROR: {exc}"

repo = Path(__file__).resolve().parents[3]
vamos = Path(r"C:\Users\nicor\Desktop\VAMOS")
pkgs = ["mola", "numpy", "scipy", "pandas", "jmetalpy", "moocore", "typer", "pytest", "ruff", "coco-experiment"]
out = {
    "python": sys.version, "python_executable": sys.executable, "platform": platform.platform(),
    "mola_repo": {"path": str(repo), "branch": run(["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"]),
                  "head": run(["git", "-C", str(repo), "rev-parse", "HEAD"]),
                  "origin_main": run(["git", "-C", str(repo), "rev-parse", "origin/main"]),
                  "remote": run(["git", "-C", str(repo), "remote", "get-url", "origin"]),
                  "status_porcelain": run(["git", "-C", str(repo), "status", "--porcelain"])},
    "vamos_repo": {"path": str(vamos),
                   "head": run(["git", "-c", f"safe.directory={vamos.as_posix()}", "-C", str(vamos), "rev-parse", "HEAD"]),
                   "branch": run(["git", "-c", f"safe.directory={vamos.as_posix()}", "-C", str(vamos), "rev-parse", "--abbrev-ref", "HEAD"])},
}
versions = {}
for p in pkgs:
    try:
        versions[p] = md.version(p)
    except md.PackageNotFoundError:
        versions[p] = None
out["packages"] = versions
print(json.dumps(out, indent=2))
