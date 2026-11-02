#!/bin/bash
# Fourth link of the NicoVM chain (user, 2026-11-02: "encadena todo"; 3e confirmed with "ok"):
# after phase 3r's link ends ("3r: CHAIN END" in ~/mola-phase3c/chain.log), run phase 3e as
# pre-registered on 2026-10-21: the 37 irace tunings in Evolver/jMetal (31 RunWorker JVMs), check
# DONE, collect the elites, then the jMetal performance matrix. The deployment in ~/mola-phase3e
# (Evolver 2.5 fat jar, compiled RunWorker, repo copy) dates from 2026-10-21 and matches the
# repository. Waits for NicoVM to be free before each heavy step; logs with the prefix "3e:".
set -uo pipefail
BASE=$HOME/mola-phase3e
REPO=$BASE/repo/research
PY=$HOME/mola-phase2b/venv/bin/python
LOG=$HOME/mola-phase3c/chain.log
export IRACE_LIB=$HOME/R/irace-4.5-lib MOLA_PHASE3_PYTHON=$PY JAVA=/usr/bin/java
export MOLA_EVOLVER_JAR=$BASE/lib/Evolver-2.5-jar-with-dependencies.jar MOLA_PHASE3E_CLASSES=$BASE/classes
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
log() { echo "$(date -u +%FT%TZ) 3e: $*" >> "$LOG"; }
wait_free() {
    local free=0 load
    while true; do
        load=$(cut -d" " -f2 /proc/loadavg)
        if ! pgrep -f "[c]hain_3r.sh" >/dev/null && ! pgrep -f "[T]rainingRunnerMain" >/dev/null \
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

until grep -qE "3r: (CHAIN END|CHAIN STOPPED|CHAIN FAILED|not started)" "$LOG" 2>/dev/null; do sleep 900; done
grep -q "3r: CHAIN END" "$LOG" || { log "not started: the previous link did not end cleanly"; exit 1; }
log "chain start"
step "irace (Evolver)" env MOLA_PHASE3_RUNS="$BASE/irace" WORKERS=31 CONCURRENT=12 PARALLEL=6 \
    MAX_EXPERIMENTS=20000 "$REPO/phase3e/irace/launch.sh"
missing=$(cd "$REPO/phase2/scripts" && "$PY" -c 'import common, os, sys
print(" ".join(p for p in common.pilot_problems() if not os.path.exists(os.path.join(sys.argv[1], p, "DONE"))))' "$BASE/irace")
[ -n "$missing" ] && { log "CHAIN STOPPED: Evolver tunings without DONE: $missing"; exit 1; }
cd "$REPO/phase3e/scripts" || exit 1
step "collect_3e" env MOLA_PHASE3_RUNS="$BASE/irace" "$PY" collect_3e.py
step "evaluate_3e" env MOLA_PHASE3E_MATRIX="$BASE/matrix/fronts" PHASE3E_WORKERS=31 "$PY" evaluate_3e.py
log "CHAIN END"
