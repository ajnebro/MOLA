#!/usr/bin/env bash
# Phase 3c: irace tuning on bbob-biobj (D = 10), 20 000 experiments per task, phase 3's space.
#   ./launch.sh                 # every task: the 55 per-problem tunings, then the 6 generalists
#   ./launch.sh f20 gen_all     # only these tasks
# Tasks:
#   fNN      c*_P for P = bbob-biobj_fNN_i01_d10 (one irace instance), seed 9000 + NN
#   gen_all  generalist over the 55 instance-1 problems, seed 9100
#   gen_gG   generalist over the instance-1 problems with no component in bbob group G, seed 9100 + G
# The persistent run_server.py of phase 3 serves every experiment (WORKERS warm VAMOS processes)
# with this phase's bounds; CONCURRENT irace runs at a time, each with --parallel PARALLEL.
# A task whose directory holds DONE is skipped; an interrupted one resumes from its irace.Rdata.
# Environment: MOLA_PHASE3_PYTHON (Python with VAMOS 1.0.0 and cocoex), IRACE_LIB, MOLA_PHASE3C_RUNS.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PHASE3="$HERE/../../phase3"
DATA="$HERE/../data"
export R_LIBS="${IRACE_LIB:-$HOME/R/irace-4.5-lib}"
IRACE="$R_LIBS/irace/bin/irace"
Rscript -e "quit(status = as.integer(packageVersion('irace') < '4.4.4'))" \
    || { echo "irace < 4.4.4 in $R_LIBS" >&2; exit 1; }
PY="${MOLA_PHASE3_PYTHON:?set MOLA_PHASE3_PYTHON}"
RUNS="${MOLA_PHASE3C_RUNS:-$HOME/mola-phase3c/irace}"
export MOLA_RUN_SOCKET="${MOLA_RUN_SOCKET:-$HOME/mola-phase3c/run.sock}"
export MOLA_TUNING_BOUNDS="$DATA/tuning_bounds.json"
WORKERS="${WORKERS:-31}"
CONCURRENT="${CONCURRENT:-12}"
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
if [ ${#TASKS[@]} -eq 0 ]; then
    for f in $(seq 1 55); do TASKS+=("$(printf 'f%02d' "$f")"); done
    TASKS+=(gen_all gen_g1 gen_g2 gen_g3 gen_g4 gen_g5)
fi

instances_of() {  # the irace instances (problem ids) of a task, one per line
    "$PY" - "$1" "$DATA/catalogue.json" <<'EOF'
import json, sys
task, catalogue = sys.argv[1], json.load(open(sys.argv[2]))
first = {k: v for k, v in catalogue.items() if v["instance"] == 1}
if task.startswith("f"):
    print(f"bbob-biobj_{task}_i01_d10")
elif task == "gen_all":
    print("\n".join(sorted(first)))
else:
    group = int(task[len("gen_g"):])
    print("\n".join(sorted(k for k, v in first.items() if group not in v["groups"])))
EOF
}

seed_of() {
    case "$1" in
        f*) echo $((9000 + 10#${1#f})) ;;
        gen_all) echo 9100 ;;
        gen_g*) echo $((9100 + ${1#gen_g})) ;;
    esac
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
export HERE PHASE3 DATA RUNS IRACE PARALLEL R_LIBS MOLA_RUN_SOCKET MOLA_TUNING_BOUNDS MAX_EXPERIMENTS PY
printf '%s\n' "${TASKS[@]}" | xargs -P "$CONCURRENT" -I{} bash -c 'run_one "$@"' _ {}
echo "$(date -u +%FT%TZ) ALL DONE"
