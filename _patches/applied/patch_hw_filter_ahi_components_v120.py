#!/usr/bin/env python3
"""
v1.2.0 HW Filter + AHI Components — docs/index.html

Two changes to the company detail page rendering:

1. HUMANWASHING box no longer duplicates HD or AH lines. Filters out any
   flag starting with 'HD: ' or 'AH: '. Hides the box entirely if no
   true HW lines remain.
   - JNJ (only HD lines): HUMANWASHING box hidden
   - Meta (HW.1, HW.3, AH lines): HUMANWASHING shows only HW.1 + HW.3
   - Companies with all three evidence types: each in its own box

2. ALGORITHMIC HARM INDEX block now renders components as mini horizontal
   bars beneath the flag list. Components like {addiction: 90, division: 85,
   manipulation: 80, transparency: 25, human_override: 30} surface the
   AHI breakdown so users see WHY the AHI score is what it is.

Both anchor on exact-string blocks; aborts if drifted.

Usage (from repo root):
  python3 docs/patch_hw_filter_ahi_components_v120.py
"""

import sys
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TARGET = SCRIPT_DIR / "index.html"
if not TARGET.exists():
    TARGET = Path("docs/index.html").resolve()

# ════════════════════════════════════════════════════════════════════
# EDIT 1: HUMANWASHING block — filter HD/AH lines, hide if empty
# ════════════════════════════════════════════════════════════════════

OLD_HW_BLOCK = """    if (hasHW) {
      h += '<div style="' + (hbActive ? 'margin-top:18px;padding-top:18px;border-top:1px solid ' + hb.color + '30' : '') + '">';
      h += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">';
      h += '<span style="color:#DC2626;font-size:13px">\\u2691</span>';
      h += '<span style="color:#DC2626;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:2px">Humanwashing</span>';
      h += '<span style="color:#7F1D1D;font-size:11px;opacity:0.6">' + c.humanwashing_flags.length + ' flags</span>';
      h += '</div>';
      h += '<div style="font-size:13px;color:#374151;margin-bottom:10px;line-height:1.5">What they say vs. what they do.</div>';
      h += '<div style="display:flex;flex-direction:column;gap:6px">';
      c.humanwashing_flags.forEach(function(f) {
        h += '<div style="display:flex;gap:10px;font-size:13px;line-height:1.5;color:#374151"><span style="color:#DC2626;font-weight:700;flex-shrink:0">\\u00b7</span><span>' + f + '</span></div>';
      });
      h += '</div>';
      h += '</div>';
    }"""

NEW_HW_BLOCK = """    if (hasHW) {
      // v1.2.0: filter HD: and AH: lines out — they belong in HARM DOCUMENTATION
      // and ALGORITHMIC HARM INDEX boxes respectively. HUMANWASHING shows only
      // true humanwashing flags (HW.* and others) to avoid duplication.
      var hwOnly = c.humanwashing_flags.filter(function(f) {
        return !(typeof f === 'string' && (f.indexOf('HD: ') === 0 || f.indexOf('AH: ') === 0));
      });
      if (hwOnly.length > 0) {
        h += '<div style="' + (hbActive ? 'margin-top:18px;padding-top:18px;border-top:1px solid ' + hb.color + '30' : '') + '">';
        h += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">';
        h += '<span style="color:#DC2626;font-size:13px">\\u2691</span>';
        h += '<span style="color:#DC2626;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:2px">Humanwashing</span>';
        h += '<span style="color:#7F1D1D;font-size:11px;opacity:0.6">' + hwOnly.length + ' flag' + (hwOnly.length !== 1 ? 's' : '') + '</span>';
        h += '</div>';
        h += '<div style="font-size:13px;color:#374151;margin-bottom:10px;line-height:1.5">What they say vs. what they do.</div>';
        h += '<div style="display:flex;flex-direction:column;gap:6px">';
        hwOnly.forEach(function(f) {
          h += '<div style="display:flex;gap:10px;font-size:13px;line-height:1.5;color:#374151"><span style="color:#DC2626;font-weight:700;flex-shrink:0">\\u00b7</span><span>' + f + '</span></div>';
        });
        h += '</div>';
        h += '</div>';
      }
    }"""

# ════════════════════════════════════════════════════════════════════
# EDIT 2: AHI block — append components mini-bars after flag list
# ════════════════════════════════════════════════════════════════════

OLD_AHI_BLOCK = """      h += '<div style="font-size:13px;color:#374151;margin-bottom:10px;line-height:1.5">Algorithms that divide, addict, or manipulate users.</div>';
      h += '<div style="display:flex;flex-direction:column;gap:6px">';
      (ah.flags || []).forEach(function(f) {
        h += '<div style="display:flex;gap:10px;font-size:13px;line-height:1.5;color:#374151"><span style="color:#DC2626;font-weight:700;flex-shrink:0">\\u203A</span><span>' + f + '</span></div>';
      });
      h += '</div>';
      h += '</div>';
    }"""

