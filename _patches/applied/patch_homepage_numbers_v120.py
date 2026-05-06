#!/usr/bin/env python3
"""
v1.2.0 Homepage Numbers Update — docs/index.html

After Patchers 26-29 + full re-collection, real coverage is 773 entries
(622 with tickers + 151 seed-only / private leaders). The homepage has
3 hardcoded company-count references that are stale.

Note: line 1160 (the "Brands Scored" stat) already pulls live from
stats.total_companies — that auto-updates with API. We only patch the
3 hardcoded references.

  Line 239: "Any of 443+ scored companies" → "Any of 750+"
  Line 344: "441+ companies · 42 data sources · 32 endpoints" → "750+"
  Line 957: "For the other 426+ companies, A.4..." → "740+"
            (iFixit covers ~15, so "the other" = 773 - 15 ≈ 758, round to 740+)

Strategy: ROUND DOWN to nearest 10 to avoid churn on every cron run that
adds or removes 1-2 tickers. "750+" stays accurate whether real count is
747, 757, or 773. Forward-stable for at least 6+ months of growth.

Anchors: exact-string content match. Each anchor verified unique in file.

Usage (from repo root):
  python3 patch_homepage_numbers_v120.py
"""

import sys
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
TARGET = REPO_ROOT / "docs" / "index.html"


# Three surgical edits using the EXACT strings from current homepage
EDITS = [
    (
        "Hero CTA — 'Any of 443+ scored companies'",
        "Any of 443+ scored companies",
        "Any of 750+ scored companies",
    ),
    (
        "API/Developer section — '441+ companies'",
        "441+ companies · 42 data sources · 32 endpoints",
        "750+ companies · 42 data sources · 32 endpoints",
    ),
    (
        "iFixit context — 'the other 426+ companies'",
        "For the other 426+ companies, A.4 (Product Lifecycle) falls back",
        "For the other 740+ companies, A.4 (Product Lifecycle) falls back",
    ),
]


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()
    new_src = src
    applied = 0
    skipped = 0

    print("Applying Patcher 30 — homepage company-count update:")
    for label, old, new in EDITS:
        # Idempotent: if new is already there and old is gone, skip
        if old not in new_src and new in new_src:
            print(f"  ⏭  [{label}] already updated")
            skipped += 1
            continue
        if old not in new_src:
            print(f"  ✗ [{label}] anchor not found")
            print(f"      Looking for: {old[:70]!r}")
            sys.exit(f"ABORT: anchor for '{label}' missing")
        if new_src.count(old) != 1:
            sys.exit(f"ABORT [{label}] — anchor appears {new_src.count(old)} times, ambiguous")
        new_src = new_src.replace(old, new, 1)
        applied += 1
        print(f"  ✓ [{label}]")

    if applied == 0 and skipped > 0:
        print(f"\n  All edits already applied. No changes.")
        return
    if applied == 0:
        sys.exit("ABORT — no edits applied.")

    # Atomic write
    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    backup = TARGET.with_suffix(TARGET.suffix + ".numbers_bak")
    tmp.write_text(new_src)

    # Sanity: file should still parse as text and contain expected content
    written = tmp.read_text()
    if "750+ scored companies" not in written and applied > 0:
        tmp.unlink()
        sys.exit("ABORT — verification failed (new text not in written file)")

    shutil.copy2(TARGET, backup)
    tmp.replace(TARGET)

    print()
    print(f"✓ Patched: {TARGET}")
    print(f"  Backup: {backup.name}")
    print(f"  {applied} edits applied, {skipped} skipped")
    print()
    print("  Note: the homepage 'Brands Scored' stat (line ~1160) already pulls")
    print("  live from stats.total_companies — auto-updates with API. No patch needed.")
    print()
    print("  Verify by viewing the page after deploy:")
    print("    https://thehibalance.org")


if __name__ == "__main__":
    main()
