#!/usr/bin/env python3
"""
HI. — BLS Data Pipeline
Pulls industry wage and employment benchmarks from Bureau of Labor Statistics.

Dimensions served:
  H — Human Consciousness (industry employment trends, wage levels)
  U — Understanding & Empathy (wage fairness vs industry median)

API: https://api.bls.gov/publicAPI/v2/timeseries/data/
Free tier: 25 requests/day without key, 500/day with free key.
Register at: https://data.bls.gov/registrationEngine/

Usage:
  python bls_pipeline.py
  python bls_pipeline.py --api-key YOUR_KEY  # Higher rate limit
"""

import json, os, sys, time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from pathlib import Path

USER_AGENT = "HI-Pipeline/1.0 (thehibalance.org; contact@thehibalance.org)"
BLS_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
RATE_LIMIT = 1.0  # BLS is strict on rate limits
OUTPUT_DIR = Path("data/bls")

# BLS series IDs for industry-level data
# Format: CEU{industry_code}01 for employment, CEU{industry_code}03 for hourly earnings
# NAICS super-sectors
INDUSTRY_SERIES = {
    "tech": {
        "name": "Information / Technology",
        "employment": "CES5000000001",     # Information sector employment (thousands)
        "earnings": "CES5000000003",        # Information sector avg hourly earnings
    },
    "retail": {
        "name": "Retail Trade",
        "employment": "CES4200000001",
        "earnings": "CES4200000003",
    },
    "finance": {
        "name": "Financial Activities",
        "employment": "CES5500000001",
        "earnings": "CES5500000003",
    },
    "healthcare": {
        "name": "Education and Health Services",
        "employment": "CES6500000001",
        "earnings": "CES6500000003",
    },
    "manufacturing": {
        "name": "Manufacturing",
        "employment": "CES3000000001",
        "earnings": "CES3000000003",
    },
    "energy": {
        "name": "Mining and Logging (includes Energy)",
        "employment": "CES1000000001",
        "earnings": "CES1000000003",
    },
    "food": {
        "name": "Leisure and Hospitality (includes Food Service)",
        "employment": "CES7000000001",
        "earnings": "CES7000000003",
    },
    "total": {
        "name": "Total Private",
        "employment": "CES0500000001",
        "earnings": "CES0500000003",
    },
}


def fetch_bls_data(series_ids, start_year=2022, end_year=2025, api_key=None):
    """Fetch time series data from BLS API."""
    time.sleep(RATE_LIMIT)

    payload = json.dumps({
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year),
        "registrationkey": api_key or "",
    }).encode("utf-8")

    req = Request(BLS_URL, data=payload, headers={
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    })

    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, Exception) as e:
        print(f"  BLS Error: {e}")
        return None


def extract_latest_value(series_data):
    """Extract the most recent value from a BLS time series."""
    if not series_data or not series_data.get("data"):
        return None

    data = series_data["data"]
    # BLS returns most recent first
    for point in data:
        if point.get("period", "").startswith("M"):  # Monthly data
            return {
                "value": float(point["value"]),
                "year": point["year"],
                "period": point["period"],
                "periodName": point.get("periodName", ""),
            }
    return None


def extract_trend(series_data, years=3):
    """Extract annual averages for trend analysis."""
    if not series_data or not series_data.get("data"):
        return []

    data = series_data["data"]
    # Filter to annual averages (M13) or compute from monthly
    annual = [d for d in data if d.get("period") == "M13"]

    if not annual:
        # Compute annual averages from monthly data
        by_year = {}
        for d in data:
            if d.get("period", "").startswith("M") and d["period"] != "M13":
                year = d["year"]
                if year not in by_year:
                    by_year[year] = []
                by_year[year].append(float(d["value"]))

        annual = [{"year": y, "value": str(round(sum(vals) / len(vals), 1))}
                  for y, vals in sorted(by_year.items(), reverse=True)]

    return [{"year": a["year"], "value": float(a["value"])} for a in annual[:years]]


