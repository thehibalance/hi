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
    want = _rpe_score(c["med"], c["rpe"])
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
    print("   A mismatch means something modifies H.1 after _rpe_score returns — an H.1_adj")
    print("   from the sub-signal store, a floor, or a seed overwrite. Find it before")
    print("   trusting any variant below. That is a finding in its own right.")

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


VARIANTS = [
    ("published (65, k=15, no domain)", dict()),
    ("A  domain only", dict(domain=True)),
    ("B  neutral 65 -> 50 only", dict(neutral=50)),
    ("C  slope 15 -> 25 only", dict(k=25)),
    ("D  full H.3 treatment", dict(domain=True, neutral=50, k=25)),
]

print(f"   {'variant':34} {'mean':>7} {'median':>7} {'@100':>6} {'=50':>6} "
      f"{'withheld':>9} {'Δmean':>7}")
print("   " + "─" * 86)
base_mean = None
results = {}
for label, kw in VARIANTS:
    vals, withheld = [], 0
    for c in joined:
        v, w = h1_variant(c, **kw)
        vals.append(v)
        withheld += w
    m = st.mean(vals)
    if base_mean is None:
        base_mean = m
    results[label] = vals
    print(f"   {label:34} {m:>7.1f} {st.median(vals):>7.1f} "
          f"{sum(1 for v in vals if v >= 99.95):>6} {sum(1 for v in vals if v == 50):>6} "
          f"{withheld:>9} {m - base_mean:>+7.1f}")

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

   The DOMAIN is the unarguable change. H.3 already refuses to score a ratio outside
   [0.25, 4] and says why in a comment. H.1 scores those same companies and clamps them
   at 100. One of the two is wrong about the same number, and the one with the stated
   reasoning is the one to copy.

   The NEUTRAL is editorial and the ratio median above decides how editorial. If the
   median is 1.000, then 65 is what the typical company scores for being typical, which
   is the thing v1.11.0 and v1.13.0 both shipped against — but H.1's 65 was CHOSEN and
   written down, and churning a deliberate choice to match a bug fix is not obviously
   right. That one is Aaron's, not a measurement.

   The SLOPE follows the neutral. Picking a domain picks k if the domain boundary and the
   score boundary are made to coincide, which is how H.3's 25 was derived rather than
   chosen.

   Ship variant A alone first if the domain holds up. It lowers scores, withholds rather
   than invents, needs no editorial decision, and is the same move as v1.3.0, v1.11.0 and
   v1.13.0. Then measure B and C against the NEW baseline, not this one.

Nothing changed. Read-only.
""")
