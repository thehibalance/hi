#!/usr/bin/env python3
"""
HI. — Master Pipeline Runner
Runs all data pipelines and scoring in sequence.

Usage:
  python run_pipeline.py                    # Run everything
  python run_pipeline.py --sec-only         # Just SEC pipeline
  python run_pipeline.py --sec-limit 10     # SEC with limit
  python run_pipeline.py --skip-sec         # Skip SEC (uses cached), run rest
  python run_pipeline.py --score-only       # Just re-score from existing data
"""

import subprocess, sys, os, time, argparse
from pathlib import Path

def run(cmd, desc):
    print(f"\n{'='*60}")
    print(f"  {desc}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=False)
    if result.returncode != 0:
        print(f"  ⚠ {desc} had issues (exit code {result.returncode})")
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="HI. Master Pipeline Runner")
    parser.add_argument("--sec-limit", type=int, default=0, help="Limit SEC companies (0=all)")
    parser.add_argument("--sec-only", action="store_true", help="Only run SEC pipeline")
    parser.add_argument("--skip-sec", action="store_true", help="Skip SEC (slow, needs internet)")
    parser.add_argument("--skip-epa", action="store_true", help="Skip EPA (needs internet)")
    parser.add_argument("--skip-bls", action="store_true", help="Skip BLS (needs internet)")
    parser.add_argument("--score-only", action="store_true", help="Only run scoring engine")
    parser.add_argument("--port", type=int, default=8080, help="API server port")
    parser.add_argument("--no-server", action="store_true", help="Don't start API server at end")
    args = parser.parse_args()

    start = time.time()
    print("HI. — Master Pipeline Runner")
    print("Find the HI balance. | thehibalance.org")
    print("=" * 60)

    if not args.score_only:
        # ── SEC EDGAR (needs internet) ──
        if not args.skip_sec:
            limit_flag = f"--limit {args.sec_limit}" if args.sec_limit else ""
            run(f"{sys.executable} sec_edgar_pipeline.py {limit_flag} --output data/sec",
                "SEC EDGAR Pipeline")
            if args.sec_only:
                print(f"\nSEC-only mode. Done in {time.time()-start:.0f}s")
                return

        # ── EPA ECHO (needs internet) ──
        if not args.skip_epa:
            run(f"{sys.executable} epa_echo_pipeline.py --output data/epa",
                "EPA ECHO Pipeline")

        # ── BLS (needs internet) ──
        if not args.skip_bls:
            run(f"{sys.executable} bls_pipeline.py --output data/bls",
                "BLS Pipeline")

        # ── CDP (built-in data, instant) ──
        run(f"{sys.executable} cdp_pipeline.py --output data/cdp",
            "CDP Climate Pipeline")

        # ── Job Boards (built-in data, instant) ──
        run(f"{sys.executable} job_board_pipeline.py --output data/jobs",
            "Job Board Pipeline")

        # ── Glassdoor (built-in data, instant) ──
        run(f"{sys.executable} glassdoor_pipeline.py --output data/glassdoor",
            "Glassdoor Pipeline")

    # ── Scoring Engine v2 ──
    run(f"{sys.executable} scoring_engine.py --output data/scores",
        "Scoring Engine v2 (all sources)")

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE — {elapsed:.0f} seconds")
    print(f"{'='*60}")

    # Show what we got
    scores_file = Path("data/scores/all_scores.json")
    if scores_file.exists():
        import json
        with open(scores_file) as f:
            scores = json.load(f)
        print(f"\n  Total scored: {len(scores)} companies")
        grades = {}
        for s in scores:
            g = s.get("hi_grade", "?")
            grades[g] = grades.get(g, 0) + 1
        for g in ["HI Certified", "A", "B", "C", "F"]:
            if g in grades:
                print(f"    {g}: {grades[g]}")

    # ── Start API server ──
    if not args.no_server:
        print(f"\n  Starting API server on port {args.port}...")
        print(f"  Press Ctrl+C to stop.\n")
        os.execvp(sys.executable, [sys.executable, "api_server.py", "--port", str(args.port)])


if __name__ == "__main__":
    main()
