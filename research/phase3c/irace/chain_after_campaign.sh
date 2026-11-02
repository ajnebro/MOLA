#!/bin/bash
# Chain on NicoVM after the phase 3c tuning campaign (user, 2026-11-02: "encadena todo"):
#   1. wait for run_campaign.sh to end; 2. re-run f20 from scratch (run_f20.sh);
#   3. stop unless all 61 phase 3c tasks hold DONE; 4. collect_3c.py;
#   5. evaluate_3c.py with tuned, gen, nsgaii, moead; 6. IBEA with the repaired VAMOS;
#   7. the 37 random configurations (amendment 1);
#   8. phase 3g: the 38 irace generalists; 9. stop unless all 38 hold DONE;
#   10. collect_3g.py; 11. evaluate_3g.py.
# Before every heavy step it waits until NicoVM is free: no Evolver training and a 5-minute load
# below 4 at two checks 10 min apart. Progress goes to ~/mola-phase3c/chain.log; the last line is
# CHAIN END, or CHAIN STOPPED / CHAIN FAILED with the reason.
set -uo pipefail
REPO=$HOME/mola-phase3/repo/research
PY=$HOME/mola-phase2b/venv/bin/python
LOG=$HOME/mola-phase3c/chain.log
export IRACE_LIB=$HOME/R/irace-4.5-lib MOLA_PHASE3_PYTHON=$PY
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
log() { echo "$(date -u +%FT%TZ) $*" >> "$LOG"; }
step() {  # step <name> <command...>: run, log, stop the chain on failure
    local name="$1"; shift
    wait_free
    log "start $name"
    if "$@" >> "$LOG" 2>&1; then log "done $name"; else log "CHAIN FAILED at $name"; exit 1; fi
}
wait_free() {
    local free=0 load
    while true; do
        load=$(cut -d" " -f2 /proc/loadavg)
        if ! pgrep -f "[r]un_campaign.sh" >/dev/null && ! pgrep -f "[T]rainingRunnerMain" >/dev/null \
            && awk "BEGIN{exit !($load < 4)}"; then
            free=$((free + 1))
        else
            free=0
        fi
        [ "$free" -ge 2 ] && return 0
        sleep 600
    done
}
missing_done() {  # missing_done <runs dir> <task...>: print the tasks without DONE
    local runs="$1"; shift
    for t in "$@"; do [ -f "$runs/$t/DONE" ] || echo "$t"; done
}

log "chain start"
step "f20 re-run" "$HOME/mola-phase3c/run_f20.sh"

TASKS_3C=$(printf 'f%02d ' $(seq 1 55); echo gen_all gen_g1 gen_g2 gen_g3 gen_g4 gen_g5)
missing=$(missing_done "$HOME/mola-phase3c/irace" $TASKS_3C | tr '\n' ' ')
[ -n "$missing" ] && { log "CHAIN STOPPED: phase 3c tasks without DONE: $missing"; exit 1; }

cd "$REPO/phase3c/scripts" || exit 1
step "collect_3c" env MOLA_PHASE3C_RUNS="$HOME/mola-phase3c/irace" "$PY" collect_3c.py
step "evaluate_3c tuned,gen,nsgaii,moead" env MOLA_PHASE3C_RAW="$HOME/mola-phase3c/matrix" \
    PHASE2_WORKERS=31 PHASE3C_CONFIGS=tuned,gen,nsgaii,moead "$PY" evaluate_3c.py
step "evaluate_3c ibea (repaired VAMOS)" env MOLA_PHASE3C_RAW="$HOME/mola-phase3c/matrix" \
    PHASE2_WORKERS=31 PHASE3C_CONFIGS=ibea PYTHONPATH="$HOME/mola-phase3/vamos-ibea/src" \
    "$PY" evaluate_3c.py
step "evaluate_3c random" env MOLA_PHASE3C_RAW="$HOME/mola-phase3c/matrix" \
    PHASE2_WORKERS=31 PHASE3C_CONFIGS=random "$PY" evaluate_3c.py
log "PHASE 3C MATRIX DONE"

step "phase 3g irace" env MOLA_PHASE3G_RUNS="$HOME/mola-phase3g/irace" WORKERS=31 CONCURRENT=6 \
    PARALLEL=6 MAX_EXPERIMENTS=20000 "$REPO/phase3g/irace/launch.sh"
TASKS_3G=$("$PY" -c 'import json, sys; print(" ".join(json.load(open(sys.argv[1]))))' \
    "$REPO/phase3g/data/generalist_tasks.json")
missing=$(missing_done "$HOME/mola-phase3g/irace" $TASKS_3G | tr '\n' ' ')
[ -n "$missing" ] && { log "CHAIN STOPPED: phase 3g tasks without DONE: $missing"; exit 1; }

cd "$REPO/phase3g/scripts" || exit 1
step "collect_3g" env MOLA_PHASE3G_RUNS="$HOME/mola-phase3g/irace" "$PY" collect_3g.py
step "evaluate_3g" env MOLA_PHASE3G_RAW="$HOME/mola-phase3g/matrix" PHASE2_WORKERS=31 \
    "$PY" evaluate_3g.py
log "CHAIN END"
