#!/usr/bin/env python3
"""
HI. Pipeline Master Runner
Runs all 17 data pipelines + scoring engine + Heartbeat in the correct order.

RECOMMENDED SCHEDULE:
  Daily:    python3 run_all.py --daily
  Weekly:   python3 run_all.py --weekly
  Monthly:  python3 run_all.py --monthly
  Full:     python3 run_all.py --full

Or run everything: python3 run_all.py
"""

import subprocess, sys, time, argparse
from datetime import datetime


def run(cmd, label):
    print(f"\n{'─'*60}")
    print(f"  ▶ {label}")
    print(f"    {cmd}")
    print(f"{'─'*60}")
    start = time.time()
    result = subprocess.run(cmd, shell=True)
    elapsed = time.time() - start
    status = "✅" if result.returncode == 0 else "❌"
    print(f"  {status} {label} — {elapsed:.0f}s")
    return result.returncode == 0


def run_daily():
    """Daily pipelines — fast, free, no rate limits."""
    print(f"\n{'='*60}")
    print(f"  DAILY RUN — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    # FMP: 80 companies/day (appends, skips fetched)
    run("python3 fmp_pipeline.py --limit 80", "FMP — financials (80 companies)")

    # Finnhub: fast, 60 req/min
    run("python3 finnhub_pipeline.py --limit 50", "Finnhub — ESG + news (50 companies)")

    # Alpha Vantage: 12 companies/day on free tier
    run("python3 alpha_vantage_pipeline.py", "Alpha Vantage — earnings (12 companies)")

    # SEC 8-K: fast, free
    run("python3 sec_8k_pipeline.py --limit 50", "SEC 8-K — material events (50 companies)")

    # Re-score
    run("python3 scoring_engine.py", "Scoring Engine — re-score all")

    # Heartbeat
    run("python3 heartbeat_monitor.py", "HUMAN Heartbeat — decay detection")


def run_weekly():
    """Weekly pipelines — slower sources, bigger batches."""
    print(f"\n{'='*60}")
    print(f"  WEEKLY RUN — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    # All daily sources with bigger limits
    run("python3 fmp_pipeline.py --limit 80", "FMP — financials")
    run("python3 finnhub_pipeline.py --limit 200", "Finnhub — ESG + news")
    run("python3 sec_8k_pipeline.py --limit 200", "SEC 8-K — material events")
    run("python3 alpha_vantage_pipeline.py", "Alpha Vantage — earnings")

    # Yahoo Finance: re-fetch all (data changes weekly)
    run("python3 yahoo_pipeline.py", "Yahoo Finance — headcount, revenue")

    # OpenCorporates: 500/month limit
    run("python3 opencorporates_pipeline.py --limit 30", "OpenCorporates — transparency")

    # FRED: benchmarks update weekly/monthly
    run("python3 fred_pipeline.py", "FRED — economic benchmarks")

    # Re-score + Heartbeat
    run("python3 scoring_engine.py", "Scoring Engine")
    run("python3 heartbeat_monitor.py", "HUMAN Heartbeat")


def run_monthly():
    """Monthly pipelines — static/manual data sources."""
    print(f"\n{'='*60}")
    print(f"  MONTHLY RUN — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    # All weekly sources
    run_weekly()

    # Slow/static sources
    run("python3 sec_edgar_pipeline.py", "SEC EDGAR — full run (all tickers)")
    run("python3 cdp_pipeline.py", "CDP — climate disclosure")
    run("python3 job_board_pipeline.py", "Job Boards — AI hiring ratio")
    run("python3 glassdoor_pipeline.py", "Glassdoor — employee ratings")
    run("python3 dei_pipeline.py", "DEI — disability inclusion")
    run("python3 hrc_pipeline.py", "HRC — LGBTQ+ inclusion")
    run("python3 layoffs_pipeline.py", "Layoffs.fyi — layoff tracker")
    run("python3 warn_pipeline.py", "WARN Act — layoff notices")

    # Final re-score + Heartbeat
    run("python3 scoring_engine.py", "Scoring Engine — final re-score")
    run("python3 heartbeat_monitor.py", "HUMAN Heartbeat — final pulse")


def run_full():
    """Full run — everything, all sources, no limits."""
    print(f"\n{'='*60}")
    print(f"  FULL RUN — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    run_monthly()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="HI. Pipeline Master Runner")
    p.add_argument("--daily", action="store_true", help="Run daily pipelines")
    p.add_argument("--weekly", action="store_true", help="Run weekly pipelines")
    p.add_argument("--monthly", action="store_true", help="Run monthly pipelines")
    p.add_argument("--full", action="store_true", help="Run everything")
    args = p.parse_args()

    if args.daily:
        run_daily()
    elif args.weekly:
        run_weekly()
    elif args.monthly:
        run_monthly()
    else:
        run_full()

    print(f"\n{'='*60}")
    print(f"  ALL DONE — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
