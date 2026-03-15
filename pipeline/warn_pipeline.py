#!/usr/bin/env python3
"""
WARN Act Pipeline — Worker Adjustment and Retraining Notification
Sources:
  1. Federal Reserve Bank of Cleveland aggregated data (free CSV)
  2. State-level WARN databases (California, New York, others)
  3. WARN Firehose search (free browsing)

The WARN Act requires employers with 100+ employees to give 60-day
advance notice of mass layoffs (50+ workers) or plant closings.
This is LEGALLY REQUIRED data — companies cannot hide it.

Maps to: H (human displacement), Heartbeat alerts
This is the strongest H-dimension signal available.

No API key needed.
"""

import json, csv, time, sys, os, re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

try:
    import requests
except ImportError:
    print("Install: pip install requests --break-system-packages")
    sys.exit(1)

HEADERS = {"User-Agent": "HI-Score-Engine admin@thehibalance.org"}

# Major state WARN databases (direct CSV/data access)
STATE_SOURCES = {
    "CA": {
        "name": "California",
        "url": "https://edd.ca.gov/en/jobs_and_training/Layoff_Services_WARN",
        "type": "manual",  # Must download manually
    },
    "NY": {
        "name": "New York",
        "url": "https://dol.ny.gov/warn-notices",
        "type": "manual",
    },
}


def load_tickers():
    """Load known companies for matching."""
    companies = {}
    sf = Path("data/scores/all_scores.json")
    if sf.exists():
        for c in json.load(open(sf)):
            name = c.get("company", "").lower().strip()
            ticker = c.get("ticker", "")
            if name:
                companies[name] = ticker
                # Also index by simplified name
                simple = re.sub(r'\s+(inc|corp|llc|ltd|co|plc|sa|ag|nv|se)\.?$', '', name, flags=re.IGNORECASE).strip()
                if simple != name:
                    companies[simple] = ticker
    return companies


def fetch_fed_warn_data():
    """
    Fetch aggregated WARN data from Federal Reserve Bank of Cleveland.
    They publish state-level monthly counts as CSV.
    """
    url = "https://www.openicpsr.org/openicpsr/project/155161/version/V8/view"
    print("  Federal Reserve WARN data:")
    print("  Note: Download manually from:")
    print(f"    {url}")
    print("  Save the WARNData CSV to: data/warn/fed_warn_data.csv")
    print("  This contains state-level monthly aggregated layoff counts.")
    return None


def fetch_california_warn():
    """
    Fetch California WARN notices.
    CA EDD publishes WARN data — we try to get the recent page.
    """
    try:
        url = "https://edd.ca.gov/en/jobs_and_training/Layoff_Services_WARN"
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            # Extract company names and layoff counts from the page
            # This is a simplified parser — real implementation would use BeautifulSoup
            text = r.text
            return {"status": "page_fetched", "size": len(text)}
        return None
    except:
        return None


def parse_warn_csv(csv_path):
    """
    Parse a WARN notice CSV file.
    Expected columns vary by state but typically include:
    Company, Location, Employees Affected, Date, Type (Layoff/Closure)
    """
    records = []
    try:
        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Flexible column matching
                company = ""
                employees = None
                date = ""
                notice_type = ""

                for key, val in row.items():
                    key_lower = key.lower().strip()
                    if "company" in key_lower or "employer" in key_lower or "business" in key_lower:
                        company = val.strip()
                    elif "employee" in key_lower or "worker" in key_lower or "affected" in key_lower or "number" in key_lower:
                        try:
                            employees = int(re.sub(r'[^\d]', '', val)) if val.strip() else None
                        except:
                            pass
                    elif "date" in key_lower:
                        date = val.strip()
                    elif "type" in key_lower or "reason" in key_lower:
                        notice_type = val.strip()

                if company:
                    records.append({
                        "company": company,
                        "employees_affected": employees,
                        "date": date,
                        "type": notice_type,
                    })
    except Exception as e:
        print(f"  Error parsing {csv_path}: {e}")

    return records


def match_to_scored_companies(warn_records, known_companies):
    """Match WARN records to companies in our scored database."""
    matched = defaultdict(lambda: {
        "total_affected": 0,
        "notices": [],
        "notice_count": 0,
        "ticker": None,
        "latest_date": "",
    })

    for record in warn_records:
        warn_name = record["company"].lower().strip()
        # Try exact match
        ticker = known_companies.get(warn_name)
        # Try simplified match
        if not ticker:
            simple = re.sub(r'\s+(inc|corp|llc|ltd|co|plc)\.?$', '', warn_name, flags=re.IGNORECASE).strip()
            ticker = known_companies.get(simple)
        # Try partial match
        if not ticker:
            for known_name, known_ticker in known_companies.items():
                if warn_name in known_name or known_name in warn_name:
                    ticker = known_ticker
                    break

        key = warn_name
        if ticker:
            # Use ticker as the canonical key
            key = ticker.lower()

        m = matched[key]
        if ticker:
            m["ticker"] = ticker
        if record["employees_affected"]:
            m["total_affected"] += record["employees_affected"]
        m["notices"].append(record)
        m["notice_count"] += 1
        if record["date"] and record["date"] > m["latest_date"]:
            m["latest_date"] = record["date"]

    return matched


