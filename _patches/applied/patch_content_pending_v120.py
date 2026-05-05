#!/usr/bin/env python3
"""
v1.2.0 Pending Logic Alignment — human-edge/content.js

Current bug:
  Extension marks any company with data_sources == ["Manual Scoring"] (or any
  single seed-source value) as PENDING → renders as gray "?" badge.

  This contradicts the web rendering (docs/index.html) and the backend's
  intent: seed-source records ARE legitimate scores. The web shows them
  with their composite + source count (e.g., "X/Twitter: 19, 1 sources").

  Result: Rivian (public company, seed-only data) shows gray in extension
  but correct score on web. Inconsistent UX.

Fix:
  Align extension with backend's standard: a company is PENDING only when
  it has truly zero data sources (or has explicit score_status: 'pending'
  from the API). Seed-source records render normally.

  This is a 1-condition simplification of the existing logic, not new logic.

Validation:
  - Exact-string anchor match (aborts loud if drifted)
  - Node.js syntax check before swap (matches your validation pattern)
  - Atomic: temp → verify → backup → rename

Usage (from repo root):
  python3 human-edge/patch_content_pending_v120.py
"""

import sys
import shutil
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TARGET = SCRIPT_DIR / "content.js"
if not TARGET.exists():
    TARGET = Path("human-edge/content.js").resolve()

# ── EXACT old block (line 140-148) ──
OLD_BLOCK = """  // Detect pending (seed) companies — show gray
  const SEED_SOURCES = ['Defaults', 'Manual Scoring', 'Seed Estimate', 'Public Reporting'];
  profile.isPending = company.score_status === 'pending' || 
    (profile.data_sources.length === 1 && SEED_SOURCES.includes(profile.data_sources[0])) ||
    (profile.data_sources.length === 0);
  if (profile.isPending) {
    profile.scoreColor = '#999';
    profile.hiBalanced = false;
    profile.isGold = false;
  }"""

# ── NEW block: align with backend / web behavior ──
# Pending only if: explicit score_status='pending' OR truly zero data sources.
# Seed-only records (Manual Scoring etc.) render normally — same as the web.
# The source count surfaces data quality to the user, not the gray treatment.
NEW_BLOCK = """  // Pending detection — aligned with backend/web standard.
  // A company is PENDING only when it has zero data sources or the API
  // explicitly marks it pending. Seed-source records (Manual Scoring,
  // Seed Estimate, etc.) render normally with their composite + source
  // count, matching docs/index.html behavior. Users judge data quality
  // via the visible source count, not via gray-out treatment.
  profile.isPending = company.score_status === 'pending' ||
    (profile.data_sources.length === 0);
  if (profile.isPending) {
    profile.scoreColor = '#999';
    profile.hiBalanced = false;
    profile.isGold = false;
  }"""


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()

    if OLD_BLOCK not in src:
        sys.exit(
            "ABORT — anchor block not found verbatim.\n"
            "File may already be patched or the pending block has drifted.\n"
            "Check around line 140 of human-edge/content.js."
        )
    if NEW_BLOCK in src:
        sys.exit("ABORT — file already contains v1.2.0 pending logic. No-op.")

    new_src = src.replace(OLD_BLOCK, NEW_BLOCK, 1)
    if new_src == src:
        sys.exit("ABORT — replacement had no effect.")

    # Atomic write — use .v120tmp.js so node --check accepts the extension
    tmp = TARGET.parent / (TARGET.stem + ".v120tmp.js")
    backup = TARGET.with_suffix(TARGET.suffix + ".bak")
    tmp.write_text(new_src)

    # Node.js syntax validation
    node = shutil.which("node")
    if node is None:
        tmp.unlink()
        sys.exit("ABORT — node not found in PATH.")

    result = subprocess.run(
        [node, "--check", str(tmp)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        tmp.unlink()
        sys.exit(f"ABORT — node --check failed:\n{result.stderr}")

    # Backup + swap
    shutil.copy2(TARGET, backup)
    tmp.replace(TARGET)

    print("✓ Patched: " + str(TARGET))
    print("  Backup:  " + str(backup))
    print("  Node syntax: clean")
    print("")
    print("  Behavior change:")
    print("    Before: data_sources=['Manual Scoring']  → isPending=true (gray)")
    print("    After:  data_sources=['Manual Scoring']  → isPending=false (colored)")
    print("    Unchanged: data_sources=[]  →  isPending=true (gray)")
    print("")
    print("  Verify:")
    print("    1. Reload extension at chrome://extensions/")
    print("    2. Visit rivian.com → badge shows colored 57 (not gray '?')")
    print("    3. Visit a domain not in any database → still shows gray (correct)")
    print("")
    print("  Then: bump version to 1.2.0 in human-edge/manifest.json,")
    print("  package, and submit to Chrome Web Store.")


if __name__ == "__main__":
    main()
