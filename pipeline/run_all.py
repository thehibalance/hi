#!/usr/bin/env python3
"""
HI. Pipeline Master Runner - Single Command
Runs all data pipelines + scoring engine + Heartbeat in order.

Usage:
  python3 run_all.py                # Full run (everything)
  python3 run_all.py --daily        # Daily pipelines (~15 min)
  python3 run_all.py --weekly       # Weekly pipelines (~30 min)
  python3 run_all.py --monthly      # Monthly full run (~2 hrs)
  python3 run_all.py --daily --push # Daily + auto-push to git/Railway
"""

import subprocess, sys, time, argparse, os
from datetime import datetime
from pathlib import Path


def run(cmd, label):
    print(f"\n{'─'*60}")
    print(f"  ▶ {label}")
    print(f"{'─'*60}")
    start = time.time()
    result = subprocess.run(cmd, shell=True)
    elapsed = time.time() - start
    status = "✅" if result.returncode == 0 else "❌"
    print(f"  {status} {label} — {elapsed:.0f}s")
    return result.returncode == 0


def has_key(name, path):
    if Path(path).exists():
        return True
    env_map = {"FMP": "FMP_KEY", "Finnhub": "FINNHUB_KEY", "FRED": "FRED_KEY",
               "Alpha Vantage": "ALPHA_VANTAGE_KEY", "NewsAPI": "NEWSAPI_KEY"}
    return bool(os.environ.get(env_map.get(name, "")))


def print_status():
    keys = {
        "FMP": "data/fmp_key.txt",
        "Finnhub": "data/finnhub_key.txt",
        "FRED": "data/fred_key.txt",
        "Alpha Vantage": "data/alpha_vantage_key.txt",
        "NewsAPI": "data/newsapi_key.txt",
    }
    print(f"\n  API Keys:")
    for name, path in keys.items():
        s = "✅" if has_key(name, path) else "❌ missing"
        print(f"    {name:20s} {s}")
    csvs = {"Layoffs.fyi": "data/layoffs/layoffs.csv", "WARN Act": "data/warn/"}
    print(f"  Manual Data:")
    for name, path in csvs.items():
        if Path(path).is_dir():
            ok = len(list(Path(path).glob("*.csv"))) > 0
        else:
            ok = Path(path).exists()
        s = "✅" if ok else "⚪ optional"
        print(f"    {name:20s} {s}")


