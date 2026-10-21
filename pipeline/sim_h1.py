#!/usr/bin/env python3
"""Simulate H.1's scale against H.3's. Read-only. From pipeline/:

    python3 sim_h1.py

WHY

`_rpe_score` (scoring_engine.py:233) and H.3's measured path are two functions of ONE input:

    rpe_ratio = industry_median / rpe

They correlated at 0.930 before PR #46, and `claude/FINDING-h1-and-h3-are-one-measurement.md`
already called them one measurement published twice. PR #46 recentred H.3 and left H.1 alone:

    H.1    n=649   mean 63.4    4% at 100
    H.3    n=556   mean 51.5    2% at 100

THE PART THAT IS NOT A BUG

`_rpe_score`'s docstring is a model of good practice. It says what it replaced and why:

    "Replaces (median/rpe)*65, which clamped at 100 for anything below 0.65x the median and
     so pinned 168 companies (15%) at the ceiling, unable to tell a company at half its
     industry median from one at a tenth."

That is H.3's defect, diagnosed and fixed in **v1.3.0** — ten releases before H.3 got the same
treatment. H.1's neutral of 65 is DECLARED ("The median company scores 65"), not stumbled into
the way H.3's 70 was. So this is not the same bug twice.

THE THREE THINGS THAT ARE OPEN, AND THEY ARE DIFFERENT SIZES

1. **The domain, and it is not arguable.** H.3 now refuses to score a ratio outside [0.25, 4]
   and returns a clean 50 marked ABSENCE_DERIVED, because a ratio of 881 (TGTX: revenue per
   employee of ~$381, a pre-revenue biotech) is not a measurement of human decision depth.
   `_rpe_score` has no domain. It computes 65 + 15*log2(881) = 211 and clamps to 100. The exact
   case the domain exists to stop is still scored at the ceiling by the twin.

2. **The neutral, and it is editorial.** 65 vs 50. BUT: H.3's recentring argued that the median
   ratio over the population DEFINING the median is exactly 1.000 by construction, so the
   typical company scored 70 by arithmetic rather than measurement. Same input means the same
   ratio median. If it comes back at 1.000 here too, then "the median company scores 65" is the
   same arithmetic artefact — declared out loud instead of stumbled into, which is better
   practice and the same number problem. **This script measures it rather than assuming it.**

3. **The slope.** 15 points per doubling vs 25. A company at half its industry median scores 80
   on H.1 and 75 on H.3, from one number.

VALIDATION FIRST

Nothing below is trustworthy until this script reproduces the CURRENTLY PUBLISHED H.1. Unlike
sim_h3.py, which reimplemented three additive terms, H.1 is one call with no adders at line 897:

    scores["H.1"] = _rpe_score(industry_median, rpe) if _med_ok else 50

So this imports `_rpe_score` directly and compares. That makes the validation a test of
something useful: whether anything ELSE in the pipeline modifies H.1 after it is scored. A
mismatch is a finding, not a bug in this script.

SEED ROWS ARE EXCLUDED, AND THAT MATTERS

Row 0 of all_scores.json is Patagonia: H.1 = 95, H.3 = 50, spec_version = None. Those cannot
both come from the engine — H.1 = 95 implies ratio exactly 4.0, where H.3's inclusive domain
would give 100 — and `_rpe_score` ends in round(x, 1), which would serialise 95.0, not 95.
Patagonia is private, has no SEC filings, and is one of the 94 hand-scored seed rows. Including
them would corrupt the validation. Only spec_version == engine rows are used.

VARIANTS ARE SEPARATE ON PURPOSE

H.3 taught this expensively: removing `h3_industry` alone RAISES the mean, because tech carries
-8 and is 181 of 641 measured companies. A combined patch is uninterpretable. Four variants here,
each measured on its own, and a fifth that is the full H.3 treatment for comparison.

Changes nothing.
"""
import json
import math
import statistics as st
import sys
from pathlib import Path

