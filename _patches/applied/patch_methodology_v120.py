#!/usr/bin/env python3
"""
v1.2.0 Methodology Patcher — docs/index.html

Replaces the stale "Balance floors" sub-expandable in the
"How was this score calculated?" section (lines ~1395-1400) with the
single v1.2.0 rule: any HUMAN dimension < 30 caps composite at 50.

Validation:
  - Exact-string anchor match (aborts loud if file already patched / drifted)
  - Sanity check: <details> open/close count must be balanced before AND after
  - Atomic: temp → verify → backup → rename

Usage (from repo root):
  python3 docs/patch_methodology_v120.py
"""

import sys
import shutil
from pathlib import Path

# Resolve target relative to script location
SCRIPT_DIR = Path(__file__).resolve().parent
TARGET = SCRIPT_DIR / "index.html"
if not TARGET.exists():
    TARGET = Path("docs/index.html").resolve()

# ── EXACT old block (5 string-concat lines describing the multi-tier floors) ──
OLD_BLOCK = """    h += '<p style=\"margin:8px 0\"><strong>Balance floors</strong> apply when one dimension drags far behind:</p>';
    h += '<div style=\"font-family:ui-monospace,monospace;background:#fff;padding:10px 12px;border-radius:6px;border:1px solid #E5E7EB;margin:8px 0;font-size:11px\">';
    h += '• Any dimension < 10 → composite capped at 40<br>';
    h += '• 2+ dimensions < 42 → capped at 41 (F)<br>';
    h += '• 1 dimension < 42 → capped at 49 (D)';
    h += '</div>';"""

# ── NEW block (v1.2.0 single rule) ──
NEW_BLOCK = """    h += '<p style=\"margin:8px 0\"><strong>Floor rule</strong> protects against severe single-dimension failure:</p>';
    h += '<div style=\"font-family:ui-monospace,monospace;background:#fff;padding:10px 12px;border-radius:6px;border:1px solid #E5E7EB;margin:8px 0;font-size:11px\">';
    h += 'Any HUMAN dimension &lt; 30 &rarr; composite capped at 50';
    h += '</div>';"""


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()

    if OLD_BLOCK not in src:
        sys.exit(
            "ABORT — anchor block not found verbatim.\n"
            "File may already be patched, or the methodology block has drifted.\n"
            "Check around line 1395 of docs/index.html."
        )
    if NEW_BLOCK in src:
        sys.exit("ABORT — file already contains v1.2.0 methodology block. No-op.")

    # Sanity: count <details> open/close BEFORE
    open_before = src.count("<details ")
    close_before = src.count("</details>")
    if open_before != close_before:
        sys.exit(f"ABORT — pre-patch <details> tags unbalanced: {open_before} open vs {close_before} close")

    new_src = src.replace(OLD_BLOCK, NEW_BLOCK, 1)
    if new_src == src:
        sys.exit("ABORT — replacement had no effect.")

    # Sanity: <details> count must still match after
    open_after = new_src.count("<details ")
    close_after = new_src.count("</details>")
    if open_after != open_before or close_after != close_before:
        sys.exit(
            f"ABORT — patch unbalanced <details> tags. Before: {open_before}/{close_before}. "
            f"After: {open_after}/{close_after}."
        )

    # Atomic: temp → backup → swap
    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    backup = TARGET.with_suffix(TARGET.suffix + ".bak")

    tmp.write_text(new_src)
    shutil.copy2(TARGET, backup)
    tmp.replace(TARGET)

    print("✓ Patched: " + str(TARGET))
    print("  Backup:  " + str(backup))
    print("")
    print("  Replaced:")
    print("    OLD: 'Balance floors' + 3 multi-tier rules (< 10/40, 2+ < 42/41, 1 < 42/49)")
    print("    NEW: 'Floor rule' + single line: any dim < 30 → cap at 50")
    print("")
    print("  Verify in browser:")
    print("    1. Load any company detail page (e.g., /?ticker=JNJ)")
    print("    2. Click 'Sources & Methodology' → 'How was this score calculated?'")
    print("    3. Confirm new copy renders, < 30 → cap at 50")


if __name__ == "__main__":
    main()
