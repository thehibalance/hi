#!/usr/bin/env python3
"""
v1.2.0 RUBRIC update — RUBRIC.md

Three changes:
  1. Bump 'Spec version: v1.1.0' → 'v1.2.0'
  2. Add a new section 'Composite Floor Rule' between the intro and the
     dimension breakdown. Documents the v1.2.0 < 30 dim → cap at 50 rule.
  3. Update the 'Path forward' language that says 'active research priority
     for v1.2' — v1.2 has shipped, so the language needs to be honest about
     where we are now (v1.3 is next research target).

Anchors are exact-string. Aborts if drifted.

Usage (from repo root):
  python3 patch_rubric_v120.py
"""

import sys
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TARGET = SCRIPT_DIR / "RUBRIC.md"
if not TARGET.exists():
    TARGET = Path("RUBRIC.md").resolve()

# ── Edit 1: Spec version line ──
OLD_SPEC = "Spec version: **v1.1.0** · Active sub-signals: **19** · Deferred: **5**"
NEW_SPEC = "Spec version: **v1.2.0** · Active sub-signals: **19** · Deferred: **5**"

# ── Edit 2: Forward-looking language about v1.2 research priority ──
OLD_FORWARD = """The dominant pattern is **UNGROUNDED**. We don't hide this — most sub-signal ladders were authored by intuition during the engine build, not by reproducing a published authority. **Grounding these ladders is the active research priority for v1.2.**

---

## H — Human Consciousness"""

NEW_FORWARD = """The dominant pattern is **UNGROUNDED**. We don't hide this — most sub-signal ladders were authored by intuition during the engine build, not by reproducing a published authority. **Grounding these ladders is the active research priority for v1.3 and beyond.**

---

## Composite Floor Rule (v1.2.0)

The composite score is the simple mean of the five HUMAN dimensions, with **one floor rule**:

> **If any HUMAN dimension scores below 30, the composite is capped at 50.**

This protects against severe single-dimension failure being averaged away by strong scores in other dimensions. A company cannot earn a composite above 50 if even one HUMAN dimension is in critical failure (< 30), regardless of how the other four perform.

When the floor fires:
- `composite` is capped at 50 (or kept at the natural mean if already ≤ 50)
- `floor_triggered: true` in the API response
- `triggering_dimension` indicates which dimension caused the cap (H/U/M/A/N)

This rule replaces a multi-tier floor system used in earlier specs (any dim < 10 → 40 / 1 dim < 42 → 49 / 2+ dims < 42 → 41), simplified to one clear, defensible threshold.

**Examples:**
- J&J: `D_M = 0` (Harm Documentation penalty) → composite capped at 50
- Costco: `D_N = 27` (CDP grade D + thin SEC filings) → composite capped at 50
- Apple: min dim `D_H = 53` → no cap, composite = mean (74)

**Sub-signal scores < 30 do NOT trigger the floor.** Only dimension-level scores (D_H, D_U, D_M, D_A, D_N) count. Sub-signals are component inputs to the dimension score; the dimension is what matters for floor evaluation.

---

## H — Human Consciousness"""

# ── Edit 3: 'DEFERRED (v1.2 target)' phrasing now stale post-v1.2 ──
OLD_DEFERRED = "| DEFERRED (v1.2 target) | 5 | Spec'd but not yet scored |"
NEW_DEFERRED = "| DEFERRED (v1.3 target) | 5 | Spec'd but not yet scored |"


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()

    missing = []
    if OLD_SPEC not in src:
        missing.append("Spec version line")
    if OLD_FORWARD not in src:
        missing.append("Forward-looking research priority paragraph")
    if OLD_DEFERRED not in src:
        missing.append("DEFERRED table row")
    if missing:
        sys.exit(
            "ABORT — anchors not found verbatim:\n  - "
            + "\n  - ".join(missing)
        )

    if NEW_SPEC in src and NEW_FORWARD in src:
        sys.exit("ABORT — file already contains v1.2.0 RUBRIC updates. No-op.")

    new_src = src
    new_src = new_src.replace(OLD_SPEC, NEW_SPEC, 1)
    new_src = new_src.replace(OLD_FORWARD, NEW_FORWARD, 1)
    new_src = new_src.replace(OLD_DEFERRED, NEW_DEFERRED, 1)

    if new_src == src:
        sys.exit("ABORT — replacements had no effect.")

    # Atomic write
    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    backup = TARGET.with_suffix(TARGET.suffix + ".bak")
    tmp.write_text(new_src)

    shutil.copy2(TARGET, backup)
    tmp.replace(TARGET)

    print("✓ Patched: " + str(TARGET))
    print("  Backup:  " + str(backup))
    print("")
    print("  Three changes:")
    print("    1. Spec version: v1.1.0 → v1.2.0")
    print("    2. Added: 'Composite Floor Rule (v1.2.0)' section")
    print("    3. Updated forward-looking language: v1.2 → v1.3")


if __name__ == "__main__":
    main()
