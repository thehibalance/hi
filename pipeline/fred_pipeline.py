#!/usr/bin/env python3
"""
FRED (Federal Reserve Economic Data) Pipeline
Source: https://fred.stlouisfed.org
Free API: Unlimited for registered users

Pulls: Industry wage benchmarks, unemployment, productivity, labor costs
Maps to: H (wage benchmarks), U (labor conditions), M (economic context)

Get free API key: https://fred.stlouisfed.org/docs/api/api_key.html
"""

import json, sys, os
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install: pip install requests --break-system-packages")
    sys.exit(1)

BASE = "https://api.stlouisfed.org/fred"

# Key economic series for HUMAN scoring
SERIES = {
    # Wage & compensation
    "avg_hourly_earnings": "CES0500000003",      # Avg hourly earnings, all private
    "avg_weekly_hours": "CES0500000002",          # Avg weekly hours, all private
    "employment_cost_index": "ECIWAG",            # Employment Cost Index - wages
    "unit_labor_costs": "ULCNFB",                 # Unit Labor Costs (nonfarm business)

    # Employment
    "unemployment_rate": "UNRATE",                 # Civilian unemployment rate
    "total_nonfarm": "PAYEMS",                     # Total nonfarm payrolls (thousands)
    "job_openings": "JTSJOL",                      # Job openings total
    "quits_rate": "JTSQUR",                        # Quits rate (people choosing to leave)

    # Productivity & output
    "labor_productivity": "OPHNFB",                # Output per hour, nonfarm business
    "real_gdp_per_capita": "A939RX0Q048SBEA",     # Real GDP per capita

    # Industry-specific
    "tech_employment": "CES6000000001",            # Info sector employment
    "manufacturing_employment": "MANEMP",          # Manufacturing employment
    "retail_employment": "USTRADE",                # Retail trade employment
    "healthcare_employment": "CES6562000001",      # Healthcare employment
    "finance_employment": "CES5000000001",         # Financial activities employment

    # AI/Automation indicators
    "industrial_production": "INDPRO",             # Industrial Production Index
    "capacity_utilization": "TCU",                 # Capacity Utilization
}


def get_api_key():
    key = os.environ.get("FRED_KEY", "")
    if not key:
        kf = Path("data/fred_key.txt")
        if kf.exists(): key = kf.read_text().strip()
    if not key:
        print("No FRED API key. Get free key at:")
        print("  https://fred.stlouisfed.org/docs/api/api_key.html")
        print("Then: echo YOUR_KEY > data/fred_key.txt")
        sys.exit(1)
    return key


def fetch_series(series_id, key, limit=12):
    """Fetch latest observations for a FRED series."""
    try:
        r = requests.get(f"{BASE}/series/observations", params={
            "series_id": series_id,
            "api_key": key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit,
        }, timeout=15)
        d = r.json()
        obs = d.get("observations", [])
        values = []
        for o in obs:
            try:
                v = float(o["value"])
                values.append({"date": o["date"], "value": v})
            except (ValueError, KeyError):
                continue
        return values
    except Exception as e:
        print(f"    Error fetching {series_id}: {e}")
        return []


def run_pipeline():
    key = get_api_key()
    output_dir = Path("data/fred")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  FRED (Federal Reserve Economic Data) Pipeline")
    print(f"{'='*60}")
    print(f"  Series to fetch: {len(SERIES)}")
    print(f"{'='*60}\n")

    benchmarks = {}
    for name, series_id in SERIES.items():
        data = fetch_series(series_id, key)
        if data:
            latest = data[0]["value"]
            prev = data[-1]["value"] if len(data) > 1 else latest
            change = round((latest - prev) / prev * 100, 2) if prev != 0 else 0

            benchmarks[name] = {
                "series_id": series_id,
                "latest_value": latest,
                "latest_date": data[0]["date"],
                "oldest_value": prev,
                "oldest_date": data[-1]["date"] if len(data) > 1 else data[0]["date"],
                "change_pct": change,
                "observations": len(data),
            }
            print(f"  {name:35s} = {latest:>12.2f}  ({change:+.1f}%)")
        else:
            print(f"  {name:35s} = FAILED")

    # Compute derived benchmarks useful for HUMAN scoring
    derived = {}

    # Productivity vs wages gap (key H dimension signal)
    if "labor_productivity" in benchmarks and "avg_hourly_earnings" in benchmarks:
        prod_change = benchmarks["labor_productivity"]["change_pct"]
        wage_change = benchmarks["avg_hourly_earnings"]["change_pct"]
        derived["productivity_wage_gap"] = round(prod_change - wage_change, 2)
        print(f"\n  DERIVED: Productivity-Wage Gap = {derived['productivity_wage_gap']:+.2f}%")

    # Quits rate (high = workers have options = good labor market)
    if "quits_rate" in benchmarks:
        derived["labor_market_strength"] = benchmarks["quits_rate"]["latest_value"]
        print(f"  DERIVED: Labor Market Strength (quits rate) = {derived['labor_market_strength']:.1f}%")

    # Tech employment trend
    if "tech_employment" in benchmarks:
        derived["tech_employment_trend"] = benchmarks["tech_employment"]["change_pct"]
        print(f"  DERIVED: Tech Employment Trend = {derived['tech_employment_trend']:+.1f}%")

    output = {
        "source": "FRED",
        "fetched": str(Path(".")),
        "series_count": len(benchmarks),
        "benchmarks": benchmarks,
        "derived": derived,
    }

    output_file = output_dir / "industry_benchmarks.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  COMPLETE — {len(benchmarks)} series fetched")
    print(f"  Derived benchmarks: {len(derived)}")
    print(f"  Output: {output_file}")
    print(f"  Used by scoring engine for industry normalization")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_pipeline()
