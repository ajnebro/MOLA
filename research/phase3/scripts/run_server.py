"""Persistent evaluation server for irace (phase 3): one warm VAMOS process per worker.

Every irace experiment used to start Python and import VAMOS (about 0.9 s, often more than the
run itself). Here W worker processes import everything once; irace's target runner is a tiny
standard-library client (run_client.py) that sends one experiment over a Unix socket and prints
the cost it gets back. Several irace instances can share the server; experiments queue for the
next free worker.

Request (one JSON line):  {"problem": ..., "seed": ..., "args": ["--name", "value", ...]}
Reply (one line):         the cost (minus the normalized HV, or 0), or "ERROR <reason>".

The run and the cost are those of phase 2b's irace_runner (20 000 evaluations, NSGA-II
configuration from the invariant space, HV after min-max normalization by data/tuning_bounds.json,
reference point 1.1), with phase 3's true-front bounds.

Run on NicoVM:  python run_server.py --socket ~/mola-phase3/run.sock --workers 31
"""

import argparse
import json
import os
import signal
import socketserver
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for _variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_variable] = "1"

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parents[1]
sys.path.insert(0, str(RESEARCH / "phase2" / "scripts"))
sys.path.insert(0, str(RESEARCH / "phase2b" / "scripts"))

BUDGET = 20_000
# Phase 3c serves bbob-biobj problems with its own bounds (MOLA_TUNING_BOUNDS).
BOUNDS_FILE = Path(os.environ.get("MOLA_TUNING_BOUNDS", HERE.parent / "data" / "tuning_bounds.json"))
_bounds: dict = {}


def _warm_up() -> None:
    """Worker initializer: import VAMOS and the run helpers once, and load the bounds."""
    import irace_runner  # noqa: F401
    import runs  # noqa: F401

    _bounds.update(json.loads(BOUNDS_FILE.read_text()))


def evaluate(problem: str, seed: int, arguments: list[str]) -> str:
    """One experiment: run the configuration and return irace's cost as text."""
    import numpy as np
    from irace_runner import normalized_hv, parse_assignment
    from runs import run

    bounds = _bounds[problem]
    front = run(problem, parse_assignment(arguments), BUDGET, seed, checkpoints=())["fronts"][BUDGET]
    hv = normalized_hv(front, np.asarray(bounds["ideal"]), np.asarray(bounds["nadir"]))
    return f"{0.0 - hv:.12g}" if hv > 0 else "0"


class _Handler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        try:
            request = json.loads(self.rfile.readline())
            cost = self.server.pool.submit(
                evaluate, request["problem"], int(request["seed"]), list(request["args"])).result()
            reply = cost
        except Exception as error:  # noqa: BLE001 - reported to irace, which then stops
            reply = f"ERROR {type(error).__name__}: {error}".replace("\n", " ")
        self.wfile.write((reply + "\n").encode())


class _Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--socket", required=True)
    parser.add_argument("--workers", type=int, default=31)
    options = parser.parse_args()
    socket_path = Path(options.socket).expanduser()
    # SIGTERM unwinds the `with` blocks below, so the pool's workers exit with the server.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    if socket_path.exists():
        socket_path.unlink()
    with ProcessPoolExecutor(max_workers=options.workers, initializer=_warm_up) as pool, \
            _Server(str(socket_path), _Handler) as server:
        server.pool = pool
        print(f"listening on {socket_path} with {options.workers} workers", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
