#!/usr/bin/env python3
"""
v1.2.0 Dedup Logic Fix — pipeline/scoring_engine.py

Bug: 42 Tier-1 tickers (BAC, ABBV, ABT, GD, NOC, BLK, BMY, etc.) were
silently dropped from all_scores.json during the v1.2.0 rescore.

Root cause: the name-collision dedup branch only replaces the existing
entry if `len(new.data_sources) > len(existing.data_sources)`. When a
seed record (no ticker, name "Bank of America Corporation") collides
with a scored record (ticker "BAC", name "Bank of America Corp"), if
the seed has equal or more raw data sources than the scored entry, the
SEED wins — orphaning the ticker.

Fix: prefer ticker-bearing entries over ticker-less seed entries.
Specifically:
  - If new has a ticker AND existing doesn't → new wins
  - If existing has a ticker AND new doesn't → existing wins
  - Otherwise → tie-break by data_sources count (current behavior)

Apply only to the NAME-collision branch (line ~1781). The ticker-collision
branch (line ~1772) is symmetric (both have tickers) so unchanged.

Anchor: exact-string match on the name-dupe block.

Usage (from repo root):
  python3 patch_dedup_v120.py
"""

import sys
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
TARGET = REPO_ROOT / "pipeline" / "scoring_engine.py"


# Anchor: the existing name-collision dedup block (lines ~1781-1789)
OLD_BLOCK = """        # Check name dupe
        elif norm and norm in seen_names:
            existing = seen_names[norm]
            if len(s.get("data_sources", [])) > len(existing.get("data_sources", [])):
                deduped.remove(existing)
                seen_names[norm] = s
                if t: seen_tickers[t] = s
                deduped.append(s)
            dupes_removed += 1
            is_dupe = True"""

NEW_BLOCK = """        # Check name dupe
        elif norm and norm in seen_names:
            existing = seen_names[norm]
            # v1.2.0 fix: prefer ticker-bearing entries over seed entries.
            # When a scored record (with ticker) collides on normalized name with
            # a seed record (no ticker), the ticker entry should ALWAYS win
            # regardless of raw data_sources count, otherwise we orphan the ticker
            # and drop a Tier-1 company from the scored universe.
            s_has_ticker = bool(s.get("ticker"))
            e_has_ticker = bool(existing.get("ticker"))
            s_sources = len(s.get("data_sources", []))
            e_sources = len(existing.get("data_sources", []))
            should_replace = False
            if s_has_ticker and not e_has_ticker:
                should_replace = True
            elif s_has_ticker == e_has_ticker and s_sources > e_sources:
                should_replace = True
            if should_replace:
                deduped.remove(existing)
                seen_names[norm] = s
                if t: seen_tickers[t] = s
                deduped.append(s)
            dupes_removed += 1
            is_dupe = True"""


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()

    if OLD_BLOCK not in src:
        sys.exit(
            "ABORT — anchor block not found verbatim.\n"
            "Expected the name-collision dedup branch around line 1781.\n"
            "File may already be patched or has drifted."
        )

    if NEW_BLOCK in src:
        sys.exit("ABORT — file already contains v1.2.0 dedup fix. No-op.")

    new_src = src.replace(OLD_BLOCK, NEW_BLOCK, 1)
    if new_src == src:
        sys.exit("ABORT — replacement had no effect.")

    # Atomic write
    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    backup = TARGET.with_suffix(TARGET.suffix + ".bak")
    tmp.write_text(new_src)

    # Python syntax validation
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(tmp)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        tmp.unlink()
        sys.exit(f"ABORT — py_compile failed:\n{result.stderr}")

    shutil.copy2(TARGET, backup)
    tmp.replace(TARGET)

    print("✓ Patched: " + str(TARGET))
    print("  Backup:  " + str(backup))
    print("  Python syntax: clean")
    print("")
    print("  Dedup logic fix applied:")
    print("    - Name-collision branch now prefers ticker-bearing entries")
    print("    - Seed records (no ticker) no longer orphan scored records (with ticker)")
    print("")
    print("  Next steps:")
    print("    1. Re-run rescore: cd pipeline && python3 run_all.py --skip-collect")
    print("    2. Verify ticker count: should be ~445 (not 262)")
    print("    3. Verify lost tickers come back:")
    print("       python3 -c \"")
    print("       import json")
    print("       d = json.load(open('pipeline/data/scores/all_scores.json'))")
    print("       tickers = {e.get('ticker') for e in d}")
    print("       check = ['BAC', 'ABBV', 'GD', 'NOC', 'BLK', 'BMY', 'PG']")
    print("       for t in check: print(t, '✓' if t in tickers else '✗ STILL MISSING')")
    print("       \"")
    print("    4. If clean, push: git add pipeline/data && git commit + git push")


if __name__ == "__main__":
    main()
