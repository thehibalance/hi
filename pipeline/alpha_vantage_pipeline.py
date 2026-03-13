#!/usr/bin/env python3
"""
Alpha Vantage Pipeline
Source: Alpha Vantage free API
URL: https://www.alphavantage.co

Pulls: earnings (quarterly/annual), income statement, balance sheet
Maps to: H (R&D spending, headcount trends), M (profitability, financial health)

Get free API key: https://www.alphavantage.co/support/#api-key
Free tier: 25 requests/day, 5 requests/minute

Install: pip install requests --break-system-packages
"""

import json, time, sys, os
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install requests: pip install requests --break-system-packages")
    sys.exit(1)

BASE_URL = "https://www.alphavantage.co/query"


def get_api_key():
    """Get API key from env var or prompt."""
    key = os.environ.get("ALPHA_VANTAGE_KEY", "")
    if not key:
        key_file = Path("data/alpha_vantage_key.txt")
        if key_file.exists():
            key = key_file.read_text().strip()
    if not key:
        print("No API key found.")
        print("Get a free key at: https://www.alphavantage.co/support/#api-key")
        print("Then either:")
        print("  export ALPHA_VANTAGE_KEY=your_key")
        print("  OR save it to: data/alpha_vantage_key.txt")
        sys.exit(1)
    return key


def load_tickers():
    """Load tickers from existing scored data."""
    tickers = set()
    scores_path = Path("data/scores/all_scores.json")
    if scores_path.exists():
        for c in json.load(open(scores_path)):
            t = c.get("ticker", "")
            if t and len(t) <= 5:
                tickers.add(t.upper())
    return sorted(tickers)


def fetch_overview(ticker, api_key):
    """Fetch company overview — includes employee count, sector, market cap."""
    try:
        r = requests.get(BASE_URL, params={
            "function": "OVERVIEW",
            "symbol": ticker,
            "apikey": api_key,
        }, timeout=15)
        data = r.json()
        
        if "Symbol" not in data:
            return None
        
        return data
    except Exception as e:
        print(f"    ✗ {ticker} overview: {e}")
        return None


def fetch_income(ticker, api_key):
    """Fetch income statement — revenue, R&D, operating expenses."""
    try:
        r = requests.get(BASE_URL, params={
            "function": "INCOME_STATEMENT",
            "symbol": ticker,
            "apikey": api_key,
        }, timeout=15)
        data = r.json()
        
        if "annualReports" not in data:
            return None
        
        return data.get("annualReports", [])[:3]  # Last 3 years
    except Exception as e:
        print(f"    ✗ {ticker} income: {e}")
        return None


def process_company(ticker, api_key):
    """Process a single company's Alpha Vantage data."""
    overview = fetch_overview(ticker, api_key)
    if not overview:
        return None
    
    time.sleep(12.5)  # 5 req/min limit = 12s between calls, adding buffer
    
    income = fetch_income(ticker, api_key)
    
    name = overview.get("Name", ticker)
    employees = None
    try:
        emp_str = overview.get("FullTimeEmployees", "")
        if emp_str and emp_str != "None" and emp_str != "-":
            employees = int(emp_str)
    except (ValueError, TypeError):
        pass
    
    revenue = None
    rd_spend = None
    operating_margin = None
    
    if income and len(income) > 0:
        latest = income[0]
        try:
            rev = latest.get("totalRevenue", "")
            if rev and rev != "None":
                revenue = int(rev)
        except (ValueError, TypeError):
            pass
        
        try:
            rd = latest.get("researchAndDevelopment", "")
            if rd and rd != "None":
                rd_spend = int(rd)
        except (ValueError, TypeError):
            pass
        
        try:
            op_income = latest.get("operatingIncome", "")
            if op_income and op_income != "None" and revenue and revenue > 0:
                operating_margin = round(int(op_income) / revenue * 100, 1)
        except (ValueError, TypeError):
            pass
    
    # Revenue per employee
    rpe = None
    if employees and revenue and employees > 0:
        rpe = round(revenue / employees)
    
    # R&D as % of revenue
    rd_pct = None
    if rd_spend and revenue and revenue > 0:
        rd_pct = round(rd_spend / revenue * 100, 1)
    
    # Revenue growth (if we have 2+ years)
    rev_growth = None
    if income and len(income) >= 2:
        try:
            rev_curr = int(income[0].get("totalRevenue", 0) or 0)
            rev_prev = int(income[1].get("totalRevenue", 0) or 0)
            if rev_prev > 0:
                rev_growth = round((rev_curr - rev_prev) / rev_prev * 100, 1)
        except (ValueError, TypeError):
            pass
    
    return {
        "company": name,
        "ticker": ticker,
        "h_signals": {
            "headcount": employees,
            "revenue_per_employee": rpe,
            "rd_spend": rd_spend,
            "rd_pct_revenue": rd_pct,
        },
        "m_signals": {
            "operating_margin": operating_margin,
            "revenue_growth_pct": rev_growth,
        },
        "meta": {
            "sector": overview.get("Sector", ""),
            "industry": overview.get("Industry", ""),
            "revenue": revenue,
            "market_cap": overview.get("MarketCapitalization"),
            "fiscal_year_end": overview.get("FiscalYearEnd"),
        },
        "source": "Alpha Vantage",
    }


