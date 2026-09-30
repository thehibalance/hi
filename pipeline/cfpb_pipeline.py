#!/usr/bin/env python3
"""CFPB consumer complaints, matched to CFPB's own registered company names.

Why this exists: the previous collector queried CFPB with our company name and got 0 complaints
for nearly every company — including Bank of America (really 54,729 over three years) — and
"0 complaints" was scored as a clean record. v1.4.0 withdrew every CFPB score. This collector
earns them back:

  1. Ask CFPB which companies it knows under that name (`_suggest_company`).
  2. Keep a suggestion only when it IS the company: same core name, or the core name plus a
     banking word ("wells fargo bank"). "APPLE FINANCIAL HOLDINGS" is not Apple Inc.
  3. Count complaints filed against each accepted name (`company=` exact filter).
  4. Score two different things from those complaints, described below.

No match means no data. It never scores an absence as good.

═══════════════════════════════════════════════════════════════════════════════════════════
TWO MEASURES, TWO CONSTRUCTS (v1.10.0)
═══════════════════════════════════════════════════════════════════════════════════════════

**U.1 Customer Empathy — how the company resolves complaints, against CFPB's published rate.**

Dividing complaints by SEC headcount, as this file did through v1.9.x, is not a rate of
anything. Headcount is a proxy for company size, not for consumer relationships, and the
ranking said so: Tesla held the best Customer Empathy score in the entire CFPB set because
134,785 people who build cars diluted 473 auto-loan complaints, while Equifax sat on the floor
with 15,000 employees and four million complaints from people who are not its customers at all.

CFPB publishes the honest comparison itself. The Consumer Response Annual Report to Congress,
Table 1 ("How companies have responded to consumer complaints", p.18), gives the share of
complaints closed with monetary relief, non-monetary relief and explanation **for every product
category**, every year. So a company can be compared to the national rate for the product it
actually sells. The neutral point is a published federal figure rather than a constant we chose.

Measured across 31 companies before adoption; see FINDING-u1-role-matched-benchmark.md.

**M.1 Pricing Ethics keeps the volume ladder, unchanged.** Complaint volume did not stop being
meaningful — it stopped being *Customer Empathy*. M.1's numbers are byte-identical to v1.9.x.

═══════════════════════════════════════════════════════════════════════════════════════════
THE ROLE RULE
═══════════════════════════════════════════════════════════════════════════════════════════

A published rate only describes a company that does what the rated population does.

CFPB's credit-reporting benchmark is set by the credit bureaus, who resolve disputes by
correcting the file — 52.5% relief in CY2024, almost all non-monetary. A bank appearing in that
category is the *furnisher*, not the bureau, and answers with an explanation. Of 22 companies
measured in credit reporting, 21 were furnishers sitting between −52.5 and −20 points below
benchmark. The single company that is actually a credit bureau was the only one above it.

So credit reporting and debt collection are scored only for SIC 732x, "Services-Consumer Credit
Reporting, Collection Agencies", and gated out for everyone else. Excluding the categories
outright would have discarded the one measurement that proves the rule.

Usage:
  python3 cfpb_pipeline.py --limit 20 --dry-run   # try it on 20 companies, write nothing
  python3 cfpb_pipeline.py                        # full run, U.1 from the volume ladder
  python3 cfpb_pipeline.py --u1 benchmark         # full run, U.1 from the benchmark delta
"""
import argparse
import json
import math
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("pip install requests --break-system-packages")

API = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1"
YEARS = 3
PAUSE = 0.3
CACHE_DAYS = 7

# Words that may follow a company's core name and still be the same company.
# "financial" is deliberately absent: APPLE FINANCIAL HOLDINGS is not Apple Inc.
CHARTER = {"bank", "national", "association", "na", "n.a", "usa"}
CHARTER_REQ = {"bank", "national", "association", "na", "n.a"}
MIN_COMPLAINTS = 100          # below this there is no evidence either way, not a good record
ANCHOR = 30.0                 # complaints per 10k employees scoring 85 (M.1 ladder)
PER_DECADE = 15               # points lost per 10x increase in the rate (M.1 ladder)
SUFFIXES = ["incorporated", "corporation", "company", "holdings", "holding", "group", "inc", "corp",
            "co", "llc", "lp", "ltd", "plc", "sa", "nv", "ag", "se", "national association", "n a"]

