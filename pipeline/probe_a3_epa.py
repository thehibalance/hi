#!/usr/bin/env python3
"""What patch two would do to A.3, measured before it ships. Read-only. From pipeline/:

    python3 probe_a3_epa.py

WHY MEASURE FIRST

v1.12.0 was predicted exactly before it shipped — H.3 non-50 at 635, zero-coverage at 270,
coverage mean 2.32 — and every figure landed. That is the standard for a scoring change in
this project, and patch two is a scoring change: it moves the EPA violation penalty out of
the dead branch at scoring_engine.py:1397 and into the `elif land_score is not None:` branch
at 1393, where `epa_data` is already in scope.

Today `score_land` receives `epa_violations=0` for every company, so the penalty is always
0 and **no company has ever been penalised for EPA violations in A.3**. The tiers are
-10 above 3 violations, -15 above 10, -20 above 20.

WHAT THIS CHECKS, AND WHY THE LAST ONE IS THE REAL QUESTION

  1. Where EPA violation data lives, and its shape — discovered, not assumed.
  2. How many of the 1,045 scored companies have a violation count at all.
  3. The distribution of counts, and which tier each would land in.
  4. How many A.3 values move, and by how much.
  5. The D_A and composite effect — A.3 is 0.25 of D_A, D_A is 0.20 of the composite, so
     a -20 on A.3 is -5 on D_A and -1 on the composite. Small, by design.
  6. **THE FLOOR RULE.** Any dimension below 42 caps the composite at 50. If D_A sits just
     above 42 for a company whose A.3 drops, the composite does not move by 1 point — it
     collapses to 50. That is the effect worth predicting, and it is the one a naive
     "how much does A.3 change" measurement would miss entirely.

Nothing here is written. The probe reports; the patch comes after, built against what it
found rather than against what was expected.
"""
import json
import re
from collections import Counter
from pathlib import Path

SC = Path("data/scores/all_scores.json")
if not SC.exists():
    raise SystemExit("  no data/scores/all_scores.json — run from pipeline/")
rows = [r for r in json.load(open(SC)) if not r.get("error") and r.get("spec_version")]
print(f"{len(rows)} pipeline rows\n")

# ── 1. Find the EPA store, rather than assuming its path ──────────────────
print("1. WHERE EPA VIOLATION DATA LIVES — found, not assumed")
cands = [p for p in Path("data").rglob("all_companies.json") if "epa" in str(p).lower()]
cands += [p for p in Path("data").rglob("*.json")
          if "epa" in p.name.lower() and p not in cands]
if not cands:
    raise SystemExit("  !! no EPA store found under data/. Refusing to predict a change\n"
                     "     from data I cannot locate.\n"
                     "       ls data/ | grep -i epa\n"
                     "       grep -n 'epa_data' scoring_engine.py | head")
for c in cands:
    print(f"   {str(c):52} {c.stat().st_size:>12,} bytes")

store = cands[0]
raw = json.load(open(store))
recs = raw if isinstance(raw, list) else list(raw.values())
print(f"\n   using {store} — {len(recs)} records")
if recs and isinstance(recs[0], dict):
    print(f"   keys on a record: {', '.join(sorted(recs[0].keys()))[:160]}")


def dig(node, key, depth=0):
    """Find `key` anywhere in a nested record."""
    if depth > 5:
        return None
    if isinstance(node, dict):
        if key in node:
            return node[key]
        for v in node.values():
            got = dig(v, key, depth + 1)
            if got is not None:
                return got
    elif isinstance(node, list):
        for v in node:
            got = dig(v, key, depth + 1)
            if got is not None:
                return got
    return None


FIELD = "total_violations_3yr"
by_ticker, by_name = {}, {}
for rec in recs:
    if not isinstance(rec, dict):
        continue
    v = dig(rec, FIELD)
    if v is None:
        continue
    tk = (rec.get("ticker") or "").upper().strip()
    nm = (rec.get("company") or rec.get("company_name") or "").lower().strip()
    if tk:
        by_ticker[tk] = v
    if nm:
        by_name[nm] = v

print(f"\n   records carrying `{FIELD}`: {len(by_ticker)} by ticker, "
      f"{len(by_name)} by name")
if not by_ticker and not by_name:
    raise SystemExit(f"  !! no `{FIELD}` found in {store}. The field name in\n"
                     f"     scoring_engine.py:1398 may differ from the store's.\n"
                     f"       python3 -c \"import json;d=json.load(open('{store}'));\"\n"
                     f"         \"print(json.dumps(d[:1] if isinstance(d,list) else d, indent=1)[:2500])\"")


def tier(v):
    if v > 20:
        return -20
    if v > 10:
        return -15
    if v > 3:
        return -10
    return 0


