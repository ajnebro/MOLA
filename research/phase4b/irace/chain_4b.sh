#!/bin/bash
# Second link of the NicoVM chain (user, 2026-11-02: "encadena todo"): after ~/mola-phase3c's
# chain ends (CHAIN END in chain.log), run phase 4b: the 24 warm-started irace runs, check that
# every one holds DONE, then evaluate the anytime elites of both arms. Waits for NicoVM to be free
# before each heavy step; logs to ~/mola-phase3c/chain.log with the prefix "4b:".
set -uo pipefail
REPO=$HOME/mola-phase3/repo/research
PY=$HOME/mola-phase2b/venv/bin/python
LOG=$HOME/mola-phase3c/chain.log
export IRACE_LIB=$HOME/R/irace-4.5-lib MOLA_PHASE3_PYTHON=$PY
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
log() { echo "$(date -u +%FT%TZ) 4b: $*" >> "$LOG"; }
wait_free() {
    local free=0 load
    while true; do
        load=$(cut -d" " -f2 /proc/loadavg)
        if ! pgrep -f "[c]hain_after_campaign.sh" >/dev/null && ! pgrep -f "[T]rainingRunnerMain" >/dev/null \
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

until grep -qE "CHAIN END|CHAIN STOPPED|CHAIN FAILED" "$LOG" 2>/dev/null; do sleep 900; done
grep -q "CHAIN END" "$LOG" || { log "not started: the first chain did not end cleanly"; exit 1; }
log "chain start"
step "irace warm starts" env MOLA_PHASE4B_RUNS="$HOME/mola-phase4b/irace" WORKERS=31 CONCURRENT=6 \
    PARALLEL=6 MAX_EXPERIMENTS=20000 "$REPO/phase4b/irace/launch.sh"
missing=""
for p in $("$PY" -c 'import json, sys; print(" ".join(json.load(open(sys.argv[1]))))' \
    "$REPO/phase4b/data/warm_start_tasks.json"); do
    [ -f "$HOME/mola-phase4b/irace/$p/DONE" ] || missing="$missing $p"
done
[ -n "$missing" ] && { log "CHAIN STOPPED: warm runs without DONE:$missing"; exit 1; }
cd "$REPO/phase4b/scripts" || exit 1
step "evaluate_4b" env MOLA_PHASE4B_RAW="$HOME/mola-phase4b/matrix" \
    MOLA_PHASE4B_RUNS="$HOME/mola-phase4b/irace" PHASE2_WORKERS=31 "$PY" evaluate_4b.py
log "CHAIN END"