NEW_AHI_BLOCK = """      h += '<div style="font-size:13px;color:#374151;margin-bottom:10px;line-height:1.5">Algorithms that divide, addict, or manipulate users.</div>';
      h += '<div style="display:flex;flex-direction:column;gap:6px">';
      (ah.flags || []).forEach(function(f) {
        h += '<div style="display:flex;gap:10px;font-size:13px;line-height:1.5;color:#374151"><span style="color:#DC2626;font-weight:700;flex-shrink:0">\\u203A</span><span>' + f + '</span></div>';
      });
      h += '</div>';
      // v1.2.0: AHI components mini-bars — surfaces WHY the AHI score is what it is.
      // High addiction/division/manipulation = bad. High transparency/human_override = mitigating.
      // Component values 0-100; bar fill width matches value.
      if (ah.components && Object.keys(ah.components).length > 0) {
        var compLabels = {
          addiction: 'Addiction',
          division: 'Division',
          manipulation: 'Manipulation',
          transparency: 'Transparency',
          human_override: 'Human Override'
        };
        // Order: harms first (high=bad), mitigations last (high=good)
        var compOrder = ['addiction', 'division', 'manipulation', 'transparency', 'human_override'];
        h += '<div style="margin-top:12px;padding-top:10px;border-top:1px dashed #DC262640">';
        h += '<div style="font-size:10px;color:#7F1D1D;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-bottom:8px;opacity:0.8">Components</div>';
        compOrder.forEach(function(key) {
          if (ah.components[key] == null) return;
          var val = ah.components[key];
          var label = compLabels[key] || key;
          // Mitigating (transparency, human_override): green when high, red when low
          // Harming (addiction, division, manipulation): red when high, green when low
          var isMitigating = (key === 'transparency' || key === 'human_override');
          var isBad = isMitigating ? (val < 50) : (val >= 50);
          var barColor = isBad ? '#DC2626' : '#16A34A';
          h += '<div style="display:flex;align-items:center;gap:10px;font-size:11px;margin-bottom:4px">';
          h += '<span style="flex:0 0 110px;color:#374151">' + label + '</span>';
          h += '<div style="flex:1;height:6px;background:#F3F4F6;border-radius:3px;overflow:hidden">';
          h += '<div style="height:100%;width:' + val + '%;background:' + barColor + ';border-radius:3px"></div>';
          h += '</div>';
          h += '<span style="flex:0 0 30px;text-align:right;font-weight:700;color:' + barColor + '">' + val + '</span>';
          h += '</div>';
        });
        h += '</div>';
      }
      h += '</div>';
    }"""


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()

    missing = []
    if OLD_HW_BLOCK not in src:
        missing.append("HUMANWASHING block (around line 1285)")
    if OLD_AHI_BLOCK not in src:
        missing.append("AHI block flag rendering (around line 1309)")
    if missing:
        sys.exit(
            "ABORT — anchors not found verbatim:\n  - "
            + "\n  - ".join(missing)
            + "\nFile may already be patched or has drifted."
        )

    if NEW_HW_BLOCK in src:
        sys.exit("ABORT — file already contains v1.2.0 HW filter. No-op.")

    new_src = src
    new_src = new_src.replace(OLD_HW_BLOCK, NEW_HW_BLOCK, 1)
    new_src = new_src.replace(OLD_AHI_BLOCK, NEW_AHI_BLOCK, 1)

    if new_src == src:
        sys.exit("ABORT — replacements had no effect.")

    # Atomic write
    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    backup = TARGET.with_suffix(TARGET.suffix + ".bak")
    tmp.write_text(new_src)

    # Sanity: line delta should be ~40 (filter adds ~5, components adds ~30)
    old_lines = src.count("\n")
    new_lines = new_src.count("\n")
    delta = new_lines - old_lines
    if delta < 30 or delta > 55:
        tmp.unlink()
        sys.exit(f"ABORT — unexpected line delta: {delta} (expected ~40).")

    shutil.copy2(TARGET, backup)
    tmp.replace(TARGET)

    print("✓ Patched: " + str(TARGET))
    print("  Backup:  " + str(backup))
    print(f"  Lines added: {delta}")
    print("")
    print("  Two changes:")
    print("    1. HUMANWASHING filters out HD: and AH: prefixed lines (no duplication)")
    print("    2. AHI block now shows component mini-bars (addiction/division/etc.)")
    print("")
    print("  Verify in browser:")
    print("    1. JNJ detail page → HUMANWASHING box should be HIDDEN")
    print("       (only HD: lines were there, now in HARM DOCUMENTATION block)")
    print("    2. Meta detail → HUMANWASHING shows only HW.1 + HW.3 (2 flags)")
    print("       AHI block shows flags + 5 component bars (addiction 90, division 85, ...)")
    print("    3. Clean company → no HW, no AHI, no HD — same as before")


if __name__ == "__main__":
    main()
