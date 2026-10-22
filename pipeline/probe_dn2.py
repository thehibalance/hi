#!/usr/bin/env python3
"""What is the composite responding to? Read-only. From pipeline/:

    python3 probe_dn2.py

CORRECTS probe_dn.py, which asked the wrong question and answered it confidently.

probe_dn.py ranked dimensions by the MEAN ABSOLUTE MOVE in composite when each was
dropped. D_N came first (3.22 points) and was reported as the most load-bearing
dimension in the system — while the same script's own first table showed D_N is a
single value for 87% of companies.

Both facts are real. The metric was wrong. D_N's modal value is 70 in a system whose
composites centre near 51, so removing it drags every company down together, in the
same direction, in the same order. Mean |move| measures a dimension's LEVEL. A pure
constant maximises it. That is why the most nearly constant dimension in the file was
crowned the most informative one.

Level and information have to be measured apart:

  LEVEL        mean SIGNED delta. How much the dimension lifts or lowers the whole
               distribution. A constant scores high here. This is bias, not signal.

  INFORMATION  how much the dimension changes the ORDER of companies, by Spearman
               rank correlation between the published composite and the leave-one-out
               composite, plus the spread of the per-company deltas. A constant scores
               ZERO here however large its level effect.

A dimension with a big level effect and no information effect is a thumb on the scale:
it moves every published grade by a fixed amount for a reason nothing measured.
"""
import json
import statistics as st
from collections import Counter
from pathlib import Path

DIMS = ["D_H", "D_U", "D_M", "D_A", "D_N"]
FLOOR, CAP = 42, 50


def ranks(v):
    """Average ranks, ties shared — needed because these dimensions are mostly ties."""
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
    n = len(a)
    ma, mb = st.mean(ra), st.mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else float("nan")


def grade(c):
    for lo, g in ((80, "A"), (70, "B"), (60, "C"), (50, "D")):
        if c >= lo:
            return g
    return "F"


p = Path("data/scores/all_scores.json")
if not p.exists():
    raise SystemExit("  no data/scores/all_scores.json — run from pipeline/")
rows = [r for r in json.load(open(p)) if not r.get("error")]
full = [r for r in rows if all(isinstance(r.get(d), (int, float)) for d in DIMS)
        and isinstance(r.get("composite"), (int, float))]
free = [r for r in full if min(r[d] for d in DIMS) >= FLOOR]
print(f"{len(full)} companies · {len(free)} above the floor (the rest are capped at "
      f"{CAP} by threshold, not by weights)\n")

# ── Level vs information ──────────────────────────────────────────────────
print("LEVEL vs INFORMATION — drop each dimension, rescore on the remaining four")
print(f"   {'dim':5} {'modal':>7} {'mean Δ':>9} {'stdev Δ':>9} {'rank rho':>9} "
      f"{'reordered':>10} {'grades':>7}")
print("   " + "─" * 64)
c1 = [r["composite"] for r in free]
out = []
for d in DIMS:
    keep = [x for x in DIMS if x != d]
    c2, gm = [], 0
    for r in free:
        c = round(st.mean(r[x] for x in keep))
        if min(r[x] for x in keep) < FLOOR:
            c = min(c, CAP)
        c2.append(c)
        if grade(c) != grade(r["composite"]):
            gm += 1
    deltas = [b - a for a, b in zip(c1, c2)]
    rho = spearman(c1, c2)
    v = [r[d] for r in full]
    share = Counter(v).most_common(1)[0][1] / len(v)
    out.append((d, share, st.mean(deltas), st.pstdev(deltas), rho, gm))
    print(f"   {d:5} {share:>6.0%} {st.mean(deltas):>+9.2f} {st.pstdev(deltas):>9.2f} "
          f"{rho:>9.4f} {1 - rho:>9.1%} {gm:>7}")

print("\n   mean Δ     = LEVEL. How far the whole distribution shifts. A constant does this.")
print("   stdev Δ    = how differently the dimension treats different companies.")
print("   rank rho   = INFORMATION. 1.0000 means dropping it reorders nobody, i.e. it")
print("                contributed no ability to tell companies apart.")

# ── The verdict, stated as the numbers support it ─────────────────────────
print("\nREADING IT")
for d, share, mean_d, sd, rho, gm in out:
    if abs(mean_d) >= 1.0 and rho >= 0.995:
        print(f"   {d}: shifts every composite by {mean_d:+.2f} and reorders essentially"
              f" nobody\n"
              f"       (rho {rho:.4f}, one value for {share:.0%} of companies). That is a"
              f" CONSTANT\n"
              f"       OFFSET, not a measurement — it moves {gm} companies across a grade"
              f" boundary\n"
              f"       for a reason nothing measured.")
    elif abs(mean_d) < 1.0 and rho >= 0.995:
        print(f"   {d}: neither shifts the distribution ({mean_d:+.2f}) nor reorders anyone"
              f" (rho {rho:.4f}).\n"
              f"       Inert. Removing it would be nearly invisible.")
    else:
        print(f"   {d}: reorders companies (rho {rho:.4f}, {1 - rho:.1%} of the ordering"
              f" changes).\n"
              f"       This one is carrying information.")

# ── What IS the ordering tracking? ────────────────────────────────────────
print("\nWHAT THE PUBLISHED ORDERING ACTUALLY TRACKS")
print("   Spearman between each dimension and the composite it feeds:")
for d in DIMS:
    print(f"      {d:5} {spearman([r[d] for r in free], c1):>7.3f}")
print("   The composite claims five equal dimensions. If one rho dominates, the public")
print("   grade is that dimension wearing five names.")

# ── What the constant is worth ────────────────────────────────────────────
print("\nWHAT THE CONSTANT IS WORTH, IN PUBLISHED GRADE POINTS")
print("   Equal weighting was confirmed exactly (963/963), so each dimension is 1/5 of")
print("   the composite. For a dimension sitting at a modal value M, companies at that")
print("   mode receive M/5 composite points from it:")
for d in DIMS:
    v = [r[d] for r in full]
    m, n = Counter(v).most_common(1)[0]
    others = st.mean([st.mean(r[x] for x in DIMS if x != d) for r in full])
    print(f"      {d:5} mode {m:>3} for {n:>4} companies → {m/5:>5.1f} pts, against a "
          f"{others:.1f} average on the other four  (lift {(m - others)/5:+.1f})")
print("\n   A dimension whose mode sits well above the others' average is inflating every")
print("   grade in the file by that lift. That is a disclosure question, not a tuning one.")

print("\nNothing changed. Read-only.")