# ── CFPB Consumer Response Annual Report, Table 1, p.18 ────────────────────────────────────
# (monetary %, non-monetary %, explanation %). "<1" transcribed as 0.5.
# CY2024: files.consumerfinance.gov/f/documents/cfpb_cr-annual-report_2025-05.pdf
#         cover May 2025; 2,829,400 complaints sent to companies; 99.7% timely
# CY2023: files.consumerfinance.gov/f/documents/cfpb_cr-annual-report_2023-03.pdf
#         cover MARCH 2024 despite the filename; 1,348,200 sent; 99.6% timely
#
# Re-derive on purpose when CFPB publishes, with a dated note. Never automatically: a company's
# score must not move because a table was refreshed under it without anyone looking.
BENCHMARK = {
    2024: {"Credit or consumer reporting": (0.5, 52, 42), "Debt collection": (0.5, 27, 67),
           "Credit card": (13, 25, 58), "Checking or savings": (14, 7, 75),
           "Mortgage": (2, 3, 91), "Money transfer/virtual currency": (8, 4, 82),
           "Student loan": (1, 2, 89), "Vehicle loan or lease": (3, 6, 84),
           "Personal loan": (5, 6, 84), "Prepaid card": (26, 5, 61),
           "Debt or credit management": (4, 10, 69), "Payday loan": (4, 2, 83),
           "Title loan": (1, 4, 91), "Deposit advance": (6, 1, 87)},
    2023: {"Credit or consumer reporting": (0.5, 47, 48), "Debt collection": (0.5, 15, 80),
           "Credit card": (15, 20, 60), "Checking or savings": (14, 6, 76),
           "Mortgage": (2, 3, 92), "Money transfer/virtual currency": (7, 5, 84),
           "Student loan": (2, 9, 79), "Vehicle loan or lease": (2, 5, 89),
           "Personal loan": (5, 5, 85), "Prepaid card": (24, 5, 65),
           "Debt or credit management": (4, 20, 71), "Payday loan": (2, 2, 87),
           "Title loan": (2, 6, 74), "Deposit advance": (7, 4, 80)},
}
BENCH_YEARS = (2023, 2024)

# CFPB renamed products mid-window: "Credit card or prepaid card" is the legacy name and
# "Credit card" the current one. Both map to the same benchmark row, and both must land in the
# same cell — treating them separately splits a company's volume against the evidence floor.
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
    # The API lumps four of the report's rows into one. No clean benchmark exists for the
    # combination, so it is excluded rather than approximated.
    "Payday loan, title loan, personal loan, or advance loan": None,
    "Payday loan, title loan, or personal loan": None,
}
ROLE_GATED = {"Credit or consumer reporting", "Debt collection"}
BUREAU_SIC_PREFIX = "732"     # Services-Consumer Credit Reporting, Collection Agencies

# Evidence floor for a benchmarked cell. The justification is resolution, not precedent: at
# n=100 one complaint moves the rate one point, and the published benchmark is rounded to one
# point. Below that we would be measuring finer than the thing we compare against.
MIN_CELL = 100
BENCH_CACHE_DAYS = 90         # a completed calendar year does not change; refresh rarely

U1_NEUTRAL = 50.0             # a company at its product's published rate scores here
U1_FLOOR, U1_CAP = 25.0, 85.0
# Slope: one percentage point of delta = one point of score. EDITORIAL, and the only editorial
# constant left in U.1 — the anchor is CFPB's published figure. Chosen as 1:1 because it is the
# least tunable option available and the easiest for a reader to check by hand.
U1_POINTS_PER_PCT = 1.0


def core(name):
    """Normalize a company name to its core: 'BANK OF AMERICA CORP /DE/' -> 'bank of america'."""
    n = (name or "").lower()
    n = re.sub(r"/[a-z]{2,3}/?(?=\s|$)", " ", n)     # SEC state markers: /DE/, /MN
    n = n.replace("&", " and ")
    n = re.sub(r"[^a-z0-9 ]+", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    changed = True
    while changed:
        changed = False
        for s in SUFFIXES:
            if n.endswith(" " + s):
                n, changed = n[: -len(s) - 1].strip(), True
        if n.endswith(" and"):            # "Wells Fargo & Company" -> "wells fargo"
            n, changed = n[:-4].strip(), True
    return n


def cores(company_name):
    """Core name, plus the form without a trailing 'financial'/'services' — Ally Financial's
    complaints are filed against ALLY BANK, Discover Financial Services' against DISCOVER BANK."""
    c = core(company_name)
    out = [c]
    trimmed = c
    for tail in ("services", "service", "financial"):
        if trimmed.endswith(" " + tail):
            trimmed = trimmed[: -len(tail) - 1].strip()
    if trimmed and trimmed != c:
        out.append(trimmed)
    return out


def accepts(company_name, suggestion):
    """Is this CFPB-registered name the same company?

    Exact core match, or the core plus bank-charter words only. The looser "core + any banking
    word" rule attributed Westlake Services (a California auto lender) to Westlake Corp
    (chemicals) — 9,491 complaints — and Southern Trust Mortgage to Southern Company, a utility.
    Wholly-owned captives such as Ford Motor Credit are rejected by the same rule: separating
    them from an unrelated lender with the same root name needs corporate-hierarchy data this
    pipeline does not have. Recorded as a known limitation rather than guessed at.
    """
    s = core(suggestion)
    if not s:
        return False
    for c in cores(company_name):
        if not c:
            continue
        if c == s:
            return True
        if s.startswith(c + " "):
            ext = set(s[len(c) + 1:].split())
            if ext <= CHARTER and (ext & CHARTER_REQ):
                return True
    return False


def get(url, params, tries=3):
    for i in range(tries):
        try:
            time.sleep(PAUSE)
            r = requests.get(url, params=params, timeout=40,
                             headers={"User-Agent": "HI Grade pipeline hi@thehibalance.org"})
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 503):
                time.sleep(5 * (i + 1))
                continue
            return None
        except Exception:
            time.sleep(2)
    return None


