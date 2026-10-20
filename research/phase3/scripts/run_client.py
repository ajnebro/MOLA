"""irace target-runner client (phase 3): forwards one experiment to run_server.py.

irace calls `target-runner <configuration id> <instance id> <seed> <instance> --name value ...`.
This client uses only the standard library (start it with `python3 -S`, about 20 ms), sends the
experiment over the server's Unix socket (MOLA_RUN_SOCKET) and prints the cost. Any error is
printed and the exit status is 1, so irace stops instead of recording a bogus cost.
"""

import json
import os
import socket
import sys


def main(argv: list[str]) -> int:
    request = {"seed": int(argv[2]), "problem": argv[3], "args": argv[4:]}
    path = os.environ.get("MOLA_RUN_SOCKET", os.path.expanduser("~/mola-phase3/run.sock"))
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.connect(path)
        connection.sendall((json.dumps(request) + "\n").encode())
        reply = connection.makefile().readline().strip()
    if not reply or reply.startswith("ERROR"):
        print(reply or "ERROR empty reply from run_server")
        return 1
    print(reply)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
