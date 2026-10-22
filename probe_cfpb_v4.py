#!/usr/bin/env python3
"""Probe v4: the role rule, two pooled years, an evidence floor, and a zero check.

Read-only. Changes no pipeline file and writes no score. From the repo root:

    python3 probe_cfpb_v4.py --limit 5     # try it
    python3 probe_cfpb_v4.py               # ~350 queries, 8-10 min

WHAT v3 ESTABLISHED

CFPB's published per-product rate is a usable anchor, but only where the rated company plays
the same role as the population that sets the rate. Of 22 companies appearing in credit
reporting, 21 are furnishers answering disputes about data they reported, and they sit between
-52.5 and -20. The single company that IS a credit bureau is the only one above the line, at
+11.3. Excluding the two role-mismatched categories moved the distribution from shifted
(median -12.7, 81% below) to centred and wide (median -5.8, 61% below).

FOUR CHANGES

**1. The role rule keys off SIC, not a hardcoded category list.** SIC 732x is
"Services-Consumer Credit Reporting, Collection Agencies" — precisely the two categories at
issue, and in this universe it is Equifax alone. A blanket category exclusion would have
thrown away Equifax's best evidence, which is the one measurement proving the rule.

**2. Two calendar years pooled, each compared to its own published table.** The delta is
computed per year against that year's benchmark, then weighted by the company's own complaint
count in that year. No approximation: CFPB publishes percentages per product but not volumes
per product, so weighting the two published tables together would have required a guess. This
avoids it entirely.

**3. The evidence floor rises to 100, matching MIN_COMPLAINTS.** v3 read cells of 50-56
complaints, where one complaint moves the rate two points against a benchmark rounded to whole
points. The project already holds that a near-zero count is not evidence of good conduct; the
same applies to placing a company against a benchmark. Companies that cannot clear the floor
get no CFPB signal rather than a noisy one. Some will drop out. That is the honest outcome, and
pooling two years gives more of them a chance to clear it.

**4. Every 0.0% cell is verified down a second path.** v3 reported Affirm at 0.0% relief across
2,231 complaints, Robinhood 0.0% across 861, Upstart 0.0% across 369. If real, that is the
strongest finding in the set. If it is an aggregation-parsing bug, it is the same class of
error this project keeps finding in its own code. So each zero is re-queried with an explicit
company_response filter and confirmed independently before it is believed.

Benchmarks transcribed from Table 1, p.18:
  CY2024 — files.consumerfinance.gov/f/documents/cfpb_cr-annual-report_2025-05.pdf
           (cover: May 2025; 2,829,400 complaints sent to companies; 99.7% timely)
  CY2023 — files.consumerfinance.gov/f/documents/cfpb_cr-annual-report_2023-03.pdf
           (cover: MARCH 2024 despite the filename; 1,348,200 sent; 99.6% timely)

It decides nothing. It reports.
"""
import argparse
import json
import statistics as st
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("  pip install requests --break-system-packages")

API = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
PAUSE = 0.3
UA = {"User-Agent": "HI Grade pipeline hi@thehibalance.org"}
YEARS = (2023, 2024)
MIN_CELL = 100                      # pooled across years; matches cfpb_pipeline.MIN_COMPLAINTS

# (monetary %, non-monetary %, explanation %). "<1" transcribed as 0.5.
BENCHMARK = {
    2024: {"All": (0.8, 48, 46), "Credit or consumer reporting": (0.5, 52, 42),
           "Debt collection": (0.5, 27, 67), "Credit card": (13, 25, 58),
           "Checking or savings": (14, 7, 75), "Mortgage": (2, 3, 91),
           "Money transfer/virtual currency": (8, 4, 82), "Student loan": (1, 2, 89),
           "Vehicle loan or lease": (3, 6, 84), "Personal loan": (5, 6, 84),
           "Prepaid card": (26, 5, 61), "Debt or credit management": (4, 10, 69),
           "Payday loan": (4, 2, 83), "Title loan": (1, 4, 91), "Deposit advance": (6, 1, 87)},
    2023: {"All": (1.5, 40, 53), "Credit or consumer reporting": (0.5, 47, 48),
           "Debt collection": (0.5, 15, 80), "Credit card": (15, 20, 60),
           "Checking or savings": (14, 6, 76), "Mortgage": (2, 3, 92),
           "Money transfer/virtual currency": (7, 5, 84), "Student loan": (2, 9, 79),
           "Vehicle loan or lease": (2, 5, 89), "Personal loan": (5, 5, 85),
           "Prepaid card": (24, 5, 65), "Debt or credit management": (4, 20, 71),
           "Payday loan": (2, 2, 87), "Title loan": (2, 6, 74), "Deposit advance": (7, 4, 80)},
}

