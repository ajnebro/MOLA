"""Phase 3r pre-registered descriptive analysis (preregistration.md): the tuning noise floor.

For each re-tuned problem Q: HVn on Q of the original c*_Q (phase 3), of the re-tuned c*_Q', of
the best donor (the oracle over the other 36 c*_P) and of the better of c*_Q and c*_Q'. Reported:
- the gap to the oracle donor before and after re-tuning, and the share of it the re-tuning closes;
- |HVn(c*_Q') - HVn(c*_Q)| on Q, the seed-to-seed spread of one irace run;
- as donors: the mean HVn of c*_Q and c*_Q' over the other 36 problems.
HVn uses phase 3's matrix normalization; the re-tuned configurations do not enter its union.

Run locally:
    MOLA_PHASE3_MATRIX=... MOLA_PHASE3R_RAW=... python research/phase3r/scripts/analyze_3r.py
Writes data/retune_summary.json.
"""

import json
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase3" / "scripts"))
sys.path.insert(0, str(HERE.parents[1] / "phase3g" / "scripts"))

import analyze_3g as a3g  # noqa: E402
import analyze_transfer as at  # noqa: E402

DATA = HERE.parent / "data"
RAW = Path(os.environ.get("MOLA_PHASE3R_RAW", r"C:\tmp\mola-phase3r\matrix"))


def main() -> None:
    problems = at.pilot_problems()
    tasks = json.loads((DATA / "retune_tasks.json").read_text())
    hvn = at.hvn_matrix(problems)
    a3g.RAW = RAW / "fronts"
    configs = [f"retuned__{p}" for p in tasks]
    table = a3g.generalists_hvn(problems, configs).pivot(
        index="config", columns="problem", values="hvn"
    )
    rows = {}
    for q in tasks:
        original = float(hvn[(f"tuned__{q}", q)].mean())
        retuned = float(table.loc[f"retuned__{q}", q])
        oracle = max(float(hvn[(f"tuned__{p}", q)].mean()) for p in problems if p != q)
        others = [p for p in problems if p != q]
        gap_before = oracle - original
        gap_after = oracle - max(original, retuned)
        rows[q] = {
            "original": round(original, 4),
            "retuned": round(retuned, 4),
            "oracle_donor": round(oracle, 4),
            "gap_before": round(gap_before, 4),
            "gap_after_best_of_two": round(gap_after, 4),
            "share_closed": round(1 - gap_after / gap_before, 3) if gap_before > 0 else None,
            "seed_spread": round(abs(retuned - original), 4),
            "as_donor_original": round(
                float(np.mean([hvn[(f"tuned__{q}", p)].mean() for p in others])), 4
            ),
            "as_donor_retuned": round(float(table.loc[f"retuned__{q}", others].mean()), 4),
        }
    summary = {
        "note": "Pre-registered, descriptive (D12, C10).",
        "problems": rows,
        "mean_seed_spread": round(float(np.mean([r["seed_spread"] for r in rows.values()])), 4),
        "mean_share_closed": round(
            float(
                np.mean([r["share_closed"] for r in rows.values() if r["share_closed"] is not None])
            ),
            3,
        ),
    }
    (DATA / "retune_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
