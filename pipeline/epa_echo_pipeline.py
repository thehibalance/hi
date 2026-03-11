#!/usr/bin/env python3
"""
HI. — EPA ECHO Data Pipeline
Pulls environmental compliance data from EPA's ECHO REST API.

Dimensions served:
  A — Alive & Environmental (violations, inspections, penalties)
  M — Moral & Ethical Conduct (enforcement actions, penalty amounts)

API: https://echo.epa.gov/tools/web-services
No authentication required. Free.

Usage:
  python epa_echo_pipeline.py --company "Apple Inc"
  python epa_echo_pipeline.py                        # All seed companies
"""

import json, os, sys, time, re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from pathlib import Path

USER_AGENT = "HI-Pipeline/1.0 (thehibalance.org; contact@thehibalance.org)"
BASE_URL = "https://echodata.epa.gov/echo"
RATE_LIMIT = 0.5  # EPA is slower, be gentle
OUTPUT_DIR = Path("data/epa")


def fetch_json(url):
    time.sleep(RATE_LIMIT)
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, Exception) as e:
        print(f"  Error: {e}")
        return None


def search_facilities(company_name):
    """Search EPA ECHO for facilities owned by a company."""
    # Use the Corporate Compliance Screener approach — search by company name
    encoded = company_name.replace(" ", "+").replace("&", "%26")
    url = f"{BASE_URL}/ccs_services/get_facilities?output=JSON&p_fn={encoded}&p_act=Y"
    data = fetch_json(url)
    if not data:
        return None
    
    # Extract facility results
    results = data.get("Results", {})
    facilities = results.get("Facilities", [])
    return {
        "query": company_name,
        "total_facilities": len(facilities),
        "facilities": facilities,
    }


def get_facility_detail(registry_id):
    """Get detailed compliance info for a specific facility."""
    url = f"{BASE_URL}/dfr_services/get_dfr?output=JSON&p_id={registry_id}"
    return fetch_json(url)


def compute_epa_signals(company_name, facilities_data):
    """Extract HUMAN-relevant signals from EPA facility data."""
    signals = {
        "company": company_name,
        "source": "EPA ECHO",
        "retrieved": time.strftime("%Y-%m-%d"),
        "a_signals": {},
        "m_signals": {},
    }

    if not facilities_data or not facilities_data.get("facilities"):
        signals["error"] = "No EPA-regulated facilities found"
        return signals

    facilities = facilities_data["facilities"]
    signals["total_facilities"] = len(facilities)

    # Aggregate across all facilities
    total_violations_3yr = 0
    total_inspections_5yr = 0
    total_penalties = 0
    total_informal_actions = 0
    total_formal_actions = 0
    caa_violations = 0  # Clean Air Act
    cwa_violations = 0  # Clean Water Act
    rcra_violations = 0  # Hazardous waste
    facilities_in_violation = 0

    for f in facilities:
        # Count violations
        v3 = int(f.get("CAAViolCnt", 0) or 0) + int(f.get("CWAViolCnt", 0) or 0) + int(f.get("RCRAViolCnt", 0) or 0)
        total_violations_3yr += v3
        if v3 > 0:
            facilities_in_violation += 1

        caa_violations += int(f.get("CAAViolCnt", 0) or 0)
        cwa_violations += int(f.get("CWAViolCnt", 0) or 0)
        rcra_violations += int(f.get("RCRAViolCnt", 0) or 0)

        # Count inspections
        total_inspections_5yr += int(f.get("Insp5yrCnt", 0) or 0)

        # Count enforcement actions
        total_informal_actions += int(f.get("InformalCnt", 0) or 0)
        total_formal_actions += int(f.get("FormalCnt", 0) or 0)

        # Penalties
        pen = f.get("TotalPenalties")
        if pen:
            try:
                total_penalties += float(str(pen).replace(",", "").replace("$", ""))
            except ValueError:
                pass

    # ── A Dimension Signals ──
    signals["a_signals"]["total_facilities"] = len(facilities)
    signals["a_signals"]["facilities_in_violation"] = facilities_in_violation
    signals["a_signals"]["violation_rate"] = round(facilities_in_violation / len(facilities) * 100, 1) if facilities else 0
    signals["a_signals"]["total_violations_3yr"] = total_violations_3yr
    signals["a_signals"]["caa_violations"] = caa_violations
    signals["a_signals"]["cwa_violations"] = cwa_violations
    signals["a_signals"]["rcra_violations"] = rcra_violations
    signals["a_signals"]["inspections_5yr"] = total_inspections_5yr

    # Violation severity flag
    if total_violations_3yr > 20:
        signals["a_signals"]["violation_flag"] = "HIGH — significant environmental violations"
    elif total_violations_3yr > 5:
        signals["a_signals"]["violation_flag"] = "MODERATE — some environmental violations"
    elif total_violations_3yr > 0:
        signals["a_signals"]["violation_flag"] = "LOW — minor violations"
    else:
        signals["a_signals"]["violation_flag"] = "CLEAN — no violations in 3 years"

    # ── M Dimension Signals ──
    signals["m_signals"]["total_penalties"] = total_penalties
    signals["m_signals"]["formal_actions"] = total_formal_actions
    signals["m_signals"]["informal_actions"] = total_informal_actions

    if total_penalties > 10000000:
        signals["m_signals"]["penalty_flag"] = f"HIGH — ${total_penalties:,.0f} in penalties"
    elif total_penalties > 1000000:
        signals["m_signals"]["penalty_flag"] = f"MODERATE — ${total_penalties:,.0f} in penalties"
    elif total_penalties > 0:
        signals["m_signals"]["penalty_flag"] = f"LOW — ${total_penalties:,.0f} in penalties"
    else:
        signals["m_signals"]["penalty_flag"] = "CLEAN — no penalties"

    return signals


