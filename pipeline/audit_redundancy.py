#!/usr/bin/env python3
"""Which sub-signals are the same measurement? Read-only. From pipeline/:

    python3 audit_redundancy.py

WHY THIS EXISTS

H.1 and H.3 were found to correlate at Spearman 0.927 — two sub-signals in the same
dimension, both functions of revenue-per-employee against the industry median, counted as
two pieces of evidence in `real_count`. That was found BY ACCIDENT while measuring H.3's
ceiling. Nothing says it is the only such pair, and a baseline that a second engineer is
meant to build on should not depend on which defect somebody tripped over first.

So: every pair, measured the same way, once.

WHAT COUNTS AS A PROBLEM

Two sub-signals in the SAME DIMENSION that rank companies alike are the serious case,
because the dimension averages them — so one datum gets half the weight while the
methodology claims two independent inputs. Across dimensions a high correlation is still
worth knowing (it means the composite is narrower than it looks) but it is not
double-counting in the same average.

WHAT THIS CANNOT SEE

Correlation is not causation and not shared provenance. Two signals can agree because they
measure genuinely linked behaviour, not because they share an input. This probe finds
candidates; the source decides. For every pair it flags, the question is the same one that
settled H.1/H.3: **do they divide by the same number?**

METHOD NOTES, learned the hard way in this project

  · Ranks are tie-averaged. These sub-signals have few distinct values and naive ranking
    inflates correlation badly.
  · Each pair is computed only on companies where BOTH are measured, and n is printed with
    every figure. Nothing below MIN_N decides anything — a rule adopted after a reported
    inversion turned out to rest on 8 companies.
  · A value of exactly 50 is not a measurement (the neutral default), and INDUSTRY_DERIVED
    signals are constants — both are excluded, the latter read from the engine rather than
    hardcoded. ABSENCE_DERIVED is NOT excluded by name: those values are always exactly 50
    and the first filter already removed them, so naming them would also discard their
    measured arm.
"""
import json
import re
import statistics as st
import subprocess
from collections import defaultdict
from pathlib import Path

MIN_N = 40
NEUTRAL = 50
FLAG = 0.60          # report pairs at or above this |rho|
SERIOUS = 0.85       # same-dimension pairs at or above this are double-counting


def git(*a):
    try:
        return subprocess.run(("git",) + a, capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:
        return "?"


def ranks(v):
    """Tie-averaged ranks."""
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(a, b):
    ra, rb = ranks(a), ranks(b)
    ma, mb = st.mean(ra), st.mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else float("nan")


p = Path("data/scores/all_scores.json")
if not p.exists():
    raise SystemExit("  no data/scores/all_scores.json — run from pipeline/")
rows = [r for r in json.load(open(p)) if not r.get("error") and r.get("spec_version")]
print(f"branch {git('rev-parse', '--abbrev-ref', 'HEAD')} · "
      f"HEAD {git('log', '-1', '--format=%h %cr')}")
print(f"{len(rows)} pipeline rows\n")

src = Path("scoring_engine.py")
CONST = set()
if src.exists():
    CONST = set(re.findall(r'INDUSTRY_DERIVED\.add\("([^"]+)"\)', src.read_text()))
print(f"excluded as industry constants: {', '.join(sorted(CONST)) or 'none'}")

# ── Gather per-company measured values, keyed by sub-signal ───────────────
vals, dim_of = defaultdict(dict), {}
for i, r in enumerate(rows):
    for dim, blk in (r.get("genome") or {}).items():
        for k, v in ((blk or {}).get("scores") or {}).items():
            if isinstance(v, (int, float)) and v != NEUTRAL and k not in CONST:
                vals[k][i] = v
                dim_of[k] = dim

keys = sorted(vals, key=lambda k: -len(vals[k]))
print(f"\n{'ss':6} {'dim':4} {'n measured':>11}")
print("─" * 24)
for k in keys:
    print(f"{k:6} {dim_of[k]:4} {len(vals[k]):>11}" +
          ("" if len(vals[k]) >= MIN_N else "   (under threshold)"))

# ── Every pair ────────────────────────────────────────────────────────────
pairs = []
for i, a in enumerate(keys):
    for b in keys[i + 1:]:
        both = sorted(set(vals[a]) & set(vals[b]))
        if len(both) < MIN_N:
            continue
        rho = spearman([vals[a][c] for c in both], [vals[b][c] for c in both])
        pairs.append((abs(rho), rho, a, b, len(both), dim_of[a] == dim_of[b]))
pairs.sort(reverse=True)

print(f"\n{len(pairs)} pairs with at least {MIN_N} companies measured on both\n")
print(f"{'rho':>7} {'n':>6}  {'pair':15} same dim")
print("─" * 46)
shown = 0
for ab, rho, a, b, n, same in pairs:
    if ab < FLAG:
        continue
    shown += 1
    mark = "  ** SAME DIMENSION" if same else ""
    print(f"{rho:>7.3f} {n:>6}  {a} / {b:8}{mark}")
if not shown:
    print(f"  none at or above |rho| {FLAG}")

# ── The serious cases ─────────────────────────────────────────────────────
serious = [(rho, a, b, n) for ab, rho, a, b, n, same in pairs if same and ab >= SERIOUS]
print("\nDOUBLE-COUNTING — same dimension, |rho| >= %.2f" % SERIOUS)
if serious:
    for rho, a, b, n in serious:
        d = dim_of[a]
        print(f"  {a} and {b} in D_{d}: rho {rho:.3f} on {n} companies")
        print(f"     D_{d} averages its sub-signals, so one measurement takes two shares")
        print(f"     of the dimension while real_count reports two independent signals.")
        print(f"     Settle it at the source:  grep -n '\"{a}\"\\|\"{b}\"' scoring_engine.py")
else:
    print("  none — no two sub-signals in the same dimension rank companies alike")
    print("  at that threshold. H.1/H.3 was the only pair, and it is already documented.")

# ── Per sub-signal: its closest partner ───────────────────────────────────
print("\nCLOSEST PARTNER FOR EACH SUB-SIGNAL")
best = {}
for ab, rho, a, b, n, same in pairs:
    for x, y in ((a, b), (b, a)):
        if x not in best or ab > abs(best[x][0]):
            best[x] = (rho, y, n, same)
print(f"  {'ss':6} {'closest':8} {'rho':>7} {'n':>6}  note")
for k in keys:
    if k not in best:
        print(f"  {k:6} {'—':8} {'—':>7} {'—':>6}  no pair reached n>={MIN_N}")
        continue
    rho, y, n, same = best[k]
    note = "same dimension" if same else ""
    print(f"  {k:6} {y:8} {rho:>7.3f} {n:>6}  {note}")

print("\n  A sub-signal whose closest partner is weak is carrying its own information.")
print("  One that sits near another, in the same dimension, is a candidate for being")
print("  counted once — which lowers published coverage and raises what it means.")
print("\nNothing changed. Read-only.")
