#!/usr/bin/env python3
"""
v1.2.0 Extension HD + AHI Mirror — human-edge/content.js

Brings the extension panel to full parity with the web detail page.
After this lands:
  · JNJ in extension = JNJ on web (HARM DOCUMENTATION block visible)
  · Meta in extension = Meta on web (ALGORITHMIC HARM INDEX with components)
  · HUMANWASHING filters HD: and AH: lines (no duplication)

Four surgical edits:
  1. Plumb algo_harm + harm_documentation through API → company mapping
  2. Plumb same fields through company → profile attachment
  3. Replace HW block to filter HD: and AH: lines (mirror web)
  4. Add HD block + AHI block (with components mini-bars), insert in template

All anchors are exact-string. Aborts if drifted.

Usage (from repo root):
  python3 human-edge/patch_panel_hd_ahi_v120.py
"""

import sys
import shutil
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TARGET = SCRIPT_DIR / "content.js"
if not TARGET.exists():
    TARGET = Path("human-edge/content.js").resolve()

# ════════════════════════════════════════════════════════════════════
# EDIT 1: API → company mapping. Add algo_harm + harm_documentation.
# ════════════════════════════════════════════════════════════════════

OLD_COMPANY_BLOCK = """        signal_coverage: d.signal_coverage || '',
        humanwashing_flags: d.humanwashing_flags || [],
      };"""

NEW_COMPANY_BLOCK = """        signal_coverage: d.signal_coverage || '',
        humanwashing_flags: d.humanwashing_flags || [],
        algo_harm: d.algo_harm || null,
        harm_documentation: d.harm_documentation || null,
      };"""

# ════════════════════════════════════════════════════════════════════
# EDIT 2: company → profile attachment. Add same fields.
# ════════════════════════════════════════════════════════════════════

OLD_PROFILE_BLOCK = """  profile.signal_coverage = company.signal_coverage || '';
  profile.humanwashing_flags = company.humanwashing_flags || [];"""

NEW_PROFILE_BLOCK = """  profile.signal_coverage = company.signal_coverage || '';
  profile.humanwashing_flags = company.humanwashing_flags || [];
  profile.algo_harm = company.algo_harm || null;
  profile.harm_documentation = company.harm_documentation || null;"""

# ════════════════════════════════════════════════════════════════════
# EDIT 3: HW block — filter HD: and AH: prefixed lines.
#   AND insert HD block + AHI block right after HW block.
# ════════════════════════════════════════════════════════════════════

OLD_HW_BLOCK = """  // Humanwashing section — mirrors web detail page (HUMANWASHING + HD lines).
  // Renders only when profile.humanwashing_flags has entries. Distinct red
  // treatment from the heartbeat section so users can tell them apart.
  let humanwashingHTML = '';
  const hwArr = profile.humanwashing_flags || [];
  if (hwArr.length > 0) {
    const hwColor = '#DC2626';
    humanwashingHTML = `
      <div style="background:${hwColor}10;border:1px solid ${hwColor}30;border-radius:8px;padding:10px 12px;margin-top:8px">
        <div style="font-weight:700;font-size:11px;color:${hwColor};letter-spacing:0.5px;text-transform:uppercase;margin-bottom:6px">⚑ Humanwashing · ${hwArr.length} flag${hwArr.length !== 1 ? 's' : ''}</div>
        <div style="font-size:10px;color:#666;margin-bottom:6px;font-style:italic">What they say vs. what they do.</div>
        ${hwArr.map(f => `<div style="font-size:11px;margin-top:3px;padding-left:14px;position:relative;color:#444"><span style="position:absolute;left:0;color:${hwColor}">›</span>${f}</div>`).join('')}
      </div>`;
  }"""

