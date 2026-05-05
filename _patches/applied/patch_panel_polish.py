#!/usr/bin/env python3
"""
HI. Extension panel polish — one-sweep update for v1.1.0 launch.

Polishes the in-page detail panel based on screenshot feedback:
  1. Header: separate heartbeat line from "HI Grade™" tier (no more "♥36" reading as score)
  2. Gates: show SPECIFIC failure reasons inline (e.g., "3 dims below 60: H, U, A")
  3. Gate count: clarify "0/3 Gates passed · Not eligible for Gold"
  4. Layout: max-height + scroll so footer never cuts off
  5. Heartbeat box: tighten label since gate row now shows decay
  6. Composite shown explicitly ("HI Grade™ · 58") so users can read it
"""
import sys, os, shutil

CHANGES = []

def patch_file(path, replacements):
    if not os.path.exists(path):
        print(f"⚠ Not found: {path}")
        return False
    src = open(path).read()
    original = src
    for label, old, new in replacements:
        if old in src:
            src = src.replace(old, new)
            CHANGES.append(f"  ✓ {os.path.basename(path)}: {label}")
        elif new in src:
            CHANGES.append(f"  ⊙ {os.path.basename(path)}: {label} (already applied)")
        else:
            CHANGES.append(f"  ✗ {os.path.basename(path)}: {label} (pattern not found)")
    if src != original:
        if not os.path.exists(path + '.polish.bak'):
            shutil.copy(path, path + '.polish.bak')
        open(path, 'w').write(src)
        return True
    return False


