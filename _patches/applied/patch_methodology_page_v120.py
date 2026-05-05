#!/usr/bin/env python3
"""
v1.2.0 Methodology Page Updates — docs/index.html

Three edits to the dedicated /methodology page (#page-methodology, line 707).
NOT the per-company sub-expandable (that was already updated in earlier patch).

  1. Subhead spec version: 'Spec v1.1.0 · April 2026' → 'Spec v1.2.0 · April 2026'
  2. Section header: 'Balanced Board — v1.1.0 criteria' → 'Balanced Board — v1.2.0 criteria'
  3. Add a new 'Composite Floor Rule' section before the Balanced Board section,
     documenting the v1.2.0 < 30 → cap at 50 rule

Anchors are exact-string. Aborts if drifted.

Usage (from repo root):
  python3 docs/patch_methodology_page_v120.py
"""

import sys
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TARGET = SCRIPT_DIR / "index.html"
if not TARGET.exists():
    TARGET = Path("docs/index.html").resolve()

# ── Edit 1: Subpage subhead ──
OLD_SUBHEAD = '<p class="subpage-sub">The math behind being human kind. Spec v1.1.0 · April 2026</p>'
NEW_SUBHEAD = '<p class="subpage-sub">The math behind being human kind. Spec v1.2.0 · April 2026</p>'

# ── Edit 2: Balanced Board section header + insertion of Composite Floor Rule ──
# Anchors on the </ul> + Balanced Board h2 boundary so we can inject a section between.
OLD_HEADER = '''</ul>

<h2 style="font-family:'DM Serif Display';font-size:26px;color:var(--navy);margin:36px 0 16px">Balanced Board — v1.1.0 criteria</h2>'''

NEW_HEADER = '''</ul>

<h2 style="font-family:'DM Serif Display';font-size:26px;color:var(--navy);margin:36px 0 16px">Composite Floor Rule — v1.2.0</h2>
<p style="color:#444;line-height:1.7;margin-bottom:16px">The composite score is the simple mean of the five HUMAN dimensions, with <strong>one floor rule</strong>:</p>

<div style="background:#FEF3F2;border-left:4px solid #DC2626;padding:16px 20px;margin:16px 0;border-radius:0 8px 8px 0">
  <p style="margin:0;font-size:15px;color:#7F1D1D;font-weight:600;line-height:1.5">If any HUMAN dimension scores below 30, the composite is capped at 50.</p>
</div>

<p style="color:#444;line-height:1.7;margin-bottom:16px">This protects against severe single-dimension failure being averaged away by strong scores in other dimensions. A company cannot earn a composite above 50 if even one HUMAN dimension is in critical failure (&lt; 30), regardless of how the other four perform.</p>

<p style="color:#444;line-height:1.7;margin-bottom:8px"><strong>When the floor fires:</strong></p>
<ul style="color:#444;line-height:1.8;margin-bottom:16px">
  <li><code style="background:#F3F4F6;padding:2px 6px;border-radius:4px;font-size:12px">composite</code> is capped at 50 (or kept at the natural mean if already ≤ 50)</li>
  <li><code style="background:#F3F4F6;padding:2px 6px;border-radius:4px;font-size:12px">floor_triggered: true</code> in the API response</li>
  <li><code style="background:#F3F4F6;padding:2px 6px;border-radius:4px;font-size:12px">triggering_dimension</code> indicates which dimension caused the cap (H/U/M/A/N)</li>
</ul>

<p style="color:#444;line-height:1.7;margin-bottom:16px">This rule replaces a multi-tier floor system used in earlier specs (any dim &lt; 10 → cap 40, one dim &lt; 42 → cap 49, two+ dims &lt; 42 → cap 41), simplified to one clear, defensible threshold.</p>

<p style="color:#444;line-height:1.7;margin-bottom:8px"><strong>Examples:</strong></p>
<ul style="color:#444;line-height:1.8;margin-bottom:16px">
  <li><strong>Johnson &amp; Johnson:</strong> D_M = 0 (Harm Documentation penalty) → composite capped at 50</li>
  <li><strong>Costco:</strong> D_N = 27 (CDP grade D + thin SEC filings) → composite capped at 50</li>
  <li><strong>Apple:</strong> minimum dimension D_H = 53 → no cap, composite = mean (74)</li>
</ul>

<p style="color:#666;line-height:1.7;margin-bottom:16px;font-size:13px;font-style:italic">Note: sub-signal scores below 30 do not trigger the floor. Only dimension-level scores (D_H, D_U, D_M, D_A, D_N) count. Sub-signals are component inputs; the dimension is what matters for floor evaluation.</p>

<h2 style="font-family:'DM Serif Display';font-size:26px;color:var(--navy);margin:36px 0 16px">Balanced Board — v1.2.0 criteria</h2>'''


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()

    missing = []
    if OLD_SUBHEAD not in src:
        missing.append("Methodology subhead 'Spec v1.1.0'")
    if OLD_HEADER not in src:
        missing.append("Balanced Board v1.1.0 header")
    if missing:
        sys.exit(
            "ABORT — anchors not found verbatim:\n  - "
            + "\n  - ".join(missing)
        )

    if NEW_SUBHEAD in src and NEW_HEADER in src:
        sys.exit("ABORT — file already contains v1.2.0 methodology updates. No-op.")

    new_src = src
    new_src = new_src.replace(OLD_SUBHEAD, NEW_SUBHEAD, 1)
    new_src = new_src.replace(OLD_HEADER, NEW_HEADER, 1)

    if new_src == src:
        sys.exit("ABORT — replacements had no effect.")

    # Atomic write
    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    backup = TARGET.with_suffix(TARGET.suffix + ".bak")
    tmp.write_text(new_src)

    # Sanity: line delta should be ~25-30 (one new section)
    old_lines = src.count("\n")
    new_lines = new_src.count("\n")
    delta = new_lines - old_lines
    if delta < 20 or delta > 35:
        tmp.unlink()
        sys.exit(f"ABORT — unexpected line delta: {delta} (expected ~25).")

    shutil.copy2(TARGET, backup)
    tmp.replace(TARGET)

    print("✓ Patched: " + str(TARGET))
    print("  Backup:  " + str(backup))
    print(f"  Lines added: {delta}")
    print("")
    print("  Three changes to the methodology page:")
    print("    1. Subhead version: v1.1.0 → v1.2.0")
    print("    2. Balanced Board section header: v1.1.0 → v1.2.0")
    print("    3. Added: 'Composite Floor Rule — v1.2.0' section with examples")
    print("")
    print("  Verify in browser:")
    print("    1. Open /methodology page")
    print("    2. Subhead reads 'Spec v1.2.0 · April 2026'")
    print("    3. New 'Composite Floor Rule — v1.2.0' section appears before Balanced Board")
    print("    4. Examples list shows JNJ, Costco, Apple cases")


if __name__ == "__main__":
    main()
