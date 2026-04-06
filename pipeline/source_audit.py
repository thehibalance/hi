#!/usr/bin/env python3
"""
HI. — Source Audit
Dynamically checks which of the 42 data sources actually produced data
on the last pipeline run. Reports coverage gaps and staleness.

Usage:
  python3 source_audit.py
  python3 source_audit.py --data data --verbose
  python3 source_audit.py --json           # Machine-readable output
"""

import json, os, sys, time
from pathlib import Path
from datetime import datetime, timedelta


# ── Master Source Registry ──────────────────────────────────────────
# Every source we claim, its data directory, expected file, and what it feeds.
SOURCE_REGISTRY = [
    # Core 6 (run_pipeline.py)
    {"id": 1,  "name": "SEC EDGAR",           "dir": "sec",          "file": "all_companies.json",      "feeds": "H.1, H.3, H.4, M, N",   "type": "core"},
    {"id": 2,  "name": "EPA ECHO",            "dir": "epa",          "file": "all_companies.json",      "feeds": "A.2, A.3",               "type": "core"},
    {"id": 3,  "name": "BLS",                 "dir": "bls",          "file": "industry_benchmarks.json", "feeds": "H.2",                   "type": "core"},
    {"id": 4,  "name": "CDP Climate",         "dir": "cdp",          "file": "all_companies.json",      "feeds": "A.1, N.2",               "type": "core"},
    {"id": 5,  "name": "Job Boards",          "dir": "jobs",         "file": "all_companies.json",      "feeds": "H.1, H.5",              "type": "core"},
    {"id": 6,  "name": "Glassdoor",           "dir": "glassdoor",    "file": "all_companies.json",      "feeds": "U.1-U.5, M.4, M.5, H.4","type": "core"},

    # Subsignal sources 7-12 (subsignal_pipelines.py)
    {"id": 7,  "name": "CFPB Complaints",     "dir": "subsignals",   "file": "all_subsignals.json",     "feeds": "U.1, M.1",              "type": "subsignal", "key": "cfpb"},
    {"id": 8,  "name": "FEC/OpenSecrets",      "dir": "subsignals",   "file": "all_subsignals.json",     "feeds": "M.5",                   "type": "subsignal", "key": "fec"},
    {"id": 9,  "name": "CPSC Recalls",         "dir": "subsignals",   "file": "all_subsignals.json",     "feeds": "M.4",                   "type": "subsignal", "key": "cpsc"},
    {"id": 10, "name": "HIBP Breaches",        "dir": "subsignals",   "file": "all_subsignals.json",     "feeds": "M.2",                   "type": "subsignal", "key": "hibp"},
    {"id": 11, "name": "iFixit/Hardware",       "dir": "subsignals",   "file": "all_subsignals.json",     "feeds": "A.4",                   "type": "subsignal", "key": "hardware"},
    {"id": 12, "name": "EPA Land/Habitat",      "dir": "subsignals",   "file": "all_subsignals.json",     "feeds": "A.3",                   "type": "subsignal", "key": "land"},

    # Extended sources 13-24 (extended_pipelines.py)
    {"id": 13, "name": "OSHA Workplace",       "dir": "subsignals/extended", "file": "all_extended.json", "feeds": "U.2",                   "type": "extended", "key": "osha"},
    {"id": 14, "name": "FTC Enforcement",      "dir": "subsignals/extended", "file": "all_extended.json", "feeds": "M.2, N.4",              "type": "extended", "key": "ftc"},
    {"id": 15, "name": "EEOC Discrimination",  "dir": "subsignals/extended", "file": "all_extended.json", "feeds": "U.2, M.3",              "type": "extended", "key": "eeoc"},
    {"id": 16, "name": "USPTO Patents",        "dir": "subsignals/extended", "file": "all_extended.json", "feeds": "H.3, H.5",              "type": "extended", "key": "patents"},
    {"id": 17, "name": "FDA Warning Letters",  "dir": "subsignals/extended", "file": "all_extended.json", "feeds": "M.4",                   "type": "extended", "key": "fda"},
    {"id": 18, "name": "DOL Wage Data",        "dir": "subsignals/extended", "file": "all_extended.json", "feeds": "U.2",                   "type": "extended", "key": "dol"},
    {"id": 19, "name": "SEC DEF 14A Pay Ratio","dir": "subsignals/extended", "file": "all_extended.json", "feeds": "M.3, H.4",              "type": "extended", "key": "pay_ratio"},
    {"id": 20, "name": "BBB Complaints",       "dir": "subsignals/extended", "file": "all_extended.json", "feeds": "U.1",                   "type": "extended", "key": "bbb"},
    {"id": 21, "name": "SEC Form 4 Insider",   "dir": "subsignals/extended", "file": "all_extended.json", "feeds": "M.3",                   "type": "extended", "key": "insider"},
    {"id": 22, "name": "GRI Sustainability",   "dir": "subsignals/extended", "file": "all_extended.json", "feeds": "N.2",                   "type": "extended", "key": "gri"},
    {"id": 23, "name": "SBTi Climate",         "dir": "subsignals/extended", "file": "all_extended.json", "feeds": "A.1",                   "type": "extended", "key": "sbti"},
    {"id": 24, "name": "IRS 990 Charity",      "dir": "subsignals/extended", "file": "all_extended.json", "feeds": "U.5",                   "type": "extended", "key": "charity"},

    # Government sources 25-30 (collect_gov_data.py + collect_extra_sources.py)
    {"id": 25, "name": "OSHA via DOL",         "dir": "gov",          "file": "osha_violations.json",    "feeds": "M.3, A.3",              "type": "gov"},
    {"id": 26, "name": "CFPB (gov direct)",    "dir": "gov",          "file": "cfpb_complaints.json",    "feeds": "U.1, U.2",              "type": "gov"},
    {"id": 27, "name": "FEC Spending",         "dir": "gov",          "file": "fec_spending.json",       "feeds": "M.2",                   "type": "gov"},
    {"id": 28, "name": "CPSC (gov direct)",    "dir": "gov",          "file": "cpsc_recalls.json",       "feeds": "M.3",                   "type": "gov"},
    {"id": 29, "name": "FDA (gov direct)",     "dir": "gov",          "file": "fda_warnings.json",       "feeds": "M.3",                   "type": "gov"},
    {"id": 30, "name": "USPTO (gov direct)",   "dir": "gov",          "file": "patent_analysis.json",    "feeds": "H.5",                   "type": "gov"},
    {"id": 31, "name": "EPA ECHO (gov direct)","dir": "gov",          "file": "epa_echo.json",           "feeds": "A.3",                   "type": "gov"},
    {"id": 32, "name": "NHTSA Vehicle Safety", "dir": "gov",          "file": "nhtsa_complaints.json",   "feeds": "M.3",                   "type": "gov"},

    # Standalone enrichment pipelines 33-42
    {"id": 33, "name": "FMP Financial",        "dir": "fmp",          "file": "all_companies.json",      "feeds": "H.1, H.4, H.5, M",     "type": "standalone"},
    {"id": 34, "name": "Finnhub ESG",          "dir": "finnhub",      "file": "all_companies.json",      "feeds": "A.1, U.2, N.2",         "type": "standalone"},
    {"id": 35, "name": "NewsAPI Media",        "dir": "newsapi",      "file": "all_companies.json",      "feeds": "Decay detection",        "type": "standalone"},
    {"id": 36, "name": "Layoffs.fyi",          "dir": "layoffs",      "file": "all_companies.json",      "feeds": "H.1, Decay",             "type": "standalone"},
    {"id": 37, "name": "WARN Act",             "dir": "warn",         "file": "all_companies.json",      "feeds": "H.1",                    "type": "standalone"},
    {"id": 38, "name": "CEO Accountability",   "dir": "ceo",          "file": "all_companies.json",      "feeds": "M.3",                    "type": "standalone"},
    {"id": 39, "name": "DEI Index",            "dir": "dei",          "file": "all_companies.json",      "feeds": "U.3",                    "type": "standalone"},
    {"id": 40, "name": "HRC CEI",              "dir": "hrc",          "file": "all_companies.json",      "feeds": "U.3",                    "type": "standalone"},
    {"id": 41, "name": "SEC 8-K Filings",      "dir": "sec_8k",       "file": "all_companies.json",      "feeds": "N.1",                    "type": "standalone"},
    {"id": 42, "name": "Algorithmic Harm Index","dir": "scores",       "file": "all_scores.json",         "feeds": "H, U, M, N (penalties)", "type": "builtin"},
]