try:
    from scoring_engine import INDUSTRY_RPE_MEDIANS, get_industry, clamp, _rpe_score
except Exception as e:                                      # noqa: BLE001
    raise SystemExit(f"  cannot import from scoring_engine ({e}) — run from pipeline/")

SEC = Path("data/sec/all_companies.json")
SCORES = Path("data/scores/all_scores.json")
for p in (SEC, SCORES):
    if not p.exists():
        raise SystemExit(f"  missing {p} — run from pipeline/")

LO, HI, K_H3, NEUTRAL_H3 = 0.25, 4.0, 25, 50

# job_board_pipeline.py:113-142 — five ai_hiring_score tiers, three trend_adjustment values.
# Fifteen reachable numbers, and the blend's second term must be one of them.
LADDER = sorted({tier + adj for tier in (20, 40, 65, 80, 95) for adj in (0, -5, -10)})
NEUTRAL_H1, K_H1 = 65, 15


def tick(rec):
    for k in ("ticker", "symbol", "Ticker"):
        v = rec.get(k)
        if v:
            return str(v).upper()
    return None


# ── inputs ────────────────────────────────────────────────────────────────────
sec = {}
for r in json.load(open(SEC)):
    t = tick(r)
    if not t:
        continue
    h = r.get("h_signals") or {}
    n = r.get("n_signals") or {}
    try:
        rpe = float(h.get("revenue_per_employee") or 0)
    except (TypeError, ValueError):
        rpe = 0
    if rpe <= 0:
        continue
    sec[t] = {"ind": get_industry(n.get("sic", "")), "rpe": rpe}

rows = json.load(open(SCORES))
engine_rows = [r for r in rows if r.get("spec_version")]
seed_rows = len(rows) - len(engine_rows)

pub = {}
for r in engine_rows:
    t = tick(r)
    g = ((r.get("genome") or {}).get("H") or {}).get("scores") or {}
    if t and "H.1" in g:
        pub[t] = g["H.1"]

print(f"{len(rows)} rows · {len(engine_rows)} engine-scored · {seed_rows} seed (excluded)")
print(f"{len(sec)} SEC records with a usable RPE · {len(pub)} engine rows publishing an H.1\n")

joined = []
for t, p in pub.items():
    s = sec.get(t)
    if not s:
        continue
    med = INDUSTRY_RPE_MEDIANS.get(s["ind"])
    if not med:
        continue
    joined.append({"t": t, "ind": s["ind"], "rpe": s["rpe"], "med": med,
                   "ratio": med / max(s["rpe"], 1), "pub": p})

if not joined:
    raise SystemExit("  no companies joined on ticker. Check the SEC store's ticker field "
                     "before reading anything below.")

# ── 1. validation ─────────────────────────────────────────────────────────────
print("1. VALIDATION — does _rpe_score reproduce the published H.1?\n")
exact = near = 0
worst = []
for c in joined:
    # v1.14.0 shipped the domain, so the engine withholds an uncredible ratio. A
    # simulator that still calls _rpe_score unconditionally disagrees with the engine on
    # exactly those companies — and then blames something else for it.
    c["in_domain"] = LO <= c["ratio"] <= HI
    want = _rpe_score(c["med"], c["rpe"]) if c["in_domain"] else 50.0
    c["recomputed"] = want
    d = abs(want - c["pub"])
    if d < 0.051:
        exact += 1
    elif d <= 10:
        near += 1
    if d >= 0.051:
        worst.append((d, c["t"], c["pub"], want))

