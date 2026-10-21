#!/usr/bin/env bash
# Phase 3e (Evolver/jMetal replication): tune c*_P with irace (>= 4.4.4) for every development
# problem, 20 000 experiments each, over Evolver's NSGA-II space minus PCX, UNDC, Laplace and
# uniform mutation (decision D6).
#   ./launch.sh               # all 37 development problems
#   ./launch.sh zdt1 dtlz3    # only these
# A persistent jrun_server.py (WORKERS single-threaded RunWorker JVMs) serves every experiment; CONCURRENT
# irace instances run at a time, each with --parallel PARALLEL clients. A problem whose run
# directory holds DONE is skipped; an interrupted one resumes from its irace.Rdata.
# Environment: MOLA_PHASE3_PYTHON (Python with numpy and moocore), IRACE_LIB, MOLA_PHASE3_RUNS,
# MOLA_EVOLVER_JAR, MOLA_PHASE3E_CLASSES, JAVA.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$HERE/../scripts"
export R_LIBS="${IRACE_LIB:-$HOME/R/irace-4.5-lib}"
IRACE="$R_LIBS/irace/bin/irace"
Rscript -e "quit(status = as.integer(packageVersion('irace') < '4.4.4'))" \
    || { echo "irace < 4.4.4 in $R_LIBS (conditional-parameter sampling bug, irace issue #94)" >&2; exit 1; }
PY="${MOLA_PHASE3_PYTHON:?set MOLA_PHASE3_PYTHON}"
RUNS="${MOLA_PHASE3_RUNS:-$HOME/mola-phase3e/irace}"
export MOLA_RUN_SOCKET="${MOLA_RUN_SOCKET:-$HOME/mola-phase3e/run.sock}"
WORKERS="${WORKERS:-31}"
CONCURRENT="${CONCURRENT:-12}"
PARALLEL="${PARALLEL:-6}"
MAX_EXPERIMENTS="${MAX_EXPERIMENTS:-20000}"
chmod +x "$HERE/../../phase3/irace/target-runner"
mkdir -p "$RUNS"

"$PY" "$SCRIPTS/jrun_server.py" --socket "$MOLA_RUN_SOCKET" --workers "$WORKERS" > "$RUNS/server.log" 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null || true; wait $SERVER 2>/dev/null || true' EXIT
for _ in $(seq 120); do grep -q listening "$RUNS/server.log" 2>/dev/null && break; sleep 1; done
grep -q listening "$RUNS/server.log" || { echo "run_server did not start" >&2; cat "$RUNS/server.log" >&2; exit 1; }

PROBLEMS=("$@")
LIST="$("$PY" -c "import sys; sys.path.insert(0, '$HERE/../../phase2/scripts'); import common; print(' '.join(common.pilot_problems()))")"
[ ${#PROBLEMS[@]} -eq 0 ] && read -r -a PROBLEMS <<< "$LIST"

run_one() {
    local problem="$1" index=0 name dir recovery=""
    for name in $LIST; do [ "$name" = "$problem" ] && break; index=$((index + 1)); done
    dir="$RUNS/$problem"
    [ -f "$dir/DONE" ] && { echo "$(date -u +%FT%TZ) skip $problem (DONE)"; return 0; }
    mkdir -p "$dir"
    if [ -f "$dir/irace.Rdata" ]; then
        recovery="$dir/recover-$(date -u +%Y%m%dT%H%M%S).Rdata"
        mv "$dir/irace.Rdata" "$recovery"
    fi
    echo "$problem" > "$dir/instances.txt"
    cat > "$dir/scenario.txt" <<EOF
parameterFile      = "$HERE/parameters.txt"
configurationsFile = "$HERE/default.txt"
trainInstancesFile = "$dir/instances.txt"
trainInstancesDir  = ""
execDir            = "$dir"
logFile            = "irace.Rdata"
targetRunner       = "$HERE/../../phase3/irace/target-runner"
maxExperiments     = $MAX_EXPERIMENTS
seed               = $((8600 + index))
deterministic      = 0
EOF
    [ -n "$recovery" ] && echo "recoveryFile       = \"$recovery\"" >> "$dir/scenario.txt"
    if "$IRACE" --scenario "$dir/scenario.txt" --parallel "$PARALLEL" >> "$dir/irace.log" 2>&1; then
        touch "$dir/DONE"; echo "$(date -u +%FT%TZ) done $problem"
    else
        echo "$(date -u +%FT%TZ) FAILED $problem (see $dir/irace.log)"
    fi
}
export -f run_one
export HERE RUNS IRACE PARALLEL LIST R_LIBS MOLA_RUN_SOCKET MAX_EXPERIMENTS
printf '%s\n' "${PROBLEMS[@]}" | xargs -P "$CONCURRENT" -I{} bash -c 'run_one "$@"' _ {}
echo "$(date -u +%FT%TZ) ALL DONE"