def compute_bls_signals(bls_data):
    """Process BLS data into HUMAN-relevant signals."""
    signals = {
        "source": "BLS",
        "retrieved": time.strftime("%Y-%m-%d"),
        "industries": {},
    }

    if not bls_data or bls_data.get("status") != "REQUEST_SUCCEEDED":
        signals["error"] = "BLS request failed"
        return signals

    # Process each series
    series_map = {}
    for series in bls_data.get("Results", {}).get("series", []):
        sid = series.get("seriesID", "")
        series_map[sid] = series

    # Compute per-industry benchmarks
    for industry_key, config in INDUSTRY_SERIES.items():
        emp_series = series_map.get(config["employment"])
        earn_series = series_map.get(config["earnings"])

        industry_data = {"name": config["name"]}

        # Latest employment
        emp_latest = extract_latest_value(emp_series)
        if emp_latest:
            industry_data["employment_thousands"] = emp_latest["value"]
            industry_data["employment_date"] = f"{emp_latest['periodName']} {emp_latest['year']}"

        # Employment trend
        emp_trend = extract_trend(emp_series)
        if len(emp_trend) >= 2:
            industry_data["employment_trend"] = emp_trend
            current = emp_trend[0]["value"]
            prior = emp_trend[1]["value"]
            if prior > 0:
                industry_data["employment_change_pct"] = round((current - prior) / prior * 100, 1)

        # Latest hourly earnings
        earn_latest = extract_latest_value(earn_series)
        if earn_latest:
            industry_data["avg_hourly_earnings"] = earn_latest["value"]
            industry_data["earnings_date"] = f"{earn_latest['periodName']} {earn_latest['year']}"

        # Earnings trend
        earn_trend = extract_trend(earn_series)
        if len(earn_trend) >= 2:
            industry_data["earnings_trend"] = earn_trend
            current = earn_trend[0]["value"]
            prior = earn_trend[1]["value"]
            if prior > 0:
                industry_data["wage_growth_pct"] = round((current - prior) / prior * 100, 1)

        signals["industries"][industry_key] = industry_data

    # Compute cross-industry insights
    total = signals["industries"].get("total", {})
    if total.get("avg_hourly_earnings"):
        national_avg = total["avg_hourly_earnings"]
        for key, ind in signals["industries"].items():
            if key != "total" and ind.get("avg_hourly_earnings"):
                ratio = ind["avg_hourly_earnings"] / national_avg
                ind["wage_vs_national"] = round(ratio, 2)
                if ratio < 0.75:
                    ind["wage_flag"] = "LOW — significantly below national average"
                elif ratio > 1.25:
                    ind["wage_flag"] = "HIGH — significantly above national average"

    return signals


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HI. BLS Pipeline")
    parser.add_argument("--api-key", help="BLS API key (optional, higher rate limit)")
    parser.add_argument("--output", default="data/bls")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("HI. BLS Pipeline — Fetching industry benchmarks")

    # Collect all series IDs
    all_series = []
    for config in INDUSTRY_SERIES.values():
        all_series.append(config["employment"])
        all_series.append(config["earnings"])

    # BLS allows up to 50 series per request
    print(f"  Fetching {len(all_series)} series...")
    bls_data = fetch_bls_data(all_series, start_year=2022, end_year=2025, api_key=args.api_key)

    if not bls_data:
        print("  Failed to fetch BLS data")
        return

    signals = compute_bls_signals(bls_data)

    # Save
    outfile = output_dir / "industry_benchmarks.json"
    with open(outfile, "w") as f:
        json.dump(signals, f, indent=2)

    # Print summary
    print(f"\n  Industry Benchmarks:")
    for key, ind in signals.get("industries", {}).items():
        emp = ind.get("employment_thousands", "?")
        earn = ind.get("avg_hourly_earnings", "?")
        change = ind.get("employment_change_pct", "?")
        print(f"    {ind['name']:40s}  {emp:>8}K jobs  ${earn}/hr  ({change}% YoY)")

    print(f"\n  Output: {outfile}")


if __name__ == "__main__":
    main()
