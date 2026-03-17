#!/usr/bin/env python3
"""
HI. — Single Command Runner
Runs all pipelines, scoring, and patent feature generators.

Usage:
  python3 run_all.py --daily --push    # Daily pipelines + patent features + auto-push
  python3 run_all.py --weekly --push   # Weekly + daily + push
  python3 run_all.py --monthly --push  # Full run + push
  python3 run_all.py --score-only      # Just re-score + generate patent features
"""

import subprocess
import sys
import os
import argparse
import shutil
from pathlib import Path


def run(cmd, label):
    print(f"\n{'─'*50}")
    print(f"  ▶ {label}")
    print(f"{'─'*50}")
    result = subprocess.run([sys.executable, cmd], cwd=os.path.dirname(os.path.abspath(__file__)))
    if result.returncode != 0:
        print(f"  ⚠ {label} exited with code {result.returncode}")
    return result.returncode


def push_repos():
    repo_dir = Path(__file__).parent.parent
    api_dir = Path.home() / "Desktop" / "hi-api"

    print(f"\n{'─'*50}")
    print(f"  ▶ Pushing to GitHub + Railway")
    print(f"{'─'*50}")

    if api_dir.exists():
        data_dir = Path(__file__).parent / "data"
        for subdir in ["scores", "heartbeat", "human100", "arbitrage", "ethical_moat",
                       "contagion", "consumer_consciousness", "empathy_watermark",
                       "collective_bargaining"]:
            src = data_dir / subdir
            dst = api_dir / "data" / subdir
            if src.exists():
                dst.mkdir(parents=True, exist_ok=True)
                for f in src.glob("*.json"):
                    shutil.copy2(f, dst / f.name)

        api_src = Path(__file__).parent / "api_server.py"
        if api_src.exists():
            shutil.copy2(api_src, api_dir / "api_server.py")

        subprocess.run(["git", "add", "."], cwd=api_dir)
        subprocess.run(["git", "commit", "-m", "Auto-update: scores + patent features"], cwd=api_dir)
        subprocess.run(["git", "push"], cwd=api_dir)

    subprocess.run(["git", "add", "."], cwd=repo_dir)
    subprocess.run(["git", "commit", "-m", "Auto-update: daily pipeline run"], cwd=repo_dir)
    subprocess.run(["git", "push"], cwd=repo_dir)


def main():
    parser = argparse.ArgumentParser(description="HI. Pipeline Runner")
    parser.add_argument("--daily", action="store_true", help="Run daily pipelines")
    parser.add_argument("--weekly", action="store_true", help="Run weekly + daily")
    parser.add_argument("--monthly", action="store_true", help="Run all pipelines")
    parser.add_argument("--score-only", action="store_true", help="Just re-score and generate features")
    parser.add_argument("--push", action="store_true", help="Auto-push to GitHub + Railway")
    args = parser.parse_args()

    if not any([args.daily, args.weekly, args.monthly, args.score_only]):
        args.daily = True

    print(f"\n{'='*60}")
    print(f"  HI. Pipeline Runner — 10 Patent Features")
    print(f"  Mode: {'monthly' if args.monthly else 'weekly' if args.weekly else 'score-only' if args.score_only else 'daily'}")
    print(f"  Push: {'yes' if args.push else 'no'}")
    print(f"{'='*60}")

    if args.monthly:
        for s, l in [("sec_edgar_pipeline.py","SEC EDGAR"),("epa_echo_pipeline.py","EPA ECHO"),
                     ("bls_pipeline.py","BLS"),("cdp_pipeline.py","CDP"),
                     ("job_board_pipeline.py","Job Boards"),("glassdoor_pipeline.py","Glassdoor"),
                     ("layoffs_pipeline.py","Layoffs.fyi"),("warn_pipeline.py","WARN Act")]:
            if Path(s).exists(): run(s, l)

    if args.weekly or args.monthly:
        for s, l in [("dei_pipeline.py","DEI/AAPD"),("hrc_pipeline.py","HRC/CEI"),
                     ("yahoo_pipeline.py","Yahoo Finance"),("fred_pipeline.py","FRED")]:
            if Path(s).exists(): run(s, l)

    if args.daily or args.weekly or args.monthly:
        for s, l in [("alpha_vantage_pipeline.py","Alpha Vantage"),("fmp_pipeline.py","FMP"),
                     ("finnhub_pipeline.py","Finnhub"),("newsapi_pipeline.py","NewsAPI"),
                     ("sec_8k_pipeline.py","SEC 8-K"),("ceo_pipeline.py","CEO Pipeline")]:
            if Path(s).exists(): run(s, l)

    # Always run scoring + all 10 patent features
    print(f"\n{'='*60}")
    print(f"  SCORING + 10 PATENT FEATURES")
    print(f"{'='*60}")

    run("scoring_engine.py", "Scoring Engine")

    for s, l in [("heartbeat_monitor.py","HUMAN Heartbeat"),("human100_index.py","HUMAN 100 Index"),
                 ("grade_arbitrage.py","HUMAN Lens"),("ethical_moat.py","HUMAN Shield"),
                 ("contagion_effect.py","HUMAN Contagion"),("consumer_consciousness.py","HUMAN Consciousness"),
                 ("empathy_watermark.py","HUMAN Watermark"),("collective_bargaining.py","HUMAN Wave")]:
        if Path(s).exists(): run(s, l)

    print(f"\n{'='*60}")
    print(f"  ALL COMPLETE — 10 patent features generated")
    print(f"{'='*60}")

    if args.push:
        push_repos()
        print(f"\n  ✅ Pushed to GitHub + Railway")

    print(f"\n  Done. Find the HI balance.\n")


if __name__ == "__main__":
    main()
