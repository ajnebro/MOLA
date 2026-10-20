#!/usr/bin/env bash
# Phase 2b arm B: one irace 4.5 run per pilot problem, CONCURRENT problems at a time, each with
# --parallel PARALLEL target runs, 400 experiments, 5 iterations (irace's default, 6, needs at least
# 504 experiments with this space) and seed 7000 + the problem's pilot index.
#   ./launch.sh                 # all 37 pilot problems
#   ./launch.sh zdt1 dtlz3      # only these
# Needs MOLA_PHASE2B_PYTHON (a Python with VAMOS 1.0.0) and irace >= 4.4.4 in IRACE_LIB.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
export R_LIBS="${IRACE_LIB:-$HOME/R/irace-4.5-lib}"
IRACE="$R_LIBS/irace/bin/irace"
VERSION="$(Rscript -e "cat(as.character(packageVersion('irace')))")"
Rscript -e "quit(status = as.integer(packageVersion('irace') < '4.4.4'))" \
    || { echo "irace $VERSION < 4.4.4 (conditional-parameter sampling bug, irace issue #94)" >&2; exit 1; }
RUNS="${MOLA_PHASE2B_RUNS:-$HOME/mola-phase2b/raw_B/irace}"
CONCURRENT="${CONCURRENT:-8}"
PARALLEL="${PARALLEL:-4}"
chmod +x "$HERE/target-runner"
PROBLEMS=("$@")
if [ ${#PROBLEMS[@]} -eq 0 ]; then
    mapfile -t PROBLEMS < <("$MOLA_PHASE2B_PYTHON" -c "import sys; sys.path.insert(0, '$HERE/../../phase2/scripts'); import common; print('\n'.join(common.pilot_problems()))")
fi
ALL="$("$MOLA_PHASE2B_PYTHON" -c "import sys; sys.path.insert(0, '$HERE/../../phase2/scripts'); import common; print(' '.join(common.pilot_problems()))")"

run_one() {
    local problem="$1" index=0 name
    for name in $ALL; do [ "$name" = "$problem" ] && break; index=$((index + 1)); done
    local dir="$RUNS/$problem"
    mkdir -p "$dir"
    echo "$problem" > "$dir/instances.txt"
    cat > "$dir/scenario.txt" <<EOF
parameterFile      = "$HERE/parameters.txt"
configurationsFile = "$HERE/default.txt"
trainInstancesFile = "$dir/instances.txt"
trainInstancesDir  = ""
execDir            = "$dir"
logFile            = "irace.Rdata"
targetRunner       = "$HERE/target-runner"
maxExperiments     = 400
nbIterations       = 5
seed               = $((7000 + index))
deterministic      = 0
EOF
    "$IRACE" --scenario "$dir/scenario.txt" --parallel "$PARALLEL" > "$dir/irace.log" 2>&1 \
        && echo "$(date -u +%FT%TZ) done $problem" || echo "$(date -u +%FT%TZ) FAILED $problem (see $dir/irace.log)"
}
export -f run_one
export HERE RUNS IRACE PARALLEL ALL R_LIBS MOLA_PHASE2B_PYTHON
printf '%s\n' "${PROBLEMS[@]}" | xargs -P "$CONCURRENT" -I{} bash -c 'run_one "$@"' _ {}
