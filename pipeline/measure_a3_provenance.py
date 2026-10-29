#!/usr/bin/env python3
"""Every company's A.3, by which of the four branches produced it. Read-only. From pipeline/:

    python3 measure_a3_provenance.py
    python3 measure_a3_provenance.py --names     # the land-only companies, listed

WHY

A.3 is in neither derived set, so the engine credits all **248** of its non-neutral values as
real data about the company. Step 2 of
`claude/FINDING-the-engine-computes-provenance-and-discards-it.md` is to mark the
table-derived part as `INDUSTRY_DERIVED`.

**The part, not the sub-signal.** On 2026-10-29 two simulations were written on the claim
that all 248 come from the `DEFORESTATION_RISK` industry lookup. That claim was inherited
from a document and never checked against the code. A.3 actually has four branches
(`scoring_engine.py:1448-1477`):

    usda_a3 and land_score   ->  round(usda*0.7 + land*0.3, 1)    USDA Organic + Industry
    usda_a3 only             ->  usda_a3                          USDA Organic
    land_score only          ->  land_score                       Industry   <-- the table
    neither, EPA present     ->  a 0/3/10/20 violation ladder      EPA
    nothing                  ->  50

Only the **land-only** branch is the industry table, and the engine already appends
`"Industry"` to `sources_used` on exactly that branch — it labels it correctly and merely
forgets to add A.3 to `INDUSTRY_DERIVED`. Marking A.3 derived unconditionally would mark real
EPA and USDA measurements as industry constants.

So the question this answers is: **how many of the 248 take the land-only path?** That is the
number that belongs in `INDUSTRY_DERIVED`, and nothing has measured it.

A second number falls out of the same replay. The EPA branch reads:

    if v == 0: scores["A.3"] = 85

A company EPA has looked at and found no violations for scores 85 — the project's signature
defect, a failure-to-find recorded as a favourable fact, in the same place. This counts those
too, because they are a different fix (absence, not industry) and nobody should conflate them
again.

HOW IT WORKS, AND WHAT IT DOES NOT ASSUME

It imports the engine's own `_get_usda_organic_record`, `_score_from_usda_organic`,
`index_by_company` and `find_match` rather than reimplementing any of them. A second
implementation of a matcher is a second answer, and this project has paid for that with a
matcher, a source rule, a prefix list and a confidence ladder.

`ss` is read the way the engine reads it — `all_subsignals.json[ticker.upper()]`, and **only
when the ticker is non-empty**, because `score_company` guards the load with `if not ss and
ticker`. A company without a ticker therefore cannot reach the land branch at all, which is a
branch-determining fact rather than an edge case.

Every row's A.3 is reconstructed from the branch and compared to the published value. A
mismatch means the branch or the inputs are wrong, so the counts below cannot be trusted; the
offenders are printed first for that reason. `measure_h1_provenance.py` is the template, and
its own lesson applies here: it matched on the score row's `company` field where the engine
passes a canonical name, and 3 of 1,045 came out wrong.

Changes nothing.
"""
import json
import sys
from collections import Counter
from pathlib import Path

try:
    from scoring_engine import (_get_usda_organic_record, _score_from_usda_organic,
                                index_by_company, find_match, _compute_confidence)
except Exception as e:                                      # noqa: BLE001
    raise SystemExit(f"  cannot import from scoring_engine ({e}) — run from pipeline/")

SCORES = Path("data/scores/all_scores.json")
EPA = Path("data/epa/all_companies.json")
SS = Path("data/subsignals/all_subsignals.json")
for p in (SCORES,):
    if not p.exists():
        raise SystemExit(f"  missing {p} — run from pipeline/")

rows = json.load(open(SCORES))
engine = [r for r in rows if r.get("spec_version")]
epa_recs = json.load(open(EPA)) if EPA.exists() else []
epa_idx = index_by_company(epa_recs) if epa_recs else {}
all_ss = json.load(open(SS)) if SS.exists() else {}

print(f"{len(rows)} rows · {len(engine)} engine-scored · {len(rows) - len(engine)} seed")
print(f"{len(epa_recs)} EPA records, {len(epa_idx)} index keys · "
      f"{len(all_ss)} subsignal entries\n")
if not SS.exists():
    print("  !! data/subsignals/all_subsignals.json is missing. Without it no company can")
    print("     reach the land branch and every A.3 will classify as EPA or neutral, which")
    print("     would look like a clean answer. Stopping instead.\n")
    sys.exit(1)


def a3_of(r):
    g = (r.get("genome") or {}).get("A") or {}
    v = (g.get("scores") or {}).get("A.3")
    return float(v) if isinstance(v, (int, float)) else None


def epa_ladder(v):
    if v == 0:
        return 85
    if v <= 3:
        return 65
    if v <= 10:
        return 45
    if v <= 20:
        return 30
    return 15


BRANCHES = ("blend", "usda-only", "land-only", "epa-ladder", "neutral")
DESC = {
    "blend": "round(usda*0.7 + land*0.3, 1) — 30% industry table",
    "usda-only": "USDA Organic — a measurement about the company",
    "land-only": "the DEFORESTATION_RISK industry table, ALONE",
    "epa-ladder": "an invented 0/3/10/20 ladder on EPA violations",
    "neutral": "50, no input at all",
}