def suggest(name):
    d = get(API + "/_suggest_company/", {"text": name})
    return d if isinstance(d, list) else []


def suggest_all(name):
    """Candidates for the stored name AND its core forms. CFPB's suggest endpoint often
    returns nothing for a raw SEC name ('BANK OF AMERICA CORP /DE/') but matches the core."""
    seen, out = set(), []
    for q in dict.fromkeys([name] + cores(name)):
        if not q:
            continue
        for c in suggest(q) or []:
            if c in seen:
                continue
            seen.add(c)
            if accepts(name, c):
                out.append(c)
    return out


def count_for(cfpb_name, since):
    d = get(API + "/", {"company": cfpb_name, "size": 0, "date_received_min": since})
    if not d:
        return None
    total = (d.get("hits") or {}).get("total")
    return total.get("value") if isinstance(total, dict) else total


def score_volume(per_10k, total):
    """Complaints per 10,000 employees -> the volume ladder, on a log scale.

    Through v1.9.x this produced U.1 as well as M.1. As of v1.10.0 it produces **M.1 only**:
    complaint volume is a reading of pricing and conduct pressure, not of how a company treats
    the customer who complained. See the module docstring.

    Every 10x increase in the rate costs 15 points, anchored at 30 per 10k = 85 and clamped to
    [25, 85]. Constants frozen from the Sept 22, 2026 snapshot. Deliberately NOT a live
    percentile: a company's score must not move because another company's data changed.
    """
    if not per_10k or per_10k <= 0:
        return None, None
    u1 = int(round(max(25, min(85, 85 - PER_DECADE * (math.log10(per_10k) - math.log10(ANCHOR))))))
    m1 = max(20, min(u1, round(u1 + 5 - 5 * math.log10(max(total, 1) / 1000 + 1))))
    return u1, m1


def score_benchmark(delta):
    """Benchmark delta in percentage points -> U.1.

    delta = (company relief rate) - (CFPB published relief rate for that product), volume
    weighted across the company's products and across the years measured.
    """
    if delta is None:
        return None
    return int(round(max(U1_FLOOR, min(U1_CAP, U1_NEUTRAL + U1_POINTS_PER_PCT * delta))))


def _buckets(payload, field):
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


def _total(payload):
    hits = ((payload or {}).get("hits") or {}).get("total") or {}
    return hits.get("value", 0) if isinstance(hits, dict) else (hits or 0)


def _year_query(name, year, product=None):
    p = {"company": name, "size": 0, "no_aggs": "false",
         "date_received_min": f"{year}-01-01", "date_received_max": f"{year}-12-31"}
    if product:
        p["product"] = product
    return get(API + "/", p)


