#!/usr/bin/env python3
"""
v1.2.0 spec_version Cache Normalization — pipeline/api_server.py

Bug: /api/v1/score/ticker/<T> serves directly from the in-memory TICKERS
cache (line 779). The line 329 fallback only fires when seed_to_record is
called, never on cache lookups. Result: RIVN-class records with
spec_version=None pass through the cache → API returns null spec_version.

Fix: when populating TICKERS at load time, normalize spec_version on each
record. None or empty string becomes '1.2.0'.

Insertion point: right before line 517 (`if t: TICKERS[t.upper()] = c`),
inside the load loop. Affects every record being indexed.

Anchor: exact-string match on the heartbeat injection block + ticker index.

Usage (from repo root):
  python3 patch_api_load_normalize_v120.py
"""

import sys
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
TARGET = REPO_ROOT / "pipeline" / "api_server.py"


OLD_BLOCK = """            # Inject heartbeat data
            if t and t.upper() in HEARTBEAT:
                hb = HEARTBEAT[t.upper()]
                c["decay_index"] = hb.get("decay_index", 0)
                c["decay_level"] = hb.get("decay_level", "stable")
                c["decay_factors"] = hb.get("factors", [])
            
            if t: TICKERS[t.upper()] = c"""

NEW_BLOCK = """            # Inject heartbeat data
            if t and t.upper() in HEARTBEAT:
                hb = HEARTBEAT[t.upper()]
                c["decay_index"] = hb.get("decay_index", 0)
                c["decay_level"] = hb.get("decay_level", "stable")
                c["decay_factors"] = hb.get("factors", [])
            
            # v1.2.0: normalize spec_version at load time so cache never serves null.
            # Seed-only tickers (RIVN class) store spec_version: null in their source
            # records; the line 329 setdefault fallback doesn't fire for cache hits.
            if not c.get("spec_version"):
                c["spec_version"] = "1.2.0"
            
            if t: TICKERS[t.upper()] = c"""


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()

    if OLD_BLOCK not in src:
        sys.exit(
            "ABORT — anchor block not found verbatim.\n"
            "Expected the heartbeat injection + TICKERS index block around line 511-517."
        )

    if NEW_BLOCK in src:
        sys.exit("ABORT — file already contains v1.2.0 cache normalization. No-op.")

    new_src = src.replace(OLD_BLOCK, NEW_BLOCK, 1)
    if new_src == src:
        sys.exit("ABORT — replacement had no effect.")

    # Atomic write
    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    backup = TARGET.with_suffix(TARGET.suffix + ".load_norm_bak")
    tmp.write_text(new_src)

    # py_compile validation
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(tmp)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        tmp.unlink()
        sys.exit(f"ABORT — py_compile failed:\n{result.stderr}")

    shutil.copy2(TARGET, backup)
    tmp.replace(TARGET)

    print(f"✓ Patched: {TARGET}")
    print(f"  Backup: {backup.name}")
    print()
    print("  spec_version is now normalized at TICKERS load time.")
    print("  Every cache lookup will return '1.2.0' instead of None for seed records.")
    print()
    print("  Next:")
    print("    git add pipeline/api_server.py")
    print("    git commit + push → Railway redeploys → audit shows 0 BLOCKERs ✨")


if __name__ == "__main__":
    main()
