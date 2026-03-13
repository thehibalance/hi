#!/usr/bin/env python3
"""
Yahoo Finance Pipeline
Source: yfinance Python library (free, no API key needed)
URL: https://finance.yahoo.com

Pulls: employee count, revenue, market cap, sector, industry
Maps to: H (headcount, revenue/employee), M (market data)

Install: pip install yfinance --break-system-packages
"""

import json, time, sys
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("Install yfinance: pip install yfinance --break-system-packages")
    sys.exit(1)


def load_tickers():
    """Load tickers from existing scored data and S&P 500 list."""
    tickers = set()
    
    # From existing scores
    scores_path = Path("data/scores/all_scores.json")
    if scores_path.exists():
        for c in json.load(open(scores_path)):
            t = c.get("ticker", "")
            if t and len(t) <= 5:
                tickers.add(t.upper())
    
    # From S&P 500 domains file
    try:
        from sp500_companies import SP500
        for t in SP500:
            if isinstance(t, tuple):
                t = t[0]
            if t and isinstance(t, str) and len(t) <= 5:
                tickers.add(t.upper())
    except ImportError:
        pass
    
    return sorted(tickers)


def fetch_company(ticker):
    """Fetch company data from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or info.get("quoteType") == "NONE":
            return None
        
        employees = info.get("fullTimeEmployees")
        revenue = info.get("totalRevenue")
        market_cap = info.get("marketCap")
        name = info.get("shortName") or info.get("longName") or ticker
        sector = info.get("sector", "")
        industry = info.get("industry", "")
        
        # Calculate revenue per employee
        rpe = None
        if employees and revenue and employees > 0:
            rpe = round(revenue / employees)
        
        return {
            "company": name,
            "ticker": ticker,
            "h_signals": {
                "headcount": employees,
                "revenue_per_employee": rpe,
            },
            "m_signals": {
                "market_cap": market_cap,
            },
            "meta": {
                "sector": sector,
                "industry": industry,
                "revenue": revenue,
            },
            "source": "Yahoo Finance",
        }
    except Exception as e:
        print(f"    ✗ {ticker}: {e}")
        return None


def run_pipeline(limit=None):
    output_dir = Path("data/yahoo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    tickers = load_tickers()
    if limit:
        tickers = tickers[:limit]
    
    print(f"\n{'='*60}")
    print(f"  Yahoo Finance Pipeline")
    print(f"{'='*60}")
    print(f"  Tickers to fetch: {len(tickers)}")
    print(f"  Rate limit: 0.5s between requests")
    print(f"{'='*60}\n")
    
    records = []
    errors = 0
    
    for i, ticker in enumerate(tickers):
        result = fetch_company(ticker)
        if result:
            records.append(result)
            emp = result["h_signals"]["headcount"]
            rpe = result["h_signals"]["revenue_per_employee"]
            emp_str = f"{emp:,}" if emp else "—"
            rpe_str = f"${rpe:,}" if rpe else "—"
            print(f"  [{i+1}/{len(tickers)}] {ticker:6s} {result['company'][:30]:30s} Emp: {emp_str:>10s}  RPE: {rpe_str:>12s}")
        else:
            errors += 1
            print(f"  [{i+1}/{len(tickers)}] {ticker:6s} — skipped")
        
        # Rate limit
        if i < len(tickers) - 1:
            time.sleep(0.5)
    
    # Save
    output_file = output_dir / "all_companies.json"
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)
    
    # Stats
    has_emp = sum(1 for r in records if r["h_signals"]["headcount"])
    has_rpe = sum(1 for r in records if r["h_signals"]["revenue_per_employee"])
    has_mcap = sum(1 for r in records if r["m_signals"]["market_cap"])
    
    print(f"\n{'='*60}")
    print(f"  COMPLETE")
    print(f"  Companies fetched: {len(records)}")
    print(f"  Errors/skipped:    {errors}")
    print(f"  With headcount:    {has_emp}")
    print(f"  With rev/employee: {has_rpe}")
    print(f"  With market cap:   {has_mcap}")
    print(f"  Output: {output_file}")
    print(f"  Maps to: H (headcount, revenue/employee), M (market data)")
    print(f"{'='*60}\n")
    
    return records


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Yahoo Finance Pipeline")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of tickers")
    args = parser.parse_args()
    run_pipeline(limit=args.limit)
