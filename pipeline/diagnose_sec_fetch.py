#!/usr/bin/env python3
"""
SEC fetch diagnostic — runs the actual SEC EDGAR fetch flow against 5 known tickers
and prints exactly what happens at each step. Identifies which step in the pipeline
is silently failing.

Usage:
    cd ~/Desktop/repo/pipeline
    python3 diagnose_sec_fetch.py

Output explains: company_tickers.json fetch, CIK lookup, companyfacts fetch, 
revenue concept lookup, employee concept lookup, fiscal year filtering.
"""

import requests
import json
import time
from datetime import datetime

SEC_HEADERS = {"User-Agent": "HI Score Bot hi@thehibalance.org", "Accept": "application/json"}
TEST_TICKERS = ["AAPL", "MSFT", "ORCL", "JNJ", "KO"]

# Common us-gaap revenue concepts (SEC reporters use any of these)
REVENUE_CONCEPTS = [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax", 
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueNet",
    "SalesRevenueGoodsNet",
    "OperatingRevenue",
]

# Common employee concepts (across us-gaap and dei namespaces)
EMPLOYEE_CONCEPTS_DEI = ["EntityNumberOfEmployees"]
EMPLOYEE_CONCEPTS_GAAP = ["EntityNumberOfEmployees", "NumberOfEmployees"]

def banner(text):
    print(f"\n{'━' * 70}\n  {text}\n{'━' * 70}")

def fetch_with_log(url, label, headers=None):
    """Fetch a URL and log exactly what happens."""
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            print(f"  ✓ {label}: HTTP 200, {len(r.content):,} bytes")
            return r.json()
        else:
            print(f"  ✗ {label}: HTTP {r.status_code} — {r.reason}")
            print(f"      URL: {url[:100]}")
            return None
    except requests.exceptions.Timeout:
        print(f"  ✗ {label}: TIMEOUT after 15s")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  ✗ {label}: REQUEST ERROR {type(e).__name__}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"  ✗ {label}: JSON PARSE ERROR — {e}")
        return None
    except Exception as e:
        print(f"  ✗ {label}: UNEXPECTED {type(e).__name__}: {e}")
        return None