def check_source(source, base_dir):
    """Check if a source has data, how much, and freshness."""
    path = base_dir / source["dir"] / source["file"]

    result = {
        "id": source["id"],
        "name": source["name"],
        "type": source["type"],
        "feeds": source["feeds"],
        "status": "missing",
        "records": 0,
        "file_age_hours": None,
        "path": str(path),
    }

    if not path.exists():
        return result

    try:
        age_hours = round((time.time() - path.stat().st_mtime) / 3600, 1)
        result["file_age_hours"] = age_hours

        data = json.load(open(path))

        if source["type"] in ("subsignal", "extended"):
            # These are dict keyed by ticker; check for specific key presence
            key = source.get("key", "")
            if isinstance(data, dict):
                count = sum(1 for t, v in data.items() if key in v) if key else len(data)
                result["records"] = count
                result["status"] = "active" if count > 0 else "empty"
            else:
                result["status"] = "wrong_format"
        elif source["type"] == "builtin":
            # AHI is embedded in scores
            if isinstance(data, list):
                count = sum(1 for c in data if c.get("algo_harm", {}).get("has_harm"))
                result["records"] = count
                result["status"] = "active" if count > 0 else "empty"
        elif isinstance(data, list):
            result["records"] = len(data)
            result["status"] = "active" if len(data) > 0 else "empty"
        elif isinstance(data, dict):
            result["records"] = len(data)
            result["status"] = "active" if len(data) > 0 else "empty"
        else:
            result["status"] = "unknown_format"

        # Staleness check
        if age_hours > 168:  # > 1 week
            result["stale"] = True
        else:
            result["stale"] = False

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HI. Source Audit")
    parser.add_argument("--data", default="data", help="Base data directory")
    parser.add_argument("--verbose", action="store_true", help="Show all sources including missing")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    base = Path(args.data)

    results = []
    for source in SOURCE_REGISTRY:
        result = check_source(source, base)
        results.append(result)

    if args.json:
        active = [r for r in results if r["status"] == "active"]
        missing = [r for r in results if r["status"] == "missing"]
        empty = [r for r in results if r["status"] == "empty"]
        stale = [r for r in results if r.get("stale")]

        print(json.dumps({
            "total_sources": len(SOURCE_REGISTRY),
            "active": len(active),
            "missing": len(missing),
            "empty": len(empty),
            "stale": len(stale),
            "active_source_count": len(active),
            "sources": results,
        }, indent=2))
        return

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  HI. — Data Source Audit                                ║")
    print("║  42 sources. The answer was always 42.                  ║")
    print("╚══════════════════════════════════════════════════════════╝")

    active = []
    missing = []
    empty = []
    stale = []

    for r in results:
        icon = "✓" if r["status"] == "active" else "✗" if r["status"] == "missing" else "○"
        stale_flag = " ⏰" if r.get("stale") else ""

        if r["status"] == "active":
            active.append(r)
            if args.verbose or True:  # Always show active
                age = f"{r['file_age_hours']:.0f}h ago" if r["file_age_hours"] is not None else ""
                print(f"  {icon} [{r['id']:2d}] {r['name']:25s} {r['records']:>6,} records  {age:>10s}{stale_flag}  → {r['feeds']}")
        elif r["status"] == "missing":
            missing.append(r)
        elif r["status"] == "empty":
            empty.append(r)

        if r.get("stale"):
            stale.append(r)

    if missing:
        print(f"\n  {'─' * 56}")
        print(f"  MISSING ({len(missing)} sources — no data file found):")
        for r in missing:
            print(f"  ✗ [{r['id']:2d}] {r['name']:25s}  {r['path']}")

    if empty:
        print(f"\n  {'─' * 56}")
        print(f"  EMPTY ({len(empty)} sources — file exists but 0 records):")
        for r in empty:
            print(f"  ○ [{r['id']:2d}] {r['name']:25s}")

    if stale:
        print(f"\n  {'─' * 56}")
        print(f"  STALE ({len(stale)} sources — data older than 1 week):")
        for r in stale:
            age_days = round(r["file_age_hours"] / 24, 1) if r["file_age_hours"] else "?"
            print(f"  ⏰ [{r['id']:2d}] {r['name']:25s}  {age_days} days old")

    # Summary
    print(f"\n{'═' * 60}")
    print(f"  AUDIT SUMMARY")
    print(f"{'═' * 60}")
    print(f"  Total registered:  {len(SOURCE_REGISTRY)}")
    print(f"  Active (has data): {len(active)}")
    print(f"  Missing (no file): {len(missing)}")
    print(f"  Empty (0 records): {len(empty)}")
    print(f"  Stale (>1 week):   {len(stale)}")
    print(f"\n  Coverage: {len(active)}/{len(SOURCE_REGISTRY)} sources producing data")

    # Dynamic source count for API
    # Only count unique active sources (some overlap between gov/subsignal/extended)
    unique_active = set()
    for r in active:
        unique_active.add(r["name"])
    print(f"  Unique active:     {len(unique_active)}")
    print(f"\n  Use --json for machine-readable output")
    print(f"  Use --verbose for full details")

    # Write count file for API server
    count_file = base / "source_count.json"
    count_data = {
        "total_registered": len(SOURCE_REGISTRY),
        "active": len(active),
        "unique_active": len(unique_active),
        "missing": len(missing),
        "last_audit": datetime.now().isoformat(),
        "active_sources": [r["name"] for r in active],
    }
    json.dump(count_data, open(count_file, "w"), indent=2)
    print(f"\n  ✓ Wrote {count_file}")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()