by = {b: [] for b in BRANCHES}
ROW = {}                 # (who, branch) -> the score row, for the label-impact section
offenders = []
zero_violations = []

for r in engine:
    name = r.get("company") or ""
    tick = (r.get("ticker") or "").strip()
    pub = a3_of(r)
    if pub is None:
        continue

    ss = all_ss.get(tick.upper(), {}) if tick else {}
    land = (ss.get("land") or {}).get("A.3")

    try:
        usda = _score_from_usda_organic(_get_usda_organic_record(tick, name))
    except Exception:                                       # noqa: BLE001
        usda = None

    epa = find_match(name, tick, epa_idx) if epa_idx else None
    viol = ((epa or {}).get("a_signals") or {}).get("total_violations_3yr")

    if usda is not None and land is not None:
        b, want = "blend", round(usda * 0.7 + land * 0.3, 1)
    elif usda is not None:
        b, want = "usda-only", usda
    elif land is not None:
        b, want = "land-only", land
    elif viol is not None:
        b, want = "epa-ladder", epa_ladder(viol)
        if viol == 0:
            zero_violations.append((tick or name, pub))
    else:
        b, want = "neutral", 50

    by[b].append((tick or name, pub, want, land, usda, viol))
    ROW[(tick or name, b)] = r
    if abs(float(want) - pub) > 0.051:
        offenders.append((abs(float(want) - pub), tick or name, b, pub, want))

total = sum(len(v) for v in by.values())

print("1. RECONSTRUCTION — all five paths modelled, over every engine row\n")
print(f"   rows with a published A.3 : {total}")
print(f"   reconstructed exactly     : {total - len(offenders)}"
      f"   {100.0 * (total - len(offenders)) / total:.1f}%" if total else "")
print(f"   not reconstructed         : {len(offenders)}")
if offenders:
    print("\n   NOT RECONSTRUCTED — read these before trusting any count below:\n")
    for d, who, b, pub, want in sorted(offenders, reverse=True)[:12]:
        print(f"      {str(who)[:18]:18} {b:11} published {pub:>6} vs modelled {want:>6}"
              f"   delta {d:.1f}")
    if len(offenders) > 12:
        print(f"      … and {len(offenders) - 12} more")
    print("\n   A wrong branch and a wrong input look different: the branch column says")
    print("   which equation was applied. If these are mostly 'usda-only', the USDA record")
    print("   lookup is matching on a name the engine does not pass — the exact mistake")
    print("   measure_h1_provenance.py made, and it cost 3 of 1,045 there.")

print("\n\n2. A.3 BY BRANCH\n")
print(f"   {'branch':12} {'n':>5} {'non-50':>7}  what produced the number")
print("   " + "─" * 76)
for b in BRANCHES:
    vals = by[b]
    nz = sum(1 for _, pub, _, _, _, _ in vals if pub != 50)
    print(f"   {b:12} {len(vals):>5} {nz:>7}  {DESC[b]}")

land_only = by["land-only"]
blend = by["blend"]
land_nz = sum(1 for _, pub, _, _, _, _ in land_only if pub != 50)
blend_nz = sum(1 for _, pub, _, _, _, _ in blend if pub != 50)

print(f"""

3. THE ANSWER

   Non-neutral A.3 values credited as real data today : {sum(1 for r in engine if (a3_of(r) or 50) != 50)}

   Of those, produced by the industry table ALONE     : {land_nz}
   Produced by a blend that is 30% that table         : {blend_nz}

   **{land_nz}** is the number that belongs in INDUSTRY_DERIVED, on the land-only branch
   alone. It is not 248. The simulations written on 2026-10-29 used 248 as the figure and
   it is the upper bound — what would move if A.3 were marked derived unconditionally,
   which would also mark USDA and EPA measurements as industry constants.

   The {blend_nz} blend {'company is' if blend_nz == 1 else 'companies are'} a judgment, not a measurement: 70% of each value is a
   USDA Organic certification and 30% is the table. The engine already lists both sources.
   Precedent says leave them credited — A.1's blend is discarded from INDUSTRY_DERIVED the
   moment real data arrives, and H.1's blend branch counts as evidence at 50% authored.
""")

if zero_violations:
    print(f"""
4. A SECOND DEFECT, IN THE SAME PLACE

   {len(zero_violations)} {'company scores' if len(zero_violations) == 1 else 'companies score'} A.3 = 85 because EPA was searched and found
   **zero violations**:

       if v == 0: scores["A.3"] = 85

   A failure to find recorded as a favourable fact — the project's signature defect, next
   door to the one being fixed. It is NOT the same fix: this is an absence, so it belongs in
   ABSENCE_DERIVED if anywhere, and M.3 is the precedent (v1.11.0 ruled a litigation value
   of zero an absence rather than a clean record). Note that M.3 still publishes a non-neutral
   score for those rows, which is why absence-derived does not imply 50.

   Worth its own decision. Do not fold it into the A.3 industry fix.""")
    for who, pub in zero_violations[:12]:
        print(f"      {str(who)[:18]:18} A.3 = {pub}")
    if len(zero_violations) > 12:
        print(f"      … and {len(zero_violations) - 12} more")

