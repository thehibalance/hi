#!/usr/bin/env python3
"""
v1.2.0 Harm Documentation Rendering — docs/index.html

Adds a HARM DOCUMENTATION (HD) rendering block to the company detail page,
mirroring the existing Algorithmic Harm Index (AHI) block exactly. Both
blocks live inside the "Section 2: The Story" navy-bordered card, alongside
Heartbeat and Humanwashing.

Why:
  The API returns harm_documentation with concealment_findings,
  deaths_attributed, settlement_5yr, sources, etc. for companies like
  Johnson & Johnson — but the web detail page has no rendering code for
  it. Meta (which has algo_harm) renders correctly via the AHI block;
  JNJ (which has harm_documentation instead) renders nothing.

  This patch adds the missing HD block so JNJ-class companies show their
  full accountability story: settlements, deaths attributed, concealment
  findings, source links — visually parallel to AHI on Meta.

Insertion location:
  Between the AHI block (currently lines ~1301-1316) and the closing
  "if (hbActive)" pre-event-data note (~line 1317). HD renders only
  when c.harm_documentation && c.harm_documentation.has_harm.

Visual treatment:
  Same red color family as HW/AHI for consistency, but uses ⚠ icon
  (vs ⚑ for HW, ⚡ for AHI) so users can distinguish at a glance.
  Each flag in c.harm_documentation.flags renders as a bullet line.
  Source URLs render as small linked text below.

Validation:
  - Exact-string anchor (the AHI block) — aborts loud if drifted
  - Atomic write: tmp → backup → rename
  - No regex magic; pure string replace

Usage (from repo root):
  python3 docs/patch_hd_rendering_v120.py
"""

import sys
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TARGET = SCRIPT_DIR / "index.html"
if not TARGET.exists():
    TARGET = Path("docs/index.html").resolve()

# ── Anchor: full AHI rendering block (lines ~1301-1316). Patcher inserts ──
# ── HD block IMMEDIATELY AFTER this AHI close brace.                    ──

OLD_BLOCK = """    if (hasAHI) {
      var ah = c.algo_harm;
      h += '<div style="' + (hbActive ? 'margin-top:18px;padding-top:18px;border-top:1px solid ' + hb.color + '30' : '') + '">';
      h += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">';
      h += '<span style="color:#DC2626;font-size:13px">\\u26A1</span>';
      h += '<span style="color:#DC2626;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:2px">Algorithmic Harm Index</span>';
      h += '<span style="color:#7F1D1D;font-size:11px;opacity:0.6">' + ah.algo_harm_score + '/100</span>';
      h += '</div>';
      h += '<div style="font-size:13px;color:#374151;margin-bottom:10px;line-height:1.5">Algorithms that divide, addict, or manipulate users.</div>';
      h += '<div style="display:flex;flex-direction:column;gap:6px">';
      (ah.flags || []).forEach(function(f) {
        h += '<div style="display:flex;gap:10px;font-size:13px;line-height:1.5;color:#374151"><span style="color:#DC2626;font-weight:700;flex-shrink:0">\\u203A</span><span>' + f + '</span></div>';
      });
      h += '</div>';
      h += '</div>';
    }
    if (hbActive) {"""

