#!/usr/bin/env python3
"""Is a fifth of the composite carrying any information? Read-only. From pipeline/:

    python3 probe_dn.py

v1.11.0 deleted N.5, so D_N is now N.2 alone. The obvious next move is to call D_N
broken and rebuild it. This probe exists to stop that move being made on a hunch,
because the score-compression finding already points somewhere else: Tesla's U.1
moved 42 points and its composite moved 2. That is not a D_N problem.

So all five dimensions are measured the same way, and the ranking decides. Three
questions, in order, each one capable of making the next one pointless:

  1. HOW CONSTANT IS EACH DIMENSION?  Distinct values, modal share, spread.
     If D_N is inert and the other four are not, D_N is the finding.
     If all five are near-constant, the composite is the finding and rebuilding
     any single dimension is wasted work.

  2. WHAT ACTUALLY SETS THE COMPOSITE?  The floor rule caps a composite at 50
     whenever any dimension falls below 42. For every company it catches, the
     weights are not determining the score at all — a hard threshold is. That
     population has to be counted before any weight is interpreted.

  3. LEAVE-ONE-OUT.  Drop each dimension, rescore on the remaining four, and
     measure how far composites and grades move. A dimension whose removal
     changes nothing is not contributing, whatever its weight says on paper.

The combining formula is DISCOVERED here, not assumed — it is read back out of the
published rows and checked. If it does not reproduce, the probe says so and stops
rather than reporting a counterfactual built on a guessed formula.
"""
import json
import statistics as st
from collections import Counter
from pathlib import Path

DIMS = ["D_H", "D_U", "D_M", "D_A", "D_N"]
FLOOR, CAP = 42, 50

p = Path("data/scores/all_scores.json")
if not p.exists():
    raise SystemExit("  no data/scores/all_scores.json — run from pipeline/")
rows = [r for r in json.load(open(p)) if not r.get("error")]
full = [r for r in rows
        if all(isinstance(r.get(d), (int, float)) for d in DIMS)
        and isinstance(r.get("composite"), (int, float))]
print(f"{len(rows)} companies · {len(full)} with all five dimensions and a composite\n")
if not full:
    raise SystemExit("  nothing to measure")

# ── 1. How constant is each dimension? ────────────────────────────────────
print("1. HOW CONSTANT IS EACH DIMENSION")
print(f"   {'dim':5} {'distinct':>9} {'modal value':>12} {'at modal':>9} "
      f"{'stdev':>7} {'min':>5} {'max':>5}")
print("   " + "─" * 62)
inert = []
for d in DIMS:
    v = [r[d] for r in full]
    c = Counter(v).most_common(1)[0]
    share = c[1] / len(v)
    if share >= 0.80:
        inert.append((d, share))
    print(f"   {d:5} {len(set(v)):>9} {c[0]:>12} {share:>8.0%} "
          f"{st.pstdev(v):>7.1f} {min(v):>5} {max(v):>5}")
print()
if inert:
    for d, s in sorted(inert, key=lambda x: -x[1]):
        print(f"   !! {d} is one value for {s:.0%} of companies.")
    if len(inert) >= 3:
        print("\n   Three or more dimensions are near-constant. The problem is not any one\n"
              "   dimension — it is that the composite averages mostly-constants. Rebuilding\n"
              "   D_N alone would not move the distribution. (This is the negative result\n"
              "   already recorded for M.3 and N.5: removing two constants from an average\n"
              "   of constants leaves an average of constants.)")
else:
    print("   No dimension is constant for 80%+ of companies.")

# ── 2. What actually sets the composite? ──────────────────────────────────
print("\n2. WHAT ACTUALLY SETS THE COMPOSITE")
floored = [r for r in full if min(r[d] for d in DIMS) < FLOOR]
print(f"   {len(floored)} of {len(full)} companies ({len(floored)/len(full):.0%}) have a "
      f"dimension below {FLOOR}.")
