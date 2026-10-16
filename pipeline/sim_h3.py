#!/usr/bin/env python3
"""Simulate four separable H.3 changes. Read-only. From pipeline/:

    python3 sim_h3.py

THE FOUR CHANGES, AND WHY THEY MUST BE REPORTED SEPARATELY

H.3's measured path is three additive terms on one measured ratio:

    h3 = clamp(40 + rpe_ratio * 30)        # rpe_ratio = industry_median / rpe
    h3 += headcount tier                   # +5 / +10 / +15 above 10k / 50k / 200k
    h3 = clamp(h3 + h3_industry[industry]) # healthcare +10 … tech -8

Four things are arguably wrong with that, in descending order of population:

  A  THE SCALE'S NEUTRAL IS 70. At the median, rpe_ratio = 1 and h3 = 40 + 30 = 70.
     The comment says "Range: ~40-70 from RPE alone", which holds only for companies
     ABOVE their median — about half of any population. Below half the median the term
     clamps at 100, so every company at or under 0.5x its industry is pinned there
     indistinguishably. Proposed: clamp(50 + 20 * log2(rpe_ratio)), which puts average
     on average, makes 2x and 0.5x symmetric, and uses the full range.

  B  SEVEN INDUSTRIES HAVE FEWER THAN TEN COMPANIES. services 2, realestate 3,
     media/auto/mining/construction 5, telecom 8. The median is computed from the
     universe it scores, so a company in a 3-company industry is close to its own
     benchmark: rpe_ratio lands near 1 and h3 is 70 by arithmetic rather than by
     measurement. v1.3.0's rule already covers this — "no credible industry baseline ->
     H.3 skips the RPE term entirely" — it just has no n behind it.

  C  INDUSTRY IS COUNTED TWICE. rpe_ratio is already industry-relative; h3_industry adds
     an editorial industry judgment on top. Named and deferred by the v1.12.0 commit.

  D  HEADCOUNT IS COUNTED TWICE. headcount is the denominator of revenue-per-employee, so
     a large workforce already produces a low rpe and a high ratio. The tier credits it
     again.

Bundled, these are uninterpretable — A lowers most scores, B lowers ~31, C moves ±10 either
way, D lowers. Each is reported alone and then together.

THE VALIDATION THAT MATTERS MOST

Before any variant is trustworthy, this script must reproduce the CURRENTLY PUBLISHED H.3
values from the same inputs. If it cannot, every number below is fiction. Section 1 does
that and the script says plainly how well it did. Expected mismatches: the USPTO H.3_adj
fold at scoring_engine.py:993, which this script does not model because patent data is not
read here.

The h3_industry table is PARSED OUT OF THE ENGINE with ast rather than copied, so it cannot
drift. The headcount tiers are hardcoded — if the match rate in section 1 is high, they are
right.
"""
import ast
import json
import math
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

try:
    from scoring_engine import INDUSTRY_RPE_MEDIANS, get_industry, clamp
except Exception as e:                                       # noqa: BLE001
    raise SystemExit(f"  cannot import from scoring_engine ({e}) — run from pipeline/")

SEC = Path("data/sec/all_companies.json")
SCORES = Path("data/scores/all_scores.json")
for p in (SEC, SCORES):
    if not p.is_file():
        raise SystemExit(f"  missing {p} — run from pipeline/")

MIN_N = 10        # section B's threshold
K = 20            # section A's log2 coefficient — a choice, not a measurement


# ── pull h3_industry out of the engine instead of copying it ──────────────
def parse_h3_industry():
    tree = ast.parse(Path("scoring_engine.py").read_text())
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and node.targets
                and getattr(node.targets[0], "id", "") == "h3_industry"):
            return ast.literal_eval(node.value)
    return None


H3_IND = parse_h3_industry()
if H3_IND is None:
    raise SystemExit("  could not parse h3_industry out of scoring_engine.py — "
                     "it may have been renamed. Not guessing.")
print(f"  h3_industry parsed from the engine: {len(H3_IND)} entries, "
      f"{min(H3_IND.values())} to {max(H3_IND.values())}\n")


def headcount_tier(hc):
    if not hc:
        return 0
    if hc > 200000:
        return 15
    if hc > 50000:
        return 10
    if hc > 10000:
        return 5
    return 0


