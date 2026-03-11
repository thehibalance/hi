#!/usr/bin/env python3
"""
HI. — SEC EDGAR Data Pipeline
Phase 2, Track A: Free Public Data Ingestion

Pulls structured XBRL financial data from SEC EDGAR (free, no API key).
Extracts signals relevant to HUMAN framework dimensions.

Data extracted per company:
  H dimension: headcount, revenue/employee, AI capex signals
  M dimension: executive compensation, fines/penalties
  A dimension: environmental disclosures presence
  N dimension: filing frequency, disclosure completeness

Usage:
  python sec_edgar_pipeline.py                    # Process all seed companies
  python sec_edgar_pipeline.py --ticker AAPL       # Process one company
  python sec_edgar_pipeline.py --output data/sec   # Custom output dir

SEC EDGAR API docs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
Rate limit: 10 requests/second with User-Agent header identifying you.
"""

import json, os, sys, time, re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────
USER_AGENT = "HI-Pipeline/1.0 (thehibalance.org; contact@thehibalance.org)"
BASE_URL = "https://data.sec.gov"
EFTS_URL = "https://efts.sec.gov/LATEST"
RATE_LIMIT = 0.12  # ~8 req/sec (stay under 10)
OUTPUT_DIR = Path("data/sec")

# XBRL tags we care about for HUMAN scoring
XBRL_TAGS = {
    # H dimension — Human Consciousness
    "headcount": [
        "us-gaap/EntityNumberOfEmployees",
        "dei/EntityNumberOfEmployees",
    ],
    "revenue": [
        "us-gaap/Revenues",
        "us-gaap/RevenueFromContractWithCustomerExcludingAssessedTax",
        "us-gaap/SalesRevenueNet",
    ],
    "rd_expense": [
        "us-gaap/ResearchAndDevelopmentExpense",
    ],
    # M dimension — Moral & Ethical
    "exec_comp": [
        "us-gaap/ShareBasedCompensation",
    ],
    "litigation": [
        "us-gaap/LossContingencyEstimateOfPossibleLoss",
        "us-gaap/LitigationSettlementAmountAwardedToOtherParty",
    ],
    # A dimension — Alive & Environmental
    "total_assets": [
        "us-gaap/Assets",
    ],
    "capex": [
        "us-gaap/PaymentsToAcquirePropertyPlantAndEquipment",
    ],
}

# ── Helpers ───────────────────────────────────────────────────────────
def fetch_json(url):
    """Fetch JSON from SEC with rate limiting and proper User-Agent."""
    time.sleep(RATE_LIMIT)
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        if e.code == 404:
            return None
        print(f"  HTTP {e.code} for {url}")
        return None
    except (URLError, Exception) as e:
        print(f"  Error: {e} for {url}")
        return None


def get_cik_from_ticker(ticker):
    """Look up CIK number from ticker symbol using SEC company tickers file."""
    url = "https://www.sec.gov/files/company_tickers.json"
    data = fetch_json(url)
    if not data:
        return None
    for entry in data.values():
        if entry.get("ticker", "").upper() == ticker.upper():
            return str(entry["cik_str"]).zfill(10)
    return None


def get_submissions(cik):
    """Get company submission history and metadata."""
    url = f"{BASE_URL}/submissions/CIK{cik}.json"
    return fetch_json(url)


def get_company_facts(cik):
    """Get all XBRL facts for a company — the richest single endpoint."""
    url = f"{BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json"
    return fetch_json(url)


