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
    result = subprocess.run(cmd, shell=True, cwd=os.path.dirname(__file__) or ".")
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
    parser.add_argument("--data", default="data/scores", help="Scores directory")
    parser.add_argument("--output", default="data", help="Output base directory")
    parser.add_argument("--port", default="8080", help="API port for restart")
    args = parser.parse_args()

    start = time.time()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  HI. — Daily Pipeline Runner                           ║")
    print("║  Find the HI balance.                                  ║")
    print("╚══════════════════════════════════════════════════════════╝")

    if not args.features_only:
        # Step 1: Run scoring engine
        run(f"python3 scoring_engine.py --output {args.data}", "Step 1: Scoring Engine (34 sources, 24 sub-signals)")

    # Step 2: Run feature pipelines
    run(f"python3 feature_pipelines.py --data {args.data} --output {args.output}", "Step 2: Feature Pipelines (Shield, Contagion, Lens, Wave, Watermark)")

    # Step 3: Run heartbeat monitor
    if Path("heartbeat_monitor.py").exists():
        run(f"python3 heartbeat_monitor.py --data {args.data} --output {args.output}/heartbeat", "Step 3: HUMAN Heartbeat")
    else:
        print("\n  ⏭ Step 3: Heartbeat monitor not found, skipping")

    # Step 4: Run HUMAN 100 Index
    if Path("human100_index.py").exists():
        run(f"python3 human100_index.py --data {args.data} --output {args.output}/human100", "Step 4: HUMAN 100 Index")
    else:
        print("\n  ⏭ Step 4: HUMAN 100 not found, skipping")

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