def benchmark_delta(names, is_bureau):
    """Volume-weighted relief-rate delta against CFPB's published per-product rates.

    Each year is compared to its own published table, then weighted by the company's own
    complaint count in that year. CFPB publishes percentages per product but not volumes per
    product, so averaging the two tables together would have required a guess; this avoids it.
    """
    vol = defaultdict(int)
    for y in BENCH_YEARS:
        for n in names[:8]:
            p = _year_query(n, y)
            if not p:
                continue
            for b in _buckets(p, "product"):
                vol[b["key"]] += b.get("doc_count", 0)
    if not vol:
        return None, [], 0, []

    grouped = defaultdict(dict)
    for api_product, count in vol.items():
        key = PRODUCT_MAP.get(api_product)
        if key:
            grouped[key][api_product] = count

    cells, gated = [], []
    for key, members in sorted(grouped.items(), key=lambda x: -sum(x[1].values())):
        key_total = sum(members.values())
        if key in ROLE_GATED and not is_bureau:
            gated.append({"product": key, "n": key_total, "reason": "role"})
            continue
        if key_total < MIN_CELL:
            continue

        yearly, pooled_n = [], 0
        for y in BENCH_YEARS:
            if key not in BENCHMARK[y]:
                continue
            resp, cell_n = Counter(), 0
            for api_product in members:
                for n in names[:8]:
                    p = _year_query(n, y, api_product)
                    if not p:
                        continue
                    cell_n += _total(p)
                    for b in _buckets(p, "company_response"):
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
        cells.append({
            "product": key, "n": pooled_n,
            "relief": round(sum(x["relief"] * x["n"] for x in yearly) / pooled_n, 1),
            "delta": round(sum(x["delta"] * x["n"] for x in yearly) / pooled_n, 1),
            "by_year": yearly,
        })

    if not cells:
        return None, [], 0, gated
    wn = sum(c["n"] for c in cells)
    return round(sum(c["delta"] * c["n"] for c in cells) / wn, 1), cells, wn, gated


def headcount_by_ticker(data_dir):
    """SEC reports revenue 0 for many banks (they file interest income, not Revenues),
    so carry headcount as a second size denominator rather than dropping the company."""
    out = {}
    try:
        for r in json.load(open(Path(data_dir) / "sec" / "all_companies.json")):
            t = (r.get("ticker") or "").upper()
            h = ((r.get("h_signals") or {}).get("headcount") or {}).get("value")
            if t and isinstance(h, (int, float)) and h > 0:
                out[t] = h
    except (OSError, ValueError):
        pass
    return out


def revenue_by_ticker(data_dir):
    out = {}
    try:
        for r in json.load(open(Path(data_dir) / "sec" / "all_companies.json")):
            t = (r.get("ticker") or "").upper()
            rev = (r.get("m_signals") or {}).get("revenue")
            if t and isinstance(rev, (int, float)) and rev > 0:
                out[t] = rev
    except (OSError, ValueError):
        pass
    return out


