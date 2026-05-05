#!/usr/bin/env python3
"""
v1.2.0 Floor Rule Patcher — pipeline/scoring_engine.py

Replaces:
  - Stale module-level docstring (lines 8-9) describing removed multi-tier floor rules
  - compute_composite() body (currently no floor) → adds new "<30 caps at 50" rule

Preserves:
  - 4-tuple return signature (composite, floor_triggered, balance_floor_unused, triggering_dim)
    so api_server caller at line 1546 keeps working without changes.
  - balance_floor_unused stays False forever — placeholder for legacy API field.

Validation:
  - py_compile before swap
  - Exact-string match guards (fails loud if file already patched / has drifted)
  - Atomic: write .tmp → verify → backup original to .bak → rename .tmp → target

Usage (run from repo root):
  python3 pipeline/patch_scoring_v120.py
"""

import sys
import shutil
import subprocess
from pathlib import Path

# ── Resolve target relative to repo root (script may be run from anywhere) ──
SCRIPT_DIR = Path(__file__).resolve().parent
TARGET = SCRIPT_DIR / "scoring_engine.py"
if not TARGET.exists():
    # Fallback: if patcher is run from repo root
    TARGET = Path("pipeline/scoring_engine.py").resolve()

# ── EXACT old text to replace (must match verbatim or patcher aborts) ──

OLD_DOCSTRING = """Floor rule: any dimension < 10 caps composite at 40.
Balance floor: any dimension < 42 flags balance. 2+ dims below 42 caps at 41. 1 dim below 42 caps at 49."""

NEW_DOCSTRING = """Floor rule (v1.2.0): any HUMAN dimension < 30 caps composite at 50."""

OLD_FN = '''def compute_composite(D_H, D_U, D_M, D_A, D_N):
    """v1.1.0: composite is the simple mean of the five HUMAN dimensions.
    
    Floors removed in v1.1.0 — Gold HI Grade eligibility is now determined per-dimension
    by check_hi_certified (each dim ≥ 60). Composite is purely a display number for users
    who want a single quick gauge; it does not gate anything.
    
    Return signature preserved for backward compatibility with callers expecting a 4-tuple,
    but the 2nd/3rd/4th elements are always False/False/None now.
    """
    composite = (D_H + D_U + D_M + D_A + D_N) / 5
    return round_score(composite), False, False, None'''

NEW_FN = '''def compute_composite(D_H, D_U, D_M, D_A, D_N):
    """v1.2.0: composite is the mean of the five HUMAN dimensions, with one floor rule.

    FLOOR RULE: if ANY dimension < 30, composite is capped at 50.
    Severe failure in any single HUMAN dimension means the company cannot earn a
    composite above 50, even if the other four dimensions average it higher. This
    protects users from companies with one severely failing dimension (e.g.,
    harm_documentation penalties zeroing out M for J&J / Bayer / Purdue-style cases).

    Returns 4-tuple (signature preserved for backward compatibility):
      (composite, floor_triggered, balance_floor_unused, triggering_dimension)

    The 3rd element (balance_floor_unused) is always False — the legacy multi-tier
    "balance floor" rule was removed in v1.1.0; the placeholder is retained so the
    api_server caller can serialize a stable schema without churn. Schedule for
    full removal in v1.3 once iOS / extension consumers are audited.

    floor_triggered fires whenever min_dim < 30, even if the mean was already ≤ 50
    (signals "severe single-dim failure" to UI consumers regardless of cap effect).
    """
    composite = (D_H + D_U + D_M + D_A + D_N) / 5
    dims = {"H": D_H, "U": D_U, "M": D_M, "A": D_A, "N": D_N}
    min_dim_value = min(dims.values())

    if min_dim_value < 30:
        composite = min(composite, 50)
        triggering_dimension = min(dims, key=dims.get)
        return round_score(composite), True, False, triggering_dimension

    return round_score(composite), False, False, None'''


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()

    # Guard: refuse to run if either anchor is missing
    missing = []
    if OLD_DOCSTRING not in src:
        missing.append("module docstring (lines 8-9 stale floor description)")
    if OLD_FN not in src:
        missing.append("compute_composite() body")
    if missing:
        sys.exit(
            "ABORT — anchor text not found verbatim:\n  - "
            + "\n  - ".join(missing)
            + "\nFile may already be patched, drifted, or be the wrong copy."
        )

    # Guard: refuse to run if NEW text is already present (re-run safety)
    if NEW_FN in src:
        sys.exit("ABORT — file already contains v1.2.0 compute_composite. No-op.")

    # Apply replacements (count=1 to be paranoid about uniqueness)
    new_src = src.replace(OLD_DOCSTRING, NEW_DOCSTRING, 1)
    new_src = new_src.replace(OLD_FN, NEW_FN, 1)

    if new_src == src:
        sys.exit("ABORT — replacements had no effect.")

    # Atomic write: temp → verify → backup → rename
    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    backup = TARGET.with_suffix(TARGET.suffix + ".bak")

    tmp.write_text(new_src)

    # Validate syntax via py_compile
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(tmp)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        tmp.unlink()
        sys.exit(f"ABORT — py_compile failed on patched file:\n{result.stderr}")

    # Backup original, then swap temp into place
    shutil.copy2(TARGET, backup)
    tmp.replace(TARGET)

    print("✓ Patched: " + str(TARGET))
    print("  Backup:  " + str(backup))
    print("  Diff summary:")
    print("    - Module docstring: stale multi-tier floor → '<30 caps at 50' (v1.2.0)")
    print("    - compute_composite(): added <30 cap rule, kept 4-tuple signature")
    print("")
    print("  Now run self-test:")
    print("    python3 pipeline/patch_scoring_v120_test.py")


if __name__ == "__main__":
    main()
