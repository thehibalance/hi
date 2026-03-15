#!/usr/bin/env python3
"""
OpenCorporates Pipeline — Corporate Transparency
Source: https://api.opencorporates.com
Free tier: 500 requests/month (no key), higher with API key

Pulls: Company status, incorporation date, subsidiaries count, officers, filings
Maps to: N (transparency - corporate structure opacity), M (governance)

No API key needed for basic access. Key available at: https://opencorporates.com/api_accounts/new
"""

import json, time, sys, os
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install: pip install requests --break-system-packages")
    sys.exit(1)

BASE = "https://api.opencorporates.com/v0.4"


def get_api_key():
    key = os.environ.get("OPENCORP_KEY", "")
    if not key:
        kf = Path("data/opencorporates_key.txt")
        if kf.exists(): key = kf.read_text().strip()
    return key  # OK if empty — works without key at lower rate


def load_companies():
    companies = []
    sf = Path("data/scores/all_scores.json")
    if sf.exists():
        for c in json.load(open(sf)):
            name = c.get("company", "")
            ticker = c.get("ticker", "")
            if name:
                companies.append({"company": name, "ticker": ticker})
    return companies


def search_company(name, key):
    """Search OpenCorporates for a company."""
    try:
        params = {"q": name, "jurisdiction_code": "us", "per_page": 1}
        if key: params["api_token"] = key
        r = requests.get(f"{BASE}/companies/search", params=params, timeout=15)
        d = r.json()
        results = d.get("results", {}).get("companies", [])
        if results:
            return results[0].get("company", {})
        return None
    except:
        return None


def process_company(name, ticker, key):
    result = search_company(name, key)
    if not result:
        return None

    oc_url = result.get("opencorporates_url", "")
    status = result.get("current_status", "")
    inc_date = result.get("incorporation_date", "")
    company_type = result.get("company_type", "")
    jurisdiction = result.get("jurisdiction_code", "")
    registered_address = result.get("registered_address_in_full", "")

    # Transparency signals
    has_address = bool(registered_address)
    has_status = bool(status)
    has_inc_date = bool(inc_date)
    is_active = status.lower() in ["active", "good standing", "in good standing"] if status else None

    # Compute transparency score (0-100)
    transparency_score = 50  # baseline
    if has_address: transparency_score += 10
    if has_status: transparency_score += 10
    if has_inc_date: transparency_score += 10
    if is_active: transparency_score += 10
    if company_type: transparency_score += 10

    return {
        "company": name,
        "ticker": ticker,
        "n_signals": {
            "corporate_transparency_score": transparency_score,
            "has_registered_address": has_address,
            "has_active_status": is_active,
            "company_type": company_type,
            "jurisdiction": jurisdiction,
            "incorporation_date": inc_date,
        },
        "meta": {
            "opencorporates_url": oc_url,
            "status": status,
        },
        "source": "OpenCorporates",
    }


def run_pipeline(limit=None):
    key = get_api_key()
    output_dir = Path("data/opencorporates")
    output_dir.mkdir(parents=True, exist_ok=True)

    companies = load_companies()

    output_file = output_dir / "all_companies.json"
    existing = {}
    if output_file.exists():
        for c in json.load(open(output_file)):
            existing[c["company"].lower()] = c

    to_fetch = [c for c in companies if c["company"].lower() not in existing]
    if limit: to_fetch = to_fetch[:limit]

    # Rate limit: 500/month without key, more with key
    rate = 3.0 if not key else 1.0
    max_batch = 100 if not key else 400
    to_fetch = to_fetch[:max_batch]

    print(f"\n{'='*60}")
    print(f"  OpenCorporates Pipeline — Corporate Transparency")
    print(f"{'='*60}")
    print(f"  API key: {'Yes' if key else 'No (500/month limit)'}")
    print(f"  New to fetch: {len(to_fetch)}")
    print(f"  Rate: {rate}s between requests")
    print(f"{'='*60}\n")

    records = list(existing.values())
    errors = 0

    for i, comp in enumerate(to_fetch):
        result = process_company(comp["company"], comp["ticker"], key)
        if result:
            records.append(result)
            existing[comp["company"].lower()] = result
            score = result["n_signals"]["corporate_transparency_score"]
            status = "Active" if result["n_signals"]["has_active_status"] else "?"
            print(f"  [{i+1}/{len(to_fetch)}] {comp['company'][:30]:30s} Transparency: {score:>3d}  Status: {status}")
        else:
            errors += 1
            print(f"  [{i+1}/{len(to_fetch)}] {comp['company'][:30]:30s} — not found")
        time.sleep(rate)

    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)

    avg_score = sum(r["n_signals"]["corporate_transparency_score"] for r in records) / len(records) if records else 0

    print(f"\n{'='*60}")
    print(f"  COMPLETE — {len(records)} total ({len(to_fetch)-errors} new)")
    print(f"  Avg transparency score: {avg_score:.1f}")
    print(f"  Errors: {errors}")
    print(f"  Output: {output_file}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    run_pipeline(limit=p.parse_args().limit)
