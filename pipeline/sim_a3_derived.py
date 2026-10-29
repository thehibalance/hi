#!/usr/bin/env python3
"""What happens to published confidence labels if A.3 joins INDUSTRY_DERIVED. Read-only.
From pipeline/:

    python3 sim_a3_derived.py

WHY

`A.3` is in neither derived set. Measured 2026-10-29 from the published rows: **248
companies** carry a non-neutral A.3 and **zero** are marked derived, so the engine counts all
248 as real data.

**CORRECTION, 2026-10-29.** The first version of this file said every one of those values
comes from the `DEFORESTATION_RISK` industry lookup. That was inherited from a document dated
2026-10-14 and never checked against the code, and it is wrong. `DEFORESTATION_RISK` is not
in `scoring_engine.py` at all; it lives in `subsignal_pipelines.py` and reaches A.3 as
`ss["land"]["A.3"]`. A.3 has **four** paths — USDA Organic blended 70/30 with the land score,
USDA alone, land alone, and an EPA `total_violations_3yr` ladder — and **only the land-only
path is an industry table**. The engine already appends `"Industry"` to `sources_used` on
exactly that branch, and merely forgets to add A.3 to `INDUSTRY_DERIVED`.

So **248 is an upper bound, not the figure.** It is what would move if A.3 were marked
derived unconditionally — which would also mark real EPA measurements as industry constants,
and is therefore the wrong change. The real count needs a branch replay:
`measure_a3_provenance.py`, with `measure_h1_provenance.py` as the template.

Everything below still holds as the **ceiling** on the label damage, which is the number
worth having before anyone touches the engine. This remains step 2 of
`claude/FINDING-the-engine-computes-provenance-and-discards-it.md`:

    2. Extend coverage to every table-derived sub-signal — A.3 first, then H.1/H.3's RPE
       divisor, using the audit's table attribution as the checklist.

The fix is one line — `INDUSTRY_DERIVED.add("A.3")`. The consequence is not.

WHY IT IS NOT COSMETIC

`real_count` feeds two published fields:

    "confidence": _compute_confidence(real_count, len(all_details)),
    "signal_coverage": f"{real_count}/{len(all_details)} sub-signals with real data",

`confidence` is a banded label — Verified / Strong / Partial / Limited / Estimated — and the
bands are populated exactly where 248 companies would land. `FINDING-signal-coverage-measured.md`
recorded 72 companies at 3/18 against 81 at 4/18. A single count moving crosses a threshold
that users see in the iOS app, the Chrome and Edge extensions and the web detail page.

So the question is not "is the fix correct" — it is, A.3 is a lookup table and the engine
should not call it evidence — but **how many published labels get worse, and which**. A
company whose label drops from Limited to Estimated has not changed; the honesty of its
description has.

HOW IT WORKS

Imports `_compute_confidence` from the engine rather than reimplementing the bands. A second
implementation of a banding rule would be a second answer, and this project has paid for that
mistake with a matcher, a source rule and a prefix list.

It first **reconstructs every row's existing label** from its published `signal_coverage` and
refuses to report anything if the reconstruction fails — if the simulation cannot reproduce
today's labels it cannot be trusted about tomorrow's.

Changes nothing.
"""
import json
import re
from collections import Counter
from pathlib import Path

try:
    from scoring_engine import _compute_confidence
except Exception as e:                                      # noqa: BLE001
    raise SystemExit(f"  cannot import _compute_confidence ({e}) — run from pipeline/")

SCORES = Path("data/scores/all_scores.json")
if not SCORES.exists():
    raise SystemExit(f"  missing {SCORES} — run from pipeline/")

rows = json.load(open(SCORES))
engine = [r for r in rows if r.get("spec_version")]
print(f"{len(rows)} rows · {len(engine)} engine-scored · {len(rows) - len(engine)} seed\n")

PUB = re.compile(r"^\s*(\d+)\s*/\s*(\d+)")
BANDS = ["Verified", "Strong", "Partial", "Limited", "Estimated"]


def sub_scores(r):
    out = {}
    for dim in (r.get("genome") or {}).values():
        if isinstance(dim, dict):
            for code, val in (dim.get("scores") or {}).items():
                if isinstance(val, (int, float)):
                    out[code] = float(val)
    return out


def derived(r):
    return set(r.get("industry_derived") or []) | set(r.get("absence_derived") or [])


# ── 0. can this script reproduce today's labels at all? ──────────────────────
print("0. RECONSTRUCTION — does _compute_confidence reproduce the published labels?\n")
parsed = ok = bad = 0
offenders = []
no_fields = 0
for r in engine:
    m = PUB.match(str(r.get("signal_coverage") or ""))
    if not m:
        continue
    parsed += 1
    n, d = int(m.group(1)), int(m.group(2))
    want = _compute_confidence(n, d)
    got = r.get("confidence")
    if want == got:
        ok += 1
    else:
        bad += 1
        if len(offenders) < 8:
            offenders.append((r.get("ticker") or r.get("company"), n, d, got, want))
    if "industry_derived" not in r:
        no_fields += 1

print(f"   rows with a parseable signal_coverage : {parsed} of {len(engine)}")
print(f"   label reproduced exactly             : {ok}")
print(f"   label NOT reproduced                 : {bad}")
for t, n, d, got, want in offenders:
    print(f"      {str(t)[:16]:16} {n}/{d}  published {got!r}  computed {want!r}")