def run_pipeline():
    output_dir = Path("data/warn")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  WARN Act Pipeline — Legally Required Layoff Notices")
    print(f"{'='*60}")
    print(f"  The strongest H-dimension signal available.")
    print(f"  Companies CANNOT hide WARN filings.")
    print(f"{'='*60}\n")

    known_companies = load_tickers()
    print(f"  Known companies to match against: {len(known_companies)}")

    # Check for manually downloaded WARN CSVs
    all_warn_records = []
    csv_files = list(output_dir.glob("*.csv"))

    if csv_files:
        for csv_file in csv_files:
            print(f"\n  Parsing: {csv_file.name}")
            records = parse_warn_csv(csv_file)
            print(f"    Found {len(records)} WARN notices")
            all_warn_records.extend(records)
    else:
        print(f"\n  No WARN CSV files found in {output_dir}/")
        print(f"  ")
        print(f"  To add WARN data, download CSVs from any of these sources:")
        print(f"  ")
        print(f"  FREE SOURCES:")
        print(f"    1. California EDD WARN:")
        print(f"       https://edd.ca.gov/en/jobs_and_training/Layoff_Services_WARN")
        print(f"       → Save as: data/warn/california_warn.csv")
        print(f"  ")
        print(f"    2. New York DOL WARN:")
        print(f"       https://dol.ny.gov/warn-notices")
        print(f"       → Save as: data/warn/newyork_warn.csv")
        print(f"  ")
        print(f"    3. Federal Reserve Cleveland (aggregated all states):")
        print(f"       https://www.openicpsr.org/openicpsr/project/155161/")
        print(f"       → Save as: data/warn/fed_warn_data.csv")
        print(f"  ")
        print(f"    4. WARN Firehose (86,000+ notices, CSV export):")
        print(f"       https://warnfirehose.com/data")
        print(f"       → Save as: data/warn/warnfirehose.csv")
        print(f"  ")
        print(f"    5. WARNTracker.com (by company/state):")
        print(f"       https://www.warntracker.com/")
        print(f"  ")
        print(f"  Place any CSV in data/warn/ and re-run this pipeline.")
        print(f"  The parser auto-detects common column formats.")

    # Also try to build from existing layoffs.fyi data
    layoffs_path = Path("data/layoffs/all_companies.json")
    if layoffs_path.exists():
        layoffs_data = json.load(open(layoffs_path))
        print(f"\n  Also incorporating layoffs.fyi data: {len(layoffs_data)} companies")
        for lo in layoffs_data:
            if lo.get("h_signals", {}).get("total_laid_off", 0) > 0:
                all_warn_records.append({
                    "company": lo.get("company", ""),
                    "employees_affected": lo["h_signals"]["total_laid_off"],
                    "date": lo["h_signals"].get("latest_layoff_date", ""),
                    "type": "layoff (via layoffs.fyi)",
                })

    if not all_warn_records:
        print(f"\n  No WARN data to process yet.")
        print(f"  Download a CSV and re-run.")

        # Create empty output so other pipelines don't break
        with open(output_dir / "all_companies.json", "w") as f:
            json.dump([], f)
        print(f"\n{'='*60}\n")
        return []

    # Match to our scored companies
    print(f"\n  Total WARN/layoff records: {len(all_warn_records)}")
    matched = match_to_scored_companies(all_warn_records, known_companies)

    # Build output records
    records = []
    for key, data in matched.items():
        company_name = data["notices"][0]["company"] if data["notices"] else key.title()

        severity = "low"
        if data["total_affected"] > 10000:
            severity = "critical"
        elif data["total_affected"] > 5000:
            severity = "high"
        elif data["total_affected"] > 1000:
            severity = "medium"

        records.append({
            "company": company_name,
            "ticker": data["ticker"],
            "h_signals": {
                "warn_total_affected": data["total_affected"],
                "warn_notice_count": data["notice_count"],
                "warn_latest_date": data["latest_date"],
            },
            "heartbeat": {
                "warn_severity": severity,
                "warn_notices": data["notice_count"],
                "warn_displaced": data["total_affected"],
            },
            "source": "WARN Act",
        })

    records.sort(key=lambda x: x["h_signals"]["warn_total_affected"], reverse=True)

    output_file = output_dir / "all_companies.json"
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)

    # Stats
    total_displaced = sum(r["h_signals"]["warn_total_affected"] for r in records)
    matched_to_scored = sum(1 for r in records if r["ticker"])
    critical = sum(1 for r in records if r["heartbeat"]["warn_severity"] == "critical")
    high = sum(1 for r in records if r["heartbeat"]["warn_severity"] == "high")

    print(f"\n  Companies with WARN data: {len(records)}")
    print(f"  Matched to scored companies: {matched_to_scored}")
    print(f"  Total workers displaced: {total_displaced:,}")
    print(f"  Critical (>10K): {critical}")
    print(f"  High (>5K): {high}")

    if records:
        print(f"\n  Top 10 by displacement:")
        for r in records[:10]:
            t = r["ticker"] or "—"
            sev = r["heartbeat"]["warn_severity"]
            icon = "🔴" if sev == "critical" else "🟡" if sev == "high" else "🟠" if sev == "medium" else "⚪"
            print(f"    {icon} {r['company'][:25]:25s} {t:>6s}  {r['h_signals']['warn_total_affected']:>8,} workers  ({r['h_signals']['warn_notice_count']} notices)")

    print(f"\n  Output: {output_file}")
    print(f"{'='*60}\n")

    return records


if __name__ == "__main__":
    run_pipeline()
