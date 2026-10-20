#!/usr/bin/env python3
"""Every company's H.1, by which branch produced it. Read-only. From pipeline/:

    python3 measure_h1_provenance.py

WHY

`sim_h1.py` decomposed H.1 over the 637 companies it could join on ticker WITH an industry
median: 617 pure RPE, 17 blend, 3 jobs-only, 0 unexplained. That accounting is complete for
those 637 and silent about the other 403 rows that publish an H.1.

The gap matters in one direction. A company with no usable SEC revenue-per-employee cannot
reach the blend branch at all, so it takes the jobs-only path by definition — **H.1 computed
entirely from JOB_DATA's five-step ladder, with no revenue and no employees in it.** Patagonia
and Dr. Bronner's both publish H.1 = 95 that way; Shein and Temu publish 10. None of them has
a ticker, so `sim_h1.py` never saw them.

So the jobs-only count of 3 is a lower bound and the real number is unknown. This measures it
over all 1,045 engine-scored rows.

WHY IT USES THE ENGINE'S OWN MATCHER

A first attempt matched `JOB_DATA`'s keys to score rows by lowercased name and got 14 of 37,
with Amazon, Apple, Google, Microsoft, Costco, Chevron, Coca-Cola, Starbucks and General Motors
all reported "unmatched" — every one of which `sim_h1.py` had just found by ticker. They are
present under other spellings: Google/Alphabet, Costco/Costco Wholesale, General Motors/GM.

`scoring_engine.py:349` already solves this with `index_by_company` and `find_match`, which try
exact name, then `normalize_name`, then `canon_name`, then ticker. That is v1.8.0's "one spelling
per company" work, and it is what the scoring loop itself uses. **A fifth matcher would be a
fifth answer.** This imports theirs.

WHAT IT CLASSIFIES

    measured     ratio in [0.25, 4], no job record       -> _rpe_score alone
    blend        ratio in domain, job record present     -> (rpe + ladder) / 2
    jobs-only    ratio withheld or absent, job present   -> ladder ALONE, wholly authored
    withheld     no credible ratio, no job record        -> 50, ABSENCE_DERIVED

Then it reconstructs H.1 for every row and compares to published. All four branches are
modelled, so a mismatch is a writer nobody has found — the same canary `sim_h1.py` carries,
over the whole universe instead of a subset.

Changes nothing.
"""
import json
import math
import statistics as st
from collections import Counter
from pathlib import Path

try:
    from scoring_engine import (INDUSTRY_RPE_MEDIANS, get_industry, clamp, _rpe_score,
                                index_by_company, find_match)
except Exception as e:                                      # noqa: BLE001
    raise SystemExit(f"  cannot import from scoring_engine ({e}) — run from pipeline/")

LO, HI = 0.25, 4.0
LADDER = sorted({tier + adj for tier in (20, 40, 65, 80, 95) for adj in (0, -5, -10)})

SCORES = Path("data/scores/all_scores.json")
SEC = Path("data/sec/all_companies.json")
JOBS = Path("data/jobs/all_companies.json")

for p in (SCORES, SEC):
    if not p.exists():
        raise SystemExit(f"  missing {p} — run from pipeline/")
if not JOBS.exists():
    raise SystemExit(f"  missing {JOBS}. The engine reads the job STORE, not JOB_DATA.\n"
                     "     If the store is absent, no company can be on a job branch and\n"
                     "     this script has nothing to measure. Check data/jobs/ first.")

rows = json.load(open(SCORES))
engine = [r for r in rows if r.get("spec_version")]
sec_idx = index_by_company(json.load(open(SEC)))
job_recs = json.load(open(JOBS))
job_idx = index_by_company(job_recs)

print(f"{len(rows)} rows · {len(engine)} engine-scored · {len(rows) - len(engine)} seed")
print(f"{len(sec_idx)} SEC index keys · {len(job_recs)} job records, "
      f"{len(job_idx)} index keys\n")

# ── classify every engine row ─────────────────────────────────────────────────
BRANCH = {}
recon_exact = recon_off = 0
offenders = []
rows_by_branch = {"measured": [], "blend": [], "jobs-only": [], "withheld": []}

for r in engine:
    name, tick = r.get("company", ""), r.get("ticker", "") or ""
    pub = ((r.get("genome") or {}).get("H") or {}).get("scores", {}).get("H.1")
    if pub is None:
        continue

    sec = find_match(name, tick, sec_idx)
    job = find_match(name, tick, job_idx)

    rpe = None
    ind = None
    if sec:
        try:
            rpe = float((sec.get("h_signals") or {}).get("revenue_per_employee") or 0) or None
        except (TypeError, ValueError):
            rpe = None
        ind = get_industry((sec.get("n_signals") or {}).get("sic", ""))
    med = INDUSTRY_RPE_MEDIANS.get(ind) if ind else None

    ratio = (med / max(rpe, 1)) if (rpe and med) else None
    ok = ratio is not None and LO <= ratio <= HI

    adj = None
    if job:
        h = job.get("h_signals") or {}
        if h.get("ai_ratio") is not None:
            adj = h.get("adjusted_score", 50)

    if ok and adj is not None:
        branch, want = "blend", round(_rpe_score(med, rpe) * 0.5 + adj * 0.5, 1)
    elif ok:
        branch, want = "measured", _rpe_score(med, rpe)
    elif adj is not None:
        branch, want = "jobs-only", adj
    else:
        branch, want = "withheld", 50

    BRANCH[name] = branch
    rows_by_branch[branch].append((name, tick, pub, want, ratio, adj))
    if abs(float(want) - float(pub)) < 0.051:
        recon_exact += 1
    else:
        recon_off += 1
        offenders.append((abs(float(want) - float(pub)), name, tick, branch, pub, want))

