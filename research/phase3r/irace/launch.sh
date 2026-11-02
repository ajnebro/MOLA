#!/usr/bin/env bash
# Phase 3r (D12, C10): re-tune with another irace seed the 5 problems whose own c*_Q is > 0.01
# below the best donor (phase3/report.md, section 15).
#   ./launch.sh                 # every problem in ../data/retune_tasks.json
#   ./launch.sh zdt1 dtlz3      # only these
# Same scenario as phase 3's per-problem tunings (space, target runner, tuning bounds, 20 000
# experiments, default NSGA-II as the initial candidate); only the seed differs (8400 + the
# problem index; phase 3 used 8000 +).
# A problem whose directory holds DONE is skipped; an interrupted one resumes from its irace.Rdata.
# Environment: MOLA_PHASE3_PYTHON (Python with VAMOS 1.0.0), IRACE_LIB, MOLA_PHASE3R_RUNS.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PHASE3="$HERE/../../phase3"
DATA="$HERE/../data"
export R_LIBS="${IRACE_LIB:-$HOME/R/irace-4.5-lib}"
IRACE="$R_LIBS/irace/bin/irace"
Rscript -e "quit(status = as.integer(packageVersion('irace') < '4.4.4'))" \
    || { echo "irace < 4.4.4 in $R_LIBS" >&2; exit 1; }
PY="${MOLA_PHASE3_PYTHON:?set MOLA_PHASE3_PYTHON}"
RUNS="${MOLA_PHASE3R_RUNS:-$HOME/mola-phase3r/irace}"
export MOLA_RUN_SOCKET="${MOLA_RUN_SOCKET:-$HOME/mola-phase3r/run.sock}"
export MOLA_TUNING_BOUNDS="$PHASE3/data/tuning_bounds.json"
WORKERS="${WORKERS:-31}"
CONCURRENT="${CONCURRENT:-5}"
PARALLEL="${PARALLEL:-6}"
MAX_EXPERIMENTS="${MAX_EXPERIMENTS:-20000}"
TASK_FILE="$DATA/retune_tasks.json"
chmod +x "$PHASE3/irace/target-runner"
mkdir -p "$RUNS"

nice -n 19 "$PY" "$PHASE3/scripts/run_server.py" --socket "$MOLA_RUN_SOCKET" --workers "$WORKERS" > "$RUNS/server.log" 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null || true; wait $SERVER 2>/dev/null || true' EXIT
for _ in $(seq 120); do grep -q listening "$RUNS/server.log" 2>/dev/null && break; sleep 1; done
grep -q listening "$RUNS/server.log" || { echo "run_server did not start" >&2; cat "$RUNS/server.log" >&2; exit 1; }

TASKS=("$@")
[ ${#TASKS[@]} -eq 0 ] && mapfile -t TASKS < <("$PY" -c 'import json, sys; [print(k) for k in json.load(open(sys.argv[1]))]' "$TASK_FILE")

seed_of() {
    "$PY" -c 'import json, sys; print(json.load(open(sys.argv[1]))[sys.argv[2]]["seed"])' "$TASK_FILE" "$1"
}

run_one() {
    local problem="$1" dir recovery=""
    dir="$RUNS/$problem"
    [ -f "$dir/DONE" ] && { echo "$(date -u +%FT%TZ) skip $problem (DONE)"; return 0; }
    mkdir -p "$dir"
    if [ -f "$dir/irace.Rdata" ]; then
        recovery="$dir/recover-$(date -u +%Y%m%dT%H%M%S).Rdata"
        mv "$dir/irace.Rdata" "$recovery"
    fi
    echo "$problem" > "$dir/instances.txt"
    cat > "$dir/scenario.txt" <<EOF
parameterFile      = "$PHASE3/irace/parameters.txt"
configurationsFile = "$PHASE3/irace/default.txt"
trainInstancesFile = "$dir/instances.txt"
trainInstancesDir  = ""
execDir            = "$dir"
logFile            = "irace.Rdata"
targetRunner       = "$PHASE3/irace/target-runner"
maxExperiments     = $MAX_EXPERIMENTS
seed               = $(seed_of "$problem")
deterministic      = 0
EOF
    [ -n "$recovery" ] && echo "recoveryFile       = \"$recovery\"" >> "$dir/scenario.txt"
    if "$IRACE" --scenario "$dir/scenario.txt" --parallel "$PARALLEL" >> "$dir/irace.log" 2>&1; then
        touch "$dir/DONE"; echo "$(date -u +%FT%TZ) done $problem"
    else
        echo "$(date -u +%FT%TZ) FAILED $problem (see $dir/irace.log)"
    fi
}
export -f run_one seed_of
export PHASE3 DATA RUNS IRACE PARALLEL R_LIBS MOLA_RUN_SOCKET MOLA_TUNING_BOUNDS MAX_EXPERIMENTS PY TASK_FILE
printf '%s\n' "${TASKS[@]}" | xargs -P "$CONCURRENT" -I{} bash -c 'run_one "$@"' _ {}
echo "$(date -u +%FT%TZ) ALL DONE"