def extract_latest_fact(facts_data, tag_path):
    """Extract the most recent annual value for a given XBRL tag."""
    parts = tag_path.split("/")
    taxonomy = parts[0]  # e.g., "us-gaap" or "dei"
    tag = parts[1]

    try:
        tag_data = facts_data["facts"][taxonomy][tag]
    except (KeyError, TypeError):
        return None

    # Get USD units (or pure number for headcount)
    units = tag_data.get("units", {})
    values = units.get("USD", units.get("pure", units.get("shares", [])))
    if not values:
        # Try first available unit
        for unit_key, unit_vals in units.items():
            if unit_vals:
                values = unit_vals
                break

    if not values:
        return None

    # Filter to annual filings (10-K) and get most recent
    annual = [v for v in values if v.get("form") in ("10-K", "10-K/A", "20-F")]
    if not annual:
        annual = values  # Fall back to any filing

    # Sort by end date, most recent first
    annual.sort(key=lambda x: x.get("end", ""), reverse=True)

    if annual:
        return {
            "value": annual[0].get("val"),
            "end": annual[0].get("end"),
            "form": annual[0].get("form"),
            "filed": annual[0].get("filed"),
        }
    return None


def extract_time_series(facts_data, tag_path, years=3):
    """Extract annual values for trend analysis (e.g., headcount over time)."""
    parts = tag_path.split("/")
    taxonomy = parts[0]
    tag = parts[1]

    try:
        tag_data = facts_data["facts"][taxonomy][tag]
    except (KeyError, TypeError):
        return []

    units = tag_data.get("units", {})
    values = units.get("USD", units.get("pure", units.get("shares", [])))
    if not values:
        for unit_vals in units.values():
            if unit_vals:
                values = unit_vals
                break

    if not values:
        return []

    # Filter to 10-K, deduplicate by fiscal year end
    annual = [v for v in values if v.get("form") in ("10-K", "10-K/A", "20-F")]
    if not annual:
        annual = values

    annual.sort(key=lambda x: x.get("end", ""), reverse=True)

    # Deduplicate by year
    seen_years = set()
    result = []
    for v in annual:
        year = v.get("end", "")[:4]
        if year and year not in seen_years:
            seen_years.add(year)
            result.append({"year": year, "value": v.get("val"), "end": v.get("end")})
        if len(result) >= years:
            break

    return result


def search_filings_for_keywords(cik, keywords):
    """Search EDGAR full-text search for AI-related terms in recent filings."""
    # Use the free EDGAR full-text search (EFTS)
    url = f"{EFTS_URL}/search-index?q=%22{'+'.join(keywords)}%22&dateRange=custom&startdt=2023-01-01&enddt=2026-12-31&forms=10-K&ciks={cik.lstrip('0')}"
    # EFTS returns HTML, so we'll use a simpler approach
    # Just check if the company mentions AI-related terms in filings
    return None  # We'll enhance this later with NLP


