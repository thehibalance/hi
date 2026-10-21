#!/usr/bin/env python3
"""Why do measured sub-signals score above the middle? Read-only. From pipeline/:

    python3 measure_ceiling.py

THE HYPOTHESIS, left open in FINDING-renormalization-rejected.md (Aug 20, 2026)

    Why do measured signals average 63.3? Likely because many sub-signals score high
    when nothing bad is found — so "we looked and found nothing" and "we looked and it
    is genuinely good" produce the same number.

TWO CORRECTIONS THIS VERSION MAKES TO ITSELF

**1. `v != 50` is not "measured".** It is only the first of real_count's three clauses.
The other two exclude INDUSTRY_DERIVED and ABSENCE_DERIVED signals — constants that are
not 50 and are not evidence either. On Oct 2 and again on Oct 6 this probe counted them
and reported a fall in the measured mean that was pure composition: the four derived
signals are ~58% of the values and all sit below the mean, so including them drags the
average down and looks like progress. Both times the real figure was higher than the
printed one, and both times the printed one got read first.

The derived names are now PARSED FROM THE ENGINE rather than hardcoded, and the result
is reported as a BAND, because membership is per-company: U.4 and A.1 have `.discard()`
branches, so some of their values genuinely are measurements. The truth is between the
two numbers and this probe does not pretend otherwise.

**2. "Scores high" is not one phenomenon.** Three different shapes produce a high mean
and they need different fixes:

    SATURATED   a real measurement whose scale tops out, so a large share pile at the
                exact maximum and stop being distinguishable. H.3's measured arm is
                clamp(40 + (industry_median/rpe) * 30), which reaches 100 at a ratio of
                2.0 — twice as many employees per dollar as the industry median. 16% of
                its companies are there. The measurement is sound; the ceiling binds.

    TOP-HEAVY   values crowded near the top without a single spike, which usually means
                the POPULATION is selected rather than the measure being wrong. U.3 is
                built from HRC CEI, Disability:IN and B Corp — published methodologies,
                but voluntary programmes whose participants self-select to score well.

    ABSENCE     the original hypothesis: the maximum means "we found no adverse record".
                That is the CFPB failed-lookup defect, and it is the one that makes a
                score unearned rather than merely compressed.

Only the scoring function can tell SATURATED from ABSENCE, so this probe names the shape
and hands you the grep.

SCOPE — pipeline rows only. The 94 hand-scored seed rows carry editorial values, not
measurements, and including them would answer a different question.

RULES, both learned the hard way: nothing below 40 companies decides anything, and the
input's branch, spec and staleness are checked FIRST, with an exit rather than a report.
"""
import json
import re
import statistics as st
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

MIN_N = 40
NEUTRAL = 50
SATURATED_AT = 0.10     # share sitting on the exact maximum
TOP_HEAVY_AT = 0.60     # share within the top fifth of the observed range


