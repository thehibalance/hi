#!/usr/bin/env python3
"""What changes if GLASSDOOR_DATA and JOB_DATA stop counting as evidence? Read-only.

    cd pipeline && python3 measure_authored_sources.py

WHY THIS EXISTS

`glassdoor_pipeline.py:26` and `job_board_pipeline.py:34` are literal Python dicts — 43 and
37 companies of hand-typed values, with prose `notes` fields and `ai_ratio` figures that are
every one a multiple of 0.05 and exactly equal to ai_postings/total_postings, which is the
arithmetic of authored numbers rather than counted ones. Neither module fetches anything.
Neither is in the nightly. The stores on disk hold exactly 43 and 37 records, so they are
1:1 dumps of the dicts.

Both are published in `get_contributing_sources()`'s list of 21 contributing sources.

They are also load-bearing: of the 34 companies reporting 11+ of 18 sub-signals with real
data — the set holding all 29 "Strong" labels and the one "Verified" — Glassdoor appears on
34 of 34 and Jobs on 31 of 34.

So three separate changes are available, with very different blast radii:

  1. drop both from the published source list        (presentation; no score moves)
  2. add both to a derived-set so `real_count`       (coverage and confidence move)
     stops counting them as measured evidence
  3. remove the dicts entirely                       (scores move)

This script measures what 2 would do, because that is the one with consequences and the
project's own practice — v1.11.0 and v1.12.0 — is to measure a downward revision before
shipping it.

WHAT IT CAN MEASURE

`evidence_pass` is per dimension and published, and `gate_evidence` is `all()` of it. A
dimension's sources are published too. So the projected evidence gate can be computed
exactly: a dimension keeps its evidence only if it cites at least one source that is neither
authored nor already excluded.

WHAT IT CANNOT MEASURE

`signal_coverage` and `confidence` derive from `real_count`, which is per SUB-SIGNAL. The
published row carries sources per DIMENSION, not per sub-signal. So the exact new coverage
numbers need an engine run, not this file. It prints an upper bound and says so rather than
guessing — the distinction between a bound and a measurement is the whole point.
"""
import json
import sys
from collections import Counter
from pathlib import Path

SCORES = Path("data/scores/all_scores.json")
if not SCORES.exists():
    raise SystemExit("  no data/scores/all_scores.json — run from pipeline/")

# Hand-authored dicts masquerading as external sources.
AUTHORED = {"Glassdoor", "Jobs"}

# Already excluded from the published source list by api_server.py:712.
NOT_EVIDENCE = {"Industry", "Manual Scoring", "Defaults", "Seed Estimate", "Industry+EPA"}

rows = [r for r in json.load(open(SCORES)) if r.get("spec_version") and not r.get("error")]
print(f"{len(rows)} engine-scored rows\n")


def dims(r):
    return (r.get("genome") or {})


def srcs(r, d):
    return set(((dims(r).get(d) or {}).get("sources") or []))


def gates(r):
    b = r.get("hi_balanced_gates") or {}
    return b, (b.get("_detail") or {})


# ── 1. Reach ──────────────────────────────────────────────────────────────
print("1. REACH — how many rows cite each authored source\n")
cite = Counter()
for r in rows:
    ds = set(r.get("data_sources") or [])
    for a in AUTHORED:
        if a in ds:
            cite[a] += 1
    if AUTHORED <= ds:
        cite["both"] += 1
for k in list(AUTHORED) + ["both"]:
    print(f"   {k:12} {cite[k]:>5} of {len(rows)}")

print("\n   per dimension — rows whose dimension sources include an authored name")
print(f"   {'dim':5} {'authored':>9} {'ONLY authored/excluded':>24}")
only_authored = Counter()
for d in "HUMAN":
    n = sum(1 for r in rows if srcs(r, d) & AUTHORED)
    # a dimension loses its evidence if nothing outside authored+excluded remains
    o = sum(1 for r in rows
            if (srcs(r, d) & AUTHORED) and not (srcs(r, d) - AUTHORED - NOT_EVIDENCE))
    only_authored[d] = o
    print(f"   {d:5} {n:>9} {o:>24}")
