#!/usr/bin/env python3
"""
Phase B scaled test — 25 tickers through the new fallback chain.

Validates that:
1. yfinance fallback works at 5x the volume we tested earlier
2. Headcount + revenue + RPE populate for the vast majority
3. The new data, when fed through the Phase A scoring engine, produces
   meaningfully different (and better-grounded) scores

This script writes to the REAL data dir so scoring can pick up the new
records. Existing records for non-test tickers are untouched.

Usage:
    cd ~/Desktop/repo/pipeline
    python3 phase_b_scaled_test.py
"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from data_collector import collect_one, load_key, safe_filename

# Diverse ticker set: launch ten + 15 more across sectors/sizes/risk profiles
TEST_TICKERS = [
    # Launch ten
    ("Apple Inc.",       "AAPL"),
    ("Microsoft Corp",   "MSFT"),
    ("Alphabet Inc.",    "GOOGL"),
    ("Amazon.com Inc",   "AMZN"),
    ("Meta Platforms",   "META"),
    ("Nike Inc",         "NKE"),
    ("Starbucks Corp",   "SBUX"),
    ("Coca-Cola Co",     "KO"),
    ("PepsiCo Inc",      "PEP"),
    ("Tesla Inc",        "TSLA"),
    # 15 diverse adds
    ("Oracle Corp",      "ORCL"),
    ("Salesforce Inc",   "CRM"),
    ("Costco Wholesale", "COST"),
    ("Walmart Inc",      "WMT"),
    ("Target Corp",      "TGT"),
    ("Johnson & Johnson","JNJ"),
    ("Pfizer Inc",       "PFE"),
    ("Berkshire Hathaway","BRK-B"),
    ("JPMorgan Chase",   "JPM"),
    ("Goldman Sachs",    "GS"),
    ("Exxon Mobil",      "XOM"),
    ("Chevron Corp",     "CVX"),
    ("Boeing Co",        "BA"),
    ("Lockheed Martin",  "LMT"),
    ("Disney Co",        "DIS"),
]

DATA_DIR = Path("data")  # Production dir, relative to pipeline/
SEC_DIR = DATA_DIR / "sec"
SEC_FILE = SEC_DIR / "all_companies.json"


def load_existing_sec():
    """Load existing all_companies.json so we can read prior records."""
    if SEC_FILE.exists():
        return json.load(open(SEC_FILE))
    return []


def index_by_ticker(records):
    return {r.get("ticker", "").upper(): r for r in records if r.get("ticker")}


def main():
    print("=" * 70)
    print("PHASE B SCALED TEST — 25 tickers through new fallback chain")
    print("=" * 70)
    
    # Snapshot existing data BEFORE we touch anything
    print("\nLoading existing SEC records for comparison...")
    existing = load_existing_sec()
    existing_idx = index_by_ticker(existing)
    print(f"  {len(existing)} existing records loaded")
    
    keys = {
        "fmp": load_key("fmp"),
        "finnhub": load_key("finnhub"),
    }
    print(f"  FMP key: {'✓' if keys['fmp'] else '✗'}")
    print(f"  Finnhub key: {'✓' if keys['finnhub'] else '✗'}")
    
    # Collect fresh data for each test ticker
    print(f"\nCollecting fresh data for {len(TEST_TICKERS)} tickers...")
    print(f"{'─' * 70}")
    
    new_records = []
    rows = []  # for the comparison table at the end
    start_time = time.time()
    
    for i, (name, ticker) in enumerate(TEST_TICKERS, 1):
        t0 = time.time()
        print(f"  [{i:2d}/{len(TEST_TICKERS)}] {ticker:6s} {name:25s}", end=" ", flush=True)
        
        try:
            company = {"name": name, "ticker": ticker, "industry": "", "domains": []}
            result = collect_one(company, keys, core=True, subsignals=False, 
                                extended=False, data_dir=DATA_DIR, incremental_hours=0)
            
            if not result or not result.get("sec"):
                print("✗ no SEC result")
                rows.append((ticker, None, None, None, "no SEC"))
                continue
            
            sec = result["sec"]
            new_records.append(sec)
            
            # Pull the headcount/revenue/RPE we got
            h = sec.get("h_signals", {})
            m = sec.get("m_signals", {})
            hc = h.get("headcount")
            if isinstance(hc, dict):
                hc = hc.get("value")
            rev = m.get("revenue", 0)
            rpe = h.get("revenue_per_employee")
            
            # Compare to existing record
            old = existing_idx.get(ticker.upper(), {})
            old_h = old.get("h_signals", {})
            old_hc = old_h.get("headcount")
            if isinstance(old_hc, dict):
                old_hc = old_hc.get("value")
            
            elapsed = time.time() - t0
            status = "✓" if hc and rev else ("⚠" if hc or rev else "✗")
            new_str = f"hc={hc:>9,}" if hc else f"hc={'None':>9}"
            old_str = f"was={old_hc:>9,}" if old_hc else f"was={'None':>9}"
            print(f"{status} {new_str} {old_str} ({elapsed:.1f}s)")
            
            rows.append((ticker, old_hc, hc, rev, "ok" if hc else "no hc"))
            
        except Exception as e:
            print(f"✗ ERROR: {type(e).__name__}: {e}")
            rows.append((ticker, None, None, None, f"err: {type(e).__name__}"))
        
        # Be gentle on yfinance — small pause between tickers
        time.sleep(0.5)
    
    total_elapsed = time.time() - start_time
    print(f"{'─' * 70}")
    print(f"Collection complete: {len(new_records)}/{len(TEST_TICKERS)} succeeded in {total_elapsed:.1f}s")
    
    # Coverage stats
    with_hc = sum(1 for r in rows if r[2])
    with_rev = sum(1 for r in rows if r[3])
    print(f"  With headcount: {with_hc}/{len(TEST_TICKERS)} ({100*with_hc/len(TEST_TICKERS):.0f}%)")
    print(f"  With revenue:   {with_rev}/{len(TEST_TICKERS)} ({100*with_rev/len(TEST_TICKERS):.0f}%)")
    
    # ─── MERGE NEW RECORDS INTO PRODUCTION FILE ───────────────────────────
    if new_records:
        print(f"\nMerging {len(new_records)} new records into {SEC_FILE}...")
        # Replace records for our test tickers, leave others untouched
        test_ticker_set = {t.upper() for _, t in TEST_TICKERS}
        merged = [r for r in existing if r.get("ticker", "").upper() not in test_ticker_set]
        merged.extend(new_records)
        SEC_DIR.mkdir(parents=True, exist_ok=True)
        # Backup first
        if SEC_FILE.exists():
            backup = SEC_FILE.with_suffix(".json.bak_phase_b")
            json.dump(existing, open(backup, "w"))
            print(f"  Backed up old file to {backup.name}")
        json.dump(merged, open(SEC_FILE, "w"), indent=2)
        print(f"  ✓ Wrote {len(merged)} total records ({len(new_records)} updated)")
    
    print()
    print("=" * 70)
    print("NEXT STEPS (run these manually):")
    print("=" * 70)
    print("  1. Re-score:    python3 scoring_engine.py --output data/scores")
    print("  2. Restart API: pkill -f api_server.py && python3 api_server.py --port 8080 &")
    print("  3. Sweep:       (see ten-ticker sweep command)")
    print()
    print("If anything looks wrong, restore the backup:")
    print(f"  cp data/sec/all_companies.json.bak_phase_b data/sec/all_companies.json")


if __name__ == "__main__":
    main()