def compute_signals(company_name, ticker, facts, submissions):
    """Compute HUMAN-relevant signals from SEC data."""
    signals = {
        "company": company_name,
        "ticker": ticker,
        "source": "SEC EDGAR",
        "retrieved": time.strftime("%Y-%m-%d"),
        "h_signals": {},
        "u_signals": {},
        "m_signals": {},
        "a_signals": {},
        "n_signals": {},
    }

    if not facts:
        signals["error"] = "No XBRL data available"
        return signals

    # ── H Dimension: Human Consciousness ──────────────────────────────
    # Headcount
    for tag in XBRL_TAGS["headcount"]:
        hc = extract_latest_fact(facts, tag)
        if hc and hc["value"]:
            signals["h_signals"]["headcount"] = hc
            # Get trend
            trend = extract_time_series(facts, tag)
            if len(trend) >= 2:
                signals["h_signals"]["headcount_trend"] = trend
                current = trend[0]["value"]
                prior = trend[1]["value"]
                if current and prior and prior > 0:
                    signals["h_signals"]["headcount_change_pct"] = round(
                        (current - prior) / prior * 100, 1
                    )
            break

    # Revenue (for revenue-per-employee)
    for tag in XBRL_TAGS["revenue"]:
        rev = extract_latest_fact(facts, tag)
        if rev and rev["value"]:
            signals["h_signals"]["revenue"] = rev
            # Revenue per employee
            hc_val = signals["h_signals"].get("headcount", {}).get("value")
            if hc_val and hc_val > 0:
                signals["h_signals"]["revenue_per_employee"] = round(
                    rev["value"] / hc_val
                )
            # Revenue trend
            trend = extract_time_series(facts, tag)
            if len(trend) >= 2:
                signals["h_signals"]["revenue_trend"] = trend
            break

    # R&D expense (proxy for AI investment)
    for tag in XBRL_TAGS["rd_expense"]:
        rd = extract_latest_fact(facts, tag)
        if rd and rd["value"]:
            signals["h_signals"]["rd_expense"] = rd
            trend = extract_time_series(facts, tag)
            if len(trend) >= 2:
                signals["h_signals"]["rd_trend"] = trend
                current = trend[0]["value"]
                prior = trend[1]["value"]
                if current and prior and prior > 0:
                    signals["h_signals"]["rd_change_pct"] = round(
                        (current - prior) / prior * 100, 1
                    )
            break

    # AI displacement signal: R&D growing while headcount shrinking
    hc_change = signals["h_signals"].get("headcount_change_pct")
    rd_change = signals["h_signals"].get("rd_change_pct")
    if hc_change is not None and rd_change is not None:
        displacement = rd_change - hc_change
        signals["h_signals"]["displacement_signal"] = round(displacement, 1)
        if displacement > 30:
            signals["h_signals"]["displacement_flag"] = "HIGH — R&D growing significantly faster than headcount"
        elif displacement > 15:
            signals["h_signals"]["displacement_flag"] = "MODERATE — R&D outpacing headcount growth"
        else:
            signals["h_signals"]["displacement_flag"] = "LOW — headcount keeping pace with R&D"

    # Revenue per employee flag (humanwashing signal)
    rpe = signals["h_signals"].get("revenue_per_employee")
    if rpe and rpe > 2000000:  # >$2M/employee is very high automation
        signals["h_signals"]["automation_flag"] = f"HIGH — ${rpe:,}/employee suggests heavy automation"
    elif rpe and rpe > 1000000:
        signals["h_signals"]["automation_flag"] = f"MODERATE — ${rpe:,}/employee"

    # ── M Dimension: Moral & Ethical ──────────────────────────────────
    for tag in XBRL_TAGS["exec_comp"]:
        ec = extract_latest_fact(facts, tag)
        if ec and ec["value"]:
            signals["m_signals"]["stock_comp"] = ec
            break

    for tag in XBRL_TAGS["litigation"]:
        lit = extract_latest_fact(facts, tag)
        if lit and lit["value"]:
            signals["m_signals"]["litigation"] = lit
            break

    # ── A Dimension: Alive & Environmental ────────────────────────────
    for tag in XBRL_TAGS["total_assets"]:
        ta = extract_latest_fact(facts, tag)
        if ta and ta["value"]:
            signals["a_signals"]["total_assets"] = ta
            break

    for tag in XBRL_TAGS["capex"]:
        cx = extract_latest_fact(facts, tag)
        if cx and cx["value"]:
            signals["a_signals"]["capex"] = cx
            trend = extract_time_series(facts, tag)
            if len(trend) >= 2:
                signals["a_signals"]["capex_trend"] = trend
            break

    # ── N Dimension: Natural Transparency ─────────────────────────────
    if submissions:
        recent = submissions.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])

        # Count filing types in last 2 years
        recent_10k = sum(1 for f, d in zip(forms, dates) if f in ("10-K", "10-K/A") and d >= "2024-01-01")
        recent_10q = sum(1 for f, d in zip(forms, dates) if f in ("10-Q", "10-Q/A") and d >= "2024-01-01")
        recent_8k = sum(1 for f, d in zip(forms, dates) if f == "8-K" and d >= "2024-01-01")

        signals["n_signals"]["recent_10k_count"] = recent_10k
        signals["n_signals"]["recent_10q_count"] = recent_10q
        signals["n_signals"]["recent_8k_count"] = recent_8k
        signals["n_signals"]["total_recent_filings"] = recent_10k + recent_10q + recent_8k

        # SIC code (industry classification)
        signals["n_signals"]["sic"] = submissions.get("sic")
        signals["n_signals"]["sic_description"] = submissions.get("sicDescription")
        signals["n_signals"]["category"] = submissions.get("category")
        signals["n_signals"]["fiscal_year_end"] = submissions.get("fiscalYearEnd")

    return signals


