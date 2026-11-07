#!/bin/bash
# 2026-11-07: the phase 3c evaluation server was swapped, without stopping irace, for one whose
# workers carry the numba-import fix (common.py, commit 1ea590e): the new server listens on
# run.sock (renamed from run.sock.new); the old one finishes its queue and stays idle until
# launch.sh's EXIT trap stops it. launch.sh does not know the new server, so this script stops it
# when run_campaign.sh ends, before the chain's f20 re-run starts its own server (>= 10 min later).
CAMPAIGN=2172689 SERVER=3987974 LOG=$HOME/mola-phase3c/chain.log
owns() { tr "\0" " " < "/proc/$1/cmdline" 2>/dev/null | grep -q -- "$2"; }
while owns "$CAMPAIGN" run_campaign.sh; do sleep 30; done
if owns "$SERVER" run.sock.new; then
    kill "$SERVER"
    echo "$(date -u +%FT%TZ) stopped the swapped-in evaluation server ($SERVER)" >> "$LOG"
fi
