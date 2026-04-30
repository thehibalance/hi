#!/usr/bin/env python3
"""
HI. Daily Pipeline Runner — All 42 Sources
Single command to collect data, score companies, and generate features.

Usage:
  python3 run_all.py                    # Daily run (all 42 sources)
  python3 run_all.py --quarterly        # Quarterly (recalculates threshold)
  python3 run_all.py --features-only    # Re-generate features from existing scores
  python3 run_all.py --skip-collect     # Skip collection, re-score from existing data
  python3 run_all.py --skip-enrichment  # Skip standalone pipelines (faster, fewer API calls)
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

def run_if_exists(script, label, args=""):
    """Run a pipeline script only if it exists. Non-blocking on failure."""
    path = Path(os.path.dirname(os.path.abspath(__file__))) / script
    if path.exists():
        return run(f"python3 {script} {args}".strip(), label)
    else:
        print(f"\n  ⏭ {label}: {script} not found, skipping")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="HI. Daily Pipeline — All 42 Sources")
    parser.add_argument("--quarterly", action="store_true", help="Recalculate threshold")
    parser.add_argument("--features-only", action="store_true", help="Skip scoring, regenerate features only")
    parser.add_argument("--skip-collect", action="store_true", help="Skip data collection, use existing data")
    parser.add_argument("--skip-enrichment", action="store_true", help="Skip standalone enrichment pipelines")
    parser.add_argument("--workers", type=int, default=8, help="Parallel collection threads (default: 8)")
    parser.add_argument("--incremental", type=int, default=0, help="Skip companies with data fresher than N hours")
    parser.add_argument("--data", default="data/scores", help="Scores directory")
    parser.add_argument("--output", default="data", help="Output base directory")
    parser.add_argument("--port", default="8080", help="API port for restart")
    args = parser.parse_args()

    start = time.time()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  HI. — Daily Pipeline Runner                           ║")
    print("║  42 data sources. The answer was always 42.             ║")
    print("║  Think human intelligence.                              ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # Verify scores exist (for features-only mode)
    scores_path = Path(args.data) / "all_scores.json"
    if not scores_path.exists():
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

        # ═══════════════════════════════════════════════════════════
        # PHASE 1: Core Data Collection (Sources 1-12)
        # ═══════════════════════════════════════════════════════════

        if not args.skip_collect:
            inc_flag = f" --incremental {args.incremental}" if args.incremental else ""
            run(f"python3 data_collector.py --all --data {args.output} --workers {args.workers}{inc_flag}",
                "Phase 1a: Core Data Collection (SEC, EPA, BLS, CDP, Jobs, Glassdoor, Finnhub, FMP)")

        else:
            print("\n  ⏭ Phase 1a: Data collection skipped (--skip-collect)")

        # Government data (OSHA + CFPB)
        run_if_exists("collect_gov_data.py",
                      "Phase 1b: Government Data (OSHA + CFPB)",
                      f"--all --output {args.output}/gov --subsignals {args.output}/subsignals")

        # Extra gov sources (FEC, CPSC, FDA, USPTO, EPA ECHO, NHTSA)
        run_if_exists("collect_extra_sources.py",
                      "Phase 1c: Extra Gov Sources (FEC, CPSC, FDA, USPTO, EPA ECHO, NHTSA)",
                      f"--all --output {args.output}/gov --subsignals {args.output}/subsignals")

        # ═══════════════════════════════════════════════════════════
        # PHASE 2: Standalone Enrichment Pipelines (Sources 13-42)
        # These write to data/<source>/ directories.
        # ═══════════════════════════════════════════════════════════

        if not args.skip_enrichment:
            print(f"\n{'═' * 60}")
            print(f"  PHASE 2: Enrichment Pipelines")
            print(f"{'═' * 60}")

            # ── Group A: No API key needed, fast ──
            run_if_exists("layoffs_pipeline.py",
                          "Phase 2a: Layoffs.fyi Tracker")

            run_if_exists("warn_pipeline.py",
                          "Phase 2a: WARN Act Layoff Notices")

            run_if_exists("dei_pipeline.py",
                          "Phase 2a: DEI Reporting Index")

            run_if_exists("hrc_pipeline.py",
                          "Phase 2a: HRC Corporate Equality Index")

            run_if_exists("harm_documentation_pipeline.py",
                          "Phase 2a: Harm Documentation (settlements, deaths, concealment)")

            # ── Group B: API keys needed, rate-limited ──
            run_if_exists("fmp_pipeline.py",
                          "Phase 2b: FMP Financial Modeling Prep (250 calls/day)")

            run_if_exists("finnhub_pipeline.py",
                          "Phase 2b: Finnhub ESG + Profile (60 calls/min)")

            run_if_exists("newsapi_pipeline.py",
                          "Phase 2b: NewsAPI Media Monitoring (100 calls/day)")

            run_if_exists("alpha_vantage_pipeline.py",
                          "Phase 2b: Alpha Vantage Fundamentals (25 calls/day)")

            run_if_exists("yahoo_pipeline.py",
                          "Phase 2b: Yahoo Finance Market Data")

            run_if_exists("fred_pipeline.py",
                          "Phase 2b: FRED Macro Economic Data")

            # ── Group C: SEC-related, depends on earlier data ──
            run_if_exists("sec_8k_pipeline.py",
                          "Phase 2c: SEC 8-K Material Events")

            run_if_exists("opencorporates_pipeline.py",
                          "Phase 2c: OpenCorporates Corporate Structure")

            # ── Group D: Depends on Group A+B outputs ──
            run_if_exists("ceo_pipeline.py",
                          "Phase 2d: CEO Accountability (reads FMP, Glassdoor, Layoffs)")

            # ── Consolidate all standalone pipeline outputs ──
            run_if_exists("consolidate_sources.py",
                          "Phase 2e: Consolidate All Sources → Scoring Format")

        else:
            print("\n  ⏭ Phase 2: Enrichment pipelines skipped (--skip-enrichment)")

        # ═══════════════════════════════════════════════════════════
        # PHASE 3: Scoring Engine
        # ═══════════════════════════════════════════════════════════

        run(f"python3 scoring_engine.py --output {args.data}",
            "Phase 3: Scoring Engine v2.1 (25 sub-signals, 42 sources)")

    # ═══════════════════════════════════════════════════════════
    # PHASE 4: Post-Scoring Features
    # ═══════════════════════════════════════════════════════════

    # Merge seed data (private companies)
    seed_path = Path("../human-edge/lib/seed-data.js")
    if not seed_path.exists():
        seed_path = Path("seed-data.js")
    if seed_path.exists():
        run(f"python3 merge_seed.py --seed {seed_path} --scores {args.data}/all_scores.json",
            "Phase 4a: Merge Seed Data (private companies)")
    else:
        print("\n  ⏭ Phase 4a: No seed-data.js found, skipping merge")

    # Feature pipelines
    run(f"python3 feature_pipelines.py --data {args.data} --output {args.output}",
        "Phase 4b: Feature Pipelines (Shield, Contagion, Lens, Wave, Watermark)")

    # Heartbeat monitor
    run_if_exists("heartbeat_monitor.py",
                  "Phase 4c: HUMAN Heartbeat",
                  f"--data {args.data} --output {args.output}/heartbeat")

    # v1.2.0: Re-evaluate Balanced Board momentum gate using fresh heartbeat data.
    # Scoring runs in Phase 2 before heartbeat exists, so the momentum gate falls
    # back to "stable" by default, false-passing companies that are actually in
    # warning/critical decay (e.g., PFE, WMT, COF). This post-process step
    # reads heartbeats.json and corrects hi_balanced + hi_balanced_gates.
    run_if_exists("post_process_balanced_board.py",
                  "Phase 4d: Balanced Board Post-Process",
                  "")

    # HUMAN 100 Index
    run_if_exists("human100_index.py",
                  "Phase 4d: HUMAN 100 Index",
                  f"--data {args.data} --output {args.output}/human100")

    # ═══════════════════════════════════════════════════════════
    # PHASE 5: Validation + Audit
    # ═══════════════════════════════════════════════════════════

    # Validate scores (3-layer defense)
    try:
        from validate_pipeline import validate_all
        report = validate_all(data_dir=args.output)
        if report.critical:
            print("❌ BLOCKED — bad data detected, scores NOT published")
            sys.exit(1)
    except ImportError:
        print("\n  ⚠ validate_pipeline.py not importable, skipping validation")

    # Source audit — dynamic count of active sources
    run_if_exists("source_audit.py",
                  "Phase 5b: Source Audit (42 sources check)",
                  f"--data {args.output}")

    # ═══════════════════════════════════════════════════════════
    # PHASE 6: History + Prices
    # ═══════════════════════════════════════════════════════════

    run_if_exists("history_tracker.py",
                  "Phase 6: History + Prices + Backtest",
                  f"--all --scores {args.data} --history {args.output}/history --prices-dir {args.output}/prices --output {args.output}")

    # ═══════════════════════════════════════════════════════════
    # DONE
    # ═══════════════════════════════════════════════════════════

    elapsed = round(time.time() - start, 1)
    print(f"\n{'═' * 60}")
    print(f"  ✓ Pipeline complete in {elapsed}s")
    print(f"  42 data sources. Zero AI in scoring. Think human.")
    print(f"{'═' * 60}")

    quarterly_flag = " --quarterly" if args.quarterly else ""
    print(f"\n  To start the API:")
    print(f"    python3 api_server.py --port {args.port}{quarterly_flag}")
    print()


if __name__ == "__main__":
    main()
