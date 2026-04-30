#!/usr/bin/env python3
"""
v1.2.0 Balanced Board Post-Process — fixes momentum gate false positives.

Bug: scoring_engine.py runs BEFORE heartbeat_monitor.py. At gate evaluation
time, decay_data is None, so the momentum gate defaults to "stable" and
passes. Companies with decay_level=warning (PFE 40, WMT 38, COF 43) end up
on the Balanced Board incorrectly.

Fix: this script runs AFTER both scoring and heartbeat. It reads the
heartbeat file, re-evaluates the momentum gate for every score record,
and updates hi_balanced + hi_balanced_gates accordingly.

Architecture decision: post-process is preferred over moving heartbeat
earlier in the pipeline because:
  1. Surgical (one new step, no reordering)
  2. Heartbeat depends on score data anyway (it analyzes the scored set)
  3. Scoring stays deterministic — Balanced Board is just a flag layered on top

Run order:
  Phase 2: scoring_engine.py     → writes all_scores.json (with decay=None)
  Phase 4c: heartbeat_monitor.py → writes heartbeats.json
  Phase 4d: THIS SCRIPT          → reads heartbeats.json, updates all_scores.json

Anchor in run_all.py: add as Phase 4d, right after heartbeat (line ~190).

Usage (from repo root):
  python3 pipeline/post_process_balanced_board.py
  python3 pipeline/post_process_balanced_board.py --dry-run
"""

import json
import sys
import shutil
import argparse
from pathlib import Path

# Find repo root by looking for pipeline/ dir
_HERE = Path(__file__).resolve().parent
if (_HERE.parent / "pipeline").exists():
    REPO_ROOT = _HERE.parent
elif (_HERE / "pipeline").exists():
    REPO_ROOT = _HERE
else:
    REPO_ROOT = Path.cwd()

SCORES_FILE = REPO_ROOT / "pipeline" / "data" / "scores" / "all_scores.json"
HEARTBEAT_FILE = REPO_ROOT / "pipeline" / "data" / "heartbeat" / "heartbeats.json"

# Must match scoring_engine.py:1262
GOLD_DECAY_BLOCKING = {"warning", "critical"}


def load_heartbeat_index():
    """Build {ticker: {decay_level, decay_index, ...}} index from heartbeat file."""
    if not HEARTBEAT_FILE.exists():
        sys.exit(f"NOT FOUND: {HEARTBEAT_FILE}\n"
                 f"Heartbeat must run before this post-process step.")

    with open(HEARTBEAT_FILE) as f:
        hb = json.load(f)

    if isinstance(hb, list):
        return {h.get("ticker"): h for h in hb if h.get("ticker")}
    elif isinstance(hb, dict):
        # Could be ticker-keyed dict, or wrapped
        if "heartbeats" in hb:
            return load_list_or_dict(hb["heartbeats"])
        return hb
    return {}


def load_list_or_dict(obj):
    if isinstance(obj, list):
        return {h.get("ticker"): h for h in obj if h.get("ticker")}
    return obj if isinstance(obj, dict) else {}


def main():
    parser = argparse.ArgumentParser(description="Post-process Balanced Board with real heartbeat data")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    if not SCORES_FILE.exists():
        sys.exit(f"NOT FOUND: {SCORES_FILE}")

    with open(SCORES_FILE) as f:
        scores = json.load(f)

    hb_index = load_heartbeat_index()
    print(f"Loaded: {len(scores)} score records, {len(hb_index)} heartbeat records")

    # Process each record
    promoted = []  # was not on Balanced Board, now is (rare — would mean decay improved)
    demoted = []   # was on Balanced Board, no longer (PFE/WMT/COF case)
    no_change_balanced = []
    no_heartbeat = []

    for rec in scores:
        ticker = rec.get("ticker")
        if not ticker:
            continue

        was_balanced = bool(rec.get("hi_balanced"))
        gates = rec.get("hi_balanced_gates") or {}
        gates_detail = gates.get("_detail") or {}

        # Get real decay from heartbeat
        hb = hb_index.get(ticker)
        if hb is None:
            # No heartbeat data — keep current state, but flag
            no_heartbeat.append(ticker)
            continue

        real_decay_level = hb.get("decay_level") or "stable"
        real_decay_index = hb.get("decay_index", 0)

        # Recompute momentum gate
        new_gate_momentum = real_decay_level not in GOLD_DECAY_BLOCKING

        # Other gates stay as-is (dimensions and evidence don't depend on heartbeat)
        gate_dimensions = gates.get("dimensions", False)
        gate_evidence = gates.get("evidence", False)

        # Recompute hi_balanced
        new_hi_balanced = bool(gate_dimensions and gate_evidence and new_gate_momentum)

        # Update record
        new_gates = {
            "dimensions": gate_dimensions,
            "evidence": gate_evidence,
            "momentum": new_gate_momentum,
            "_detail": {
                **gates_detail,
                "decay_level": real_decay_level,
                "decay_index": real_decay_index,
            },
        }

        # Track changes
        if was_balanced and not new_hi_balanced:
            demoted.append((ticker, real_decay_level, real_decay_index))
        elif not was_balanced and new_hi_balanced:
            promoted.append((ticker, real_decay_level, real_decay_index))
        elif was_balanced and new_hi_balanced:
            no_change_balanced.append(ticker)

        rec["hi_balanced"] = new_hi_balanced
        rec["hi_balanced_gates"] = new_gates
        # Also expose decay at top level for surface consistency
        rec["decay_level"] = real_decay_level
        rec["decay_index"] = real_decay_index

    # Report
    print()
    print("Balanced Board changes:")
    print(f"  Stayed:   {len(no_change_balanced)} {no_change_balanced}")
    print(f"  Demoted:  {len(demoted)} (were Balanced Board, now warning/critical decay)")
    for t, lvl, idx in demoted:
        print(f"    - {t}: decay_level={lvl}, decay_index={idx}")
    print(f"  Promoted: {len(promoted)} (rare — decay improved)")
    for t, lvl, idx in promoted:
        print(f"    + {t}: decay_level={lvl}, decay_index={idx}")
    print()
    if no_heartbeat:
        print(f"  Without heartbeat data: {len(no_heartbeat)} (unchanged)")

    if args.dry_run:
        print()
        print("[dry-run] No file written.")
        return

    # Atomic write
    tmp = SCORES_FILE.with_suffix(".json.tmp")
    backup = SCORES_FILE.with_suffix(".json.bb_bak")

    with open(tmp, "w") as f:
        json.dump(scores, f, indent=2)

    # Validate
    try:
        with open(tmp) as f:
            check = json.load(f)
        if len(check) != len(scores):
            tmp.unlink()
            sys.exit("ABORT — written file has wrong length")
    except (json.JSONDecodeError, OSError) as e:
        tmp.unlink()
        sys.exit(f"ABORT — written file unreadable: {e}")

    shutil.copy2(SCORES_FILE, backup)
    tmp.replace(SCORES_FILE)

    print()
    print(f"✓ Updated: {SCORES_FILE}")
    print(f"  Backup: {backup.name}")

    # Final tally
    final_balanced = [r for r in scores if r.get("hi_balanced")]
    print()
    print(f"Final Balanced Board: {len(final_balanced)} companies")
    for r in sorted(final_balanced, key=lambda x: -x.get("composite", 0)):
        print(f"  {r.get('ticker'):<6} {r.get('composite'):>3} | "
              f"decay={r.get('decay_level')} ({r.get('decay_index')})")


if __name__ == "__main__":
    main()