print(f"   For those, the composite is capped at {CAP} by a hard threshold, so the\n"
      f"   dimension weights do not determine their score at all.")
flag = sum(1 for r in full if r.get("floor_triggered"))
print(f"   Rows self-reporting floor_triggered: {flag}"
      + ("   OK, matches" if flag == len(floored) else
         f"   !! differs from the {len(floored)} measured here — worth a look"))
trig = Counter(r.get("triggering_dimension") for r in floored if r.get("triggering_dimension"))
if trig:
    print("   Triggering dimension: " + ", ".join(f"{k} × {v}" for k, v in trig.most_common()))

free = [r for r in full if min(r[d] for d in DIMS) >= FLOOR]
print(f"\n   {len(free)} companies are above the floor — only these can tell us anything\n"
      f"   about how the dimensions combine.")
if not free:
    raise SystemExit("\n   Every company is floored. The weights are untestable from this file.")

# Discover the formula rather than assuming it.
ok_mean = sum(1 for r in free if abs(r["composite"] - st.mean(r[d] for d in DIMS)) <= 0.51)
print(f"   composite == round(mean of five): {ok_mean}/{len(free)} ({ok_mean/len(free):.0%})")
if ok_mean / len(free) < 0.95:
    resid = sorted(((r["composite"] - st.mean(r[d] for d in DIMS)), r.get("ticker"))
                   for r in free)
    print("\n   !! Equal weighting does not reproduce the published composite, so the\n"
          "      leave-one-out below would be built on a guessed formula. Stopping here.")
    print(f"      residual range {resid[0][0]:+.1f} ({resid[0][1]}) to "
          f"{resid[-1][0]:+.1f} ({resid[-1][1]})")
    print("      Point me at the combining step in scoring_engine.py and I'll redo this.")
    raise SystemExit(0)

# ── 3. Leave-one-out ──────────────────────────────────────────────────────
print("\n3. LEAVE-ONE-OUT — drop each dimension, rescore on the remaining four")


def grade(c):
    for lo, g in ((80, "A"), (70, "B"), (60, "C"), (50, "D")):
        if c >= lo:
            return g
    return "F"


print(f"   {'dropped':9} {'mean |move|':>12} {'max move':>9} {'moved >2':>9} "
      f"{'grades move':>12}")
print("   " + "─" * 56)
rank = []
for drop in DIMS:
    keep = [d for d in DIMS if d != drop]
    moves, gm = [], 0
    for r in free:
        c2 = round(st.mean(r[d] for d in keep))
        if min(r[d] for d in keep) < FLOOR:
            c2 = min(c2, CAP)
        moves.append(abs(c2 - r["composite"]))
        if grade(c2) != grade(r["composite"]):
            gm += 1
    rank.append((st.mean(moves), drop, max(moves), sum(1 for m in moves if m > 2), gm))
    print(f"   {drop:9} {st.mean(moves):>12.2f} {max(moves):>9} "
          f"{sum(1 for m in moves if m > 2):>9} {gm:>12}")

rank.sort()
least, most = rank[0], rank[-1]
print(f"\n   Least load-bearing: {least[1]} (mean move {least[0]:.2f})")
print(f"   Most  load-bearing: {most[1]} (mean move {most[0]:.2f})")
if least[0] < 1.0:
    print(f"\n   {least[1]} can be deleted outright and the average company's composite moves\n"
          f"   less than one point. A fifth of the stated methodology is doing nothing\n"
          f"   measurable. That is a publishable negative result, and it is the honest\n"
          f"   answer to 'what is the composite responding to?'")
if most[0] - least[0] < 0.5:
    print("\n   All five are within half a point of each other — no dimension is special.\n"
          "   The compression is in the averaging, not in any one dimension, so the fix\n"
          "   is to the composite's construction. Rebuilding D_N would not show up.")

print("\nNothing changed. Read-only.")