print("\n   The second column is the one that matters: those dimensions have no evidence")
print("   left once the authored values are withdrawn.")

# ── 2. The evidence gate, projected exactly ───────────────────────────────
print("\n\n2. EVIDENCE GATE — computable exactly, because it is per dimension\n")
now_pass = proj_pass = 0
lost = []
for r in rows:
    b, det = gates(r)
    ep = det.get("evidence_pass") or {}
    if not ep:
        continue
    cur = all(bool(v) for v in ep.values())
    new = {}
    for d, v in ep.items():
        if not v:
            new[d] = False
            continue
        remaining = srcs(r, d) - AUTHORED - NOT_EVIDENCE
        new[d] = bool(remaining)
    nxt = all(new.values())
    now_pass += cur
    proj_pass += nxt
    if cur and not nxt:
        lost.append((r.get("company"), r.get("ticker"), r.get("confidence"),
                     [d for d, v in new.items() if not v]))

print(f"   rateable now        {now_pass:>5}")
print(f"   rateable projected  {proj_pass:>5}")
print(f"   would lose it       {len(lost):>5}")
if lost:
    print(f"\n   {'company':34} {'tkr':6} {'label':10} dimensions losing evidence")
    for name, tkr, conf, ds in sorted(lost, key=lambda x: (x[0] or "")):
        print(f"   {(name or '?')[:34]:34} {(tkr or '')[:6]:6} {(conf or ''):10} "
              f"{','.join(ds)}")

# ── 3. Confidence labels among the affected ───────────────────────────────
print("\n\n3. CONFIDENCE LABELS — current, among rows citing an authored source\n")
aff = [r for r in rows if set(r.get("data_sources") or []) & AUTHORED]
print(f"   {len(aff)} rows cite Glassdoor or Jobs")
print(f"   {dict(Counter(r.get('confidence') for r in aff))}")
allc = Counter(r.get("confidence") for r in rows)
print(f"\n   whole file: {dict(allc)}")
strong = [r for r in rows if r.get("confidence") in ("Strong", "Verified")]
share = sum(1 for r in strong if set(r.get("data_sources") or []) & AUTHORED)
print(f"\n   'Strong' or 'Verified' rows: {len(strong)}")
print(f"   of those, citing an authored source: **{share}**")

# ── 4. The bound, labelled as a bound ─────────────────────────────────────
print("\n\n4. COVERAGE — upper bound only, NOT a measurement\n")
cov = []
for r in aff:
    s = (r.get("signal_coverage") or "0/18").split("/")[0]
    cov.append(int(s) if s.isdigit() else 0)
if cov:
    cov.sort()
    print(f"   affected rows' signal_coverage: min {cov[0]}, median "
          f"{cov[len(cov)//2]}, max {cov[-1]}")
print("\n   `signal_coverage` and `confidence` come from `real_count`, which is per")
print("   SUB-SIGNAL. The published row lists sources per DIMENSION. So this file cannot")
print("   compute the new coverage — only the engine can, by adding the two names to a")
print("   derived-set and re-running. Treat section 2 as measured and this as a bound.")

print("\n\nWHAT TO DO WITH THIS\n")
print("   Change 1 — drop both from get_contributing_sources() — moves no score and")
print("   can ship today. api_server.py:712 already has the mechanism: _NOT_SOURCES.")
print("   21 contributing sources becomes 19.")
print("\n   Change 2 — stop counting them as evidence — is the real revision, and section")
print("   2 above is its exact effect on the rateable count. Precedent for shipping it:")
print("   v1.11.0 published a median composite drop of 5.0 points with the before/after")
print("   measured, and called every point of it unearned.")
print("\n   Nothing changed. Read-only.")
