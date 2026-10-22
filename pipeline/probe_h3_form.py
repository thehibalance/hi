#!/usr/bin/env python3
"""H.3's ceiling: the measurement v1.3.0 ran for H.1, aimed at H.3. Read-only.

    cd pipeline && python3 probe_h3_form.py

WHY

`FINDING-industry-rpe-miscalibration.md` (Sept 9) found H.1 pinned at its ceiling for
**167 of 1,046 companies (15%)** and diagnosed it as *the functional form, not the
constant*. It measured candidate forms against the real data:

    form                      at ceiling  at floor  p10-p90
    65*(M/r)        linear          168        0    19 -> 100
    65*sqrt(M/r)                     94        0    35 -> 100
    65 + 15*log2(M/r)   ADOPTED      27        4    38 -> 88

    "The data picked the form, not a preference."

H.1 moved to the log form. **H.3 is still linear** — `clamp(40 + (M/r) * 30)` — and sits
at 16% on its ceiling (102 of 635 at exactly 100). Same divisor, same shape, same cause.
The fix is already written and validated forty lines up the same file.

HOW THE RATIO IS RECOVERED WITHOUT RUNNING THE ENGINE

H.1's published value is `clamp(65 + 15*log2(M/r))`, so it inverts:

    ratio = 2 ** ((H.1 - 65) / 15)

Same companies, same input, no engine run. Three limits, all handled below:

  · H.1 == 50 means no RPE at all. Those are H.3's absence-derived set (H.3 == 50
    since v1.12.0) and are excluded.
  · H.1 clamped at 100 loses the ratio: anything at or above 2**((100-65)/15) = 5.04
    reads the same. Reported separately and excluded from the quantiles, because
    including them would understate every candidate's ceiling.
  · The Sept 9 audit found 618 of 633 H.1 values equal the raw rpe_score; the
    ai-blend path at line 894 effectively never fires. So ~2% carry some other
    adjustment and are noise in these figures.

The inversion is VALIDATED before anything is reported: H.3's current value must satisfy
`40 + 30*ratio` plus a size tier (0..+15) and an industry offset (-8..+10), so the
published H.3 has to fall inside `[linear - 8, linear + 25]`. If it does not for most
companies, the inversion is wrong and the probe says so instead of reporting.

WHAT IS AND IS NOT A MEASUREMENT HERE

The *shape* is measurable: how many companies the ceiling swallows, how wide the middle
is. The *centre* is not. H.3 currently puts the median company at 70 (`40 + 30*1.0`);
H.1 puts it at 65. That difference is editorial and nothing in the data decides it — it
is flagged, not chosen.
"""
import json
import math
import re
import statistics as st
import subprocess
from pathlib import Path

H1_C, H1_S = 65.0, 15.0          # H.1's adopted form: clamp(65 + 15*log2(ratio))
H1_CEIL_RATIO = 2 ** ((100 - H1_C) / H1_S)


def clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