PRODUCT_MAP = {
    "Checking or savings account": "Checking or savings",
    "Credit reporting or other personal consumer reports": "Credit or consumer reporting",
    "Credit reporting, credit repair services, or other personal consumer reports":
        "Credit or consumer reporting",
    "Credit card": "Credit card", "Credit card or prepaid card": "Credit card",
    "Mortgage": "Mortgage", "Debt collection": "Debt collection",
    "Money transfer, virtual currency, or money service": "Money transfer/virtual currency",
    "Student loan": "Student loan", "Vehicle loan or lease": "Vehicle loan or lease",
    "Debt or credit management": "Debt or credit management", "Prepaid card": "Prepaid card",
    # The API lumps four of the report's rows into one. No clean benchmark; excluded.
    "Payday loan, title loan, personal loan, or advance loan": None,
    "Payday loan, title loan, or personal loan": None,
}

# Categories where the benchmark population plays a role most rated companies do not.
ROLE_GATED = {"Credit or consumer reporting", "Debt collection"}
# SIC 7320/7323 — "Services-Consumer Credit Reporting, Collection Agencies".
BUREAU_SIC_PREFIX = "732"
RELIEF_RESPONSES = ["Closed with monetary relief", "Closed with non-monetary relief"]


def get(params, tries=3):
    for i in range(tries):
        try:
            time.sleep(PAUSE)
            r = requests.get(API, params=params, timeout=40, headers=UA)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 503):
                time.sleep(5 * (i + 1))
                continue
            return None
        except Exception:
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


def total_of(payload):
    hits = ((payload or {}).get("hits") or {}).get("total") or {}
    return hits.get("value", 0) if isinstance(hits, dict) else (hits or 0)


def query(name, year, product=None, response=None):
    p = {"company": name, "size": 0, "no_aggs": "false",
         "date_received_min": f"{year}-01-01", "date_received_max": f"{year}-12-31"}
    if product:
        p["product"] = product
    if response:
        p["company_response"] = response
    return get(p)


