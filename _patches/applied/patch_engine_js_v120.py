#!/usr/bin/env python3
"""
v1.2.0 Floor Rule Patcher — human-edge/lib/engine.js

Updates the extension's local scoring engine to mirror the backend:
  1. computeComposite(): implement <30 cap at 50 (was: returns floorTriggered: false always)
  2. computeComposite docstring: replace "No floor rule in v1.1.0" with v1.2.0 description
  3. getProfile(): wire computeComposite's floorTriggered/floorDimension through to result
                   (was: hardcoded `floorTriggered: false`)

Validation:
  - Exact-string anchor matches (aborts loud if drifted)
  - Node.js syntax check on patched file before swap (matches your validation pattern)
  - Atomic: temp → verify → backup → rename

Usage (from repo root):
  python3 human-edge/lib/patch_engine_js_v120.py
"""

import sys
import shutil
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TARGET = SCRIPT_DIR / "engine.js"
if not TARGET.exists():
    TARGET = Path("human-edge/lib/engine.js").resolve()

# ── Edit 1: docstring + body of computeComposite ──
OLD_COMPOSITE = """  /**
   * Compute composite HUMAN score from dimension scores.
   * Formula (v1.1.0): composite = (H + U + M + A + N) / 5
   * No floor rule in v1.1.0 — the Dimensions gate (all ≥ 60) replaces it.
   */
  computeComposite(company) {
    const scores = this.DIMENSIONS.map(d => company[d] || 0);
    const composite = Math.round(scores.reduce((sum, s) => sum + s, 0) / 5);
    return { composite, floorTriggered: false, floorDimension: null };
  },"""

NEW_COMPOSITE = """  /**
   * Compute composite HUMAN score from dimension scores.
   * Formula (v1.2.0): composite = (H + U + M + A + N) / 5
   * Floor rule (v1.2.0): if any HUMAN dimension < 30, composite is capped at 50.
   *   - Mirrors backend pipeline/scoring_engine.py:compute_composite
   *   - floorTriggered fires whenever min_dim < 30, regardless of cap effect
   *   - floorDimension is the uppercase letter of the lowest dim ('H','U','M','A','N')
   */
  computeComposite(company) {
    const scores = this.DIMENSIONS.map(d => company[d] || 0);
    let composite = Math.round(scores.reduce((sum, s) => sum + s, 0) / 5);
    const minDim = Math.min(...scores);
    let floorTriggered = false;
    let floorDimension = null;
    if (minDim < 30) {
      composite = Math.min(composite, 50);
      floorTriggered = true;
      floorDimension = this.DIMENSIONS[scores.indexOf(minDim)].toUpperCase();
    }
    return { composite, floorTriggered, floorDimension };
  },"""

# ── Edit 2: getProfile must consume floorTriggered/floorDimension from computeComposite ──
OLD_GETPROFILE_HEAD = """  getProfile(company, _legacyArg) {
    const { composite } = this.computeComposite(company);
    const hwFlags = this.detectHumanwashing(company);"""

NEW_GETPROFILE_HEAD = """  getProfile(company, _legacyArg) {
    const { composite, floorTriggered, floorDimension } = this.computeComposite(company);
    const hwFlags = this.detectHumanwashing(company);"""

# ── Edit 3: getProfile return — replace hardcoded false with computed values ──
OLD_GETPROFILE_RETURN = """      floorTriggered: false,          // v1.1.0 has no floor
      floorDimension: null,"""

NEW_GETPROFILE_RETURN = """      floorTriggered,                 // v1.2.0: any dim < 30 → cap composite at 50
      floorDimension,"""


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()

    # Anchor checks
    missing = []
    if OLD_COMPOSITE not in src:
        missing.append("computeComposite() block")
    if OLD_GETPROFILE_HEAD not in src:
        missing.append("getProfile() destructure")
    if OLD_GETPROFILE_RETURN not in src:
        missing.append("getProfile() return floorTriggered/floorDimension")
    if missing:
        sys.exit(
            "ABORT — anchors not found verbatim:\n  - "
            + "\n  - ".join(missing)
            + "\nFile may already be patched or has drifted."
        )

    # Re-run guard
    if NEW_COMPOSITE in src:
        sys.exit("ABORT — file already contains v1.2.0 computeComposite. No-op.")

    # Apply
    new_src = src
    new_src = new_src.replace(OLD_COMPOSITE, NEW_COMPOSITE, 1)
    new_src = new_src.replace(OLD_GETPROFILE_HEAD, NEW_GETPROFILE_HEAD, 1)
    new_src = new_src.replace(OLD_GETPROFILE_RETURN, NEW_GETPROFILE_RETURN, 1)

    if new_src == src:
        sys.exit("ABORT — replacements had no effect.")

    # Atomic write
    # Use ".v120tmp.js" suffix so node --check recognizes the extension
    tmp = TARGET.parent / (TARGET.stem + ".v120tmp.js")
    backup = TARGET.with_suffix(TARGET.suffix + ".bak")
    tmp.write_text(new_src)

    # Node.js syntax validation
    node = shutil.which("node")
    if node is None:
        tmp.unlink()
        sys.exit("ABORT — node not found in PATH. Install Node.js or skip JS validation manually.")

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
    print("  Diff summary:")
    print("    1. computeComposite(): added <30 cap at 50, sets floorTriggered + floorDimension")
    print("    2. getProfile(): destructures floorTriggered/floorDimension from computeComposite")
    print("    3. getProfile() return: uses computed values (was hardcoded false/null)")
    print("")
    print("  Quick sanity check:")
    print("    node -e \"const e=require('./human-edge/lib/engine.js');\" ")
    print("    (or load the extension and test on a JNJ-style company)")


if __name__ == "__main__":
    main()