def process_company(ticker, company_name=None):
    """Full pipeline for one company: look up CIK, fetch data, compute signals."""
    print(f"\n{'='*60}")
    print(f"Processing: {company_name or ticker} ({ticker})")
    print(f"{'='*60}")

    # Step 1: Get CIK
    print(f"  Looking up CIK for {ticker}...")
    cik = get_cik_from_ticker(ticker)
    if not cik:
        print(f"  ✗ CIK not found for {ticker}")
        return {"company": company_name, "ticker": ticker, "error": "CIK not found"}

    print(f"  ✓ CIK: {cik}")

    # Step 2: Get submissions (metadata)
    print(f"  Fetching submissions...")
    submissions = get_submissions(cik)
    if submissions:
        name = submissions.get("name", company_name)
        print(f"  ✓ Company: {name}")
    else:
        name = company_name
        print(f"  ✗ No submissions data")

    # Step 3: Get XBRL company facts
    print(f"  Fetching XBRL facts...")
    facts = get_company_facts(cik)
    if facts:
        fact_count = sum(
            len(tags) for taxonomy in facts.get("facts", {}).values()
            for tags in [taxonomy] if isinstance(taxonomy, dict)
        )
        print(f"  ✓ XBRL data loaded")
    else:
        print(f"  ✗ No XBRL data")

    # Step 4: Compute signals
    print(f"  Computing HUMAN signals...")
    signals = compute_signals(name or ticker, ticker, facts, submissions)
    signals["cik"] = cik

    # Print summary
    h = signals.get("h_signals", {})
    print(f"\n  H signals:")
    if h.get("headcount"):
        print(f"    Headcount: {h['headcount']['value']:,} (as of {h['headcount']['end']})")
    if h.get("revenue_per_employee"):
        print(f"    Revenue/employee: ${h['revenue_per_employee']:,}")
    if h.get("displacement_flag"):
        print(f"    Displacement: {h['displacement_flag']}")
    if h.get("automation_flag"):
        print(f"    Automation: {h['automation_flag']}")

    m = signals.get("m_signals", {})
    if m.get("litigation"):
        print(f"  M signals:")
        print(f"    Litigation: ${m['litigation']['value']:,}")

    n = signals.get("n_signals", {})
    if n.get("total_recent_filings"):
        print(f"  N signals:")
        print(f"    Recent filings: {n['total_recent_filings']} (10-K: {n['recent_10k_count']}, 10-Q: {n['recent_10q_count']}, 8-K: {n['recent_8k_count']})")
        print(f"    Industry: {n.get('sic_description', 'Unknown')}")

    return signals


