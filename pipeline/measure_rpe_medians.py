#!/usr/bin/env python3
"""The denominator of the largest real sub-signal. Read-only. From pipeline/:

    python3 measure_rpe_medians.py

WHY

`INDUSTRY_RPE_MEDIANS` is a 19-entry literal dict. It divides H.1 and H.3 — H.3 being the
largest real sub-signal in the system at n=635, mean 73.4. Two dated artefacts put the
universe at **439 on 2026-04-18** and **445 on 2026-05-01**, so the medians were almost
certainly computed when the universe was a third of its current size and have not moved since.

Three separate things can be wrong with a frozen median, and they need separating:

  1. **It is stale** — the right companies, the wrong year.
  2. **It rests on too few companies** — `services` has 2 companies with an RPE today,
     `realestate` 3, and five industries have 5. A median of two is not a median.
  3. **It is circular** — the median is computed from the same universe it scores. For a
     two-company industry a company is essentially its own benchmark, so
     `rpe_ratio = median / rpe` lands near 1, and H.3 = `40 + 1*30` = **70 by construction**
     rather than by measurement.

That third one matters most, because H.3's scale already puts "average for your industry" at
70 (see claude/FINDING-h3s-neutral-point-is-seventy.md). In a thin industry the 70 is not a
finding about the company at all.

WHAT IT DOES

Recomputes the median from the current SEC store, prints it beside the frozen value with the
shift, flags every industry with too few companies to support a median, and names any industry
`get_industry` can return that has no entry at all. Then shows what H.3 the recomputed median
would give a company sitting exactly at the old one.

Changes nothing. The recompute is a decision, and this is the number it needs.
"""
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

try:
    from scoring_engine import INDUSTRY_RPE_MEDIANS, get_industry, clamp
except Exception as e:                                      # noqa: BLE001
    raise SystemExit(f"  cannot import from scoring_engine ({e}) — run from pipeline/")

SEC = Path("data/sec/all_companies.json")
if not SEC.is_dir() and not SEC.is_file():
    raise SystemExit("  no data/sec/all_companies.json — run from pipeline/")

MIN_N = 10          # below this, a median is a sample of opinion, not a benchmark

rows = json.load(open(SEC))
by_ind = defaultdict(list)
no_rpe = 0
for r in rows:
    h = r.get("h_signals") or {}
    n = r.get("n_signals") or {}
    rpe = h.get("revenue_per_employee")
    if not rpe:
        no_rpe += 1
        continue
    try:
        rpe = float(rpe)
    except (TypeError, ValueError):
        continue
    if rpe <= 0:
        continue
    by_ind[get_industry(n.get("sic", ""))].append(rpe)

total = sum(len(v) for v in by_ind.values())
print(f"{len(rows)} SEC records · {total} with a usable revenue-per-employee · "
      f"{no_rpe} without\n")

print(f"  {'industry':16} {'n':>5} {'frozen':>12} {'current':>12} {'shift':>8}  flag")
print("  " + "─" * 74)

thin, missing, shifts = [], [], []
for ind, vals in sorted(by_ind.items(), key=lambda t: -len(t[1])):
    cur = st.median(vals)
    frozen = INDUSTRY_RPE_MEDIANS.get(ind)
    flags = []
    if frozen is None:
        missing.append((ind, len(vals), cur))
        flags.append("** NO FROZEN MEDIAN — H.3 skips the RPE term entirely")
    if len(vals) < MIN_N:
        thin.append((ind, len(vals)))
        flags.append(f"** only {len(vals)} companies")
    if frozen:
        pct = (cur / frozen - 1) * 100
        shifts.append((abs(pct), ind, len(vals), frozen, cur, pct))
        print(f"  {ind:16} {len(vals):>5} {frozen:>12,.0f} {cur:>12,.0f} "
              f"{pct:>+7.0f}%  {' '.join(flags)}")
    else:
        print(f"  {ind:16} {len(vals):>5} {'—':>12} {cur:>12,.0f} {'—':>8}  "
              f"{' '.join(flags)}")

