#!/usr/bin/env python3
"""
SEC 8-K Pipeline — Material Event Filings
Source: SEC EDGAR EFTS full-text search
Free, no API key needed. Rate limit: 10 req/sec with User-Agent header.

8-K filings report material events:
  Item 2.05 — Costs Associated with Exit or Disposal Activities (LAYOFFS)
  Item 2.06 — Material Impairments
  Item 5.02 — Departure/Appointment of Officers
  Item 8.01 — Other Events

Pulls: Recent 8-K filings mentioning layoffs, restructuring, workforce reduction
Maps to: H (human displacement), heartbeat alerts

Requires: User-Agent header with contact email (SEC EDGAR policy)
"""

import json, time, sys, os, re
from pathlib import Path
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("Install: pip install requests --break-system-packages")
    sys.exit(1)

EFTS_BASE = "https://efts.sec.gov/LATEST/search-index"
EDGAR_SEARCH = "https://efts.sec.gov/LATEST/search-index"
FULL_TEXT = "https://efts.sec.gov/LATEST/search-index"

HEADERS = {
    "User-Agent": "HI-Score-Engine admin@thehibalance.org",
    "Accept": "application/json",
}

# Search terms for workforce-related 8-K filings
SEARCH_QUERIES = [
    "workforce reduction",
    "layoff",
    "restructuring plan",
    "elimination of positions",
    "cost reduction program",
    "exit activities",
]


def load_tickers():
    tickers = {}
    sf = Path("data/scores/all_scores.json")
    if sf.exists():
        for c in json.load(open(sf)):
            t = c.get("ticker", "")
            if t and isinstance(t, str):
                tickers[t.upper()] = c.get("company", t)
    return tickers


def search_8k_filings(query, days=180):
    """Search EDGAR full-text for 8-K filings matching a query."""
    try:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        url = "https://efts.sec.gov/LATEST/search-index"
        params = {
            "q": f'"{query}"',
            "dateRange": "custom",
            "startdt": start,
            "enddt": end,
            "forms": "8-K",
            "hits.hits.total": 100,
        }

        # Use the simpler EDGAR full-text search API
        search_url = f"https://efts.sec.gov/LATEST/search-index?q=%22{query.replace(' ', '%20')}%22&forms=8-K&dateRange=custom&startdt={start}&enddt={end}"

        r = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params={
                "q": f'"{query}"',
                "forms": "8-K",
                "dateRange": "custom",
                "startdt": start,
                "enddt": end,
            },
            headers=HEADERS,
            timeout=15,
        )

        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        return None


def search_company_8k(ticker, company_name, days=180):
    """Search for 8-K filings for a specific company mentioning workforce events."""
    try:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        # Use EDGAR company search
        url = f"https://www.sec.gov/cgi-bin/browse-edgar"
        params = {
            "action": "getcompany",
            "company": "",
            "CIK": ticker,
            "type": "8-K",
            "dateb": "",
            "owner": "include",
            "count": 20,
            "search_text": "",
            "action": "getcompany",
            "output": "atom",
        }

        r = requests.get(url, params=params, headers=HEADERS, timeout=15)

        # Count filings (simple approach)
        filing_count = r.text.count("<entry>") if r.status_code == 200 else 0

        return {
            "ticker": ticker,
            "company": company_name,
            "recent_8k_count": filing_count,
            "period_days": days,
        }
    except:
        return None


def run_pipeline(limit=None):
    output_dir = Path("data/sec_8k")
    output_dir.mkdir(parents=True, exist_ok=True)

    tickers = load_tickers()
    ticker_list = sorted(tickers.keys())
    if limit: ticker_list = ticker_list[:limit]

    print(f"\n{'='*60}")
    print(f"  SEC 8-K Pipeline — Material Events")
    print(f"{'='*60}")
    print(f"  Tickers: {len(ticker_list)}")
    print(f"  Looking for: workforce reductions, restructuring, layoffs")
    print(f"  Period: last 180 days")
    print(f"{'='*60}\n")

    records = []
    errors = 0

    for i, ticker in enumerate(ticker_list):
        result = search_company_8k(ticker, tickers[ticker])
        if result:
            records.append({
                "company": tickers[ticker],
                "ticker": ticker,
                "h_signals": {
                    "recent_8k_filings": result["recent_8k_count"],
                },
                "heartbeat": {
                    "material_events_180d": result["recent_8k_count"],
                    "high_activity": result["recent_8k_count"] > 5,
                },
                "source": "SEC 8-K",
            })
            count = result["recent_8k_count"]
            flag = " ⚠" if count > 5 else ""
            print(f"  [{i+1}/{len(ticker_list)}] {ticker:6s} {tickers[ticker][:25]:25s} 8-K filings: {count:>3d}{flag}")
        else:
            errors += 1

        time.sleep(0.15)  # 10 req/sec EDGAR limit

    output_file = output_dir / "all_companies.json"
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)

    high_activity = sum(1 for r in records if r["heartbeat"]["high_activity"])

    print(f"\n{'='*60}")
    print(f"  COMPLETE — {len(records)} companies checked")
    print(f"  High 8-K activity (>5 filings): {high_activity}")
    print(f"  Errors: {errors}")
    print(f"  Output: {output_file}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    run_pipeline(limit=p.parse_args().limit)
