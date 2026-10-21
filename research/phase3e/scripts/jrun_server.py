"""Persistent evaluation server for irace, phase 3e (Evolver/jMetal): a pool of RunWorker JVMs.

The same protocol as phase 3's run_server.py, so irace's target runner is phase 3's run_client.py
unchanged: one JSON request per Unix-socket connection, {"problem", "seed", "args"}, answered
with the cost. Here each experiment goes to the next free RunWorker JVM. A JVM serves one run at a
time, so jMetal's process-global random generator is never shared and every run is reproducible
from its seed.

The run: NSGA-II from Evolver's NSGAIIDouble.yaml with population 100 and 20 000 evaluations on
the problem's jMetal implementation (catalogue_3e.SPECS). The cost: minus the hypervolume of the
result's non-dominated front after min-max normalization by data/tuning_bounds.json (true
fronts), reference point 1.1 -- the same objective as phase 3.

Run on NicoVM:  python jrun_server.py --socket ~/mola-phase3e/run.sock --workers 31
"""

import argparse
import json
import queue
import signal
import socketserver
import sys
from pathlib import Path

import moocore
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from catalogue_3e import SPECS  # noqa: E402
from jworker import PHASE3E, JWorker  # noqa: E402

BUDGET = 20_000
REFERENCE = 1.1
BOUNDS = json.loads((PHASE3E / "data" / "tuning_bounds.json").read_text())


def cost(problem: str, seed: int, arguments: list[str], worker: JWorker) -> str:
    bounds = BOUNDS[problem]
    ideal, nadir = np.asarray(bounds["ideal"]), np.asarray(bounds["nadir"])
    front = worker.run(SPECS[problem], seed, BUDGET, " ".join(arguments), len(ideal))
    front = front[moocore.is_nondominated(front, keep_weakly=False)]
    scaled = (front - ideal) / (nadir - ideal)
    reference = np.full(len(ideal), REFERENCE)
    scaled = scaled[np.all(scaled < reference, axis=1)]
    hv = float(moocore.hypervolume(scaled, ref=reference)) if len(scaled) else 0.0
    return f"{0.0 - hv:.12g}" if hv > 0 else "0"


class _Handler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        worker = self.server.free.get()
        try:
            request = json.loads(self.rfile.readline())
            reply = cost(request["problem"], int(request["seed"]), list(request["args"]), worker)
        except Exception as error:  # noqa: BLE001 - reported to irace, which then stops
            reply = f"ERROR {type(error).__name__}: {error}".replace("\n", " ")
        finally:
            self.server.free.put(worker)
        self.wfile.write((reply + "\n").encode())


class _Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--socket", required=True)
    parser.add_argument("--workers", type=int, default=31)
    options = parser.parse_args()
    socket_path = Path(options.socket).expanduser()
    if socket_path.exists():
        socket_path.unlink()
    workers = [JWorker() for _ in range(options.workers)]
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        with _Server(str(socket_path), _Handler) as server:
            server.free = queue.Queue()
            for worker in workers:
                server.free.put(worker)
            print(f"listening on {socket_path} with {options.workers} RunWorker JVMs", flush=True)
            server.serve_forever()
    finally:
        for worker in workers:
            worker.process.kill()


if __name__ == "__main__":
    main()