if no_fields:
    print(f"\n   !! {no_fields} row(s) carry no `industry_derived` field. These scores predate")
    print("      2026-10-28 and A.3's derived state cannot be read from them. Run a nightly")
    print("      first; this simulation would otherwise guess.")
    raise SystemExit(1)

if bad or parsed != len(engine):
    print("\n   STOPPING. The simulation cannot reproduce today's published labels, so it")
    print("   cannot be trusted about tomorrow's. Fix the reconstruction before reading any")
    print("   migration below — the likeliest cause is that _compute_confidence's bands or")
    print("   its denominator changed and this script is reading a stale assumption.")
    raise SystemExit(1)

print("\n   All labels reproduced. The simulation is using the engine's own banding.\n")

# ── 1. who is affected ───────────────────────────────────────────────────────
print("\n1. WHO LOSES A COUNT\n")
affected, rows_by = [], {}
for r in engine:
    m = PUB.match(str(r.get("signal_coverage") or ""))
    n, d = int(m.group(1)), int(m.group(2))
    a3 = sub_scores(r).get("A.3")
    credited = a3 is not None and a3 != 50 and "A.3" not in derived(r)
    new = n - 1 if credited else n
    rows_by[id(r)] = (n, d, new, credited)
    if credited:
        affected.append(r)

print(f"   A.3 credited as evidence today        : {len(affected)} companies")
already = sum(1 for r in engine if "A.3" in derived(r))
print(f"   A.3 already marked derived            : {already}")
neutral = sum(1 for r in engine if (sub_scores(r).get("A.3") or 50) == 50)
print(f"   A.3 at exactly 50 (already excluded)  : {neutral}")
print(f"   unaffected                            : {len(engine) - len(affected)}")

# ── 2. the label migration ───────────────────────────────────────────────────
print("\n\n2. CONFIDENCE LABEL MIGRATION\n")
before = Counter()
after = Counter()
moved = Counter()
movers = []
for r in engine:
    n, d, new, credited = rows_by[id(r)]
    b = r.get("confidence")
    a = _compute_confidence(new, d)
    before[b] += 1
    after[a] += 1
    if a != b:
        moved[(b, a)] += 1
        movers.append((r.get("ticker") or r.get("company"), n, new, b, a))

print(f"   {'label':12} {'before':>8} {'after':>8} {'delta':>8}")
print("   " + "─" * 40)
for lab in BANDS:
    if before[lab] or after[lab]:
        d_ = after[lab] - before[lab]
        print(f"   {lab:12} {before[lab]:>8} {after[lab]:>8} {d_:>+8}")
tot_b, tot_a = sum(before.values()), sum(after.values())
print(f"   {'TOTAL':12} {tot_b:>8} {tot_a:>8}")
if tot_b != tot_a:
    print("   !! totals differ — a label went missing, which is a bug in this script")

print(f"\n   companies whose published label changes: {sum(moved.values())}\n")
if moved:
    for (b, a), k in moved.most_common():
        print(f"      {k:>5}   {b} -> {a}")
else:
    print("      none — every affected company stays in its band. The fix would move")
    print("      coverage counts and no published label, which makes it cheap to ship.")

if movers:
    print(f"\n   The first 25 of {len(movers)}:\n")
    print(f"      {'company':20} {'cov':>8}  label")
    for t, n, new, b, a in movers[:25]:
        print(f"      {str(t)[:20]:20} {n:>3}->{new:<3}  {b} -> {a}")
    if len(movers) > 25:
        print(f"      … and {len(movers) - 25} more")

# ── 3. the coverage distribution ─────────────────────────────────────────────
print("\n\n3. COVERAGE DISTRIBUTION\n")
db = Counter(rows_by[id(r)][0] for r in engine)
da = Counter(rows_by[id(r)][2] for r in engine)
print("   before: " + " ".join(f"{k}:{db[k]}" for k in sorted(db)))
print("   after : " + " ".join(f"{k}:{da[k]}" for k in sorted(da)))
zb, za = db.get(0, 0), da.get(0, 0)
print(f"\n   companies measuring nothing at all: {zb} -> {za}  ({za - zb:+d})")
print(f"   total credited sub-signal-instances: {sum(k * v for k, v in db.items())} -> "
      f"{sum(k * v for k, v in da.items())}")

print(f"""

4. WHAT TO DO WITH THIS

   The fix is NOT the one-liner this section first described. `INDUSTRY_DERIVED.add("A.3")`
   belongs on the land-only branch alone, with the add-then-discard pattern U.4 and A.1
   already use, because A.3's other three paths — USDA Organic, the USDA/land blend, and the
   EPA violation ladder — are measurements about the company. A.3's own RUBRIC entry
   calls it "the strongest signal in A" at 248 companies; after the fix it is an industry
   lookup table reaching 248 companies and saying so, which is the same trade A.4's path
   forward already argues for in that document's own words:

       "A sub-signal that covers 266 of 1,045 and says so is a better artefact than one
        that covers 1,045 and invents 732 of them."

   The cost is in section 2. Every label that moves is a company whose published confidence
   gets *more honest and lower*, and nothing about the company changed. That is a
   communications decision, not an engineering one, and it belongs to Aaron.

   If section 2 shows zero movers, there is no decision to make and the fix is free.

Nothing changed. Read-only.
""")
