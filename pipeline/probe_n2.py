#!/usr/bin/env python3
"""Where does N.2 = 70 come from, and does this project call it evidence?

Read-only. From pipeline/:   python3 probe_n2.py

THE CLAIM UNDER TEST

D_N is a single sub-signal, N.2, sitting at exactly 70 for 995 of 1,139 companies and
contributing 14.0 of the 100 composite points to each of them.

Coverage median is 2/18, so this project has already ruled that most sub-signals are
not evidence — that is v1.6.0's rule, constants are excluded from `real_count`.

If N.2's 70 is one of the values excluded from `real_count` while still being averaged
into the composite, then the v1.6.0 rule was applied to the COVERAGE METRIC and not to
the SCORE. A value too weak to count as evidence would be worth three grade points on
every company in the file. Same shape as the last three defects, one surface over.

If instead N.2 is counted in `real_count`, the claim is wrong and the finding is a
different one — that coverage is counting a constant as evidence. Either answer is a
defect. This probe decides WHICH, and does not assume.
"""
import json
import re
import statistics as st
from collections import Counter
from pathlib import Path

rows = [r for r in json.load(open("data/scores/all_scores.json")) if not r.get("error")]
gen = lambda r, d: ((r.get("genome") or {}).get(d) or {}).get("scores", {})

n2 = [(r.get("ticker"), gen(r, "N").get("N.2"), r.get("signal_coverage"),
       r.get("data_sources") or []) for r in rows]
have = [x for x in n2 if x[1] is not None]
print(f"{len(rows)} companies · {len(have)} carry an N.2\n")

print("1. THE DISTRIBUTION")
c = Counter(v for _, v, _, _ in have)
for val, n in c.most_common(8):
    print(f"   N.2 = {str(val):>5}   {n:>5} companies  ({n/len(have):>5.1%})")
if len(c) > 8:
    print(f"   ... {len(c) - 8} further values")

# ── 2. Is the modal value counted as evidence? ────────────────────────────
print("\n2. IS THE MODAL VALUE COUNTED AS EVIDENCE?")
mode = c.most_common(1)[0][0]
at_mode = [x for x in have if x[1] == mode]
off_mode = [x for x in have if x[1] != mode]


def num(cov):
    m = re.match(r"(\d+)\s*/", str(cov or ""))
    return int(m.group(1)) if m else None


cm = [num(x[2]) for x in at_mode if num(x[2]) is not None]
co = [num(x[3] and x[2] or x[2]) for x in off_mode if num(x[2]) is not None]
co = [num(x[2]) for x in off_mode if num(x[2]) is not None]
print(f"   companies AT the mode ({mode}):     n={len(cm):>5}  coverage median "
      f"{int(st.median(cm)) if cm else '?'}  mean {st.mean(cm):.2f}" if cm else "   none")
print(f"   companies OFF the mode:          n={len(co):>5}  coverage median "
      f"{int(st.median(co)) if co else '?'}  mean {st.mean(co):.2f}" if co else "")
if cm and co:
    d = st.mean(co) - st.mean(cm)
    print(f"\n   difference in mean coverage: {d:+.2f} sub-signals")
    if d >= 0.7:
        print("   → Companies off the mode count about one MORE sub-signal as real. That is")
        print("     consistent with the modal 70 being EXCLUDED from real_count: it is not")
        print("     evidence for coverage purposes, yet it is 14 points of every composite.")
        print("     THE CLAIM HOLDS — v1.6.0's rule reached the coverage metric, not the score.")
    elif abs(d) < 0.3:
        print("   → Coverage is the same either way, so the modal 70 appears to be COUNTED")
        print("     as evidence. The claim is wrong and the defect is the mirror image:")
        print("     coverage is counting a constant as a measurement.")
    else:
        print("   → Ambiguous at this margin. Settle it from the engine, not from here:")
        print("     grep -n 'N.2' scoring_engine.py")

# ── 3. What is attributed as its source? ──────────────────────────────────
print("\n3. WHAT SOURCE IS ATTRIBUTED")
NOT_EV = {"Industry", "Manual Scoring", "Defaults", "Seed Estimate"}
src = Counter()
for _, v, _, s in at_mode:
    real = [x for x in s if x not in NOT_EV]
    src["(only non-evidence sources)" if not real else f"{len(real)} real source(s)"] += 1
for k, n in src.most_common():
    print(f"   {k:32} {n:>5} companies at the mode")
print("\n   If companies at the modal 70 carry no real source, nothing measured the 70.")

# ── 4. The cost, stated plainly ───────────────────────────────────────────
print("\n4. WHAT IT COSTS")
others = st.mean([st.mean(r[d] for d in ("D_H", "D_U", "D_M", "D_A"))
                  for r in rows if all(isinstance(r.get(d), (int, float))
                                       for d in ("D_H", "D_U", "D_M", "D_A"))])
print(f"   mode {mode} → {mode/5:.1f} composite points, against {others:.1f} on the other four.")
print(f"   Lift on {len(at_mode)} companies: {(mode - others)/5:+.2f} grade points each.")
print(f"   Withdrawing it would move the published median DOWN by about "
      f"{abs((mode - others)/5):.0f} points.")

print("\n   Confirm the mechanism in the engine before writing any of this down:")
print("     grep -n 'N\\.2' scoring_engine.py | head -20")
print("     grep -n 'INDUSTRY_DERIVED\\|ABSENCE_DERIVED\\|real_count' scoring_engine.py | head")

print("\nNothing changed. Read-only.")
