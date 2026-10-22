#!/usr/bin/env python3
"""Probe v3: each company against CFPB's own published rate for its product.

Read-only. Changes no pipeline file and writes no score. From the repo root:

    python3 probe_cfpb_benchmark.py --limit 6      # try it
    python3 probe_cfpb_benchmark.py                # full run, ~200-300 queries, ~5 min

WHAT CHANGED SINCE v2

CFPB publishes the benchmark. Table 1, "How companies have responded to consumer complaints",
page 18 of the Consumer Response Annual Report to Congress — and page 18 of the prior year's
too, so it is a recurring series rather than a one-off. Every product category, every response
outcome, as a percentage. That is the anchor U.1 never had: the neutral point is a published
federal figure, not a constant we chose.

  CY2024 report: 2,829,400 complaints, 99.7% timely
  CY2023 report: 1,348,200 complaints, 99.6% timely

TWO CORRECTIONS TO WHAT v2 CONCLUDED

**The denominator is all complaints, not closed ones.** I said to divide by closed. Wrong for
this purpose: CFPB's own columns sum to 100% across monetary, non-monetary, explanation,
administrative, still-reviewing and untimely. Their denominator is every complaint in the
window, so ours must be too or the comparison is rigged in our favour. The concern that
prompted it mostly dissolves anyway — querying a CLOSED calendar year means almost nothing is
still in progress.

**The window has to match.** v2 used a trailing three years against a benchmark covering one
calendar year, and CY2024's volume was more than double CY2023's. This queries the exact
calendar year the report covers.

WHAT THIS MEASURES

For every company-product cell with enough complaints, the gap in percentage points between
the company's relief rate and CFPB's published rate for that product. Then the company-level
figure, volume-weighted across its products.

The mix objection from v2 disappears here: nothing is compared across products, only against
each product's own published number.

THE FAILURE MODE TO WATCH, AND IT IS A REAL ONE

CFPB's benchmark covers every company it supervises — thousands of small servicers, debt
buyers and fintechs, not just large public issuers. Our 57 are S&P 500 members. If large public
companies systematically differ from that universe, the deltas will be SHIFTED (nearly everyone
below, or above) and NARROW, which measures "is a big public company" rather than conduct. A
usable ladder needs the deltas centred and spread.

This probe reports the shape of that distribution before anyone builds anything on it. If the
deltas come back shifted and narrow, the honest outcome is disclosure only, and the finding
gets written up as a dead end.

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

# ── CFPB Consumer Response Annual Report, Table 1, p.18 ──────────────────────
# (monetary %, non-monetary %, explanation %). "<1" transcribed as 0.5.
# 2024: files.consumerfinance.gov/f/documents/cfpb_cr-annual-report_2025-05.pdf
# 2023: files.consumerfinance.gov/f/documents/cfpb_cr-annual-report_2023-03.pdf
BENCHMARK = {
    2024: {
        "All":                            (0.8, 48, 46),
        "Credit or consumer reporting":   (0.5, 52, 42),
        "Debt collection":                (0.5, 27, 67),
        "Credit card":                    (13,  25, 58),
        "Checking or savings":            (14,   7, 75),
        "Mortgage":                       (2,    3, 91),
        "Money transfer/virtual currency":(8,    4, 82),
        "Student loan":                   (1,    2, 89),
        "Vehicle loan or lease":          (3,    6, 84),
        "Personal loan":                  (5,    6, 84),
        "Prepaid card":                   (26,   5, 61),
        "Debt or credit management":      (4,   10, 69),
        "Payday loan":                    (4,    2, 83),
        "Title loan":                     (1,    4, 91),
        "Deposit advance":                (6,    1, 87),
    },
    2023: {
        "All":                            (1.5, 40, 53),
        "Credit or consumer reporting":   (0.5, 47, 48),
        "Debt collection":                (0.5, 15, 80),
        "Credit card":                    (15,  20, 60),
        "Checking or savings":            (14,   6, 76),
        "Mortgage":                       (2,    3, 92),
        "Money transfer/virtual currency":(7,    5, 84),
        "Student loan":                   (2,    9, 79),
        "Vehicle loan or lease":          (2,    5, 89),
        "Personal loan":                  (5,    5, 85),
        "Prepaid card":                   (24,   5, 65),
        "Debt or credit management":      (4,   20, 71),
        "Payday loan":                    (2,    2, 87),
        "Title loan":                     (2,    6, 74),
        "Deposit advance":                (7,    4, 80),
    },
}

# The API's product names are not the report's. Mapped explicitly; anything unmapped is
# reported rather than silently dropped.
PRODUCT_MAP = {
    "Checking or savings account": "Checking or savings",
    "Credit reporting or other personal consumer reports": "Credit or consumer reporting",
    "Credit reporting, credit repair services, or other personal consumer reports":
        "Credit or consumer reporting",
    "Credit card": "Credit card",
    "Credit card or prepaid card": "Credit card",
    "Mortgage": "Mortgage",
    "Debt collection": "Debt collection",
    "Money transfer, virtual currency, or money service": "Money transfer/virtual currency",
    "Student loan": "Student loan",
    "Vehicle loan or lease": "Vehicle loan or lease",
    "Debt or credit management": "Debt or credit management",
    "Prepaid card": "Prepaid card",
    # The API lumps four of the report's rows into one. No clean benchmark exists for the
    # combination, so it is measured and excluded from scoring rather than approximated.
    "Payday loan, title loan, personal loan, or advance loan": None,
    "Payday loan, title loan, or personal loan": None,
}

MIN_CELL = 50          # per company-product; below this CFPB's whole-point rounding dominates


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


def query(name, year, product=None):
    p = {"company": name, "size": 0, "no_aggs": "false",
         "date_received_min": f"{year}-01-01", "date_received_max": f"{year}-12-31"}
    if product:
        p["product"] = product
    return get(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="pipeline/data")
    ap.add_argument("--year", type=int, default=2024, choices=[2023, 2024])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="cfpb_benchmark_probe.json")
    a = ap.parse_args()

    src = Path(a.data) / "cfpb" / "all_companies.json"
    if not src.exists():
        sys.exit(f"  no {src} — run this from the repo root, or pass --data")
    matched = json.load(open(src))
    bench = BENCHMARK[a.year]

    print(f"CFPB benchmark probe — calendar {a.year}, matching the report's own window\n")
    print(f"Benchmark: Consumer Response Annual Report Table 1, p.18 ({a.year})")
    print(f"Denominator: all complaints in the window, as CFPB's own columns use.\n")

    items = list(matched.items())
    if a.limit:
        items = items[:a.limit]

    out, unmapped, no_bench = {}, Counter(), Counter()
    for ticker, row in items:
        names = row.get("cfpb_names") or []
        if not names:
            continue

        # Step 1: what products, and how many, in this calendar year.
        prod = Counter()
        year_total = 0
        for n in names[:8]:
            p = query(n, a.year)
            if not p:
                continue
            hits = ((p.get("hits") or {}).get("total") or {})
            year_total += hits.get("value", 0) if isinstance(hits, dict) else (hits or 0)
            for b in buckets(p, "product"):
                prod[b["key"]] += b.get("doc_count", 0)

        if not year_total:
            continue

        # Step 2: one query per product with enough volume to read.
        cells = []
        for api_product, count in prod.most_common():
            if count < MIN_CELL:
                continue
            if api_product not in PRODUCT_MAP:
                unmapped[api_product] += count
                continue
            key = PRODUCT_MAP[api_product]
            if key is None:
                no_bench[api_product] += count
                continue
            if key not in bench:
                no_bench[api_product] += count
                continue

            resp = Counter()
            cell_n = 0
            for n in names[:8]:
                p = query(n, a.year, api_product)
                if not p:
                    continue
                hits = ((p.get("hits") or {}).get("total") or {})
                cell_n += hits.get("value", 0) if isinstance(hits, dict) else (hits or 0)
                for b in buckets(p, "company_response"):
                    resp[b["key"]] += b.get("doc_count", 0)
            if not cell_n or not resp:
                continue

            tot = sum(resp.values())
            mon = sum(v for k, v in resp.items()
                      if "monetary" in k.lower() and "non-monetary" not in k.lower()) / tot * 100
            non = sum(v for k, v in resp.items() if "non-monetary" in k.lower()) / tot * 100
            relief = mon + non
            b_mon, b_non, _ = bench[key]
            b_relief = b_mon + b_non

            cells.append({
                "api_product": api_product, "benchmark_product": key, "n": cell_n,
                "relief": round(relief, 1), "monetary": round(mon, 1),
                "benchmark_relief": b_relief, "benchmark_monetary": b_mon,
                "delta": round(relief - b_relief, 1),
                "delta_monetary": round(mon - b_mon, 1),
            })

        if not cells:
            continue

        wn = sum(c["n"] for c in cells)
        wdelta = sum(c["delta"] * c["n"] for c in cells) / wn
        out[ticker] = {
            "company": row.get("company"), "year": a.year,
            "complaints_in_year": year_total, "cells": cells,
            "benchmarked_n": wn,
            "weighted_delta": round(wdelta, 1),
            "published_U.1": row.get("U.1"),
            "probed": datetime.now().isoformat(),
        }
        head = f"{ticker:6} {(row.get('company') or '')[:24]:24} {year_total:>8,} in {a.year}"
        print(f"{head}   weighted delta {wdelta:+6.1f} pts   was U.1 {row.get('U.1')}")
        for c in cells:
            print(f"       {c['benchmark_product'][:30]:30} n={c['n']:>7,}  "
                  f"relief {c['relief']:5.1f}%  vs CFPB {c['benchmark_relief']:5.1f}%  "
                  f"{c['delta']:+6.1f} pts")

    # ── Is the delta usable, or does it just say "large public company"? ─────
    print("\n" + "═" * 92)
    if unmapped:
        print("API product names with no mapping (fix PRODUCT_MAP before trusting the run):")
        for k, v in unmapped.most_common():
            print(f"    {v:>8,}  {k}")
    if no_bench:
        print("\nProducts deliberately excluded — the API lumps together rows the report splits:")
        for k, v in no_bench.most_common():
            print(f"    {v:>8,}  {k}")

    deltas = [v["weighted_delta"] for v in out.values()]
    if len(deltas) >= 6:
        ds = sorted(deltas)
        p10, p50, p90 = ds[int(len(ds)*.10)], st.median(ds), ds[min(int(len(ds)*.90), len(ds)-1)]
        below = sum(1 for d in ds if d < 0)
        print(f"\nweighted delta vs benchmark:  n={len(ds)}")
        print(f"    min {ds[0]:+.1f}   p10 {p10:+.1f}   median {p50:+.1f}   "
              f"p90 {p90:+.1f}   max {ds[-1]:+.1f}")
        print(f"    spread p10-p90: {p90-p10:.1f} pts   stdev {st.pstdev(ds):.1f}")
        print(f"    below benchmark: {below} of {len(ds)}  ({below/len(ds)*100:.0f}%)")

        shifted = abs(p50) > 10
        narrow = (p90 - p10) < 15
        print()
        if shifted and narrow:
            print("    ==> SHIFTED AND NARROW. Nearly everyone sits the same distance from the")
            print("        benchmark. This is measuring 'is a large public company', not conduct.")
            print("        Disclosure only. Write it up as a dead end.")
        elif narrow:
            print("    ==> CENTRED BUT NARROW. Little to separate companies. Disclose, don't score.")
        elif shifted:
            print("    ==> SHIFTED BUT WIDE. Real separation, but the benchmark's universe differs")
            print("        from ours, so the neutral point is not where CFPB puts it. A ladder")
            print("        would need its own centre — which is renormalization again. Careful.")
        else:
            print("    ==> CENTRED AND WIDE. The published rate is a usable neutral point and")
            print("        companies separate around it. This is the case for a scored ladder.")

    # Per-product, so one product's peculiarity is not read as a system-wide result.
    byp = defaultdict(list)
    for v in out.values():
        for c in v["cells"]:
            byp[c["benchmark_product"]].append(c["delta"])
    if byp:
        print(f"\n{'product':34} {'n':>3} {'median delta':>13} {'min':>8} {'max':>8}")
        print("─" * 72)
        for p, xs in sorted(byp.items(), key=lambda x: -len(x[1])):
            xs = sorted(xs)
            if len(xs) < 2:
                print(f"{p[:34]:34} {len(xs):>3}   (single company: {xs[0]:+.1f})")
                continue
            print(f"{p[:34]:34} {len(xs):>3} {st.median(xs):>+12.1f} "
                  f"{xs[0]:>+8.1f} {xs[-1]:>+8.1f}")

    Path(a.out).write_text(json.dumps(out, indent=2))
    print(f"\nwrote {a.out}  ({len(out)} companies)")
    print("\nNothing in the pipeline changed.")


if __name__ == "__main__":
    main()