# ── load inputs ──────────────────────────────────────────────────────────
pub = {}
for r in json.load(open(SCORES)):
    if not r.get("spec_version"):
        continue
    t = (r.get("ticker") or "").upper()
    g = ((r.get("genome") or {}).get("H") or {}).get("scores") or {}
    if t and "H.3" in g:
        pub[t] = g["H.3"]

cos = []
ind_vals = defaultdict(list)
for r in json.load(open(SEC)):
    h = r.get("h_signals") or {}
    n = r.get("n_signals") or {}
    t = (r.get("ticker") or "").upper()
    rpe = h.get("revenue_per_employee")
    hc = h.get("headcount")
    if isinstance(hc, dict):
        hc = hc.get("value", 0)
    try:
        hc = int(hc) if hc else 0
    except (TypeError, ValueError):
        hc = 0
    try:
        rpe = float(rpe) if rpe else None
    except (TypeError, ValueError):
        rpe = None
    ind = get_industry(n.get("sic", ""))
    if rpe and rpe > 0:
        ind_vals[ind].append(rpe)
    cos.append({"t": t, "rpe": rpe, "hc": hc, "ind": ind})

counts = {k: len(v) for k, v in ind_vals.items()}
thin = {k for k, v in counts.items() if v < MIN_N}


def h3_of(c, recentre=False, drop_thin=False, no_industry=False, no_headcount=False):
    """Reimplementation of scoring_engine.py:935-963 plus the v1.12.0 absence reset."""
    med = INDUSTRY_RPE_MEDIANS.get(c["ind"])
    med_ok = med is not None
    if drop_thin and c["ind"] in thin:
        med_ok = False
    measured = bool(c["rpe"]) and med_ok

    h3 = 50.0
    if measured:
        ratio = med / max(c["rpe"], 1)
        if recentre:
            h3 = clamp(50 + K * math.log2(ratio)) if ratio > 0 else 50
        else:
            h3 = clamp(40 + ratio * 30)
    if not no_headcount and c["hc"]:
        h3 = min(100, h3 + headcount_tier(c["hc"]))
    if not no_industry:
        h3 = clamp(h3 + H3_IND.get(c["ind"], 0))
    if not measured:
        h3 = 50.0                      # v1.12.0 absence reset
    return round(h3, 1), measured


# ══ 1. VALIDATION ════════════════════════════════════════════════════════
print("1. VALIDATION — can this script reproduce the published H.3?\n")
exact = near = off = 0
offenders = []
for c in cos:
    if c["t"] not in pub:
        continue
    mine, _ = h3_of(c)
    theirs = pub[c["t"]]
    d = abs(mine - theirs)
    if d < 0.05:
        exact += 1
    elif d <= 10.0:
        near += 1
        offenders.append((c["t"], theirs, mine, d))
    else:
        off += 1
        offenders.append((c["t"], theirs, mine, d))

checked = exact + near + off
pct = 100 * exact / checked if checked else 0
print(f"   {checked} companies with both SEC inputs and a published H.3")
print(f"   exact match        {exact:>5}  ({pct:.1f}%)")
print(f"   within 10 points   {near:>5}  <- consistent with the USPTO H.3_adj fold")
print(f"   off by more        {off:>5}")

if pct < 90:
    print("\n   ** STOP. Under 90% exact means the reimplementation is wrong, and every")
    print("   ** number below would be fiction. Worst offenders:")
    for t, th, mi, d in sorted(offenders, key=lambda x: -x[3])[:10]:
        print(f"        {t:8} published {th:>6} · simulated {mi:>6} · off {d:>5.1f}")
    raise SystemExit(1)
print("   Good enough to simulate. Deltas below are computed from the simulated")
print("   baseline, not the published one, so the USPTO fold cancels out.")

# ══ 2. THE FOUR CHANGES, SEPARATELY ══════════════════════════════════════
VARIANTS = [
    ("current",                     {}),
    ("A  recentre (log2)",          {"recentre": True}),
    ("B  drop thin medians",        {"drop_thin": True}),
    ("C  no h3_industry",           {"no_industry": True}),
    ("D  no headcount tier",        {"no_headcount": True}),
    ("ALL  A+B+C+D",                {"recentre": True, "drop_thin": True,
                                     "no_industry": True, "no_headcount": True}),
]

