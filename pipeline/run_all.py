#!/usr/bin/env python3
"""
HI. Daily Pipeline Runner
Single command to score all companies and generate all features.

Usage:
  python3 run_all.py                    # Daily run (uses saved threshold)
  python3 run_all.py --quarterly        # Quarterly (recalculates threshold)
  python3 run_all.py --features-only    # Re-generate features from existing scores
"""

import subprocess, sys, os, time
from pathlib import Path

def run(cmd, label):
    print(f"\n{'═' * 60}")
    print(f"  {label}")
    print(f"{'═' * 60}")
    start = time.time()
    result = subprocess.run(cmd, shell=True, cwd=os.path.dirname(os.path.abspath(__file__)))
    elapsed = round(time.time() - start, 1)
    if result.returncode != 0:
        print(f"  ⚠ {label} failed (exit {result.returncode}) in {elapsed}s")
        return False
    print(f"  ✓ {label} done in {elapsed}s")
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description="HI. Daily Pipeline")
    parser.add_argument("--quarterly", action="store_true", help="Recalculate threshold")
    parser.add_argument("--features-only", action="store_true", help="Skip scoring, regenerate features only")
    parser.add_argument("--skip-collect", action="store_true", help="Skip data collection, use existing data")
    parser.add_argument("--workers", type=int, default=8, help="Parallel collection threads (default: 8)")
    parser.add_argument("--incremental", type=int, default=0, help="Skip companies with data fresher than N hours")
    parser.add_argument("--data", default="data/scores", help="Scores directory")
    parser.add_argument("--output", default="data", help="Output base directory")
    parser.add_argument("--port", default="8080", help="API port for restart")
    args = parser.parse_args()

    start = time.time()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  HI. — Daily Pipeline Runner                           ║")
    print("║  Think human intelligence.                                  ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # Verify scores exist
    scores_path = Path(args.data) / "all_scores.json"
    if not scores_path.exists():
        # Try relative to script dir
        script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        scores_path = script_dir / args.data / "all_scores.json"
    
    if not args.features_only and not scores_path.exists():
        print(f"\n  Scores will be generated at: {args.data}/all_scores.json")
    elif scores_path.exists():
        scores = __import__('json').load(open(scores_path))
        print(f"\n  Found {len(scores)} companies in {scores_path}")
    else:
        print(f"\n  ⚠ No scores found at {args.data}/all_scores.json")
        print(f"    Run without --features-only first to generate scores")
        return

    if not args.features_only:
        # Step 1: Collect fresh data from all 42 sources
        if not args.skip_collect:
            inc_flag = f" --incremental {args.incremental}" if args.incremental else ""
            run(f"python3 data_collector.py --all --data {args.output} --workers {args.workers}{inc_flag}", "Step 1: Data Collection (42 sources)")
        else:
            print("\n  ⏭ Step 1: Data collection skipped (--skip-collect)")
        # Step 1b: Government data (CFPB + OSHA)
        run(f"python3 collect_gov_data.py --all --output {args.output}/gov --subsignals {args.output}/subsignals", "Step 1b: CFPB + OSHA (Government Data)")
         # Step 1c: Extra sources (FEC, CPSC, FDA, EPA, Patents)
        run(f"python3 collect_extra_sources.py --all --output {args.output}/gov --subsignals {args.output}/subsignals", "Step 1c: FEC + CPSC + FDA + EPA")
        # Step 1d: Sub-signal scoring (HIBP, hardware, land)
        if Path("subsignal_pipelines.py").exists():
            run(f"python3 subsignal_pipelines.py", "Step 1d: Sub-Signal Scoring (HIBP, Hardware, Land)")
        # Step 1e: Extended pipelines (OSHA, FTC, DOL, BBB, EEOC, Patents, FDA, Pay Ratio, Insider, GRI, SBTi, Charity)
        if Path("extended_pipelines.py").exists():
            run(f"python3 extended_pipelines.py", "Step 1e: Extended Pipelines (12 signals for 300+ companies)")
        # Step 1f: B Corp + Charity Navigator
        if Path("bcorp_charity_pipeline.py").exists():
            run(f"python3 bcorp_charity_pipeline.py", "Step 1f: B Corp + Charity Navigator")
        # Step 2: Run scoring engine
        run(f"python3 scoring_engine.py --output {args.data}", "Step 2: Scoring Engine (24 sub-signals, 42 sources)")
    
    # Step 3: Merge seed data (private companies)
    seed_path = Path("../human-edge/lib/seed-data.js")
    if not seed_path.exists():
        seed_path = Path("seed-data.js")  # Fallback
    if seed_path.exists():
        run(f"python3 merge_seed.py --seed {seed_path} --scores {args.data}/all_scores.json", "Step 3: Merge Seed Data (private companies)")
    else:
        print("\n  ⏭ Step 3: No seed-data.js found, skipping merge")

    # Step 4: Run feature pipelines
    run(f"python3 feature_pipelines.py --data {args.data} --output {args.output}", "Step 4: Feature Pipelines (Shield, Contagion, Lens, Wave, Watermark)")

    # Step 5: Run heartbeat monitor
    if Path("heartbeat_monitor.py").exists():
        run(f"python3 heartbeat_monitor.py --data {args.data} --output {args.output}/heartbeat", "Step 5: HUMAN Heartbeat")
    else:
        print("\n  ⏭ Step 5: Heartbeat monitor not found, skipping")

    # Step 6: Run HUMAN 100 Index
    if Path("human100_index.py").exists():
        run(f"python3 human100_index.py --data {args.data} --output {args.output}/human100", "Step 6: HUMAN 100 Index")
    else:
        print("\n  ⏭ Step 6: HUMAN 100 not found, skipping")

    # Step 7: Validate scores (3-layer defense))
    from validate_pipeline import validate_all    
    report = validate_all(data_dir=args.output)
    if report.critical:
        print("❌ BLOCKED — bad data detected, scores NOT published")
        sys.exit(1)
    # Step 8: History snapshot + price capture + backtest
    run(f"python3 history_tracker.py --all --scores {args.data} --history {args.output}/history --prices-dir {args.output}/prices --output {args.output}", "Step 8: History + Prices + Backtest")

    elapsed = round(time.time() - start, 1)
    print(f"\n{'═' * 60}")
    print(f"  ✓ Pipeline complete in {elapsed}s")
    print(f"{'═' * 60}")
    
    quarterly_flag = " --quarterly" if args.quarterly else ""
    print(f"\n  To start the API:")
    print(f"    python3 api_server.py --port {args.port}{quarterly_flag}")
    print()


if __name__ == "__main__":
    main()