n = len(joined)
pct = 100.0 * exact / n
print(f"   joined on ticker with an industry median : {n}")
print(f"   exact (within 0.05)                      : {exact:>5}   {pct:.1f}%")
print(f"   within 10 points                         : {near:>5}")
if worst:
    print(f"\n   {len(worst)} mismatch(es). Largest, published -> recomputed:")
    for d, t, p, w in sorted(worst, reverse=True)[:8]:
        print(f"      {t:8} {p:>7} -> {w:<7}  delta {d:.1f}")
    print("   The domain is modelled, so a mismatch is no longer a withheld company.")
    print("   What should remain is the BLEND branch at scoring_engine.py:927 —")
    print("   H.1 = (rpe_score + JOB_DATA's adjusted_score) / 2 for companies holding both")
    print("   an RPE and a JOB_DATA entry. Solving for the second term tests that:")
    print()
    # Two branches produce a mismatch, and they need different equations.
    #
    #   blend      (scoring_engine.py:927)  H.1 = (rpe_score + adjusted_score) / 2
    #   jobs-only  (scoring_engine.py:934)  H.1 = adjusted_score
    #
    # The discriminator is exact rather than a tolerance: the blend requires _ratio_ok,
    # so a company this script WITHHELD (recomputed == 50) cannot be on it. Using the
    # blend equation everywhere reported SBUX as a third writer of H.1 (implied 110) and
    # passed GOOGL and NFLX for the wrong reason — 2L-50 maps some ladder values back
    # onto the ladder, so the single-equation test accepted coincidences.
    blend, jobs, off = [], [], []
    for d, t_, p_, w_ in sorted(worst, reverse=True):
        withheld_here = abs(w_ - 50.0) < 0.051
        implied = p_ if withheld_here else 2 * p_ - w_
        hit = min(LADDER, key=lambda L: abs(L - implied))
        # both terms round to 1dp and the blend doubles the published one, so error
        # reaches 0.15. Ladder values are integers >= 5 apart, so 0.5 cannot false-match
        # and 0.15 could false-MISS — which is how a nonexistent third writer gets hunted.
        row = (t_, p_, w_, implied, hit, "jobs" if withheld_here else "blend")
        if abs(hit - implied) >= 0.5:
            off.append(row)
        elif withheld_here:
            jobs.append(row)
        else:
            blend.append(row)
    on = blend + jobs
    print(f"      blend branch, confirmed    : {len(blend):>4}   "
          f"H.1 = (rpe + ladder) / 2")
    print(f"      jobs-only branch, confirmed: {len(jobs):>4}   "
          f"H.1 = ladder alone, ratio withheld")
    print(f"      NOT on the ladder          : {len(off):>4}   "
          f"<- a third writer of H.1")
    for t_, p_, w_, implied, hit, kind in on[:8]:
        eq = "pub" if kind == "jobs" else "2*pub - rpe"
        print(f"         {t_:8} {kind:6} {eq:12} -> {implied:>6.1f} = {hit}")
    if off:
        print("\n      OFF-LADDER, and these are the finding:")
        for t_, p_, w_, implied, hit, kind in off[:8]:
            print(f"         {t_:8} {kind:6} pub {p_:>6} rpe {w_:>6} -> implied "
                  f"{implied:>6.1f} (nearest ladder value {hit})")
        print("      An implied second term that is not a tier plus a trend adjustment means")
        print("      something other than JOB_DATA writes H.1. Find it before trusting the")
        print("      variants below.")
    else:
        print("\n      Every mismatch is on the ladder, so the domain and JOB_DATA together")
        print("      account for every disagreement between _rpe_score and the published H.1.")
        print(f"      {len(blend)} companies have H.1 HALF authored (blend) and {len(jobs)} have it")
        print("      WHOLLY authored (ratio withheld, ladder alone). Neither figure is")
        print("      stated on any surface, and the second is the sharper one: a sub-signal")
        print("      documented as revenue-per-employee, computed entirely from a five-step")
        print("      function on a hand-typed field, and counted as evidence in real_count.")
    print("   See claude/FINDING-h1s-authored-half-is-a-five-step-ladder-on-a-typed-ratio.md")

if pct < 95:
    print(f"\n   !! {pct:.1f}% is not a reproduction. Everything below is void. Stop here and")
    print("      find what else writes H.1.")
    sys.exit(1)
print()