if "--names" in sys.argv and land_only:
    print(f"\n\n5. THE LAND-ONLY COMPANIES — the {len(land_only)} that would be marked\n")
    print(f"   {'company':22} {'A.3':>7} {'land':>7}")
    for who, pub, want, land, usda, viol in sorted(land_only, key=lambda x: -x[1])[:60]:
        print(f"   {str(who)[:22]:22} {pub:>7} {str(land)[:7]:>7}")
    if len(land_only) > 60:
        print(f"   … and {len(land_only) - 60} more")
elif land_only:
    print(f"\n   Run with --names for the {len(land_only)} land-only companies.")

# ── the consequence, under whatever bands and derived sets the engine currently has ──
import re as _re

_PUB = _re.compile(r"^\s*(\d+)\s*/\s*(\d+)")

# Which side of v1.16.0 are these rows from? The engine publishes industry_derived per row,
# so ask the data rather than assuming. Subtracting a coverage point from rows that have
# ALREADY had it subtracted would charge the same change twice — the precise failure this
# whole section exists to avoid.
derived_rows = sum(1 for r in engine if "A.3" in (r.get("industry_derived") or []))
APPLIED = derived_rows > len(engine) // 2
if 0 < derived_rows <= len(engine) // 2:
    print(f"\n   !! A.3 is industry_derived on {derived_rows} of {len(engine)} rows — a")
    print("      partial state no release produces. The store is probably mid-rewrite or")
    print("      mixes two nightlies. Section 6 below assumes PROSPECTIVE and may be wrong.")
if not any("industry_derived" in r for r in engine):
    print("\n   !! no row carries an industry_derived field — the store predates v1.11.1.")
    print("      Section 6 assumes PROSPECTIVE; verify against the engine before quoting it.")

movers = Counter()
examples = []
no_cov = 0
for who, pub, want, land, usda, viol in land_only:
    if pub == 50:
        continue                      # already excluded by the v != 50 half of real_count
    r = ROW.get((who, "land-only")) or {}
    m = _PUB.match(str(r.get("signal_coverage") or ""))
    if not m:
        no_cov += 1
        continue
    n, d = int(m.group(1)), int(m.group(2))
    if APPLIED:
        before, after = _compute_confidence(n + 1, d), r.get("confidence")
        shown = (n + 1, n)
    else:
        before, after = r.get("confidence"), _compute_confidence(n - 1, d)
        shown = (n, n - 1)
    if before != after:
        movers[(before, after)] += 1
        examples.append((who, shown, before, after))

affected = sum(1 for _, p, _, _, _, _ in land_only if p != 50)
mode = "APPLIED — v1.16.0 is live in these rows" if APPLIED else "PROSPECTIVE — not yet live"
print(f"""

6. WHAT MARKING THEM COSTS — {mode}

   companies whose coverage A.3 {'no longer feeds' if APPLIED else 'feeds'} : {affected}
   published label changes {'realised' if APPLIED else 'that would follow'}  : {sum(movers.values())}
""")
if no_cov:
    print(f"   !! {no_cov} of them have no parseable signal_coverage and were skipped.")
if movers:
    for (a, b), k in movers.most_common():
        print(f"      {k:>5}   {a} -> {b}")
    print(f"\n   The first 20 of {len(examples)}:\n")
    print(f"      {'company':22} {'cov':>8}  label")
    for who, (hi, lo), a, b in examples[:20]:
        print(f"      {str(who)[:22]:22} {hi:>3}->{lo:<3}  {a} -> {b}")
    if len(examples) > 20:
        print(f"      … and {len(examples) - 20} more")
else:
    print("   None. Every affected company keeps its label, so the fix is free: coverage")
    print("   counts drop and no published word changes.")

if APPLIED:
    got = sum(movers.values())
    print(f"""
   VERIFICATION. 68 labels were predicted to move when v1.16.0 shipped
   (claude/STATUS-v1160-a3s-table-stops-being-evidence.md). This run reconstructs
   **{got}**. {'They agree.' if got == 68 else 'THEY DISAGREE — the prediction or the branch replay is wrong, and'}
   {'' if got == 68 else 'a disagreement between two measurements is not evidence against either until both'}
   {'' if got == 68 else 'rules are stated. State them before changing anything.'}""")

print("""
   This uses `_compute_confidence` as imported, not a copy of the bands, and reads
   `industry_derived` off the rows rather than assuming which side of v1.16.0 they come
   from, so it re-answers itself when either changes. The previous figure for this — 66,
   from sim_a3_derived.py on 2026-10-28 — was measured against the five percentage bands
   v1.15.0 retired AND over 248 companies rather than 235. Both inputs had moved, and
   nothing complained.

Nothing changed. Read-only.
""")