CONTENT_JS_PATCHES = [

    # ─── 1. PANEL LAYOUT: add max-height + scroll so footer never cuts off ───
    ("Add max-height + scroll to panel",
     """  const panel = document.createElement('div');
  panel.id = 'human-detail-panel';
  panel.className = 'human-panel';

  const scoreColor = profile.isPending ? "#999" : profile.hiBalanced ? "#C49B20" : HumanEngine.getScoreColor(profile.composite, profile.balancedThreshold);""",
     """  const panel = document.createElement('div');
  panel.id = 'human-detail-panel';
  panel.className = 'human-panel';
  // Ensure panel scrolls if content overflows viewport (prevents footer cutoff)
  panel.style.maxHeight = 'calc(100vh - 40px)';
  panel.style.overflowY = 'auto';

  const scoreColor = profile.isPending ? "#999" : profile.hiBalanced ? "#C49B20" : HumanEngine.getScoreColor(profile.composite, profile.balancedThreshold);"""),

    # ─── 2. HEADER: separate heartbeat from grade line, show composite explicitly ───
    ("Separate heartbeat from grade tier line",
     """      <div>
        <div class="human-panel__name">${profile.name}</div>
        <div class="human-panel__tier" style="color: ${scoreColor}">${profile.isPending ? "Pending Verification" : profile.hiBalanced ? "Gold HI Grade™" : "HI Grade™"}${pulseDotHTML}</div>
      </div>
    </div>
    ${profile.hiBalanced ? '<div style="padding:4px 16px;font-size:20px;font-weight:900;color:#C49B20;background:white">'+profile.composite+'</div><div style="padding:2px 16px;font-size:11px;color:#C49B20;font-weight:600;background:white">All 3 gates passed</div>' : ''}""",
     """      <div style="flex:1;min-width:0">
        <div class="human-panel__name">${profile.name}</div>
        <div class="human-panel__tier" style="color: ${scoreColor};font-weight:600">${profile.isPending ? "Pending Verification" : profile.hiBalanced ? "Gold HI Grade™" : "HI Grade™"} · ${profile.composite}/100</div>
        ${(profile.decay_level && profile.decay_level !== 'stable' && profile.decay_index > 0) ? `<div style="font-size:11px;color:${pulseColor};margin-top:3px;font-weight:600">\u2665 ${profile.decay_level.charAt(0).toUpperCase()+profile.decay_level.slice(1)} decay \u00b7 ${profile.decay_index}/100</div>` : (profile.decay_level === 'stable' ? '<div style="font-size:11px;color:#16A34A;margin-top:3px;font-weight:600">\u2665 Stable</div>' : '')}
      </div>
    </div>
    ${profile.hiBalanced ? '<div style="padding:6px 16px;font-size:12px;color:#C49B20;font-weight:700;background:white;letter-spacing:0.5px">\u2728 ALL 3 GATES PASSED \u00b7 GOLD HI GRADE</div>' : ''}"""),

    # ─── 3. GATES: show specific failure reasons inline ───
    ("Show specific failure reasons in each gate",
     """    ${(() => {
      const gates = profile.goldGates || {};
      const g1 = !!gates.dimensions;
      const g2 = !!gates.evidence;
      const g3 = !!gates.momentum;
      const passed = [g1, g2, g3].filter(Boolean).length;
      const total = 3;
      const gc = (icon, name, desc, ok) => '<div style="padding:4px 0;color:' + (ok ? '#16A34A' : '#DC2626') + '"><div style="font-size:11px;font-weight:600">' + (ok ? '✓' : '✗') + ' ' + icon + ' ' + name + '</div><div style="font-size:9px;color:#888;margin-left:14px;font-weight:400">' + desc + '</div></div>';
      return '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px"><span style="font-size:11px;font-weight:700;color:#1B3A5C">' + passed + '/' + total + ' GATES</span><div style="flex:1;height:4px;background:#EEF1F5;border-radius:2px"><div style="height:100%;width:' + (passed/total*100) + '%;background:' + (passed === total ? '#C49B20' : '#1B3A5C') + ';border-radius:2px"></div></div></div>' +
        gc('📊', 'DIMENSIONS', 'All 5 HUMAN dimensions ≥ 60', g1) +
        gc('🔬', 'EVIDENCE', 'Each dimension verified by public data', g2) +
        gc('⏱', 'MOMENTUM', 'No critical decay (90-day Heartbeat)', g3);
    })()}""",
     """    ${(() => {
      const gates = profile.goldGates || {};
      const g1 = !!gates.dimensions;
      const g2 = !!gates.evidence;
      const g3 = !!gates.momentum;
      const passed = [g1, g2, g3].filter(Boolean).length;
      const total = 3;

      // Compute SPECIFIC failure reasons
      const dimMap = ['h','u','m','a','n'];
      const failedDims = dimMap.filter(d => (profile.dimensions[d] || 0) < 60).map(d => d.toUpperCase());
      const dimDesc = g1 ? 'All 5 HUMAN dimensions \u2265 60' :
        (failedDims.length === 1 ? failedDims[0] + ' below 60 (Gold needs all 5)' :
         failedDims.length + ' dims below 60: ' + failedDims.join(', '));

      const evDesc = g2 ? 'Each dimension verified by public data' : 'Coverage gap \u2014 some dims need more verified sources';

      const decayLevel = profile.decay_level || 'stable';
      const decayLabel = {warning:'Warning', critical:'Critical', watch:'Watch', stable:'Stable'}[decayLevel] || decayLevel;
      const momDesc = g3 ? 'No warning or critical decay (90-day Heartbeat)' :
        decayLabel + ' decay' + (profile.decay_index ? ' (' + profile.decay_index + '/100)' : '');

      const headerLabel = passed + '/' + total + ' Gates passed' +
        (passed === total ? ' \u00b7 GOLD' : passed === 0 ? ' \u00b7 Not eligible for Gold' : ' \u00b7 Partial');
      const gc = (icon, name, desc, ok) => '<div style="padding:5px 0;color:' + (ok ? '#16A34A' : '#DC2626') + '"><div style="font-size:11px;font-weight:700">' + (ok ? '\u2713' : '\u2717') + ' ' + icon + ' ' + name + '</div><div style="font-size:10px;color:' + (ok ? '#15803D' : '#DC2626') + ';margin-left:16px;font-weight:500;margin-top:1px">' + desc + '</div></div>';
      return '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px"><span style="font-size:11px;font-weight:700;color:#1B3A5C">' + headerLabel + '</span><div style="flex:1;height:4px;background:#EEF1F5;border-radius:2px"><div style="height:100%;width:' + (passed/total*100) + '%;background:' + (passed === total ? '#C49B20' : '#1B3A5C') + ';border-radius:2px"></div></div></div>' +
        gc('\ud83d\udcca', 'DIMENSIONS', dimDesc, g1) +
        gc('\ud83d\udd2c', 'EVIDENCE', evDesc, g2) +
        gc('\u23f1', 'MOMENTUM', momDesc, g3);
    })()}"""),

    # ─── 4. HEARTBEAT BOX: tighten since gate row now shows decay status ───
    ("Tighten heartbeat decay box (gates row already shows status)",
     """    decayHTML = `
      <div style="background:${dc}10;border:1px solid ${dc}30;border-radius:8px;padding:10px 12px;margin-top:8px">
        <div style="font-weight:700;font-size:12px;color:${dc}">♥ ${profile.decay_level.charAt(0).toUpperCase() + profile.decay_level.slice(1)} · Decay: ${profile.decay_index}/100</div>
        ${profile.decay_factors.map(f => `<div style="font-size:10px;margin-top:4px;padding-left:14px;position:relative;color:#444"><span style="position:absolute;left:0">›</span>${f}</div>`).join('')}
      </div>`;""",
     """    decayHTML = `
      <div style="background:${dc}10;border:1px solid ${dc}30;border-radius:8px;padding:10px 12px;margin-top:8px">
        <div style="font-weight:700;font-size:11px;color:${dc};letter-spacing:0.5px;text-transform:uppercase;margin-bottom:6px">\u2665 What the Heartbeat caught</div>
        ${profile.decay_factors.map(f => `<div style="font-size:11px;margin-top:3px;padding-left:14px;position:relative;color:#444"><span style="position:absolute;left:0;color:${dc}">\u203a</span>${f}</div>`).join('')}
      </div>`;"""),

    # ─── 5. ECOSYSTEM PULSE: smaller, less prominent ───
    ("Make ecosystem pulse less prominent",
     """    pulseHTML = `<div style="font-size:11px;color:${pColor};margin-top:8px;text-align:center">♥ Ecosystem: <strong>${pulse.pulse.toUpperCase()}</strong> · ${pulse.alerts_count || 0} alerts</div>`;""",
     """    pulseHTML = `<div style="font-size:10px;color:${pColor};margin-top:6px;text-align:center;opacity:0.8">Market pulse: <strong>${pulse.pulse}</strong> \u00b7 ${pulse.alerts_count || 0} active alerts</div>`;"""),

    # ─── 6. TIMER ROW: tighten and integrate into dark footer ───
    ("Move timer into dark footer (save vertical space)",
     """    <div style="padding:8px 16px;text-align:center">
      <div style="display:flex;align-items:center;justify-content:center;gap:4px;margin-bottom:8px">
        <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#16A34A"></span>
        <span id="hiPipelineCountdown" style="font-size:10px;font-family:monospace;color:#888">Connected · API live</span>
      </div>
    </div>

    <div style="background:#1B3A5C;padding:12px 16px;border-radius:0 0 14px 14px">
      <div style="display:flex;justify-content:center;gap:12px;margin-bottom:8px">
        <a href="https://thehibalance.org" target="_blank" style="font-size:10px;font-weight:600;color:#C49B20;text-decoration:none">🌐 thehibalance.org</a>
        <a href="https://apps.apple.com/app/hi/id6761270596" target="_blank" style="font-size:10px;font-weight:600;color:#C49B20;text-decoration:none">🍎 iOS App</a>
      </div>
      <div style="font-size:8px;color:#5A7A9A;line-height:1.4;text-align:center">Spec v1.1.0 · 3 gates: Dimensions, Evidence, Momentum · All dims ≥ 60. Estimated from public data. Not financial or legal advice.</div>
    </div>""",
     """    <div style="background:#1B3A5C;padding:14px 16px;border-radius:0 0 14px 14px;margin-top:8px">
      <div style="display:flex;justify-content:center;align-items:center;gap:14px;margin-bottom:10px;flex-wrap:wrap">
        <a href="https://thehibalance.org" target="_blank" style="font-size:11px;font-weight:600;color:#C49B20;text-decoration:none">\ud83c\udf10 thehibalance.org</a>
        <a href="https://apps.apple.com/app/hi/id6761270596" target="_blank" style="font-size:11px;font-weight:600;color:#C49B20;text-decoration:none">\ud83c\udf4e iOS App</a>
      </div>
      <div style="display:flex;align-items:center;justify-content:center;gap:5px;margin-bottom:8px">
        <span style="display:inline-block;width:5px;height:5px;border-radius:50%;background:#16A34A"></span>
        <span id="hiPipelineCountdown" style="font-size:9px;font-family:'DM Mono',monospace;color:#5A7A9A;letter-spacing:0.3px">Connected \u00b7 API live</span>
      </div>
      <div style="font-size:8px;color:#5A7A9A;line-height:1.4;text-align:center">Spec v1.1.0 \u00b7 3 gates: Dimensions, Evidence, Momentum \u00b7 All dims \u2265 60. Estimated from public data. Not financial or legal advice.</div>
    </div>"""),
]


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--dir', default='.')
    args = p.parse_args()
    root = os.path.abspath(args.dir)
    print(f"Polishing extension panel at: {root}\n")

    if not os.path.exists(os.path.join(root, 'manifest.json')):
        print(f"ERROR: No manifest.json at {root}")
        sys.exit(1)

    patch_file(os.path.join(root, 'content.js'), CONTENT_JS_PATCHES)

    print("Changes:")
    for c in CHANGES:
        print(c)
    print()
    success = sum(1 for c in CHANGES if c.strip().startswith('✓'))
    failed = sum(1 for c in CHANGES if c.strip().startswith('✗'))
    print(f"{success}/{len(CHANGES)} patches applied successfully" + (f" \u00b7 {failed} not found" if failed else ""))


if __name__ == '__main__':
    main()
