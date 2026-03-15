#!/usr/bin/env python3
"""
Layoffs.fyi Pipeline — Tech Layoff Tracker
Source: https://layoffs.fyi
No API — data scraped from public Google Sheet

Pulls: Company layoff history (date, count, percentage, industry, stage)
Maps to: H (human consciousness — are they cutting humans?), heartbeat alerts

Note: layoffs.fyi maintains a public Google Sheet. This pipeline reads a cached CSV.
Download latest from: https://layoffs.fyi/ (click "Download Data")
Save as: data/layoffs/layoffs.csv
"""

import json, csv, sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


def run_pipeline():
    output_dir = Path("data/layoffs")
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "layoffs.csv"
    if not csv_path.exists():
        print(f"\n{'='*60}")
        print(f"  Layoffs.fyi Pipeline")
        print(f"{'='*60}")
        print(f"  CSV not found at: {csv_path}")
        print(f"  ")
        print(f"  To get the data:")
        print(f"  1. Visit https://layoffs.fyi")
        print(f"  2. Click the spreadsheet link")
        print(f"  3. File > Download > CSV")
        print(f"  4. Save as: {csv_path}")
        print(f"{'='*60}\n")
        return []

    print(f"\n{'='*60}")
    print(f"  Layoffs.fyi Pipeline")
    print(f"{'='*60}\n")

    # Parse CSV
    events = []
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            company = row.get("Company", "").strip()
            if not company:
                continue

            laid_off = row.get("# Laid Off", "").strip()
            try:
                laid_off = int(laid_off) if laid_off else None
            except ValueError:
                laid_off = None

            pct = row.get("Percentage", "").strip().replace("%", "")
            try:
                pct = float(pct) if pct else None
            except ValueError:
                pct = None

            date_str = row.get("Date", "").strip()
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d") if date_str else None
            except ValueError:
                try:
                    date = datetime.strptime(date_str, "%m/%d/%Y") if date_str else None
                except ValueError:
                    date = None

            events.append({
                "company": company,
                "laid_off": laid_off,
                "percentage": pct,
                "date": date_str,
                "date_parsed": date,
                "industry": row.get("Industry", "").strip(),
                "stage": row.get("Stage", "").strip(),
                "country": row.get("Country", "").strip(),
                "location": row.get("Location_HQ", "").strip(),
            })

    # Aggregate by company
    company_data = defaultdict(lambda: {
        "total_laid_off": 0,
        "events": [],
        "event_count": 0,
        "latest_date": None,
        "industry": "",
    })

    cutoff_1yr = datetime.now() - timedelta(days=365)

    for e in events:
        key = e["company"].lower().strip()
        cd = company_data[key]
        if e["laid_off"]:
            cd["total_laid_off"] += e["laid_off"]
        cd["events"].append({
            "date": e["date"],
            "laid_off": e["laid_off"],
            "percentage": e["percentage"],
        })
        cd["event_count"] += 1
        cd["industry"] = e["industry"] or cd["industry"]
        if e["date"]:
            if not cd["latest_date"] or e["date"] > cd["latest_date"]:
                cd["latest_date"] = e["date"]

    # Build output records
    records = []
    recent_layoffs = 0

    for name, data in company_data.items():
        # Count recent events (last 12 months)
        recent_events = [e for e in data["events"]
                        if e.get("date") and len(e["date"]) >= 10]

        record = {
            "company": name.title(),
            "ticker": None,
            "h_signals": {
                "total_laid_off": data["total_laid_off"],
                "layoff_events": data["event_count"],
                "latest_layoff_date": data["latest_date"],
            },
            "heartbeat": {
                "layoff_event_count": data["event_count"],
                "total_displaced": data["total_laid_off"],
                "severity": "high" if data["total_laid_off"] > 5000 else "medium" if data["total_laid_off"] > 1000 else "low",
            },
            "meta": {"industry": data["industry"]},
            "source": "Layoffs.fyi",
        }
        records.append(record)

    records.sort(key=lambda x: x["h_signals"]["total_laid_off"] or 0, reverse=True)

    output_file = output_dir / "all_companies.json"
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)

    total_displaced = sum(r["h_signals"]["total_laid_off"] for r in records)
    high_severity = sum(1 for r in records if r["heartbeat"]["severity"] == "high")

    print(f"  Companies with layoffs: {len(records)}")
    print(f"  Total workers displaced: {total_displaced:,}")
    print(f"  High severity (>5000): {high_severity}")
    print(f"\n  Top 10 by layoffs:")
    for r in records[:10]:
        print(f"    {r['company']:25s} {r['h_signals']['total_laid_off']:>8,}  ({r['h_signals']['layoff_events']} events)")

    print(f"\n  Output: {output_file}")
    print(f"{'='*60}\n")

    return records


if __name__ == "__main__":
    run_pipeline()
