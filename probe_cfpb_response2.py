#!/usr/bin/env python3
"""Probe v2: relief rate, the posture behind it, and the product mix underneath.

Read-only. Changes no pipeline file and writes no score. From the repo root:

    python3 probe_cfpb_response2.py              # all 60 matched companies
    python3 probe_cfpb_response2.py --limit 10

WHAT v1 SETTLED

Relief rate discriminates: 0.4% to 30.2% across eight companies. `timely` does not — 0% to
1% untimely, a near-constant, exactly the shape validate_pipeline flags as a failed lookup.
So timely is a disclosure field, not a ladder input. That question is closed.

WHAT v1 GOT WRONG

v1 printed "they move together, so the new ladder would mostly restate the old one" off a
correlation of r = +0.58. That reading was backwards, and the heuristic that produced it was
mine. The current ladder is DESCENDING — more complaints per employee, lower score. A relief
ladder would be ASCENDING — more relief, higher score. A positive correlation between the two
raw quantities therefore means the two ladders **rank companies in opposite directions**.

The eight companies say so directly:

    Bank of America       2,601 per 10k   relief 30.2%   U.1 56   <- worst-scored, most relief
    JPMorgan              2,112           relief 15.9%   U.1 57
    PNC                   1,684           relief  8.9%   U.1 59
    Associated Banc-Corp    845           relief  2.3%   U.1 63
    Cullen/Frost            521           relief  8.3%   U.1 66
    Zions                   387           relief  8.4%   U.1 68
    Columbia Banking        383           relief  0.4%   U.1 68   <- best-scored, least relief

Columbia Banking closes 99.6% of its complaints with an explanation and nothing else, and is
currently published near the top of Customer Empathy. Bank of America returns money in 24% of
cases and is published in the middle. Swapping the ladder would not recalibrate U.1; it would
invert a large part of a published ranking.

Also: r = +0.58 on n = 8 is not distinguishable from zero. Two-tailed significance at n = 8
needs about r = 0.71. Nothing above should be trusted until the full set runs.

WHAT THIS PROBE ADDS

The inversion raises a question the relief rate alone cannot answer, and it is the same
ambiguity as `FINDING-renormalization-rejected.md` — two different realities producing one
number:

    0.4% relief because almost nothing was actually wrong
    0.4% relief because relief is refused

CFPB carries a field that separates them. The endpoint returns a `company_public_response`
aggregation — the company's own stated position, including whether it disputes the facts or
believes it acted appropriately. A firm that resolves complaints upstream and a firm that
stonewalls have the same relief rate and different postures.

The endpoint also returns `product` and `issue`. Relief rates are not comparable across
product mixes — a mortgage book and a credit-reporting book do not behave alike — so this
probe records each company's mix so we can see whether the comparison is even legitimate
before anyone builds a ladder on it.

All of it arrives in the same size=0 response. Still zero extra requests per company.

This probe decides nothing. It reports.
"""
import argparse
import json
import math
import statistics as st
import sys
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("  pip install requests --break-system-packages")

API = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
PAUSE = 0.3
YEARS = 3
UA = {"User-Agent": "HI Grade pipeline hi@thehibalance.org"}

# Matched by substring against whatever keys CFPB returns, so a wording change degrades to a
# zero share rather than a crash. Every observed key is printed at the end regardless.
DISPUTE_MARKERS = ("disputes the facts", "acted appropriately", "can't verify", "cannot verify")


def fetch(cfpb_name, since):
    for attempt in range(3):
        try:
            time.sleep(PAUSE)
            r = requests.get(API, timeout=40, headers=UA, params={
                "company": cfpb_name,
                "size": 0,
                "no_aggs": "false",
                "date_received_min": since,
            })
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 503):
                time.sleep(5 * (attempt + 1))
                continue
            print(f"      HTTP {r.status_code}")
            return None
        except Exception as e:
            print(f"      {type(e).__name__}: {str(e)[:60]}")
            time.sleep(2)
    return None


def buckets(payload, field):
    agg = (payload or {}).get("aggregations") or {}
    node = agg.get(field)
    if not isinstance(node, dict):
        return []
    if "buckets" in node:
        return node["buckets"]
    inner = node.get(field)
    if isinstance(inner, dict) and "buckets" in inner:
        return inner["buckets"]
    return []