def sic_by_ticker(data_dir):
    """SIC carries the role rule. Without it every company is treated as a non-bureau, which
    is the conservative direction: credit reporting and debt collection stay gated out."""
    out = {}
    try:
        for r in json.load(open(Path(data_dir) / "scores" / "all_scores.json")):
            t = (r.get("ticker") or "").upper()
            if t and r.get("sic"):
                out[t] = str(r["sic"])
    except (OSError, ValueError):
        pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--limit", type=int, default=0, help="only the first N companies (testing)")
    ap.add_argument("--tickers", help="comma-separated tickers to run (testing)")
    ap.add_argument("--dry-run", action="store_true", help="print, write nothing")
    ap.add_argument("--u1", choices=["volume", "benchmark"], default="benchmark",
                    help="which measure becomes U.1. 'benchmark' is the shipped measure; "
                         "'volume' reproduces v1.9.x for comparison. Diff the engine, "
                         "never just the collector — they read different files.")
    a = ap.parse_args()

    data = Path(a.data)
    since = (datetime.now() - timedelta(days=365 * YEARS)).strftime("%Y-%m-%d")
    try:
        companies = json.load(open(data / "scores" / "all_scores.json"))
    except (OSError, ValueError):
        sys.exit(f"  no {a.data}/scores/all_scores.json — run the scoring engine first")
    rev, emp, sic = revenue_by_ticker(data), headcount_by_ticker(data), sic_by_ticker(data)
    want = {t.strip().upper() for t in (a.tickers or "").split(",") if t.strip()}
    rows, matched, checked, scored, unsized, benched = {}, 0, 0, 0, 0, 0
    cache_dir = data / "cfpb" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"  CFPB — U.1 from the {a.u1} measure; M.1 always from the volume ladder\n")

    for c in companies:
        ticker, name = (c.get("ticker") or "").upper(), c.get("company") or ""
        if not ticker or not name:
            continue
        if want and ticker not in want:
            continue
        if not want and a.limit and checked >= a.limit:
            break
        checked += 1
        cache = cache_dir / f"{ticker}.json"
        # Age comes from the timestamp inside the file, never the file's mtime: a fresh git
        # checkout resets mtimes, which is exactly how the pipeline stopped refreshing data.
        row = json.load(open(cache)) if cache.exists() else None
        if row and (datetime.now() - datetime.fromisoformat(row.get("fetched", "2000-01-01"))).days >= CACHE_DAYS:
            row = None
        if row is not None:
            # The acceptance rule is code, not data: re-apply it to cached names so a rule
            # change takes effect now instead of whenever the cache happens to expire.
            keep = [x for x in row.get("cfpb_names") or [] if accepts(name, x)]
            if keep != (row.get("cfpb_names") or []):
                row["cfpb_names"] = keep
                row["counts"] = {k: v for k, v in (row.get("counts") or {}).items() if k in keep}
                row["total_complaints_3yr"] = sum(row["counts"].values()) if row["counts"] else None
        if row is None:
            names = suggest_all(name)
            counts = {}
            for n in names[:8]:
                v = count_for(n, since)
                if v is not None:
                    counts[n] = v
            total = sum(counts.values()) if counts else None
            row = {"company": name, "ticker": ticker, "cfpb_names": names, "counts": counts,
                   "total_complaints_3yr": total, "since": since,
                   "fetched": datetime.now().isoformat(), "source": "CFPB", "match": "suggest-exact"}
        if row.get("total_complaints_3yr") is None:
            continue

        r, h = rev.get(ticker), emp.get(ticker)
        row["revenue_b"] = round(r / 1e9, 2) if r else None
        row["headcount"] = h
        row["per_b"] = round(row["total_complaints_3yr"] / (r / 1e9), 1) if r else None
        row["per_10k_emp"] = round(row["total_complaints_3yr"] / (h / 1e4), 1) if h else None

        u1_vol, m1 = score_volume(row["per_10k_emp"], row["total_complaints_3yr"])
        row["U.1_volume"], row["M.1"] = u1_vol, m1

        # ── Benchmark measure. A closed calendar year does not change, so this is cached hard.
        bench = row.get("benchmark")
        stale = not bench or (datetime.now() - datetime.fromisoformat(
            bench.get("computed", "2000-01-01"))).days >= BENCH_CACHE_DAYS
        if stale and row.get("cfpb_names"):
            is_bureau = sic.get(ticker, "").startswith(BUREAU_SIC_PREFIX)
            delta, cells, wn, gated = benchmark_delta(row["cfpb_names"], is_bureau)
            bench = {"delta": delta, "cells": cells, "benchmarked_n": wn,
                     "role_gated": gated, "is_bureau": is_bureau,
                     "years": list(BENCH_YEARS), "computed": datetime.now().isoformat(),
                     "source": "CFPB Consumer Response Annual Report, Table 1"}
            row["benchmark"] = bench
        row["U.1_benchmark"] = score_benchmark((bench or {}).get("delta"))

        if (row["total_complaints_3yr"] or 0) < MIN_COMPLAINTS:
            row["M.1"] = None
            row["U.1_volume"] = None
            row["note"] = f"under the {MIN_COMPLAINTS}-complaint evidence floor"

        row["U.1"] = row["U.1_benchmark"] if a.u1 == "benchmark" else row["U.1_volume"]
        row["u1_source"] = a.u1

        # Disclosed alongside the score, never folded into it: the volume a score built on
        # resolution cannot express. Equifax resolves slightly better than its published
        # benchmark AND carries about a third of every complaint CFPB receives. Both are true.
        row["disclosure"] = {
            "complaints_3yr": row["total_complaints_3yr"],
            "benchmarked_complaints": (bench or {}).get("benchmarked_n"),
            "relief_vs_benchmark_pts": (bench or {}).get("delta"),
        }

        if not a.dry_run:
            json.dump(row, open(cache, "w"), indent=2)
        rows[ticker] = row
        matched += 1
        if (bench or {}).get("delta") is not None:
            benched += 1

        if row["U.1"] is None:      # never drop a company with real complaints in silence
            unsized += 1
            print(f"  {ticker:6} {name[:30]:30} {row['total_complaints_3yr']:>8,} complaints"
                  f"   {row.get('note') or 'no benchmarkable product'}  NOT SCORED")
            continue
        scored += 1
        d = (bench or {}).get("delta")
        print(f"  {ticker:6} {name[:30]:30} {row['total_complaints_3yr']:>8,} complaints"
              f"   U.1 {row['U.1']:>3} ({a.u1})"
              f"   delta {('%+.1f' % d) if d is not None else '   n/a':>6}"
              f"   M.1 {row['M.1']}")

    print(f"\n  CFPB: {matched} of {checked} matched; {scored} scored, {unsized} unscored, "
          f"{benched} with a benchmark delta")
    if not a.dry_run:
        out = data / "cfpb" / "all_companies.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        json.dump(rows, open(out, "w"), indent=2)
        print(f"  wrote {out}")


if __name__ == "__main__":
    main()