NEW_HW_BLOCK = """  // Humanwashing section — filter HD: and AH: lines (they belong in HD/AHI boxes
  // respectively). HUMANWASHING shows only true HW.* and other humanwashing flags.
  // Mirrors web detail page rendering.
  let humanwashingHTML = '';
  const hwArrAll = profile.humanwashing_flags || [];
  const hwArr = hwArrAll.filter(f => {
    return !(typeof f === 'string' && (f.indexOf('HD: ') === 0 || f.indexOf('AH: ') === 0));
  });
  if (hwArr.length > 0) {
    const hwColor = '#DC2626';
    humanwashingHTML = `
      <div style="background:${hwColor}10;border:1px solid ${hwColor}30;border-radius:8px;padding:10px 12px;margin-top:8px">
        <div style="font-weight:700;font-size:11px;color:${hwColor};letter-spacing:0.5px;text-transform:uppercase;margin-bottom:6px">⚑ Humanwashing · ${hwArr.length} flag${hwArr.length !== 1 ? 's' : ''}</div>
        <div style="font-size:10px;color:#666;margin-bottom:6px;font-style:italic">What they say vs. what they do.</div>
        ${hwArr.map(f => `<div style="font-size:11px;margin-top:3px;padding-left:14px;position:relative;color:#444"><span style="position:absolute;left:0;color:${hwColor}">›</span>${f}</div>`).join('')}
      </div>`;
  }

  // Algorithmic Harm Index block — mirrors web detail page AHI rendering.
  // Renders when algo_harm.has_harm. Includes components mini-bars (addiction,
  // division, manipulation = harming; transparency, human_override = mitigating).
  let algoHarmHTML = '';
  const ah = profile.algo_harm;
  if (ah && ah.has_harm) {
    const ahColor = '#DC2626';
    const compLabels = {
      addiction: 'Addiction',
      division: 'Division',
      manipulation: 'Manipulation',
      transparency: 'Transparency',
      human_override: 'Human Override'
    };
    const compOrder = ['addiction', 'division', 'manipulation', 'transparency', 'human_override'];
    const components = ah.components || {};
    let componentsHTML = '';
    if (Object.keys(components).length > 0) {
      const compRows = compOrder
        .filter(k => components[k] != null)
        .map(k => {
          const val = components[k];
          const isMitigating = (k === 'transparency' || k === 'human_override');
          const isBad = isMitigating ? (val < 50) : (val >= 50);
          const barColor = isBad ? '#DC2626' : '#16A34A';
          return `
            <div style="display:flex;align-items:center;gap:6px;font-size:10px;margin-bottom:3px">
              <span style="flex:0 0 78px;color:#374151">${compLabels[k] || k}</span>
              <div style="flex:1;height:5px;background:#F3F4F6;border-radius:3px;overflow:hidden">
                <div style="height:100%;width:${val}%;background:${barColor};border-radius:3px"></div>
              </div>
              <span style="flex:0 0 22px;text-align:right;font-weight:700;color:${barColor}">${val}</span>
            </div>`;
        }).join('');
      componentsHTML = `
        <div style="margin-top:8px;padding-top:8px;border-top:1px dashed ${ahColor}40">
          <div style="font-size:9px;color:#7F1D1D;text-transform:uppercase;letter-spacing:0.5px;font-weight:700;margin-bottom:5px;opacity:0.8">Components</div>
          ${compRows}
        </div>`;
    }
    algoHarmHTML = `
      <div style="background:${ahColor}10;border:1px solid ${ahColor}30;border-radius:8px;padding:10px 12px;margin-top:8px">
        <div style="font-weight:700;font-size:11px;color:${ahColor};letter-spacing:0.5px;text-transform:uppercase;margin-bottom:6px">⚡ Algorithmic Harm Index · ${ah.algo_harm_score}/100</div>
        <div style="font-size:10px;color:#666;margin-bottom:6px;font-style:italic">Algorithms that divide, addict, or manipulate users.</div>
        ${(ah.flags || []).map(f => `<div style="font-size:11px;margin-top:3px;padding-left:14px;position:relative;color:#444"><span style="position:absolute;left:0;color:${ahColor}">›</span>${f}</div>`).join('')}
        ${componentsHTML}
      </div>`;
  }

  // Harm Documentation block — mirrors web detail page HD rendering.
  // Renders when harm_documentation.has_harm. Shows public-record harm:
  // settlements, attributed deaths, concealment findings, source links, M penalty.
  let harmDocHTML = '';
  const hd = profile.harm_documentation;
  if (hd && hd.has_harm) {
    const hdColor = '#DC2626';
    const hdPenalty = (hd.penalties && hd.penalties.M) ? hd.penalties.M : null;
    const sourcesHTML = (hd.sources && hd.sources.length > 0)
      ? `<div style="margin-top:8px;font-size:10px;color:#7F1D1D;opacity:0.75;line-height:1.5"><strong style="font-weight:700">Sources:</strong> ${hd.sources.map(s => {
          const label = s.replace(/^https?:\\/\\//, '').split('/')[0];
          return `<a href="${s}" target="_blank" rel="noopener" style="color:#7F1D1D;text-decoration:underline">${label}</a>`;
        }).join(' · ')}</div>`
      : '';
    harmDocHTML = `
      <div style="background:${hdColor}10;border:1px solid ${hdColor}30;border-radius:8px;padding:10px 12px;margin-top:8px">
        <div style="font-weight:700;font-size:11px;color:${hdColor};letter-spacing:0.5px;text-transform:uppercase;margin-bottom:6px">⚠ Harm Documentation${hdPenalty != null ? ` · M ${hdPenalty}` : ''}</div>
        <div style="font-size:10px;color:#666;margin-bottom:6px;font-style:italic">Public-record harm: settlements, attributed deaths, concealment findings.</div>
        ${(hd.flags || []).map(f => `<div style="font-size:11px;margin-top:3px;padding-left:14px;position:relative;color:#444"><span style="position:absolute;left:0;color:${hdColor}">›</span>${f}</div>`).join('')}
        ${sourcesHTML}
      </div>`;
  }"""