# ── 2. the ratio, which is the editorial crux ─────────────────────────────────
print("2. THE RATIO — H.3's whole argument rests on this number\n")
ratios = sorted(c["ratio"] for c in joined)
qs = [("min", ratios[0]), ("p10", ratios[len(ratios) // 10]),
      ("p25", ratios[len(ratios) // 4]), ("MEDIAN", st.median(ratios)),
      ("p75", ratios[3 * len(ratios) // 4]), ("p90", ratios[9 * len(ratios) // 10]),
      ("max", ratios[-1])]
for label, v in qs:
    mark = "   <- 1.000 means the typical company is scored by arithmetic" \
        if label == "MEDIAN" and abs(v - 1.0) < 0.02 else ""
    print(f"      {label:7} {v:>12,.3f}{mark}")

out = [c for c in joined if not (LO <= c["ratio"] <= HI)]
out_hi = [c for c in out if c["ratio"] > HI]
out_lo = [c for c in out if c["ratio"] < LO]
at100 = [c for c in joined if c["pub"] >= 99.95]
out_at100 = [c for c in out if c["pub"] >= 99.95]

print(f"\n      outside [{LO}, {HI}]            : {len(out):>5}  of {n}  "
      f"({100.0*len(out)/n:.0f}%)")
print(f"         ratio > {HI} (thin revenue): {len(out_hi):>5}")
print(f"         ratio < {LO} (thin staff)  : {len(out_lo):>5}")
print(f"      at exactly 100                : {len(at100):>5}")
print(f"         ...of those, out-of-domain : {len(out_at100):>5}  "
      f"<- scored at the ceiling on a ratio H.3 refuses to score")

if out_hi:
    print("\n      Largest ratios, with what H.1 publishes for them:")
    for c in sorted(out_hi, key=lambda c: -c["ratio"])[:6]:
        implied = c["med"] / max(c["ratio"], 1e-9)
        print(f"         {c['t']:8} ratio {c['ratio']:>10,.1f}  H.1 {c['pub']:>5}  "
              f"rpe ~${implied:,.0f}")
    print("      A ratio of 881 is revenue-per-employee of about $381. That is a company")
    print("      with no revenue yet, not a company full of human decisions.")

# ── 3. variants, each alone ───────────────────────────────────────────────────
print("\n\n3. VARIANTS — each measured separately, never combined\n")


def h1_variant(c, domain=False, neutral=None, k=None):
    """None = the value is withheld (absence-derived, a clean 50)."""
    neutral = NEUTRAL_H1 if neutral is None else neutral
    k = K_H1 if k is None else k
    if domain and not (LO <= c["ratio"] <= HI):
        return 50.0, True
    return round(clamp(neutral + k * math.log2(c["ratio"])), 1), False


# v1.14.0 shipped the domain, so it belongs in the baseline and every candidate keeps it.
# Measuring the neutral or the slope against the pre-domain world would answer a question
# nobody has. The pre-domain row stays only as a reference point.
VARIANTS = [
    ("shipped: 65, k=15, domain", dict(domain=True)),
    ("pre-v1.14.0: no domain", dict()),
    ("B  neutral 65 -> 50", dict(domain=True, neutral=50)),
    ("C  slope 15 -> 25", dict(domain=True, k=25)),
    ("D  full H.3 treatment", dict(domain=True, neutral=50, k=25)),
]

print(f"   {'variant':28} {'mean ALL':>9} {'mean != 50':>11} {'median':>7} "
      f"{'@100':>6} {'=50':>6} {'Δ ALL':>7}")
print("   " + "─" * 82)
base_mean = None
results = {}
for label, kw in VARIANTS:
    vals, withheld = [], 0
    for c in joined:
        v, w = h1_variant(c, **kw)
        vals.append(v)
        withheld += w
    m = st.mean(vals)
    nn = [v for v in vals if v != 50]
    if base_mean is None:
        base_mean = m
    results[label] = vals
    print(f"   {label:28} {m:>9.1f} {st.mean(nn) if nn else 0:>11.1f} "
          f"{st.median(vals):>7.1f} "
          f"{sum(1 for v in vals if v >= 99.95):>6} {sum(1 for v in vals if v == 50):>6} "
          f"{m - base_mean:>+7.1f}")

print("\n   TWO MEANS, ON PURPOSE, AND THEY ARE NOT INTERCHANGEABLE.")
print("   `mean ALL`    averages every joined company, withheld counted as 50.")
print("   `mean != 50`  averages non-neutral values only — what measure_ceiling.py reports")
print("                 per sub-signal, and therefore what any published H.1 mean means.")
print("   v1.14.0's mean prediction came out backwards because 62.7 (ALL, simulated) was")
print("   quoted against 63.4 (!=50, published): the domain was expected to lower a mean")
print("   it raised, because the removed tail was net-LOW. Same label, two denominators.")
print("   See claude/FINDING-the-horizon-metric-measured-the-wrong-denominator.md")

print("\n   Δmean is against the published row, not against each other. Reading two")
print("   variants' deltas as additive is the mistake that made H.3's h3_industry look")
print("   like a safe removal when it RAISES the mean.")

# ── 4. composite impact, with the same caveat sim_h3 carried ──────────────────
print("\n4. WHAT IT COSTS THE COMPOSITE\n")
print("   H.1 is one of four scored H sub-signals; the composite is the mean of five")
print("   dimensions. So one H.1 point is worth about 1/20 of a composite point IF D_H")
print("   weights its sub-signals equally. That is an assumption this script does not")
print("   verify — check the D_H assembly before quoting any figure here.\n")
for label in list(results)[1:]:
    d = st.mean(results[label]) - base_mean
    print(f"      {label:34} {d:>+7.1f} on H.1  ~{d/20:>+6.2f} composite")

# ── 5. what to do ─────────────────────────────────────────────────────────────
print("""

5. READING IT

   THE DOMAIN SHIPPED (v1.14.0, PR #51). H.1's maximum is now 95, which is
   65 + 15*log2(4) — the score at the domain's upper edge, so the domain is provably
   binding rather than incidentally satisfied. The 26 companies H.1 used to publish at
   exactly 100 all had a ratio H.3 refused to score. That is done; the baseline row above
   includes it.

   THE SLOPE IS STILL HARMFUL, AND THE DOMAIN DID NOT FIX IT. Measured: raising k to 25
   takes the companies at exactly 100 from 0 to 34, because 65 + 25*log2(4) = 115 and
   clamps, so everything above ratio 2.64 pins at the ceiling. That is MORE saturation
   than the domain just removed. Do not ship it alone.

   THE NEUTRAL AND THE SLOPE ARE ONE DECISION, NOT TWO. With a domain of [0.25, 4] the
   log2 span is exactly +/-2, so a scale reaches its own ceiling without clamping only
   when neutral + 2k = 100. H.3 satisfies it by construction: 50 + 2(25). With neutral 65
   there is no k that works symmetrically — k = 17.5 tops out at 100 and bottoms at 30,
   leaving a third of the range unreachable. So keeping 65 means permanently using part
   of the scale, which is an argument from the scale rather than from honesty.

   WHAT IS LEFT IS BINARY, AND IT IS AARON'S. Keep 65, declared in _rpe_score's docstring
   and deliberate — though the ratio median is exactly 1.000, so 65 is what the typical
   company scores for being typical. Or move to 50 with k = 25, where the full range is
   used and the domain boundary is the score boundary. B and D land within 0.3 of each
   other, so the slope adds almost nothing once the neutral moves: the choice is 65 or 50,
   worth about -0.67 of a composite point.

   NOT A SCALE QUESTION AT ALL: the jobs-only count in section 1. Those companies have
   H.1 computed entirely from JOB_DATA's ladder, and no neutral or slope touches them.
   That is the 30-of-30 decision, and it is larger than this script.

Nothing changed. Read-only.
""")