base = {c["t"]: h3_of(c)[0] for c in cos if c["t"]}
base_measured = [c for c in cos if h3_of(c)[1]]
print(f"\n\n2. THE FOUR CHANGES — {len(base_measured)} companies on the measured path\n")
print(f"   {'variant':24} {'n meas':>7} {'mean':>7} {'median':>7} {'@100':>6} "
      f"{'@50':>6} {'mean d':>8} {'~composite d':>13}")
print("   " + "─" * 88)

for name, kw in VARIANTS:
    vals, deltas, nm = [], [], 0
    at100 = at50 = 0
    for c in cos:
        v, measured = h3_of(c, **kw)
        if measured:
            nm += 1
            vals.append(v)
            if v >= 99.95:
                at100 += 1
            if abs(v - 50) < 0.05:
                at50 += 1
        if c["t"] in base:
            deltas.append(v - base[c["t"]])
    md = st.mean(deltas) if deltas else 0
    # H.3 is one of four active H sub-signals; composite is the mean of five dimensions.
    # So a point on H.3 is worth about 1/20 of a composite point IF H is equally weighted.
    if vals:
        print(f"   {name:24} {nm:>7} {st.mean(vals):>7.1f} {st.median(vals):>7.1f} "
              f"{at100:>6} {at50:>6} {md:>+8.1f} {md/20:>+13.2f}")
    else:
        # no company left on the measured path — print dashes, not zeros, so the row
        # cannot be misread as "every score became 0"
        print(f"   {name:24} {nm:>7} {'—':>7} {'—':>7} {'—':>6} {'—':>6} "
              f"{md:>+8.1f} {md/20:>+13.2f}")

print("\n   The composite column assumes H's four active sub-signals are equally")
print("   weighted and the composite is the mean of five dimensions, so one H.3 point")
print("   is 1/20 of a composite point. VERIFY before quoting it:")
print("     grep -n 'D_H =' scoring_engine.py")
print("   The floor rule can also move a composite non-linearly, which this ignores.")

# ══ 3. WHO MOVES MOST ════════════════════════════════════════════════════
print("\n\n3. BIGGEST MOVERS UNDER A (recentre alone)\n")
movers = []
for c in cos:
    if not c["t"] or not h3_of(c)[1]:
        continue
    v = h3_of(c, recentre=True)[0]
    movers.append((v - base[c["t"]], c["t"], c["ind"], base[c["t"]], v,
                   INDUSTRY_RPE_MEDIANS.get(c["ind"], 0) / max(c["rpe"], 1)))
movers.sort()
print(f"   {'ticker':8} {'industry':14} {'ratio':>7} {'now':>7} {'after':>7} {'delta':>8}")


def row(m):
    d, t, ind, b, v, ratio = m
    print(f"   {t:8} {ind:14} {ratio:>7.2f} {b:>7.1f} {v:>7.1f} {d:>+8.1f}")


if len(movers) <= 12:
    for m in movers:
        row(m)
else:
    for m in movers[:6]:
        row(m)
    print(f"   … {len(movers) - 12} more …")
    for m in movers[-6:]:
        row(m)
print("\n   A company at ratio 1.0 is exactly typical for its industry. Under the current")
print("   scale it scores 70; under the recentring, 50. That single row is the finding.")

# ══ 4. THE THIN CELLS ════════════════════════════════════════════════════
print("\n\n4. VARIANT B IN DETAIL — industries with fewer than "
      f"{MIN_N} companies\n")
aff = 0
for ind in sorted(thin, key=lambda i: counts[i]):
    n_scored = sum(1 for c in cos if c["ind"] == ind and h3_of(c)[1])
    aff += n_scored
    has = "yes" if INDUSTRY_RPE_MEDIANS.get(ind) else "no"
    print(f"   {ind:16} {counts[ind]:>3} companies · median in table: {has:<4}"
          f" · {n_scored} currently scored from it")
print(f"\n   Dropping those medians moves **{aff} companies** to an honest 50,")
print("   excluded from real_count. That is v1.3.0's own rule with an n behind it.")

print("\n\nNothing changed. Read-only.")