# ════════════════════════════════════════════════════════════════════
# EDIT 4: Insert algoHarmHTML + harmDocHTML into the panel template,
#         right after humanwashingHTML, matching web order:
#         heartbeat → HW → AHI → HD
# ════════════════════════════════════════════════════════════════════

OLD_TEMPLATE_INSERTS = """    ${humanwashingHTML ? `<div style="background:white;padding:4px 16px">${humanwashingHTML}</div>` : ''}

    ${pulseHTML ? `<div style="background:white;padding:4px 16px">${pulseHTML}</div>` : ''}"""

NEW_TEMPLATE_INSERTS = """    ${humanwashingHTML ? `<div style="background:white;padding:4px 16px">${humanwashingHTML}</div>` : ''}
    ${algoHarmHTML ? `<div style="background:white;padding:4px 16px">${algoHarmHTML}</div>` : ''}
    ${harmDocHTML ? `<div style="background:white;padding:4px 16px">${harmDocHTML}</div>` : ''}

    ${pulseHTML ? `<div style="background:white;padding:4px 16px">${pulseHTML}</div>` : ''}"""


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()

    missing = []
    if OLD_COMPANY_BLOCK not in src:
        missing.append("API→company mapping (signal_coverage block)")
    if OLD_PROFILE_BLOCK not in src:
        missing.append("company→profile attachment (signal_coverage line)")
    if OLD_HW_BLOCK not in src:
        missing.append("HUMANWASHING block (humanwashingHTML builder)")
    if OLD_TEMPLATE_INSERTS not in src:
        missing.append("template insertion block (humanwashingHTML + pulseHTML)")
    if missing:
        sys.exit(
            "ABORT — anchors not found verbatim:\n  - "
            + "\n  - ".join(missing)
            + "\nFile may already be patched or has drifted."
        )

    if NEW_COMPANY_BLOCK in src:
        sys.exit("ABORT — file already contains v1.2.0 HD/AHI mirror. No-op.")

    new_src = src
    new_src = new_src.replace(OLD_COMPANY_BLOCK, NEW_COMPANY_BLOCK, 1)
    new_src = new_src.replace(OLD_PROFILE_BLOCK, NEW_PROFILE_BLOCK, 1)
    new_src = new_src.replace(OLD_HW_BLOCK, NEW_HW_BLOCK, 1)
    new_src = new_src.replace(OLD_TEMPLATE_INSERTS, NEW_TEMPLATE_INSERTS, 1)

    if new_src == src:
        sys.exit("ABORT — replacements had no effect.")

    # Atomic write — .v120tmp.js so node --check accepts the extension
    tmp = TARGET.parent / (TARGET.stem + ".v120tmp.js")
    backup = TARGET.with_suffix(TARGET.suffix + ".bak")
    tmp.write_text(new_src)

    # Node syntax validation
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
    print("  Four surgical edits to extension panel:")
    print("    1. API → company: + algo_harm, + harm_documentation")
    print("    2. company → profile: + algo_harm, + harm_documentation")
    print("    3. HW block: filter out 'HD: ' and 'AH: ' lines")
    print("    4. Template: + AHI block (with components bars), + HD block (with sources)")
    print("")
    print("  Verify:")
    print("    1. chrome://extensions → reload HI Grade")
    print("    2. jnj.com → click badge → panel:")
    print("       · NO Humanwashing box (only had HD lines, filtered)")
    print("       · ⚠ HARM DOCUMENTATION · M -70 with sources")
    print("    3. meta.com or facebook.com → click badge → panel:")
    print("       · ⚑ HUMANWASHING · 2 flags (HW.1, HW.3 only — AH lines filtered)")
    print("       · ⚡ AHI · 81.5/100 with 4 flags + 5 component bars")
    print("    4. apple.com → no AHI/HD (correct)")


if __name__ == "__main__":
    main()
