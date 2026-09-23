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
  4. Normalize per $B of revenue, and record the matched names, counts and query dates so any
     number can be re-checked or disputed.

No match means no data. It never scores an absence as good.

  python3 cfpb_pipeline.py --limit 20 --dry-run     # try it on 20 companies, write nothing
  python3 cfpb_pipeline.py                          # full run, writes data/cfpb/all_companies.json
"""
import argparse
import json
import math
import os
import re
import sys
import time
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
ANCHOR = 30.0                 # complaints per 10k employees scoring 85
PER_DECADE = 15               # points lost per 10x increase in the rate
SUFFIXES = ["incorporated", "corporation", "company", "holdings", "holding", "group", "inc", "corp",
            "co", "llc", "lp", "ltd", "plc", "sa", "nv", "ag", "se", "national association", "n a"]


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
        if n.endswith(" and"):            # "Wells Fargo & Company" -> "wells fargo and" -> "wells fargo"
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
            r = requests.get(url, params=params, timeout=30,
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


def score(per_10k, total):
    """Complaints per 10,000 employees -> U.1 / M.1, on a log scale.

    Every 10x increase in the rate costs 15 points, anchored at 30 per 10k = 85 and clamped to
    [25, 85]. Constants frozen from the Sept 22, 2026 snapshot: 37 scoreable companies spanning
    35 (Tesla) to 2,643,987 (Equifax) complaints per 10k employees — five orders of magnitude,
    which no set of linear cutoffs can band honestly.

    Deliberately NOT a live percentile. A company's score must not move because another
    company's data changed, or the engine stops producing the same output from the same inputs.
    Re-derive these constants on purpose, with a dated note, never automatically.
    """
    if not per_10k or per_10k <= 0:
        return None, None
    u1 = int(round(max(25, min(85, 85 - PER_DECADE * (math.log10(per_10k) - math.log10(ANCHOR))))))
    m1 = max(20, min(u1, round(u1 + 5 - 5 * math.log10(max(total, 1) / 1000 + 1))))
    return u1, m1


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--limit", type=int, default=0, help="only the first N companies (testing)")
    ap.add_argument("--tickers", help="comma-separated tickers to run (testing)")
    ap.add_argument("--dry-run", action="store_true", help="print, write nothing")
    a = ap.parse_args()

    data = Path(a.data)
    since = (datetime.now() - timedelta(days=365 * YEARS)).strftime("%Y-%m-%d")
    try:
        companies = json.load(open(data / "scores" / "all_scores.json"))
    except (OSError, ValueError):
        sys.exit(f"  no {a.data}/scores/all_scores.json — run the scoring engine first")
    rev = revenue_by_ticker(data)
    emp = headcount_by_ticker(data)
    want = {t.strip().upper() for t in (a.tickers or "").split(",") if t.strip()}
    rows, matched, checked, scored, unsized = {}, 0, 0, 0, 0
    cache_dir = data / "cfpb" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

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
            # change takes effect now instead of whenever the cache happens to expire. The
            # first v1.5.0 run still scored Ford Motor Credit and Snap Credit from day-old rows.
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
            if not a.dry_run:
                json.dump(row, open(cache, "w"), indent=2)
        if row.get("total_complaints_3yr") is None:
            continue
        r, h = rev.get(ticker), emp.get(ticker)
        row["revenue_b"] = round(r / 1e9, 2) if r else None
        row["headcount"] = h
        row["per_b"] = round(row["total_complaints_3yr"] / (r / 1e9), 1) if r else None
        row["per_10k_emp"] = round(row["total_complaints_3yr"] / (h / 1e4), 1) if h else None
        row["U.1"], row["M.1"] = score(row["per_10k_emp"], row["total_complaints_3yr"])
        if (row["total_complaints_3yr"] or 0) < MIN_COMPLAINTS:
            row["U.1"] = row["M.1"] = None
            row["note"] = f"under the {MIN_COMPLAINTS}-complaint evidence floor"
        rows[ticker] = row
        matched += 1
        if row["U.1"] is None:      # never drop a company with real complaints in silence
            unsized += 1
            print(f"  {ticker:6} {name[:34]:34} {row['total_complaints_3yr']:>7,} complaints"
                  f"   {row.get('note') or 'no headcount'}  NOT SCORED")
            continue
        scored += 1
        print(f"  {ticker:6} {name[:34]:34} {row['total_complaints_3yr']:>7,} complaints"
              f"  {str(row['per_10k_emp']):>9}/10k  U.1 {row['U.1']}  M.1 {row['M.1']}  {row['cfpb_names'][:2]}")

    print(f"\n  CFPB: {matched} of {checked} matched a CFPB name; {scored} scored, {unsized} unscored")
    if not a.dry_run:
        out = data / "cfpb" / "all_companies.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        json.dump(rows, open(out, "w"), indent=2)
        print(f"  wrote {out}")


if __name__ == "__main__":
    main()
