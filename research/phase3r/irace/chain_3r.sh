#!/bin/bash
# Third link of the NicoVM chain (user, 2026-11-02: "encadena todo"): after phase 4b's link ends
# ("4b: CHAIN END" in ~/mola-phase3c/chain.log), run phase 3r: the 5 re-tunings with another irace
# seed, check DONE, then collect and evaluate the new elites on the 37 problems. Waits for NicoVM to
# be free before each heavy step; logs to ~/mola-phase3c/chain.log with the prefix "3r:".
set -uo pipefail
REPO=$HOME/mola-phase3/repo/research
PY=$HOME/mola-phase2b/venv/bin/python
LOG=$HOME/mola-phase3c/chain.log
export IRACE_LIB=$HOME/R/irace-4.5-lib MOLA_PHASE3_PYTHON=$PY
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
log() { echo "$(date -u +%FT%TZ) 3r: $*" >> "$LOG"; }
wait_free() {
    local free=0 load
    while true; do
        load=$(cut -d" " -f2 /proc/loadavg)
        if ! pgrep -f "[c]hain_4b.sh" >/dev/null && ! pgrep -f "[T]rainingRunnerMain" >/dev/null \
            && awk "BEGIN{exit !($load < 4)}"; then
            free=$((free + 1))
        else
            free=0
        fi
        [ "$free" -ge 2 ] && return 0
        sleep 600
    done
}
step() {
    local name="$1"; shift
    wait_free
    log "start $name"
    if "$@" >> "$LOG" 2>&1; then log "done $name"; else log "CHAIN FAILED at $name"; exit 1; fi
}

until grep -qE "4b: (CHAIN END|CHAIN STOPPED|CHAIN FAILED|not started)|^[^ ]+ (CHAIN STOPPED|CHAIN FAILED)" "$LOG" 2>/dev/null; do sleep 900; done
grep -q "4b: CHAIN END" "$LOG" || { log "not started: the previous link did not end cleanly"; exit 1; }
log "chain start"
step "irace re-tunings" env MOLA_PHASE3R_RUNS="$HOME/mola-phase3r/irace" WORKERS=31 CONCURRENT=5 \
    PARALLEL=6 MAX_EXPERIMENTS=20000 "$REPO/phase3r/irace/launch.sh"
missing=""
for p in $("$PY" -c 'import json, sys; print(" ".join(json.load(open(sys.argv[1]))))' \
    "$REPO/phase3r/data/retune_tasks.json"); do
    [ -f "$HOME/mola-phase3r/irace/$p/DONE" ] || missing="$missing $p"
done
[ -n "$missing" ] && { log "CHAIN STOPPED: re-tunings without DONE:$missing"; exit 1; }
cd "$REPO/phase3r/scripts" || exit 1
step "evaluate_3r" env MOLA_PHASE3R_RUNS="$HOME/mola-phase3r/irace" \
    MOLA_PHASE3R_RAW="$HOME/mola-phase3r/matrix" PHASE2_WORKERS=31 "$PY" evaluate_3r.py
log "CHAIN END"