# ── Public company tickers from seed database ─────────────────────────
# These are the public companies from our 206-company seed database
# that will have SEC EDGAR data available
SEED_PUBLIC_COMPANIES = [
    ("AAPL", "Apple"),
    ("MSFT", "Microsoft"),
    ("GOOGL", "Google (Alphabet)"),
    ("AMZN", "Amazon"),
    ("META", "Meta (Facebook)"),
    ("TSLA", "Tesla"),
    ("NVDA", "NVIDIA"),
    ("CRM", "Salesforce"),
    ("ADBE", "Adobe"),
    ("NFLX", "Netflix"),
    ("SPOT", "Spotify"),
    ("UBER", "Uber"),
    ("ABNB", "Airbnb"),
    ("SQ", "Block (Square)"),
    ("SHOP", "Shopify"),
    ("ZM", "Zoom"),
    ("PLTR", "Palantir"),
    ("COIN", "Coinbase"),
    ("WMT", "Walmart"),
    ("TGT", "Target"),
    ("COST", "Costco"),
    ("KO", "Coca-Cola"),
    ("PEP", "PepsiCo"),
    ("MCD", "McDonald's"),
    ("SBUX", "Starbucks"),
    ("NKE", "Nike"),
    ("DIS", "Disney"),
    ("CMCSA", "Comcast"),
    ("T", "AT&T"),
    ("VZ", "Verizon"),
    ("JPM", "JPMorgan Chase"),
    ("BAC", "Bank of America"),
    ("GS", "Goldman Sachs"),
    ("WFC", "Wells Fargo"),
    ("V", "Visa"),
    ("MA", "Mastercard"),
    ("UNH", "UnitedHealth"),
    ("JNJ", "Johnson & Johnson"),
    ("PFE", "Pfizer"),
    ("CVS", "CVS Health"),
    ("XOM", "ExxonMobil"),
    ("CVX", "Chevron"),
    ("NEE", "NextEra Energy"),
    ("BA", "Boeing"),
    ("LMT", "Lockheed Martin"),
    ("RTX", "RTX (Raytheon)"),
    ("CAT", "Caterpillar"),
    ("DE", "John Deere"),
    ("GM", "General Motors"),
    ("F", "Ford"),
    ("HD", "Home Depot"),
    ("LOW", "Lowe's"),
    ("ETSY", "Etsy"),
    ("CHWY", "Chewy"),
    ("W", "Wayfair"),
    ("EBAY", "eBay"),
    ("PYPL", "PayPal"),
    ("SYY", "Sysco"),
    ("KR", "Kroger"),
]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HI. SEC EDGAR Data Pipeline")
    parser.add_argument("--ticker", help="Process a single ticker")
    parser.add_argument("--output", default="data/sec", help="Output directory")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of companies (0=all)")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.ticker:
        # Process single company
        signals = process_company(args.ticker)
        outfile = output_dir / f"{args.ticker.upper()}.json"
        with open(outfile, "w") as f:
            json.dump(signals, f, indent=2)
        print(f"\n✓ Saved to {outfile}")
    else:
        # Process all seed public companies
        companies = SEED_PUBLIC_COMPANIES
        if args.limit:
            companies = companies[:args.limit]

        print(f"HI. SEC EDGAR Pipeline — Processing {len(companies)} companies")
        print(f"Output: {output_dir}")
        print(f"Rate limit: {RATE_LIMIT}s between requests")

        all_signals = []
        for ticker, name in companies:
            try:
                signals = process_company(ticker, name)
                all_signals.append(signals)

                # Save individual file
                outfile = output_dir / f"{ticker}.json"
                with open(outfile, "w") as f:
                    json.dump(signals, f, indent=2)

            except Exception as e:
                print(f"  ✗ Error processing {ticker}: {e}")
                all_signals.append({"company": name, "ticker": ticker, "error": str(e)})

        # Save combined file
        combined = output_dir / "all_companies.json"
        with open(combined, "w") as f:
            json.dump(all_signals, f, indent=2)

        # Print summary
        print(f"\n{'='*60}")
        print(f"PIPELINE COMPLETE")
        print(f"{'='*60}")
        successful = [s for s in all_signals if "error" not in s]
        failed = [s for s in all_signals if "error" in s]
        print(f"  Processed: {len(all_signals)}")
        print(f"  Successful: {len(successful)}")
        print(f"  Failed: {len(failed)}")

        # Displacement flags
        displaced = [s for s in successful if s.get("h_signals", {}).get("displacement_flag", "").startswith("HIGH")]
        print(f"  High displacement signal: {len(displaced)}")
        for d in displaced:
            print(f"    - {d['company']}: {d['h_signals']['displacement_flag']}")

        # Automation flags
        automated = [s for s in successful if s.get("h_signals", {}).get("automation_flag", "").startswith("HIGH")]
        print(f"  High automation signal: {len(automated)}")
        for a in automated:
            print(f"    - {a['company']}: {a['h_signals']['automation_flag']}")

        print(f"\n  Output: {combined}")
        print(f"  Individual files: {output_dir}/<TICKER>.json")


if __name__ == "__main__":
    main()
