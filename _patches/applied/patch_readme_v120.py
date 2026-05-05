#!/usr/bin/env python3
"""
v1.2.0 README update — README.md

Three edits:
  1. Spec badge: v1.1.0 → v1.2.0
  2. Deferred sub-signals line: 'deferred to v1.2' → 'deferred to v1.3'
     (since v1.2 has shipped, the deferred items target the next minor)
  3. Add a 'What's new in v1.2.0' callout near the top after the framework table

Anchors are exact-string. Aborts if drifted.

Usage (from repo root):
  python3 patch_readme_v120.py
"""

import sys
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TARGET = SCRIPT_DIR / "README.md"
if not TARGET.exists():
    TARGET = Path("README.md").resolve()

# ── Edit 1: Spec badge ──
OLD_BADGE = "[![Spec](https://img.shields.io/badge/spec-v1.1.0-1B3A5C.svg)](https://thehibalance.org/#methodology)"
NEW_BADGE = "[![Spec](https://img.shields.io/badge/spec-v1.2.0-1B3A5C.svg)](https://thehibalance.org/#methodology)"

# ── Edit 2: Deferred sub-signals line ──
OLD_DEFERRED = "**19 active sub-signals. 5 deferred to v1.2** (H.4, U.5, N.1, N.3, N.4 — spec'd but not yet scored). Our [methodology page](https://thehibalance.org/#methodology) documents every formula and threshold."
NEW_DEFERRED = "**19 active sub-signals. 5 deferred to v1.3** (H.4, U.5, N.1, N.3, N.4 — spec'd but not yet scored). Our [methodology page](https://thehibalance.org/#methodology) documents every formula and threshold."

# ── Edit 3: Insert "What's new in v1.2.0" after the HUMAN Framework table ──
# Anchor on the line right after the framework table, before "## The Balanced Board"
OLD_TRANSITION = """**19 active sub-signals. 5 deferred to v1.3** (H.4, U.5, N.1, N.3, N.4 — spec'd but not yet scored). Our [methodology page](https://thehibalance.org/#methodology) documents every formula and threshold.

## The Balanced Board"""

NEW_TRANSITION = """**19 active sub-signals. 5 deferred to v1.3** (H.4, U.5, N.1, N.3, N.4 — spec'd but not yet scored). Our [methodology page](https://thehibalance.org/#methodology) documents every formula and threshold.

## What's new in v1.2.0

**Composite Floor Rule.** If any HUMAN dimension scores below 30, the composite is capped at 50. Replaces an earlier multi-tier floor system with one clear, defensible threshold. See `RUBRIC.md` for examples (J&J, Costco, Apple).

**Standardized harm rendering across surfaces.** Web detail page and Chrome extension panel now show identical evidence blocks: ⚠ Harm Documentation (J&J-class public-record harm with linked sources), ⚡ Algorithmic Harm Index with components mini-bars (Meta-class algorithmic decision-making at scale), and 🚩 Humanwashing (filtered to true HW flags only — no duplication across blocks).

**Coverage expansion.** S&P 500 + Russell 1000 universe (589 US tickers) now feeds SEC EDGAR, FMP, and Yahoo pipelines. Earlier list was 315 tickers.

## The Balanced Board"""


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()

    missing = []
    if OLD_BADGE not in src:
        missing.append("Spec badge line")
    if OLD_DEFERRED not in src:
        missing.append("Deferred sub-signals line")
    if missing:
        sys.exit(
            "ABORT — anchors not found verbatim:\n  - "
            + "\n  - ".join(missing)
        )

    if NEW_BADGE in src and "What's new in v1.2.0" in src:
        sys.exit("ABORT — file already contains v1.2.0 README updates. No-op.")

    # Apply: bump badge first, then deferred (which becomes part of transition anchor)
    new_src = src
    new_src = new_src.replace(OLD_BADGE, NEW_BADGE, 1)
    new_src = new_src.replace(OLD_DEFERRED, NEW_DEFERRED, 1)
    # Now the transition anchor will match (it uses NEW_DEFERRED text)
    new_src = new_src.replace(OLD_TRANSITION, NEW_TRANSITION, 1)

    if new_src == src:
        sys.exit("ABORT — replacements had no effect.")

    # Atomic write
    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    backup = TARGET.with_suffix(TARGET.suffix + ".bak")
    tmp.write_text(new_src)

    # Sanity: line delta ~10 (one new section)
    old_lines = src.count("\n")
    new_lines = new_src.count("\n")
    delta = new_lines - old_lines
    if delta < 5 or delta > 20:
        tmp.unlink()
        sys.exit(f"ABORT — unexpected line delta: {delta} (expected ~8).")

    shutil.copy2(TARGET, backup)
    tmp.replace(TARGET)

    print("✓ Patched: " + str(TARGET))
    print("  Backup:  " + str(backup))
    print(f"  Lines added: {delta}")
    print("")
    print("  Three changes to README:")
    print("    1. Spec badge: v1.1.0 → v1.2.0")
    print("    2. Deferred sub-signals: v1.2 → v1.3 (since v1.2 shipped)")
    print("    3. Added: 'What's new in v1.2.0' section (floor rule + harm")
    print("       rendering standardization + coverage expansion)")


if __name__ == "__main__":
    main()