def run_pipeline(limit=None):
    api_key = get_api_key()
    output_dir = Path("data/alphavantage")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    tickers = load_tickers()
    if limit:
        tickers = tickers[:limit]
    
    # Alpha Vantage free tier: 25 requests/day, 5/min
    # Each company = 2 requests (overview + income)
    # So max ~12 companies per day on free tier
    max_companies = min(len(tickers), 12) if not limit else limit
    tickers = tickers[:max_companies]
    
    print(f"\n{'='*60}")
    print(f"  Alpha Vantage Pipeline")
    print(f"{'='*60}")
    print(f"  API key: {api_key[:4]}...{api_key[-4:]}")
    print(f"  Tickers to fetch: {len(tickers)}")
    print(f"  Rate limit: 5 req/min (12.5s between calls)")
    print(f"  Free tier: ~12 companies/day (25 req/day)")
    print(f"  Estimated time: {len(tickers) * 25 // 60} minutes")
    print(f"{'='*60}\n")
    
    # Load existing data to append
    output_file = output_dir / "all_companies.json"
    existing = {}
    if output_file.exists():
        for c in json.load(open(output_file)):
            existing[c["ticker"]] = c
        print(f"  Existing data: {len(existing)} companies")
    
    # Skip already-fetched tickers
    to_fetch = [t for t in tickers if t not in existing]
    print(f"  New to fetch: {len(to_fetch)}")
    
    records = list(existing.values())
    errors = 0
    
    for i, ticker in enumerate(to_fetch):
        result = process_company(ticker, api_key)
        if result:
            records.append(result)
            existing[ticker] = result
            emp = result["h_signals"]["headcount"]
            rpe = result["h_signals"]["revenue_per_employee"]
            rd = result["h_signals"]["rd_pct_revenue"]
            emp_str = f"{emp:,}" if emp else "—"
            rpe_str = f"${rpe:,}" if rpe else "—"
            rd_str = f"{rd}%" if rd else "—"
            print(f"  [{i+1}/{len(to_fetch)}] {ticker:6s} {result['company'][:25]:25s} Emp: {emp_str:>10s}  RPE: {rpe_str:>12s}  R&D: {rd_str:>6s}")
        else:
            errors += 1
            print(f"  [{i+1}/{len(to_fetch)}] {ticker:6s} — skipped")
        
        # Rate limit between companies (2 calls each, need ~12.5s between calls)
        if i < len(to_fetch) - 1:
            time.sleep(13)
    
    # Save all (existing + new)
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)
    
    has_emp = sum(1 for r in records if r["h_signals"]["headcount"])
    has_rpe = sum(1 for r in records if r["h_signals"]["revenue_per_employee"])
    has_rd = sum(1 for r in records if r["h_signals"]["rd_pct_revenue"])
    
    print(f"\n{'='*60}")
    print(f"  COMPLETE")
    print(f"  Total companies: {len(records)}")
    print(f"  New this run:    {len(to_fetch) - errors}")
    print(f"  Errors/skipped:  {errors}")
    print(f"  With headcount:  {has_emp}")
    print(f"  With rev/emp:    {has_rpe}")
    print(f"  With R&D data:   {has_rd}")
    print(f"  Output: {output_file}")
    print(f"  Maps to: H (headcount, R&D), M (margins, growth)")
    print(f"")
    print(f"  NOTE: Free tier = 25 req/day. Run daily to build up data.")
    print(f"  Each run appends to existing data (won't re-fetch).")
    print(f"{'='*60}\n")
    
    return records


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Alpha Vantage Pipeline")
    parser.add_argument("--limit", type=int, default=None, help="Limit companies (default: 12 for free tier)")
    args = parser.parse_args()
    run_pipeline(limit=args.limit)
