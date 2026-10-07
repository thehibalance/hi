#!/usr/bin/env python3
"""Tier 1: how much of each 'constant' sub-signal is actually constant. Read-only.

    cd pipeline && python3 audit_constants.py

THE MISTAKE THIS CORRECTS

`audit_rubric_vs_engine.py` classified A.1, A.4, H.2 and U.4 as CONSTANT because the engine
source contains `INDUSTRY_DERIVED.add("<ss>")`. That is wrong reasoning: the `.add()` is
*inside a branch*. A.4 has three measured paths — iFixit hardware scores, a certification
average, CDP Forests — and only falls to `hw_defaults` when all three miss. A static grep
cannot tell which branch ran for which company.

That is the same error three times over in this audit: using a source-level fact to decide a
per-company runtime property. First `v != 50` read as "measured", then absence-derived
sub-signals excluded by name, now a conditional `.add()` read as unconditional. Each time the
output was plausible, and each time it described something other than what was claimed.

THE PROXY THAT DOES WORK

Each fallback draws from a small dict of hand-written integers. A published value that equals
one of those integers is almost certainly the default; anything else came from a measured
path. Same trick that separated H.3's two arms via its no-RPE lattice.

It is a proxy, not proof:
  · a measured path can land on a lattice value by coincidence — inflates the constant count
  · a default table value that equals 50 is already excluded as neutral, so it is invisible
    here (A.4's `manufacturing: 50` is exactly this case)

The real answer needs the engine to publish `derived_signals` per row. Until it does, every
audit of this question will keep making the mistake above. That open item is now the highest-
value small change in the project.

WHAT IT DOES

Parses the default dicts straight out of scoring_engine.py by brace matching, so nothing is
hardcoded here and the figures cannot drift from the code.
"""
import ast
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

NEUTRAL = 50
# sub-signal -> the dict its fallback branch reads
TABLES = {"H.2": "craft_defaults", "U.4": "u4_industry", "A.4": "hw_defaults"}

eng_p, sc_p = Path("scoring_engine.py"), Path("data/scores/all_scores.json")
for f in (eng_p, sc_p):
    if not f.exists():
        raise SystemExit(f"  missing {f} — run from pipeline/")
eng = eng_p.read_text()
rows = [r for r in json.load(open(sc_p)) if not r.get("error") and r.get("spec_version")]


def git(*a):
    try:
        return subprocess.run(("git",) + a, capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:
        return "?"


def grab_dict(name):
    """Pull `name = { ... }` out of the source by brace matching, however many lines."""
    m = re.search(re.escape(name) + r"\s*=\s*\{", eng)
    if not m:
        return None
    i = m.end() - 1
    depth = 0
    for j in range(i, len(eng)):
        if eng[j] == "{":
            depth += 1
        elif eng[j] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return ast.literal_eval(eng[i:j + 1])
                except Exception:
                    return None
    return None


print(f"branch {git('rev-parse', '--abbrev-ref', 'HEAD')} · "
      f"HEAD {git('log', '-1', '--format=%h %cr')}")
print(f"{len(rows)} pipeline rows\n")

g = lambda r, d, k: ((r.get("genome") or {}).get(d) or {}).get("scores", {}).get(k)

print("TIER 1 — the industry-default sub-signals, measured vs constant\n")
print(f"  {'ss':5} {'table':16} {'values':>7} {'constant':>9} {'measured':>9} {'neutral':>8}  "
      f"% constant")
print("  " + "─" * 74)
summary = {}
for ss, tname in TABLES.items():
    tbl = grab_dict(tname)
    if tbl is None:
        print(f"  {ss:5} {tname:16}  !! could not parse the table from the source")
        continue
    lattice = {v for v in tbl.values() if isinstance(v, (int, float))}
    dim = ss.split(".")[0]
    vals = [g(r, dim, ss) for r in rows]
    vals = [v for v in vals if isinstance(v, (int, float))]
    neutral = sum(1 for v in vals if v == NEUTRAL)
    const = sum(1 for v in vals if v in lattice and v != NEUTRAL)
    meas = sum(1 for v in vals if v not in lattice)
    pct = 100 * (const + neutral) / len(vals) if vals else 0
    summary[ss] = (len(vals), const, meas, neutral, pct, tbl, lattice)
    print(f"  {ss:5} {tname:16} {len(vals):>7} {const:>9} {meas:>9} {neutral:>8}  {pct:>9.1f}%")

print("\n  'neutral' = published as exactly 50, so already excluded from coverage. A table")
print("  value of 50 is indistinguishable from no-data, which is right by accident and")
print("  breaks silently if anyone edits that entry.\n")

for ss, (n, const, meas, neut, pct, tbl, lat) in summary.items():
    print(f"  {ss} — {TABLES[ss]} = {tbl}")
    dim = ss.split(".")[0]
    vals = [g(r, dim, ss) for r in rows]
    vals = [v for v in vals if isinstance(v, (int, float))]
    top = Counter(vals).most_common(6)
    print("      " + " · ".join(f"{v}×{c}{'*' if v in lat else ''}" for v, c in top)
          + "    (* = on the lattice)")
    print()

# ── A.1 has no single named table — report its branches instead ───────────
print("A.1 — no single default dict; its fallback is inline. The assignment sites:")
for m in re.finditer(r'^.*scores\["A\.1"\]\s*=.*$', eng, re.M):
    ln = eng[:m.start()].count("\n") + 1
    print(f"   {ln:5}: {m.group(0).strip()[:92]}")
a1 = [g(r, "A", "A.1") for r in rows]
a1 = [v for v in a1 if isinstance(v, (int, float))]
print(f"\n   A.1 distribution: " + " · ".join(f"{v}×{c}" for v, c in
                                              Counter(a1).most_common(8)))
print("   A spike on a few round integers is the fallback; a spread is CDP data.")

print("\nWHAT THIS CHANGES IN THE BASELINE")
tot_const = sum(s[1] + s[3] for s in summary.values())
tot_meas = sum(s[2] for s in summary.values())
print(f"  Across H.2, U.4 and A.4: {tot_const:,} constant values and {tot_meas:,} measured.")
print("  These sub-signals are not wholly constants, and the RUBRIC is not wrong to call")
print("  them PARTIAL — it is right for the measured minority and wrong for the rest.")
print("\n  The defect is in the FORMAT, not the status: one word cannot describe a")
print("  sub-signal that is authoritative for a tenth of companies and a constant for the")
print("  other nine tenths. Every status line needs its coverage beside it:")
print('      "PARTIAL for 101 of 1,045; industry constant for the remaining 944."')
print("\nNothing changed. Read-only.")