def verify_zero(names, year, api_product):
    """Independent confirmation that a 0.0% relief cell really is zero.

    Asks CFPB directly for the count of relief-closed complaints instead of deriving it from
    an aggregation we parsed ourselves. A parsing bug and a real zero look identical until
    something asks the question a different way.
    """
    found = 0
    for n in names[:8]:
        for resp in RELIEF_RESPONSES:
            p = query(n, year, api_product, resp)
            if p is None:
                return None            # could not verify; do not claim either way
            found += total_of(p)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="pipeline/data")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="cfpb_v4_probe.json")
    a = ap.parse_args()

    base = Path(a.data)
    src = base / "cfpb" / "all_companies.json"
    if not src.exists():
        sys.exit(f"  no {src} — run this from the repo root, or pass --data")
    matched = json.load(open(src))

    sic = {}
    try:
        for r in json.load(open(base / "scores" / "all_scores.json")):
            t = (r.get("ticker") or "").upper()
            if t and r.get("sic"):
                sic[t] = str(r["sic"])
    except (OSError, ValueError):
        print("  ! could not read all_scores.json — no SIC, so the role rule cannot run")

    print(f"CFPB probe v4 — {'+'.join(map(str, YEARS))} pooled, role rule by SIC, "
          f"floor {MIN_CELL}\n")

    items = list(matched.items())
    if a.limit:
        items = items[:a.limit]

    out, dropped, zero_rows, unmapped = {}, [], [], Counter()
    for ticker, row in items:
        names = row.get("cfpb_names") or []
        if not names:
            continue
        is_bureau = sic.get(ticker, "").startswith(BUREAU_SIC_PREFIX)

        # Volumes per API product per year, then GROUPED BY BENCHMARK ROW.
        #
        # CFPB renamed products over time: "Credit card or prepaid card" is the legacy name and
        # "Credit card" the current one, so both appear across a two-year window and both map to
        # the same benchmark row. Treating them as separate cells listed one product twice per
        # company and, worse, split a company's volume in two — so a small issuer could fail the
        # evidence floor on both halves while clearing it combined.
        vol = defaultdict(lambda: defaultdict(int))
        for y in YEARS:
            for n in names[:8]:
                p = query(n, y)
                if not p:
                    continue
                for b in buckets(p, "product"):
                    vol[b["key"]][y] += b.get("doc_count", 0)
        if not vol:
            continue

        grouped = defaultdict(lambda: defaultdict(int))   # bench key -> api product -> total
        for api_product, per_year in vol.items():
            if api_product not in PRODUCT_MAP:
                unmapped[api_product] += sum(per_year.values())
                continue
            key = PRODUCT_MAP[api_product]
            if key is None:
                continue
            grouped[key][api_product] = sum(per_year.values())

        cells, skipped_role, below_floor = [], [], []
        for key, members in sorted(grouped.items(), key=lambda x: -sum(x[1].values())):
            key_total = sum(members.values())
            if key in ROLE_GATED and not is_bureau:
                skipped_role.append((key, key_total))
                continue
            if key_total < MIN_CELL:
                below_floor.append((key, key_total))
                continue

            # Delta per year against that year's own table; weight by the company's volume.
            yearly, pooled_n = [], 0
            for y in YEARS:
                if key not in BENCHMARK[y]:
                    continue
                resp = Counter()
                cell_n = 0
                for api_product in members:
                    for n in names[:8]:
                        p = query(n, y, api_product)
                        if not p:
                            continue
                        cell_n += total_of(p)
                        for b in buckets(p, "company_response"):
                            resp[b["key"]] += b.get("doc_count", 0)
                tot = sum(resp.values())
                if not tot:
                    continue
                relief = sum(v for k, v in resp.items() if "relief" in k.lower()) / tot * 100
                b_mon, b_non, _ = BENCHMARK[y][key]
                yearly.append({"year": y, "n": cell_n, "relief": round(relief, 1),
                               "benchmark": b_mon + b_non,
                               "delta": round(relief - (b_mon + b_non), 1)})
                pooled_n += cell_n

            if not yearly or pooled_n < MIN_CELL:
                continue
            delta = sum(x["delta"] * x["n"] for x in yearly) / pooled_n
            relief_p = sum(x["relief"] * x["n"] for x in yearly) / pooled_n

            cell = {"product": key, "n": pooled_n, "relief": round(relief_p, 1),
                    "delta": round(delta, 1), "by_year": yearly}

            if relief_p == 0.0:
                checked = 0
                ok = True
                for x in yearly:
                    v = verify_zero(names, x["year"], api_product)
                    if v is None:
                        ok = False
                        break
                    checked += v
                cell["zero_verified"] = ok
                cell["zero_check_count"] = checked if ok else None
                zero_rows.append((ticker, key, pooled_n, checked if ok else "unverified"))
            cells.append(cell)

        if not cells:
            # State the reason that was actually measured. Saying "role-gated only" whenever
            # anything was gated asserted a cause nothing had established — which is the bug
            # class this whole project keeps finding.
            bits = []
            if skipped_role:
                bits.append("role-gated: " + ", ".join(
                    f"{k} {n:,}" for k, n in skipped_role))
            if below_floor:
                bits.append("below floor: " + ", ".join(
                    f"{k} {n:,}" for k, n in sorted(below_floor, key=lambda x: -x[1])[:3]))
            if not bits:
                bits.append("no product mapped to a benchmark row")
            dropped.append((ticker, row.get("company"), "; ".join(bits)))
            continue

        wn = sum(c["n"] for c in cells)
        wdelta = sum(c["delta"] * c["n"] for c in cells) / wn
        out[ticker] = {"company": row.get("company"), "sic": sic.get(ticker),
                       "is_bureau": is_bureau, "benchmarked_n": wn,
                       "weighted_delta": round(wdelta, 1), "cells": cells,
                       "role_gated_out": skipped_role,
                       "published_U.1": row.get("U.1"), "probed": datetime.now().isoformat()}
        flag = "  [bureau: credit reporting & debt collection scored]" if is_bureau else ""
        print(f"{ticker:6} {(row.get('company') or '')[:24]:24} n={wn:>7,}  "
              f"delta {wdelta:+6.1f}   was U.1 {row.get('U.1')}{flag}")
        for c in cells:
            z = ""
            if c.get("zero_verified") is True:
                z = f"   [zero confirmed: {c['zero_check_count']} relief complaints]"
            elif c.get("zero_verified") is False:
                z = "   [zero NOT verified — treat with suspicion]"
            print(f"       {c['product'][:30]:30} n={c['n']:>7,}  relief {c['relief']:5.1f}%"
                  f"  {c['delta']:+6.1f} pts{z}")

    print("\n" + "═" * 92)
    if unmapped:
        print("unmapped API product names — fix PRODUCT_MAP before trusting this run:")
        for k, v in unmapped.most_common():
            print(f"    {v:>8,}  {k}")

    if zero_rows:
        print("\nZero-relief cells, checked down a second path:")
        for t, p, n, c in zero_rows:
            mark = "CONFIRMED" if c == 0 else ("UNVERIFIED" if c == "unverified"
                                               else f"CONTRADICTED — found {c}")
            print(f"    {t:6} {p[:30]:30} {n:>7,} complaints   {mark}")

    if dropped:
        print(f"\n{len(dropped)} companies get no CFPB signal under the floor of {MIN_CELL}:")
        for t, c, why in dropped:
            print(f"    {t:6} {(c or '')[:26]:26} {why}")
        print("    Consistent with v1.5.0: absence of evidence is not evidence of good conduct.")

    ds = sorted(v["weighted_delta"] for v in out.values())
    if len(ds) >= 6:
        p10, p50, p90 = ds[int(len(ds)*.10)], st.median(ds), ds[min(int(len(ds)*.90), len(ds)-1)]
        print(f"\nweighted delta, role-matched:  n={len(ds)}")
        print(f"    min {ds[0]:+.1f}  p10 {p10:+.1f}  median {p50:+.1f}  p90 {p90:+.1f}  "
              f"max {ds[-1]:+.1f}")
        print(f"    p10-p90 spread {p90-p10:.1f} pts   stdev {st.pstdev(ds):.1f}   "
              f"below benchmark {sum(1 for d in ds if d < 0)}/{len(ds)}")
        shifted, narrow = abs(p50) > 10, (p90 - p10) < 15
        print()
        if shifted and narrow:
            print("    ==> SHIFTED AND NARROW. Measuring 'is a large public company'. Disclose only.")
        elif narrow:
            print("    ==> CENTRED BUT NARROW. Little separation. Disclose, don't score.")
        elif shifted:
            print("    ==> SHIFTED BUT WIDE. Re-centring would be renormalization. Careful.")
        else:
            print("    ==> CENTRED AND WIDE. The published rate is a usable neutral point.")

    byp = defaultdict(list)
    for v in out.values():
        for c in v["cells"]:
            byp[c["product"]].append(c["delta"])
    if byp:
        print(f"\n{'product':34} {'n':>3} {'median':>9} {'min':>8} {'max':>8}")
        print("─" * 68)
        for p, xs in sorted(byp.items(), key=lambda x: -len(x[1])):
            xs = sorted(xs)
            if len(xs) < 2:
                print(f"{p[:34]:34} {len(xs):>3}   (single: {xs[0]:+.1f})")
                continue
            print(f"{p[:34]:34} {len(xs):>3} {st.median(xs):>+9.1f} {xs[0]:>+8.1f} {xs[-1]:>+8.1f}")

    Path(a.out).write_text(json.dumps(out, indent=2))
    print(f"\nwrote {a.out}  ({len(out)} companies scored, {len(dropped)} dropped)")
    print("\nNothing in the pipeline changed.")


if __name__ == "__main__":
    main()
