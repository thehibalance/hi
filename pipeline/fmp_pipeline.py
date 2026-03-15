#!/usr/bin/env python3
"""
FMP (Financial Modeling Prep) Pipeline
Source: https://financialmodelingprep.com
Free tier: 250 requests/day

Pulls: employee count, revenue, R&D, market cap, income, ratios
Maps to: H (headcount, revenue/employee, R&D), M (margins, growth), N (filing quality)

Get free API key: https://site.financialmodelingprep.com/developer/docs
"""

import json, time, sys, os
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install: pip install requests --break-system-packages")
    sys.exit(1)

BASE = "https://financialmodelingprep.com/api/v3"


def get_api_key():
    key = os.environ.get("FMP_KEY", "")
    if not key:
        kf = Path("data/fmp_key.txt")
        if kf.exists(): key = kf.read_text().strip()
    if not key:
        print("No FMP API key. Get free key at:")
        print("  https://site.financialmodelingprep.com/developer/docs")
        print("Then: echo YOUR_KEY > data/fmp_key.txt")
        sys.exit(1)
    return key


def load_tickers():
    tickers = set()
    sf = Path("data/scores/all_scores.json")
    if sf.exists():
        for c in json.load(open(sf)):
            t = c.get("ticker", "")
            if t and isinstance(t, str) and len(t) <= 5:
                tickers.add(t.upper())
    try:
        from sp500_companies import SP500
        for t in SP500:
            if isinstance(t, tuple): t = t[0]
            if t and isinstance(t, str) and len(t) <= 5:
                tickers.add(t.upper())
    except ImportError:
        pass
    return sorted(tickers)


def fetch_profile(ticker, key):
    try:
        r = requests.get(f"{BASE}/profile/{ticker}?apikey={key}", timeout=15)
        d = r.json()
        return d[0] if d and isinstance(d, list) else None
    except:
        return None


def fetch_income(ticker, key):
    try:
        r = requests.get(f"{BASE}/income-statement/{ticker}?period=annual&limit=3&apikey={key}", timeout=15)
        d = r.json()
        return d if isinstance(d, list) else None
    except:
        return None


def fetch_ratios(ticker, key):
    try:
        r = requests.get(f"{BASE}/ratios/{ticker}?period=annual&limit=1&apikey={key}", timeout=15)
        d = r.json()
        return d[0] if d and isinstance(d, list) else None
    except:
        return None


def process_company(ticker, key):
    profile = fetch_profile(ticker, key)
    if not profile: return None

    time.sleep(0.5)
    income = fetch_income(ticker, key)
    time.sleep(0.5)
    ratios = fetch_ratios(ticker, key)

    employees = profile.get("fullTimeEmployees")
    if isinstance(employees, str):
        try: employees = int(employees)
        except: employees = None

    revenue = profile.get("revenue") or (income[0].get("revenue") if income else None)
    rd = income[0].get("researchAndDevelopmentExpenses") if income else None
    market_cap = profile.get("mktCap")
    sector = profile.get("sector", "")
    industry = profile.get("industry", "")
    name = profile.get("companyName", ticker)

    rpe = round(revenue / employees) if employees and revenue and employees > 0 else None
    rd_pct = round(rd / revenue * 100, 1) if rd and revenue and revenue > 0 else None

    # Revenue growth
    rev_growth = None
    if income and len(income) >= 2:
        try:
            r0 = income[0].get("revenue", 0) or 0
            r1 = income[1].get("revenue", 0) or 0
            if r1 > 0: rev_growth = round((r0 - r1) / r1 * 100, 1)
        except: pass

    # Employee change (if we have 2 years — FMP doesn't always have historical)
    headcount_change = None

    op_margin = ratios.get("operatingProfitMargin") if ratios else None
    if op_margin: op_margin = round(op_margin * 100, 1)

    return {
        "company": name, "ticker": ticker,
        "h_signals": {
            "headcount": employees,
            "revenue_per_employee": rpe,
            "rd_spend": rd,
            "rd_pct_revenue": rd_pct,
            "headcount_change_pct": headcount_change,
        },
        "m_signals": {
            "market_cap": market_cap,
            "operating_margin": op_margin,
            "revenue_growth_pct": rev_growth,
        },
        "n_signals": {
            "sector": sector,
            "industry": industry,
        },
        "meta": {"revenue": revenue},
        "source": "FMP",
    }


def run_pipeline(limit=None):
    key = get_api_key()
    output_dir = Path("data/fmp")
    output_dir.mkdir(parents=True, exist_ok=True)

    tickers = load_tickers()

    # Load existing to append
    output_file = output_dir / "all_companies.json"
    existing = {}
    if output_file.exists():
        for c in json.load(open(output_file)):
            existing[c["ticker"]] = c
        print(f"  Existing: {len(existing)} companies")

    to_fetch = [t for t in tickers if t not in existing]
    if limit: to_fetch = to_fetch[:limit]

    # 3 API calls per company, 250/day limit = ~83 companies/day
    max_daily = min(len(to_fetch), 80)
    to_fetch = to_fetch[:max_daily]

    print(f"\n{'='*60}")
    print(f"  FMP (Financial Modeling Prep) Pipeline")
    print(f"{'='*60}")
    print(f"  API key: {key[:4]}...{key[-4:]}")
    print(f"  New to fetch: {len(to_fetch)}")
    print(f"  Rate: 3 calls/company, 250/day max (~80 companies/run)")
    print(f"{'='*60}\n")

    records = list(existing.values())
    errors = 0

    for i, ticker in enumerate(to_fetch):
        result = process_company(ticker, key)
        if result:
            records.append(result)
            existing[ticker] = result
            emp = result["h_signals"]["headcount"]
            rpe = result["h_signals"]["revenue_per_employee"]
            emp_s = f"{emp:,}" if emp else "—"
            rpe_s = f"${rpe:,}" if rpe else "—"
            print(f"  [{i+1}/{len(to_fetch)}] {ticker:6s} {result['company'][:30]:30s} Emp: {emp_s:>10s}  RPE: {rpe_s:>12s}")
        else:
            errors += 1
            print(f"  [{i+1}/{len(to_fetch)}] {ticker:6s} — skipped")
        time.sleep(0.5)

    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)

    has_emp = sum(1 for r in records if r["h_signals"]["headcount"])
    has_rpe = sum(1 for r in records if r["h_signals"]["revenue_per_employee"])
    has_rd = sum(1 for r in records if r["h_signals"]["rd_pct_revenue"])

    print(f"\n{'='*60}")
    print(f"  COMPLETE — {len(records)} total ({len(to_fetch)-errors} new)")
    print(f"  With headcount:  {has_emp}")
    print(f"  With rev/emp:    {has_rpe}")
    print(f"  With R&D data:   {has_rd}")
    print(f"  Errors: {errors}")
    print(f"  Output: {output_file}")
    print(f"  Run daily to accumulate (appends, doesn't re-fetch)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    run_pipeline(limit=p.parse_args().limit)