NEW_BLOCK = """    if (hasAHI) {
      var ah = c.algo_harm;
      h += '<div style="' + (hbActive ? 'margin-top:18px;padding-top:18px;border-top:1px solid ' + hb.color + '30' : '') + '">';
      h += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">';
      h += '<span style="color:#DC2626;font-size:13px">\\u26A1</span>';
      h += '<span style="color:#DC2626;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:2px">Algorithmic Harm Index</span>';
      h += '<span style="color:#7F1D1D;font-size:11px;opacity:0.6">' + ah.algo_harm_score + '/100</span>';
      h += '</div>';
      h += '<div style="font-size:13px;color:#374151;margin-bottom:10px;line-height:1.5">Algorithms that divide, addict, or manipulate users.</div>';
      h += '<div style="display:flex;flex-direction:column;gap:6px">';
      (ah.flags || []).forEach(function(f) {
        h += '<div style="display:flex;gap:10px;font-size:13px;line-height:1.5;color:#374151"><span style="color:#DC2626;font-weight:700;flex-shrink:0">\\u203A</span><span>' + f + '</span></div>';
      });
      h += '</div>';
      h += '</div>';
    }

    // v1.2.0: HARM DOCUMENTATION block — mirrors AHI structure for JNJ-class
    // public-record harm (settlements, attributed deaths, concealment findings).
    // Anchored to DOJ/SEC/CDC sources. Renders when harm_documentation.has_harm.
    if (c.harm_documentation && c.harm_documentation.has_harm) {
      var hd = c.harm_documentation;
      h += '<div style="' + (hbActive ? 'margin-top:18px;padding-top:18px;border-top:1px solid ' + hb.color + '30' : '') + '">';
      h += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">';
      h += '<span style="color:#DC2626;font-size:13px">\\u26A0</span>';
      h += '<span style="color:#DC2626;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:2px">Harm Documentation</span>';
      var hdPenalty = (hd.penalties && hd.penalties.M) ? hd.penalties.M : null;
      if (hdPenalty != null) h += '<span style="color:#7F1D1D;font-size:11px;opacity:0.6">M ' + hdPenalty + '</span>';
      h += '</div>';
      h += '<div style="font-size:13px;color:#374151;margin-bottom:10px;line-height:1.5">Public-record harm: settlements, attributed deaths, concealment findings.</div>';
      h += '<div style="display:flex;flex-direction:column;gap:6px">';
      (hd.flags || []).forEach(function(f) {
        h += '<div style="display:flex;gap:10px;font-size:13px;line-height:1.5;color:#374151"><span style="color:#DC2626;font-weight:700;flex-shrink:0">\\u203A</span><span>' + f + '</span></div>';
      });
      h += '</div>';
      // Source links — small, muted, below flag list
      if (hd.sources && hd.sources.length > 0) {
        h += '<div style="margin-top:10px;font-size:11px;color:#7F1D1D;opacity:0.75;line-height:1.6">';
        h += '<strong style="font-weight:700">Sources:</strong> ';
        h += hd.sources.map(function(s) {
          var label = s.replace(/^https?:\\/\\//, '').split('/')[0];
          return '<a href="' + s + '" target="_blank" rel="noopener" style="color:#7F1D1D;text-decoration:underline">' + label + '</a>';
        }).join(' \\u00b7 ');
        h += '</div>';
      }
      h += '</div>';
    }
    if (hbActive) {"""


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()

    if OLD_BLOCK not in src:
        sys.exit(
            "ABORT — anchor block (AHI rendering) not found verbatim.\n"
            "File may already be patched or has drifted. Check around line 1301."
        )
    if NEW_BLOCK in src:
        sys.exit("ABORT — file already contains v1.2.0 HD rendering. No-op.")

    new_src = src.replace(OLD_BLOCK, NEW_BLOCK, 1)
    if new_src == src:
        sys.exit("ABORT — replacement had no effect.")

    # Atomic write
    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    backup = TARGET.with_suffix(TARGET.suffix + ".bak")
    tmp.write_text(new_src)

    # Sanity: line count delta should be modest (~30 new lines, no removals)
    old_lines = src.count("\n")
    new_lines = new_src.count("\n")
    delta = new_lines - old_lines
    if delta < 25 or delta > 40:
        tmp.unlink()
        sys.exit(
            f"ABORT — unexpected line delta: {delta} (expected ~30). "
            "Patch may have applied wrongly."
        )

    shutil.copy2(TARGET, backup)
    tmp.replace(TARGET)

    print("✓ Patched: " + str(TARGET))
    print("  Backup:  " + str(backup))
    print(f"  Lines added: {delta}")
    print("")
    print("  New block: HARM DOCUMENTATION rendering for JNJ-class companies")
    print("    - Mirrors AHI block structure (red + ⚠ icon)")
    print("    - Renders when harm_documentation.has_harm is true")
    print("    - Shows flags + M penalty + source links")
    print("")
    print("  Verify:")
    print("    1. Open docs/index.html in browser (or push to live)")
    print("    2. Search 'JNJ' or 'Johnson & Johnson' → detail page")
    print("    3. Should see HD block in the pink story card with:")
    print("       · ⚠ HARM DOCUMENTATION · M -70")
    print("       · 'Harm settlements: $12.5B (5y)'")
    print("       · 'Documented deaths attributed: 50,000'")
    print("       · 'Concealment findings: 3'")
    print("       · Source links (justice.gov, reuters.com, cdc.gov)")
    print("    4. Open Meta detail → AHI block still renders (unchanged)")
    print("    5. Open clean company → no HD block (correct)")


if __name__ == "__main__":
    main()