# Company name mappings for EPA search
COMPANY_EPA_NAMES = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "AMZN": "Amazon",
    "META": "Meta Platforms",
    "TSLA": "Tesla",
    "NVDA": "NVIDIA",
    "XOM": "Exxon Mobil",
    "CVX": "Chevron",
    "BA": "Boeing",
    "LMT": "Lockheed Martin",
    "GM": "General Motors",
    "F": "Ford Motor",
    "JNJ": "Johnson Johnson",
    "PFE": "Pfizer",
    "KO": "Coca-Cola",
    "PEP": "PepsiCo",
    "WMT": "Walmart",
    "HD": "Home Depot",
    "CAT": "Caterpillar",
    "DE": "Deere",
    "NEE": "NextEra Energy",
    "DIS": "Walt Disney",
    "MCD": "McDonald",
    "NKE": "Nike",
    "COST": "Costco",
}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HI. EPA ECHO Pipeline")
    parser.add_argument("--company", help="Search a single company name")
    parser.add_argument("--output", default="data/epa")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.company:
        print(f"Searching EPA ECHO for: {args.company}")
        facilities = search_facilities(args.company)
        signals = compute_epa_signals(args.company, facilities)
        print(json.dumps(signals, indent=2))
        outfile = output_dir / f"{args.company.replace(' ', '_')}.json"
        with open(outfile, "w") as f:
            json.dump(signals, f, indent=2)
    else:
        companies = list(COMPANY_EPA_NAMES.items())
        if args.limit:
            companies = companies[:args.limit]

        print(f"HI. EPA ECHO Pipeline — Processing {len(companies)} companies")
        all_signals = []

        for ticker, name in companies:
            print(f"\n  {ticker}: Searching for '{name}'...")
            facilities = search_facilities(name)
            signals = compute_epa_signals(name, facilities)
            signals["ticker"] = ticker
            all_signals.append(signals)

            outfile = output_dir / f"{ticker}.json"
            with open(outfile, "w") as f:
                json.dump(signals, f, indent=2)

            if signals.get("a_signals", {}).get("total_violations_3yr", 0) > 0:
                v = signals["a_signals"]["total_violations_3yr"]
                flag = signals["a_signals"].get("violation_flag", "")
                print(f"    {v} violations — {flag}")
            else:
                print(f"    Clean or no facilities found")

        combined = output_dir / "all_companies.json"
        with open(combined, "w") as f:
            json.dump(all_signals, f, indent=2)

        print(f"\nDone. Output: {combined}")


if __name__ == "__main__":
    main()