def run_daily():
    """Daily: news + API sources that accumulate + scoring + Heartbeat."""
    print(f"\n{'='*60}")
    print(f"  ⚡ DAILY RUN — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    print_status()

    # News monitoring (breaking stories)
    if has_key("NewsAPI", "data/newsapi_key.txt"):
        run("python3 newsapi_pipeline.py --limit 90", "NewsAPI — media monitoring (90 companies)")
    if has_key("Finnhub", "data/finnhub_key.txt"):
        run("python3 finnhub_pipeline.py --limit 50", "Finnhub — ESG + news (50 companies)")

    # Financial data (accumulates)
    if has_key("FMP", "data/fmp_key.txt"):
        run("python3 fmp_pipeline.py --limit 80", "FMP — financials (80 companies)")
    if has_key("Alpha Vantage", "data/alpha_vantage_key.txt"):
        run("python3 alpha_vantage_pipeline.py", "Alpha Vantage — earnings (12 companies)")

    # SEC filings (free)
    run("python3 sec_8k_pipeline.py --limit 50", "SEC 8-K — material events")

    # CEO accountability
    run("python3 ceo_pipeline.py", "CEO Accountability — leadership signals")

    # Score + Heartbeat
    run("python3 scoring_engine.py", "Scoring Engine — re-score all")
    run("python3 heartbeat_monitor.py", "HUMAN Heartbeat — decay detection")


def run_weekly():
    """Weekly: daily + slower sources + bigger batches."""
    print(f"\n{'='*60}")
    print(f"  📅 WEEKLY RUN — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    print_status()

    # News (bigger batches)
    if has_key("NewsAPI", "data/newsapi_key.txt"):
        run("python3 newsapi_pipeline.py --limit 90", "NewsAPI — media monitoring")
    if has_key("Finnhub", "data/finnhub_key.txt"):
        run("python3 finnhub_pipeline.py --limit 200", "Finnhub — ESG + news")

    # Financial data
    if has_key("FMP", "data/fmp_key.txt"):
        run("python3 fmp_pipeline.py --limit 80", "FMP — financials")
    if has_key("Alpha Vantage", "data/alpha_vantage_key.txt"):
        run("python3 alpha_vantage_pipeline.py", "Alpha Vantage — earnings")
    run("python3 yahoo_pipeline.py", "Yahoo Finance — headcount, revenue (all)")

    # Benchmarks + SEC
    if has_key("FRED", "data/fred_key.txt"):
        run("python3 fred_pipeline.py", "FRED — economic benchmarks")
    run("python3 sec_8k_pipeline.py --limit 200", "SEC 8-K — material events")

    # Inclusion + CEO
    run("python3 dei_pipeline.py", "DEI — disability inclusion")
    run("python3 hrc_pipeline.py", "HRC — LGBTQ+ inclusion")
    run("python3 ceo_pipeline.py", "CEO Accountability")

    # Score + Heartbeat
    run("python3 scoring_engine.py", "Scoring Engine")
    run("python3 heartbeat_monitor.py", "HUMAN Heartbeat")


def run_monthly():
    """Monthly: everything including slow/manual sources."""
    print(f"\n{'='*60}")
    print(f"  📆 MONTHLY RUN — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    run_weekly()

    # Slow/static sources
    run("python3 sec_edgar_pipeline.py", "SEC EDGAR — full run")
    run("python3 cdp_pipeline.py", "CDP — climate disclosure")
    run("python3 job_board_pipeline.py", "Job Boards — AI hiring ratio")
    run("python3 glassdoor_pipeline.py", "Glassdoor — employee ratings")
    run("python3 layoffs_pipeline.py", "Layoffs.fyi — layoff tracker")
    run("python3 warn_pipeline.py", "WARN Act — layoff notices")

    # Final score + Heartbeat
    run("python3 scoring_engine.py", "Scoring Engine — final")
    run("python3 heartbeat_monitor.py", "HUMAN Heartbeat — final pulse")


def auto_push():
    """Push scores to Railway and repo to GitHub."""
    print(f"\n{'='*60}")
    print(f"  🚀 AUTO-PUSH")
    print(f"{'='*60}")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    hi_api = os.path.expanduser("~/Desktop/hi-api")
    repo = os.path.expanduser("~/Desktop/repo")
    scores = os.path.join(repo, "pipeline/data/scores/all_scores.json")

    if os.path.exists(scores) and os.path.exists(hi_api):
        run(f"cp {scores} {hi_api}/data/scores/all_scores.json", "Copy scores → API repo")
        run(f"cd {hi_api} && git add . && git commit -m 'Scores update {ts}' && git push", "Push → Railway")

    if os.path.exists(repo):
        run(f"cd {repo} && git add . && git commit -m 'Pipeline update {ts}' && git push", "Push → GitHub")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="HI. Pipeline Master Runner")
    p.add_argument("--daily", action="store_true", help="Daily pipelines (~15 min)")
    p.add_argument("--weekly", action="store_true", help="Weekly pipelines (~30 min)")
    p.add_argument("--monthly", action="store_true", help="Monthly full run (~2 hrs)")
    p.add_argument("--push", action="store_true", help="Auto-push to git + Railway")
    args = p.parse_args()

    start = time.time()

    if args.daily:
        run_daily()
    elif args.weekly:
        run_weekly()
    elif args.monthly:
        run_monthly()
    else:
        run_monthly()

    if args.push:
        auto_push()

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  ✅ ALL DONE — {int(elapsed//60)}m {int(elapsed%60)}s")
    print(f"{'='*60}\n")