def diagnose_ticker(ticker, ticker_map):
    """Run the full SEC fetch flow for one ticker and report each step."""
    banner(f"DIAGNOSING: {ticker}")
    
    # STEP 1: CIK lookup
    cik = None
    company_name = None
    if ticker_map:
        for entry in ticker_map.values():
            if entry.get("ticker", "").upper() == ticker.upper():
                cik = str(entry["cik_str"]).zfill(10)
                company_name = entry.get("title", ticker)
                break
    
    if not cik:
        print(f"  ✗ STEP 1 (CIK lookup): NO MATCH for ticker {ticker}")
        print(f"      ticker_map type: {type(ticker_map)}")
        if isinstance(ticker_map, dict):
            print(f"      ticker_map size: {len(ticker_map)}")
        return
    print(f"  ✓ STEP 1 (CIK lookup): {ticker} → CIK {cik} ({company_name})")
    
    # STEP 2: Fetch companyfacts
    time.sleep(0.3)
    facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    facts = fetch_with_log(facts_url, "STEP 2 (companyfacts)", headers=SEC_HEADERS)
    
    if not facts:
        return
    
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    dei = facts.get("facts", {}).get("dei", {})
    print(f"      us-gaap concepts available: {len(us_gaap)}")
    print(f"      dei concepts available: {len(dei)}")
    
    # STEP 3: Find a revenue concept
    print(f"\n  STEP 3 — Searching for revenue concept:")
    found_rev = None
    for concept in REVENUE_CONCEPTS:
        if concept in us_gaap:
            usd_units = us_gaap[concept].get("units", {}).get("USD", [])
            annual = [u for u in usd_units if u.get("form") == "10-K" and u.get("fy", 0) >= 2022]
            print(f"      • {concept}: present, {len(usd_units)} total units, {len(annual)} annual ≥2022")
            if annual and not found_rev:
                latest = sorted(annual, key=lambda x: x.get("fy", 0), reverse=True)[0]
                found_rev = latest.get("val", 0)
                print(f"        → USED. Latest fy={latest.get('fy')}, val=${found_rev:,}")
        else:
            print(f"      • {concept}: NOT in us-gaap")
    
    if not found_rev:
        print(f"  ✗ STEP 3: NO REVENUE CONCEPT MATCHED any of {len(REVENUE_CONCEPTS)} attempts")
    
    # STEP 4: Find employee concept
    print(f"\n  STEP 4 — Searching for employee concept:")
    found_emp = None
    
    # Try dei namespace (where EntityNumberOfEmployees actually lives)
    for concept in EMPLOYEE_CONCEPTS_DEI:
        if concept in dei:
            units = dei[concept].get("units", {})
            print(f"      • dei:{concept}: present, units = {list(units.keys())}")
            for unit_name, unit_data in units.items():
                annual = [u for u in unit_data if u.get("form") == "10-K" and u.get("fy", 0) >= 2021]
                annual_anyform = [u for u in unit_data if u.get("fy", 0) >= 2021]
                print(f"          unit '{unit_name}': {len(unit_data)} total, {len(annual)} on 10-K ≥2021, {len(annual_anyform)} on any form ≥2021")
                if annual and not found_emp:
                    latest = sorted(annual, key=lambda x: x.get("fy", 0), reverse=True)[0]
                    found_emp = latest.get("val", 0)
                    print(f"            → USED. fy={latest.get('fy')}, val={found_emp:,}")
                elif annual_anyform and not found_emp:
                    # Form filter is the bug — try ANY form
                    latest = sorted(annual_anyform, key=lambda x: x.get("fy", 0), reverse=True)[0]
                    print(f"            ⚠ NOTE: data exists but not on 10-K form. Latest form: {latest.get('form')}, fy={latest.get('fy')}, val={latest.get('val'):,}")
        else:
            print(f"      • dei:{concept}: NOT in dei namespace")
    
    # Also try us-gaap
    for concept in EMPLOYEE_CONCEPTS_GAAP:
        if concept in us_gaap:
            units = us_gaap[concept].get("units", {})
            print(f"      • us-gaap:{concept}: present, units = {list(units.keys())}")
    
    if not found_emp:
        print(f"  ✗ STEP 4: NO EMPLOYEE CONCEPT MATCHED")
    
    # SUMMARY
    print(f"\n  SUMMARY for {ticker}:")
    print(f"      Revenue:   {'✓' if found_rev else '✗'} {f'${found_rev:,}' if found_rev else 'MISSING'}")
    print(f"      Employees: {'✓' if found_emp else '✗'} {f'{found_emp:,}' if found_emp else 'MISSING'}")
    if found_rev and found_emp:
        print(f"      RPE:       ✓ ${round(found_rev/found_emp):,}")


def main():
    print("SEC EDGAR Fetch Diagnostic")
    print("=" * 70)
    print(f"Testing {len(TEST_TICKERS)} tickers: {', '.join(TEST_TICKERS)}")
    
    # STEP 0: Fetch the ticker→CIK map ONCE
    banner("STEP 0: Fetch company_tickers.json (CIK map)")
    ticker_map = fetch_with_log(
        "https://www.sec.gov/files/company_tickers.json",
        "company_tickers.json",
        headers=SEC_HEADERS
    )
    
    if not ticker_map:
        print("\n✗ FATAL: Cannot proceed without ticker map. SEC EDGAR may be unreachable.")
        return
    
    print(f"  ticker_map has {len(ticker_map)} entries")
    
    # Run each test ticker
    for ticker in TEST_TICKERS:
        diagnose_ticker(ticker, ticker_map)
        time.sleep(0.5)  # Be nice to SEC EDGAR
    
    print(f"\n{'=' * 70}")
    print("Diagnostic complete.")


if __name__ == "__main__":
    main()