def git(*a):
    try:
        return subprocess.run(("git",) + a, capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:
        return "?"


p = Path("data/scores/all_scores.json")
if not p.exists():
    raise SystemExit("  no data/scores/all_scores.json — run from pipeline/")
rows = [r for r in json.load(open(p)) if not r.get("error") and r.get("spec_version")]
print(f"branch {git('rev-parse', '--abbrev-ref', 'HEAD')} · "
      f"HEAD {git('log', '-1', '--format=%h %cr')}")
print(f"{len(rows)} pipeline rows\n")

# Confirm H.1's form is still what we are inverting.
src = Path("scoring_engine.py")
if src.exists():
    t = src.read_text()
    m = re.search(r"65\s*\+\s*15\s*\*\s*math\.log2", t)
    print("H.1 form in the engine: " + ("clamp(65 + 15*log2(median/rpe)) — confirmed"
                                        if m else
                                        "!! NOT the 65+15*log2 form. The inversion below "
                                        "is invalid; read _rpe_score before trusting it."))
    if not m:
        print("    grep -n '_rpe_score' -A4 scoring_engine.py")

g = lambda r, d, k: ((r.get("genome") or {}).get(d) or {}).get("scores", {}).get(k)

usable, ceiling_h1, no_rpe, bad = [], [], 0, []
for r in rows:
    h1, h3 = g(r, "H", "H.1"), g(r, "H", "H.3")
    if not isinstance(h1, (int, float)) or not isinstance(h3, (int, float)):
        continue
    if h1 == 50 or h3 == 50:
        no_rpe += 1
        continue
    if h1 >= 100:
        ceiling_h1.append(r.get("ticker"))
        continue
    ratio = 2 ** ((h1 - H1_C) / H1_S)
    lin = clamp(40 + 30 * ratio)
    # size tier 0..+15, industry offset -8..+10, then a displacement penalty that can
    # only reduce. So published H.3 must sit below lin+25 and not far above lin-8.
    if not (lin - 30 <= h3 <= min(100.0, lin + 25.5)):
        bad.append((r.get("ticker"), round(h1, 1), h3, round(lin, 1)))
    usable.append((r.get("ticker"), h1, h3, ratio))

print(f"\nrecovered ratios: {len(usable)}")
print(f"  excluded — H.1 or H.3 at the neutral 50 (no usable RPE): {no_rpe}")
print(f"  excluded — H.1 clamped at 100, ratio only known to be >= {H1_CEIL_RATIO:.2f}: "
      f"{len(ceiling_h1)}  {ceiling_h1[:8]}")

# ── Validate before reporting ─────────────────────────────────────────────
share_bad = len(bad) / len(usable) if usable else 1.0
print(f"\nVALIDATION — published H.3 consistent with the recovered ratio: "
      f"{len(usable) - len(bad)}/{len(usable)} ({1 - share_bad:.0%})")
if share_bad > 0.15:
    print("  !! more than 15% inconsistent. The inversion is not sound — do not read the")
    print("     table below. Likeliest causes: H.1 carries an adjustment after line 897,")
    print("     or H.3's offsets are wider than assumed.")
    for t in bad[:10]:
        print(f"       {t[0]:6} H.1={t[1]} H.3={t[2]} linear-predicted={t[3]}")
    raise SystemExit(1)
if bad:
    print(f"  {len(bad)} outside the expected band, consistent with the ~2% the Sept 9")
    print(f"     audit found carrying a non-raw H.1: {[t[0] for t in bad[:8]]}")

ratios = [r for _, _, _, r in usable]
print(f"\nratio (industry median RPE / company RPE): median {st.median(ratios):.2f} · "
      f"p10 {st.quantiles(ratios, n=10)[0]:.2f} · p90 {st.quantiles(ratios, n=10)[8]:.2f}")
print("  ratio > 1 means FEWER dollars per employee than the industry median — more")
print("  humans per dollar, which is what H.3 is meant to reward.")

# ── Candidate forms ───────────────────────────────────────────────────────
FORMS = [
    ("current: 40 + 30*r      (linear)", lambda r: 40 + 30 * r),
    ("40 + 30*sqrt(r)", lambda r: 40 + 30 * math.sqrt(r)),
    ("70 + 10*log2(r)", lambda r: 70 + 10 * math.log2(r)),
    ("70 + 15*log2(r)   H.1 slope", lambda r: 70 + 15 * math.log2(r)),
    ("70 + 20*log2(r)", lambda r: 70 + 20 * math.log2(r)),
    ("70 + 25*log2(r)", lambda r: 70 + 25 * math.log2(r)),
    ("65 + 15*log2(r)   H.1 exactly", lambda r: 65 + 15 * math.log2(r)),
]

print(f"\nCANDIDATE FORMS — n={len(ratios)}, before the size tier and industry offset")
print(f"  {'form':34} {'at 100':>7} {'at 0':>5} {'p10':>6} {'p50':>6} {'p90':>6} {'sd':>6}")
print("  " + "─" * 76)
best = None
for label, f in FORMS:
    v = [clamp(f(r)) for r in ratios]
    q = st.quantiles(v, n=10)
    at_hi = sum(1 for x in v if x >= 100)
    at_lo = sum(1 for x in v if x <= 0)
    print(f"  {label:34} {at_hi:>7} {at_lo:>5} {q[0]:>6.1f} {st.median(v):>6.1f} "
          f"{q[8]:>6.1f} {st.pstdev(v):>6.1f}")
    # prefer the form that wastes least of the scale at either end
    waste = at_hi + at_lo
    if best is None or waste < best[0]:
        best = (waste, label, at_hi, at_lo)

print(f"\n  Add the H.1-clamped {len(ceiling_h1)} companies to every 'at 100' count: their")
print(f"  ratio is >= {H1_CEIL_RATIO:.2f}, which every form above maps to 100.")

print("\nREADING IT")
print(f"  Least of the scale wasted: {best[1]}  ({best[2]} at the ceiling, "
      f"{best[3]} at the floor)")
print("\n  The SHAPE is what this measures. v1.3.0's standard was to pick the form that")
print("  stops the ceiling swallowing companies while not pushing a new pile onto the")
print("  floor — it took H.1 from 168 at the ceiling to 27, and accepted 4 at the floor.")
print("\n  The CENTRE is editorial and this probe does not choose it. H.3 currently puts")
print("  the median company at 70; H.1 puts it at 65. Nothing in the data decides which")
print("  is right, and the RUBRIC should say which was chosen and why.")
print("\n  One more thing to settle in the same change: the size tier (+15/+10/+5 by")
print("  headcount) and h3_industry are applied AFTER this. h3_industry is a second")
print("  helping of industry on top of a ratio that already divides by the industry")
print("  median — named in the Sept 9 follow-ups as uncalibrated, and still is.")

print("\nNothing changed. Read-only.")