total = recon_exact + recon_off
print("1. RECONSTRUCTION — all four branches modelled, over every engine row\n")
print(f"   rows with a published H.1 : {total}")
print(f"   reconstructed exactly     : {recon_exact:>5}   {100.0*recon_exact/total:.1f}%")
print(f"   not reconstructed         : {recon_off:>5}")
if offenders:
    print("\n   NOT RECONSTRUCTED — a writer of H.1 that none of the four branches explains:")
    for d, n_, t_, b_, p_, w_ in sorted(offenders, reverse=True)[:12]:
        print(f"      {(t_ or n_)[:18]:18} {b_:10} published {p_:>6} vs modelled {w_:>6}"
              f"   delta {d:.1f}")
    print("   Read these before trusting the counts below. The branch column says which")
    print("   equation was applied, so a wrong branch and a wrong writer look different.")

# ── the counts ────────────────────────────────────────────────────────────────
print("\n\n2. H.1 BY BRANCH\n")
print(f"   {'branch':12} {'n':>5} {'mean':>7} {'median':>7}  what produced the number")
print("   " + "─" * 78)
DESC = {
    "measured": "_rpe_score alone — revenue per employee",
    "blend": "(rpe + authored ladder) / 2 — HALF authored",
    "jobs-only": "the authored ladder ALONE — WHOLLY authored",
    "withheld": "50, ABSENCE_DERIVED — no claim made",
}
for b in ("measured", "blend", "jobs-only", "withheld"):
    vals = [float(x[2]) for x in rows_by_branch[b]]
    if not vals:
        print(f"   {b:12} {0:>5}       -       -  {DESC[b]}")
        continue
    print(f"   {b:12} {len(vals):>5} {st.mean(vals):>7.1f} {st.median(vals):>7.1f}  {DESC[b]}")

authored = len(rows_by_branch["blend"]) + len(rows_by_branch["jobs-only"])
print(f"\n   H.1 touched by an authored table : {authored} companies")
print(f"      HALF authored  (blend)        : {len(rows_by_branch['blend'])}")
print(f"      WHOLLY authored (jobs-only)   : {len(rows_by_branch['jobs-only'])}")

# ── the wholly authored, named ────────────────────────────────────────────────
jo = rows_by_branch["jobs-only"]
if jo:
    print("\n\n3. WHOLLY AUTHORED — H.1 with no revenue and no employees in it\n")
    print(f"   {'company':26} {'ticker':8} {'H.1':>6} {'on ladder':>10}  coverage / confidence")
    print("   " + "─" * 84)
    byrow = {(r.get("company") or ""): r for r in engine}
    for name, tick, pub, want, ratio, adj in sorted(jo, key=lambda x: -float(x[2]))[:40]:
        r = byrow.get(name, {})
        hit = min(LADDER, key=lambda L: abs(L - float(pub)))
        on = "yes" if abs(hit - float(pub)) < 0.5 else f"NO ({hit}?)"
        print(f"   {name[:26]:26} {tick[:8]:8} {pub:>6} {on:>10}  "
              f"{str(r.get('signal_coverage'))[:30]} / {r.get('confidence')}")
    if len(jo) > 40:
        print(f"   … and {len(jo) - 40} more")

    print("\n   Every one of these is a published 'revenue-per-employee' sub-signal computed")
    print("   from a five-step function on a hand-typed ai_ratio plus a penalty-only trend")
    print("   adjustment. None is 50, none is in INDUSTRY_DERIVED or ABSENCE_DERIVED, so")
    print("   real_count counts each as a sub-signal WITH REAL DATA and it raises the")
    print("   coverage and confidence printed above.")
    print("   See claude/FINDING-h1s-authored-half-is-a-five-step-ladder-on-a-typed-ratio.md")

# ── what it means for the open decision ───────────────────────────────────────
print(f"""

4. WHAT THIS IS FOR

   The 30-of-30 decision is whether an authored table should count as evidence in
   real_count. That decision has been described as large and unmeasured. This is the
   H.1 half of it, measured: {authored} companies have H.1 touched by JOB_DATA, of which
   {len(rows_by_branch['jobs-only'])} have nothing else in it at all.

   Adding "Jobs" to a derived set would move those {len(rows_by_branch['jobs-only'])} companies' H.1 out of
   real_count entirely and halve the evidentiary weight of the other {len(rows_by_branch['blend'])}. The
   coverage and confidence columns in section 3 are what would change.

   This says nothing about GLASSDOOR_DATA, which feeds U and M rather than H and is the
   larger of the two tables at 43 companies. Same decision, different dimensions, and
   `measure_authored_sources.py` already computes the evidence gate for both.

Nothing changed. Read-only.
""")