def shares(counter):
    total = sum(counter.values())
    if not total:
        return {}, 0
    return {k: v / total for k, v in counter.items()}, total


def spearman(xs, ys):
    """Rank correlation, average ranks for ties. Direction is the whole point here."""
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank(xs), rank(ys)
    mx, my = st.fmean(rx), st.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else 0.0


def crit_r(n):
    """Rough two-tailed 5% critical |r|. Enough to stop us over-reading a small sample."""
    return 2.0 / math.sqrt(n) if n > 4 else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="pipeline/data")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="cfpb_response_probe2.json")
    a = ap.parse_args()

    src = Path(a.data) / "cfpb" / "all_companies.json"
    if not src.exists():
        sys.exit(f"  no {src} — run this from the repo root, or pass --data")
    matched = json.load(open(src))
    since = (datetime.now() - timedelta(days=365 * YEARS)).strftime("%Y-%m-%d")

    print(f"CFPB probe v2 — {len(matched)} matched companies, since {since}\n")
    print(f"{'TKR':6} {'company':26} {'n':>8}  {'relief':>7} {'money':>6} "
          f"{'dispute':>8}  {'top product':28} {'U.1':>4}")
    print("─" * 104)

    out, skipped = {}, []
    resp_keys, pub_keys = Counter(), Counter()
    items = list(matched.items())
    if a.limit:
        items = items[:a.limit]

    for ticker, row in items:
        names = row.get("cfpb_names") or []
        if not names:
            skipped.append((ticker, "no accepted CFPB name"))
            continue

        resp, pub, prod, timely, total = Counter(), Counter(), Counter(), Counter(), 0
        for name in names[:8]:
            p = fetch(name, since)
            if p is None:
                continue
            hits = ((p.get("hits") or {}).get("total") or {})
            total += hits.get("value", 0) if isinstance(hits, dict) else (hits or 0)
            for b in buckets(p, "company_response"):
                resp[b["key"]] += b.get("doc_count", 0)
            for b in buckets(p, "company_public_response"):
                pub[b["key"]] += b.get("doc_count", 0)
            for b in buckets(p, "product"):
                prod[b["key"]] += b.get("doc_count", 0)
            for b in buckets(p, "timely"):
                timely[b["key"]] += b.get("doc_count", 0)

        if not resp:
            skipped.append((ticker, "no company_response buckets"))
            print(f"{ticker:6} {(row.get('company') or '')[:26]:26}  no company_response aggregation")
            continue

        resp_keys.update(resp.keys())
        pub_keys.update(pub.keys())

        rs, rn = shares(resp)
        ps, pn = shares(pub)
        ms, _ = shares(prod)
        ts, _ = shares(timely)

        relief = sum(v for k, v in rs.items() if "relief" in k.lower())
        monetary = sum(v for k, v in rs.items()
                       if "monetary" in k.lower() and "non-monetary" not in k.lower())
        explanation = sum(v for k, v in rs.items() if "explanation" in k.lower())
        dispute = sum(v for k, v in ps.items()
                      if any(m in k.lower() for m in DISPUTE_MARKERS))
        top_product = max(ms.items(), key=lambda x: x[1]) if ms else ("", 0.0)

        out[ticker] = {
            "company": row.get("company"),
            "total_in_window": total,
            "response_total": rn,
            "public_response_total": pn,
            "relief_rate": round(relief, 4),
            "monetary_relief_rate": round(monetary, 4),
            "explanation_only_rate": round(explanation, 4),
            "dispute_posture_rate": round(dispute, 4) if pn else None,
            "untimely_rate": round(1 - ts.get("Yes", 1.0), 4) if ts else None,
            "response_mix": {k: round(v, 4) for k, v in sorted(rs.items(), key=lambda x: -x[1])},
            "public_response_mix": {k: round(v, 4) for k, v in sorted(ps.items(), key=lambda x: -x[1])},
            "product_mix": {k: round(v, 4) for k, v in sorted(ms.items(), key=lambda x: -x[1])[:6]},
            "top_product": top_product[0],
            "top_product_share": round(top_product[1], 4),
            "published_U.1": row.get("U.1"),
            "per_10k_emp": row.get("per_10k_emp"),
            "probed": datetime.now().isoformat(),
        }
        print(f"{ticker:6} {(row.get('company') or '')[:26]:26} {rn:>8,}  "
              f"{relief*100:6.1f}% {monetary*100:5.1f}% "
              f"{(('%.1f%%' % (dispute*100)) if pn else 'none'):>8}  "
              f"{top_product[0][:26]:26} {str(row.get('U.1')):>4}")

    # ── The taxonomies, printed rather than assumed ──────────────────────────
    print("\n" + "═" * 104)
    print("company_response values CFPB returned:")
    for k in sorted(resp_keys):
        print(f"    {k}")
    print("\ncompany_public_response values CFPB returned:")
    for k in sorted(pub_keys) or ["    (none — the field came back empty for every company)"]:
        print(f"    {k}")
    if skipped:
        print(f"\n{len(skipped)} skipped:")
        for t, why in skipped:
            print(f"    {t:6} {why}")

    # ── Does each candidate discriminate? ────────────────────────────────────
    print("\n" + "─" * 104)
    for label, key in (("relief rate", "relief_rate"),
                       ("monetary relief rate", "monetary_relief_rate"),
                       ("dispute posture rate", "dispute_posture_rate"),
                       ("untimely rate", "untimely_rate")):
        vals = sorted(v[key] for v in out.values() if v.get(key) is not None)
        if len(vals) < 5:
            print(f"\n{label}: too few values to judge ({len(vals)})")
            continue
        p10, p50, p90 = vals[int(len(vals) * .10)], st.median(vals), vals[min(int(len(vals) * .90), len(vals) - 1)]
        spread = p90 - p10
        print(f"\n{label}:  n={len(vals)}  min {vals[0]*100:.1f}%  p10 {p10*100:.1f}%  "
              f"median {p50*100:.1f}%  p90 {p90*100:.1f}%  max {vals[-1]*100:.1f}%"
              f"   (p10–p90 spread {spread*100:.1f} pts)")
        if spread < 0.05:
            print("    ==> NOT DISCRIMINATING — cannot carry a ladder.")
        elif spread < 0.15:
            print("    ==> WEAK — worth disclosing, not worth a spec bump.")
        else:
            print("    ==> DISCRIMINATING.")

    # ── The question that matters: same ranking, or inverted? ────────────────
    pairs = [(v["published_U.1"], v["relief_rate"]) for v in out.values()
             if v.get("published_U.1") is not None and v.get("relief_rate") is not None]
    if len(pairs) >= 6:
        n = len(pairs)
        rho = spearman([x for x, _ in pairs], [y for _, y in pairs])
        thresh = crit_r(n)
        print("\n" + "═" * 104)
        print(f"published U.1  vs  relief rate:  Spearman rho = {rho:+.2f}  (n={n}, "
              f"|rho| > {thresh:.2f} to be meaningful at this n)")
        if abs(rho) < thresh:
            print("    ==> No reliable relationship. The two measures are close to independent:")
            print("        relief rate would be NEW information, not a restatement and not an")
            print("        inversion. That is the best case for adding it.")
        elif rho < 0:
            print("    ==> INVERTED. Companies the current ladder scores best give the least")
            print("        relief. Adopting relief rate as an ascending ladder would turn a large")
            print("        part of the published Customer Empathy ranking upside down. That is a")
            print("        change of construct and it needs an argument, not a patch.")
        else:
            print("    ==> AGREES with the current ladder. Relief rate would mostly restate it,")
            print("        which is a reason to prefer the ladder already shipped.")

    # Is the comparison even legitimate? Mixed product books are not comparable.
    tops = Counter(v["top_product"] for v in out.values() if v.get("top_product"))
    if tops:
        print("\nWhat each company's complaints are mostly about:")
        for k, c in tops.most_common():
            print(f"    {c:>3} companies   {k}")
        conc = [v["top_product_share"] for v in out.values() if v.get("top_product_share")]
        print(f"\n  median share held by a company's single largest product: "
              f"{st.median(conc)*100:.0f}%")
        if len(tops) > 1:
            print("  ==> Companies do not share a product mix, so a relief rate compared across")
            print("      all of them is partly comparing books of business. Any ladder built on")
            print("      it has to be within-product, which needs one query per company-product.")

    Path(a.out).write_text(json.dumps(out, indent=2))
    print(f"\nwrote {a.out}  ({len(out)} companies)")
    print("\nNothing in the pipeline changed.")


if __name__ == "__main__":
    main()
