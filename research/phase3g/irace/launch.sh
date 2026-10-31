#!/usr/bin/env bash
# Phase 3g (D11): irace generalists over phase 3's development problems, 20 000 experiments each.
#   ./launch.sh                    # every task
#   ./launch.sh gen_lofo_zdt       # only these tasks
# Tasks, with their instances and seeds in ../data/generalist_tasks.json:
#   gen_lofo_<family>  generalist over the development problems outside <family>, seed 8101-8105
#                      (dtlz, lz09uf, rerwa, zcat, zdt, in that order)
#   gen_all            generalist over the 37 development problems, seed 8100 (final evaluation)
# Same space, default candidate, target runner and tuning bounds as phase 3's per-problem tunings.
# The persistent run_server.py serves every experiment (WORKERS warm VAMOS processes); CONCURRENT
# irace runs at a time, each with --parallel PARALLEL. A task whose directory holds DONE is skipped;
# an interrupted one resumes from its irace.Rdata.
# Environment: MOLA_PHASE3_PYTHON (Python with VAMOS 1.0.0), IRACE_LIB, MOLA_PHASE3G_RUNS.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PHASE3="$HERE/../../phase3"
export R_LIBS="${IRACE_LIB:-$HOME/R/irace-4.5-lib}"
IRACE="$R_LIBS/irace/bin/irace"
Rscript -e "quit(status = as.integer(packageVersion('irace') < '4.4.4'))" \
    || { echo "irace < 4.4.4 in $R_LIBS" >&2; exit 1; }
PY="${MOLA_PHASE3_PYTHON:?set MOLA_PHASE3_PYTHON}"
RUNS="${MOLA_PHASE3G_RUNS:-$HOME/mola-phase3g/irace}"
export MOLA_RUN_SOCKET="${MOLA_RUN_SOCKET:-$HOME/mola-phase3g/run.sock}"
export MOLA_TUNING_BOUNDS="$PHASE3/data/tuning_bounds.json"
WORKERS="${WORKERS:-31}"
CONCURRENT="${CONCURRENT:-6}"
PARALLEL="${PARALLEL:-6}"
MAX_EXPERIMENTS="${MAX_EXPERIMENTS:-20000}"
chmod +x "$PHASE3/irace/target-runner"
mkdir -p "$RUNS"

nice -n 19 "$PY" "$PHASE3/scripts/run_server.py" --socket "$MOLA_RUN_SOCKET" --workers "$WORKERS" > "$RUNS/server.log" 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null || true; wait $SERVER 2>/dev/null || true' EXIT
for _ in $(seq 120); do grep -q listening "$RUNS/server.log" 2>/dev/null && break; sleep 1; done
grep -q listening "$RUNS/server.log" || { echo "run_server did not start" >&2; cat "$RUNS/server.log" >&2; exit 1; }

TASKS=("$@")
[ ${#TASKS[@]} -eq 0 ] && TASKS=(gen_lofo_dtlz gen_lofo_lz09uf gen_lofo_rerwa gen_lofo_zcat gen_lofo_zdt gen_all)

TASK_FILE="$HERE/../data/generalist_tasks.json"
instances_of() {  # the irace instances (development problems) of a task, one per line
    "$PY" -c 'import json, sys; [print(p) for p in json.load(open(sys.argv[1]))[sys.argv[2]]["instances"]]' "$TASK_FILE" "$1"
}

seed_of() {
    "$PY" -c 'import json, sys; print(json.load(open(sys.argv[1]))[sys.argv[2]]["seed"])' "$TASK_FILE" "$1"
}

run_one() {
    local task="$1" dir recovery=""
    dir="$RUNS/$task"
    [ -f "$dir/DONE" ] && { echo "$(date -u +%FT%TZ) skip $task (DONE)"; return 0; }
    mkdir -p "$dir"
    if [ -f "$dir/irace.Rdata" ]; then
        recovery="$dir/recover-$(date -u +%Y%m%dT%H%M%S).Rdata"
        mv "$dir/irace.Rdata" "$recovery"
    fi
    instances_of "$task" > "$dir/instances.txt"
    cat > "$dir/scenario.txt" <<EOF
parameterFile      = "$PHASE3/irace/parameters.txt"
configurationsFile = "$PHASE3/irace/default.txt"
trainInstancesFile = "$dir/instances.txt"
trainInstancesDir  = ""
execDir            = "$dir"
logFile            = "irace.Rdata"
targetRunner       = "$PHASE3/irace/target-runner"
maxExperiments     = $MAX_EXPERIMENTS
seed               = $(seed_of "$task")
deterministic      = 0
EOF
    [ -n "$recovery" ] && echo "recoveryFile       = \"$recovery\"" >> "$dir/scenario.txt"
    if "$IRACE" --scenario "$dir/scenario.txt" --parallel "$PARALLEL" >> "$dir/irace.log" 2>&1; then
        touch "$dir/DONE"; echo "$(date -u +%FT%TZ) done $task"
    else
        echo "$(date -u +%FT%TZ) FAILED $task (see $dir/irace.log)"
    fi
}
export -f run_one instances_of seed_of
export HERE PHASE3 TASK_FILE RUNS IRACE PARALLEL R_LIBS MOLA_RUN_SOCKET MOLA_TUNING_BOUNDS MAX_EXPERIMENTS PY
printf '%s\n' "${TASKS[@]}" | xargs -P "$CONCURRENT" -I{} bash -c 'run_one "$@"' _ {}
echo "$(date -u +%FT%TZ) ALL DONE"