# ── 2-3. Coverage and distribution against the SCORED universe ────────────
g = lambda r, d, k: ((r.get("genome") or {}).get(d) or {}).get("scores", {}).get(k)
matched, unmatched = [], []
for r in rows:
    tk = (r.get("ticker") or "").upper().strip()
    nm = (r.get("company") or "").lower().strip()
    v = by_ticker.get(tk)
    if v is None:
        v = by_name.get(nm)
    (matched if v is not None else unmatched).append((r, v))

print(f"\n2. COVERAGE AGAINST THE SCORED UNIVERSE")
print(f"   scored companies with a violation count : {len(matched):>5} "
      f"({100 * len(matched) / len(rows):.1f}%)")
print(f"   scored companies with none              : {len(unmatched):>5}")
print("   A company with no count keeps its score. Absence is not a penalty and must")
print("   not become one — that is the inverse of the bug this fixes.")

counts = [v for _, v in matched]
if counts:
    tiers = Counter(tier(v) for v in counts)
    print(f"\n3. VIOLATION COUNTS AND THE TIER EACH LANDS IN")
    print(f"   {'violations':>12}  {'companies':>10}")
    for v, n in sorted(Counter(counts).most_common()[:14]):
        print(f"   {v:>12}  {n:>10}")
    print(f"\n   {'penalty':>8}  {'companies':>10}  rule")
    for pen, label in ((0, "<= 3 violations — no penalty"),
                       (-10, "> 3"), (-15, "> 10"), (-20, "> 20")):
        print(f"   {pen:>8}  {tiers.get(pen, 0):>10}  {label}")
    movers = sum(n for p, n in tiers.items() if p != 0)
    print(f"\n   companies whose A.3 would move: **{movers}**")

# ── 4-6. What moves, and whether the floor rule catches anyone ────────────
print(f"\n4-6. WHAT MOVES, AND THE FLOOR")
FLOOR = 42
a3_moves, da_moves, newly_floored, comp_deltas = 0, 0, [], []
for r, v in matched:
    pen = tier(v)
    if pen == 0:
        continue
    a3 = g(r, "A", "A.3")
    if not isinstance(a3, (int, float)):
        continue
    new_a3 = max(0.0, min(100.0, a3 + pen))
    if new_a3 == a3:
        continue
    a3_moves += 1
    d_a = r.get("D_A")
    if not isinstance(d_a, (int, float)):
        continue
    new_da = d_a + (new_a3 - a3) * 0.25
    da_moves += 1
    comp = r.get("composite")
    if isinstance(comp, (int, float)):
        comp_deltas.append((new_da - d_a) * 0.20)
    already = bool(r.get("floor_triggered"))
    if not already and d_a >= FLOOR and new_da < FLOOR:
        newly_floored.append((r.get("ticker"), r.get("company"), v, round(d_a, 1),
                              round(new_da, 1), comp))

print(f"   A.3 values that move        : {a3_moves}")
print(f"   D_A values that move        : {da_moves}")
if comp_deltas:
    import statistics as st
    print(f"   composite change            : mean {st.mean(comp_deltas):+.2f} · "
          f"worst {min(comp_deltas):+.2f}")

print(f"\n   NEWLY FLOOR-TRIGGERED — D_A crosses below {FLOOR}: **{len(newly_floored)}**")
if newly_floored:
    print(f"   {'ticker':8} {'viol':>5} {'D_A':>6} {'->':>3} {'new':>6} {'composite':>10}")
    for tk, nm, v, da, nda, comp in sorted(newly_floored, key=lambda x: x[3]):
        print(f"   {str(tk)[:8]:8} {v:>5} {da:>6} {'->':>3} {nda:>6} "
              f"{comp:>10}  -> capped at 50")
    print("\n   These do not move by a point. Their composite is capped at 50 outright.")
    print("   Each one needs reading by hand before this ships: a company dropping 15")
    print("   points because an EPA count crossed a threshold set by us is exactly the")
    print("   kind of change that should be defended company by company, not in aggregate.")
else:
    print("   none — no company's D_A crosses the floor. The change is bounded to the")
    print("   per-point effect above.")

print("\nWHAT THIS PROBE CANNOT SETTLE")
print("  Whether the tiers (-10 / -15 / -20 above 3 / 10 / 20 violations) are the right")
print("  cutoffs. They are editorial, they were written before anything used them, and")
print("  nothing in the data chose them. EPA ECHO publishes violation counts, not")
print("  severity tiers — so the ladder is ours and the RUBRIC should say so, the way")
print("  it now does for the other editorial ladders.")
print("\n  Also unsettled: a raw count favours small companies. 12 violations across 400")
print("  facilities is not 12 across 3. EPA's own data has a facility count; using it")
print("  would make this a rate rather than a tally.")
print("\nNothing changed. Read-only.")