# ── industries with no median at all ─────────────────────────────────────
print(f"\n  industries in the data: {len(by_ind)}  ·  "
      f"entries in INDUSTRY_RPE_MEDIANS: {len(INDUSTRY_RPE_MEDIANS)}")
unused = sorted(set(INDUSTRY_RPE_MEDIANS) - set(by_ind))
if unused:
    print(f"  medians for industries with no company in the store: {', '.join(unused)}")
if missing:
    n_affected = sum(n for _, n, _ in missing)
    print(f"\n  NO MEDIAN, so `_med_ok` is False and H.3 falls to 50 — "
          f"**{n_affected} companies**")
    for ind, n, cur in missing:
        print(f"      {ind:16} {n:>4} companies · current median would be {cur:>12,.0f}")
    print("  Those companies are ABSENCE_DERIVED on H.3 today, which is correct behaviour.")
    print("  Adding a median for them would move them from honest-50 to measured — worth")
    print("  doing only where n supports it.")

# ── the thin ones, which is the real finding ─────────────────────────────
if thin:
    print(f"\n  TOO FEW COMPANIES TO SUPPORT A MEDIAN (n < {MIN_N}): "
          f"**{len(thin)} of {len(by_ind)} industries**")
    for ind, n in sorted(thin, key=lambda t: t[1]):
        bench = "is its own benchmark" if n <= 3 else "shares a benchmark with a handful"
        print(f"      {ind:16} {n:>4} companies — a company here {bench}")
    print("\n  This is the circularity, and it is worse than staleness. The median is")
    print("  computed from the universe it scores, so in a 2-company industry")
    print("  rpe_ratio = median/rpe lands near 1 and H.3 = 40 + 30 = 70 by construction.")
    print("  A 70 there is not a measurement of the company; it is arithmetic.")

# ── biggest movers ───────────────────────────────────────────────────────
if shifts:
    print("\n  LARGEST SHIFTS since the medians were frozen (n >= "
          f"{MIN_N} only, so these are real)")
    big = [s for s in sorted(shifts, reverse=True) if s[2] >= MIN_N][:8]
    print(f"      {'industry':16} {'n':>5} {'frozen':>12} {'current':>12} {'shift':>8}"
          f" {'H.3 at old median':>19}")
    for _, ind, n, frozen, cur, pct in big:
        # a company sitting exactly at the OLD median, scored against the NEW one
        ratio = cur / frozen
        h3_now = clamp(40 + 1.0 * 30)
        h3_new = clamp(40 + ratio * 30)
        print(f"      {ind:16} {n:>5} {frozen:>12,.0f} {cur:>12,.0f} {pct:>+7.0f}%"
              f" {h3_now:>8.0f} -> {h3_new:<8.0f}")
    print("\n  Read that last column as: a company whose revenue-per-employee has not")
    print("  changed at all, rescored against a current median. Any movement there is")
    print("  the frozen denominator, not the company.")

print("\n\nWHAT TO DO WITH THIS\n")
print("  Recompute the medians ONLY where n supports one. For an industry with 2 or 3")
print("  companies there is no honest median, and the correct behaviour is the one the")
print("  engine already has for a missing median: `_med_ok` False, H.3 a clean 50,")
print("  excluded from real_count. v1.3.0's comment says exactly this —")
print("  \"no credible industry baseline -> H.3 skips the RPE term entirely, rather than")
print("  deriving a 'human decision depth' from a fictional peer group.\" The rule is")
print("  already written; it just has no n threshold behind it.")
print("\n  So the change is two things, and they are separable:")
print("    1. refresh the medians that have enough companies")
print("    2. REMOVE the medians that do not, which moves those companies to an honest 50")
print("\n  Step 2 lowers scores and raises honesty, which is the same shape as v1.11.0.")
print("  Step 1 may move them either way. Simulate them separately or the result is")
print("  uninterpretable.")
print("\nNothing changed. Read-only.")
