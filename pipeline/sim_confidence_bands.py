#!/usr/bin/env python3
"""Four plain labels instead of five vague ones, with A.3 marked derived. Read-only.
From pipeline/:

    python3 sim_confidence_bands.py
    python3 sim_confidence_bands.py --names        # every company that changes label

WHY

Two problems, one change.

**1. A.3 is PARTLY an industry lookup counted as evidence.** 248 companies carry a
non-neutral A.3 and none is marked derived, so `real_count` credits all 248 as real data.

**CORRECTION, 2026-10-29:** this said every value comes from the `DEFORESTATION_RISK` table.
A.3 has four paths and only the land-only one is that table; the others are USDA Organic, a
USDA/land blend, and an EPA violation ladder. **248 is the upper bound.** The A.3 half of
this simulation was not shipped for that reason — see
`claude/STATUS-v1150-four-labels-one-ladder.md`. The band change below **was** shipped, as
v1.15.0 / spec 1.14.0, and stands on its own: it needed no A.3 change to be worth making.

**2. The five confidence labels are false resolution.** They band on percentage-of-18
thresholds designed for a system expected to reach 12-15 sub-signals. The median company has
**2**. The result:

    Estimated   856 of 1,045     82% of the index gets the same label
    Limited     146
    Strong       29
    Partial      13
    Verified      1              one company, and nothing here is verified

A label that 82% of the index shares is not a rating. Worse, the Limited/Estimated boundary
falls at 3.8 of 18 — it separates a company with four real sub-signals from one with three,
a distinction with no evidentiary meaning, in the exact spot where most of the index sits. So
any honest correction flips dozens of labels: A.3 alone moves 66 of them.

THE PROPOSED LADDER

Four labels, one word each, banded where the data actually clusters rather than at
percentages:

    0        None        no sub-signal has real data
    1-3      Limited
    4-9      Partial
    10+      Strong

`Verified` retires because nothing in this index is verified. `Estimated` retires because it
described 82% of companies and therefore described nothing. `None` is the one new word, and it
is the honest name for 334 companies that currently read "Estimated" — which implies an
estimate was made.

Strong keeps its meaning: today it means 12+ of 18 and covers 29 companies; at 10+ it covers
34. Nearly the same set, same word, so the label a reader has already seen does not change
under them.

WHAT THIS PRINTS

The whole index under four schemes, so the choice is between measured distributions:

    1. today                      published labels, as they are
    2. A.3 derived, old bands     the A.3 fix alone — 66 labels move
    3. today's counts, new bands  the re-band alone
    4. BOTH                       what shipping this actually produces

Plus the full migration matrix from 1 to 4, and with --names every company that changes.

Changes nothing.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

try:
    from scoring_engine import _compute_confidence
except Exception as e:                                      # noqa: BLE001
    raise SystemExit(f"  cannot import _compute_confidence ({e}) — run from pipeline/")

SCORES = Path("data/scores/all_scores.json")
if not SCORES.exists():
    raise SystemExit(f"  missing {SCORES} — run from pipeline/")

PUB = re.compile(r"^\s*(\d+)\s*/\s*(\d+)")
OLD_ORDER = ["Verified", "Strong", "Partial", "Limited", "Estimated"]
NEW_ORDER = ["Strong", "Partial", "Limited", "None"]


def new_band(n):
    """The proposed ladder. Absolute counts, not percentages."""
    if n >= 10:
        return "Strong"
    if n >= 4:
        return "Partial"
    if n >= 1:
        return "Limited"
    return "None"


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


rows = json.load(open(SCORES))
engine = [r for r in rows if r.get("spec_version")]
print(f"{len(rows)} rows · {len(engine)} engine-scored · {len(rows) - len(engine)} seed\n")

missing = [r for r in engine if "industry_derived" not in r]
if missing:
    raise SystemExit(f"  {len(missing)} row(s) carry no `industry_derived` field — these "
                     "scores predate 2026-10-28.\n     Run a nightly first; this would "
                     "otherwise guess at A.3's state.")

# ── 0. the gate: reproduce today's labels before predicting any ──────────────
print("0. RECONSTRUCTION — can this script reproduce today's published labels?\n")
state = []
bad = 0
for r in engine:
    m = PUB.match(str(r.get("signal_coverage") or ""))
    if not m:
        bad += 1
        continue
    n, d = int(m.group(1)), int(m.group(2))
    if _compute_confidence(n, d) != r.get("confidence"):
        bad += 1
    a3 = sub_scores(r).get("A.3")
    credited = a3 is not None and a3 != 50 and "A.3" not in derived(r)
    state.append((r.get("ticker") or r.get("company") or "?", n, d,
                  n - 1 if credited else n, r.get("confidence")))

print(f"   rows checked            : {len(engine)}")
print(f"   labels reproduced       : {len(state) - bad if bad <= len(state) else 0}")
print(f"   not reproduced          : {bad}")
if bad:
    print("\n   STOPPING. A simulation that cannot reproduce today's labels has no standing")
    print("   on tomorrow's. The likeliest cause is that _compute_confidence's bands or its")
    print("   denominator changed and this script holds a stale copy of the assumption.")
    sys.exit(1)
print("   All reproduced — this uses the engine's own banding for the 'today' column.\n")

# ── 1. four schemes ──────────────────────────────────────────────────────────
S1 = Counter(lab for _, _, _, _, lab in state)                          # today
S2 = Counter(_compute_confidence(new, d) for _, _, d, new, _ in state)  # A.3 only
S3 = Counter(new_band(n) for _, n, _, _, _ in state)                    # re-band only
S4 = Counter(new_band(new) for _, _, _, new, _ in state)                # both

print("\n1. THE INDEX UNDER FOUR SCHEMES\n")
print(f"   {'label':12} {'today':>8} {'A.3 only':>10} {'re-band':>9} {'BOTH':>8}")
print("   " + "─" * 52)
for lab in OLD_ORDER + [l for l in NEW_ORDER if l not in OLD_ORDER]:
    a, b, c, dd = S1[lab], S2[lab], S3[lab], S4[lab]
    if a or b or c or dd:
        f = lambda x: str(x) if x else "—"                              # noqa: E731
        print(f"   {lab:12} {f(a):>8} {f(b):>10} {f(c):>9} {f(dd):>8}")
print("   " + "─" * 52)
print(f"   {'TOTAL':12} {sum(S1.values()):>8} {sum(S2.values()):>10} "
      f"{sum(S3.values()):>9} {sum(S4.values()):>8}")

print("\n   Read the last column. That is what shipping both changes produces.")
share = 100.0 * max(S1.values()) / len(state)
share4 = 100.0 * max(S4.values()) / len(state)
big1 = max(S1, key=S1.get)
big4 = max(S4, key=S4.get)
print(f"   Largest single label: today {big1} at {share:.0f}% of the index; "
      f"after {big4} at {share4:.0f}%.")

# ── 2. migration, today -> both ──────────────────────────────────────────────
print("\n\n2. MIGRATION — today's label to the proposed one\n")
mig = Counter((lab, new_band(new)) for _, _, _, new, lab in state)
print(f"   {'from':12} {'to':12} {'n':>6}")
print("   " + "─" * 32)
for (a, b), k in sorted(mig.items(), key=lambda kv: -kv[1]):
    mark = "" if a == b else "   <-- changes"
    print(f"   {a:12} {b:12} {k:>6}{mark}")
changed = sum(k for (a, b), k in mig.items() if a != b)
print(f"\n   {changed} of {len(state)} companies see a different word "
      f"({100.0 * changed / len(state):.0f}%).")
print("   Every one of them is a label replaced by a more honest label. No company's")
print("   data changed; only what the index claims to know about it.")

# ── 3. what each new label will mean ─────────────────────────────────────────
print("\n\n3. WHAT EACH LABEL WILL MEAN, PLAINLY\n")
desc = {
    "None": "no sub-signal has real data for this company",
    "Limited": "1 to 3 sub-signals of 18",
    "Partial": "4 to 9 of 18",
    "Strong": "10 or more of 18",
}
for lab in NEW_ORDER:
    n = S4[lab]
    print(f"   {lab:9} {n:>5} companies  ({100.0 * n / len(state):>4.1f}%)   {desc[lab]}")

print("\n   Retiring: `Verified` — nothing in this index is verified, and one company held")
print("   it. `Estimated` — it described 82% of the index and therefore described nothing.")

# ── 4. names ─────────────────────────────────────────────────────────────────
if "--names" in sys.argv:
    print("\n\n4. EVERY COMPANY THAT CHANGES LABEL\n")
    movers = [(t, n, new, lab, new_band(new)) for t, n, d, new, lab in state
              if lab != new_band(new)]
    movers.sort(key=lambda x: (NEW_ORDER.index(x[4]), -x[2]))
    print(f"   {'company':22} {'cov':>9}  from -> to")
    for t, n, new, a, b in movers:
        print(f"   {str(t)[:22]:22} {n:>3}->{new:<3}  {a} -> {b}")
else:
    print("\n   Run with --names for every company that changes label.")

print("""

5. WHAT SHIPPING THIS TAKES

   Engine, two changes in one release:
     * INDUSTRY_DERIVED.add("A.3") on the LAND-ONLY branch, with the add-then-discard
       pattern U.4 and A.1 use — not unconditionally, because A.3's other three paths are
       measurements about the company. NOT SHIPPED; the band change below was.
     * _compute_confidence rewritten to the four absolute bands above

   This changes the formula, so the spec stamp moves and every surface that quotes it
   follows — check_continuity.py enforces that. It also rewrites every published
   `confidence` value, so the API, the site, both extensions and the iOS app all show
   new words the morning after.

   RUBRIC needs A.3's entry rewritten: it currently calls A.3 "the strongest signal in A"
   at 248 companies. After this it is an industry lookup table reaching 248 companies and
   saying so.

Nothing changed. Read-only.
""")
