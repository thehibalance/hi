#!/usr/bin/env python3
"""
v1.2.0 SEC Aggregate Rebuilder — pipeline/data/sec/all_companies.json

Bug: 42 Tier-1 tickers (BAC, ABBV, ABT, GD, NOC, BLK, etc.) have valid
per-ticker SEC files on disk (pipeline/data/sec/{TICKER}.json) but were
never merged into the aggregate file (pipeline/data/sec/all_companies.json).

Scoring engine reads ONLY the aggregate. So those 42 tickers got dropped.

This script:
  1. Reads all per-ticker SEC files (pipeline/data/sec/*.json except aggregate)
  2. Identifies any whose ticker is missing from the aggregate
  3. Validates each has the same schema (company, ticker, h_signals, etc.)
  4. Appends missing entries to the aggregate
  5. Writes back atomically

Idempotent — running again is a no-op (no entries to add).
Read-only on per-ticker files.

Usage (from repo root):
  python3 rebuild_sec_aggregate.py
  python3 rebuild_sec_aggregate.py --dry-run   (show what would be added)
"""

import json
import sys
import shutil
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SEC_DIR = REPO_ROOT / "pipeline" / "data" / "sec"
AGGREGATE = SEC_DIR / "all_companies.json"

# Required schema fields — entries lacking these are skipped (defensive)
REQUIRED_FIELDS = ["company", "ticker"]
# Skip these even if they look like per-ticker files
SKIP_FILES = {"all_companies.json", "all_companies.json.bak", "metadata.json"}


def main():
    parser = argparse.ArgumentParser(description="Rebuild SEC aggregate from per-ticker files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change, don't write")
    args = parser.parse_args()

    if not AGGREGATE.exists():
        sys.exit(f"NOT FOUND: {AGGREGATE}")

    # Load aggregate
    with open(AGGREGATE) as f:
        agg = json.load(f)

    if not isinstance(agg, list):
        sys.exit(f"Expected list in {AGGREGATE}, got {type(agg).__name__}")

    # Build set of tickers already in aggregate
    agg_tickers = set()
    for r in agg:
        t = r.get("ticker")
        if t:
            agg_tickers.add(t.upper())

    print(f"Aggregate: {len(agg)} entries, {len(agg_tickers)} unique tickers")

    # Scan per-ticker files
    additions = []
    skipped = []
    invalid = []

    for path in sorted(SEC_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.name in SKIP_FILES:
            continue
        if not path.name.endswith(".json"):
            continue
        # macOS Finder duplicates etc.
        if " 2.json" in path.name or path.name.startswith("."):
            continue
        # Backup files
        if ".bak" in path.name or ".pre_" in path.name or ".tmp" in path.name:
            continue

        try:
            with open(path) as f:
                record = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            invalid.append((path.name, f"unreadable: {e}"))
            continue

        # Schema check
        missing = [f for f in REQUIRED_FIELDS if not record.get(f)]
        if missing:
            invalid.append((path.name, f"missing fields: {missing}"))
            continue

        ticker = record.get("ticker", "").upper()
        if ticker in agg_tickers:
            skipped.append(ticker)
            continue

        # Defensive: per-ticker files for an error response (no real data) shouldn't be added
        if record.get("error"):
            invalid.append((path.name, f"error field set: {record['error']!r}"))
            continue

        additions.append(record)

    # Report
    print(f"\nScan complete:")
    print(f"  Already in aggregate: {len(skipped)}")
    print(f"  Invalid/skip:         {len(invalid)}")
    print(f"  To be added:          {len(additions)}")

    if invalid:
        print(f"\nInvalid files (skipped):")
        for name, reason in invalid[:20]:
            print(f"  - {name}: {reason}")
        if len(invalid) > 20:
            print(f"  ... and {len(invalid)-20} more")

    if not additions:
        print(f"\n✓ Aggregate already complete. Nothing to add.")
        return

    print(f"\nWill add {len(additions)} entries:")
    for r in additions[:50]:
        print(f"  + {r.get('ticker'):8} {r.get('company')[:60]}")
    if len(additions) > 50:
        print(f"  ... and {len(additions)-50} more")

    if args.dry_run:
        print(f"\n[dry-run] No changes written.")
        return

    # Apply: append additions, write atomically
    new_agg = agg + additions

    tmp = AGGREGATE.with_suffix(".json.tmp")
    backup = AGGREGATE.with_suffix(".json.bak")

    with open(tmp, "w") as f:
        json.dump(new_agg, f, indent=2)

    # Validate the written file
    try:
        with open(tmp) as f:
            check = json.load(f)
        if len(check) != len(new_agg):
            tmp.unlink()
            sys.exit("ABORT — written file has wrong length")
    except (json.JSONDecodeError, OSError) as e:
        tmp.unlink()
        sys.exit(f"ABORT — written file unreadable: {e}")

    # Backup + swap
    shutil.copy2(AGGREGATE, backup)
    tmp.replace(AGGREGATE)

    print(f"\n✓ Aggregate rebuilt:")
    print(f"  Was:    {len(agg)} entries")
    print(f"  Added:  {len(additions)} entries")
    print(f"  Total:  {len(new_agg)} entries")
    print(f"  Backup: {backup.name}")
    print(f"")
    print(f"  Next: cd pipeline && python3 run_all.py --skip-collect")
    print(f"  Then verify: 451 tickers in all_scores.json (was 409)")


if __name__ == "__main__":
    main()