def git(*a):
    try:
        return subprocess.run(("git",) + a, capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:
        return "?"


p = Path("data/scores/all_scores.json")
if not p.exists():
    raise SystemExit("  no data/scores/all_scores.json — run from pipeline/")
rows = [r for r in json.load(open(p)) if not r.get("error")]
pipe = [r for r in rows if r.get("spec_version")]
seed = [r for r in rows if not r.get("spec_version")]
age = datetime.now() - datetime.fromtimestamp(p.stat().st_mtime)

print(f"branch {git('rev-parse', '--abbrev-ref', 'HEAD')} · "
      f"HEAD {git('log', '-1', '--format=%h %cr')}")
print(f"all_scores.json · {age.days}d {age.seconds // 3600}h old · {len(rows)} rows "
      f"({len(pipe)} pipeline, {len(seed)} seed)")
print(f"spec_version: {dict(Counter(r.get('spec_version') for r in rows))}")

n5 = sum(1 for r in pipe
         if "N.5" in (((r.get("genome") or {}).get("N") or {}).get("scores") or {}))
if n5:
    print(f"\n  !! STOP. {n5} pipeline rows still carry N.5, deleted in v1.11.0, so this")
    print("     file predates it:  git checkout main && git pull --ff-only\n")
    raise SystemExit(1)

# Is the engine newer than the scores? mtime cannot answer — git checkout rewrites it.
e, s_ = git("log", "-1", "--format=%ct", "--", "scoring_engine.py"), \
        git("log", "-1", "--format=%ct", "--", "data/scores/all_scores.json")
if e.isdigit() and s_.isdigit() and int(e) > int(s_):
    print(f"\n  !! the engine changed {(int(e) - int(s_)) / 3600:.0f}h AFTER these scores")
    print("     were published. Figures below describe the previous version.\n")

# ── Which sub-signals are derived? Read it from the engine. ───────────────
# ONLY the industry constants are excluded by name. ABSENCE_DERIVED must NOT be.
#
# An absence-derived value is always exactly 50 by construction — `h3 = 50;
# ABSENCE_DERIVED.add("H.3")`, and `scores["M.3"] = 50` likewise. So `v != 50` has
# already removed every one of them. Excluding those sub-signals by NAME as well is
# redundant for the constants and destructive for the measurements: the first version
# of this parse dropped all 635 H.3 values, including the 635 that were genuinely
# scored, and reported 63.4 where the answer is 66.2.
#
# INDUSTRY_DERIVED is the opposite case. Those values are 46.5, 48.3, 52.0 — not 50,
# so they survive the first filter and have to be named.
src = Path("scoring_engine.py")
DERIVED, absence = set(), set()
if src.exists():
    t = src.read_text()
    DERIVED = set(re.findall(r'INDUSTRY_DERIVED\.add\("([^"]+)"\)', t))
    absence = set(re.findall(r'ABSENCE_DERIVED\.add\("([^"]+)"\)', t))
    discards = set(re.findall(r'INDUSTRY_DERIVED\.discard\("([^"]+)"\)', t))
else:
    discards = set()
print(f"\nindustry constants, excluded by name: {', '.join(sorted(DERIVED)) or 'none'}")
print(f"absence-derived, already excluded by v != 50: {', '.join(sorted(absence)) or 'none'}"
      f"  (their MEASURED values are kept)")
if discards:
    print(f"  conditionally undone for: {', '.join(sorted(discards))} — so some of their")
    print("  values ARE measurements, which is why the figure below is a band")

# ── Collect ───────────────────────────────────────────────────────────────
by_ss = {}
for r in pipe:
    for dim, blk in (r.get("genome") or {}).items():
        for k, v in ((blk or {}).get("scores") or {}).items():
            if isinstance(v, (int, float)):
                by_ss.setdefault(k, []).append(v)

loose = [v for k, vs in by_ss.items() for v in vs if v != NEUTRAL]
strict = [v for k, vs in by_ss.items() for v in vs if v != NEUTRAL and k not in DERIVED]

print("\n1. THE AUGUST NUMBER, RE-MEASURED")
print(f"   non-neutral, derived INCLUDED : {st.mean(loose):.1f}   n={len(loose):,}"
      f"   <- not 'measured'; the derived signals are constants")
print(f"   non-neutral, derived EXCLUDED : {st.mean(strict):.1f}   n={len(strict):,}"
      f"   <- upper bound")
print(f"\n   August 20, 2026: 63.3, at coverage 7/19.")
print("   The true measured mean is between those two lines, nearer the second.")
print("   Caveat: it is not recorded whether August's 63.3 included seed rows or")
print("   derived signals, so the comparison is indicative, not exact.")
d = st.mean(strict) - 63.3
if abs(d) < 3:
    print(f"\n   → {d:+.1f} against August. ESSENTIALLY UNMOVED. Nineteen versions of")
    print("     retirements did not change what the surviving signals score, so the")
    print("     problem is in what remains, not in what was withdrawn.")
elif d <= -3:
    print(f"\n   → fallen {abs(d):.1f}. The retirements reached the measured signals.")
else:
    print(f"\n   → RISEN {d:+.1f}. Withdrawing constants left the measured arm behind,")
    print("     and it scores higher than the mixture did. Understand this before")
    print("     anything else: the cleanup made the remaining numbers look better.")

# ── Per sub-signal ────────────────────────────────────────────────────────
print(f"\n2. PER SUB-SIGNAL — pipeline rows, non-neutral values")
print(f"   {'ss':6} {'n':>6} {'mean':>6} {'max':>6} {'at max':>7} {'top20':>6}  shape")
print("   " + "─" * 68)
sat, heavy, thin = [], [], []
for k in sorted(by_ss):
    vals = [v for v in by_ss[k] if v != NEUTRAL]
    if not vals:
        continue
    n, mx, lo = len(vals), max(vals), min(vals)
    at_max = sum(1 for v in vals if v == mx) / n
    span = mx - lo
    top20 = sum(1 for v in vals if span and v >= mx - 0.2 * span) / n
    tag = "  (derived)" if k in DERIVED else ""
    if n < MIN_N:
        thin.append((k, n))
        continue
    shape = ""
    if k not in DERIVED:
        if at_max >= SATURATED_AT:
            shape, _ = "SATURATED", sat.append((k, n, at_max, mx))
        elif top20 >= TOP_HEAVY_AT:
            shape, _ = "TOP-HEAVY", heavy.append((k, n, top20, mx))
    print(f"   {k:6} {n:>6} {st.mean(vals):>6.1f} {mx:>6} {at_max:>6.0%} {top20:>5.0%}"
          f"  {shape}{tag}")
if thin:
    print(f"\n   Under {MIN_N} companies, printed and ignored: "
          + ", ".join(f"{k}({n})" for k, n in sorted(thin, key=lambda x: -x[1])))

# ── Reading it ────────────────────────────────────────────────────────────
print("\n3. READING IT")
if sat:
    print(f"   SATURATED — the scale tops out and stops discriminating:")
    for k, n, share, mx in sorted(sat, key=lambda x: -x[2]):
        print(f"      {k:6} {share:.0%} of {n} sit at exactly {mx}")
    print("      A real measurement can do this. The question is whether the maximum")
    print("      means WE MEASURED EXCELLENCE or WE FOUND NO ADVERSE RECORD — only the")
    print("      scoring function says which, and the answer decides whether this is a")
    print("      compression problem or the CFPB failed-lookup defect one level in.")
if heavy:
    print(f"   TOP-HEAVY — crowded near the top with no single spike:")
    for k, n, share, mx in sorted(heavy, key=lambda x: -x[2]):
        print(f"      {k:6} {share:.0%} of {n} within the top fifth, max {mx}")
    print("      This shape usually means the POPULATION is selected, not that the")
    print("      measure is wrong. Check who gets measured at all before changing how.")
if not sat and not heavy:
    print("   No sub-signal above the threshold is saturated or top-heavy.")
print("\n   Check the scoring functions:")
for k, _, _, _ in sorted(sat + heavy, key=lambda x: -x[2])[:4]:
    print(f"     grep -n '\"{k}\"' scoring_engine.py")

print("\nNothing changed. Read-only.")
