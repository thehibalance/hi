#!/usr/bin/env python3
"""
v1.2.0 Score Audit — comprehensive sweep.

Three passes:
  1. DEFENSIBILITY  — every score has sources, coverage, version
  2. COVERAGE       — every universe ticker is scored (or known-deferred)
  3. CONSISTENCY    — math/floor-rule correctness

Strategy:
  - Iterate pipeline/data/scores/all_scores.json (445 entries) for ticker list
  - Query https://api.thehibalance.org/api/v1/score/ticker/{T} for each
  - Run all three passes per ticker
  - Generate AUDIT_v1.2.0.md sorted by severity

Severity tiers:
  🔴 BLOCKER       — must fix before launch (math errors, missing critical fields)
  🟡 LAUNCH-OK     — defensible but flag for v1.2.1 follow-up
  🟢 KNOWN-DEFERRED — already tracked in ROADMAP, not new

Usage (from repo root):
  python3 audit_v120.py

Output:
  AUDIT_v1.2.0.md (in repo root)
  Console summary with pass/fail counts
"""

import json
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

REPO_ROOT = Path(__file__).resolve().parent
SCORES_FILE = REPO_ROOT / "pipeline" / "data" / "scores" / "all_scores.json"
API_BASE = "https://api.thehibalance.org/api/v1/score/ticker/"
OUTPUT = REPO_ROOT / "AUDIT_v1.2.0.md"

# ── Tier-1 tickers we MUST have working at launch ──
TIER_1 = {
    # Big tech (AHI exemplars)
    "AAPL", "MSFT", "GOOGL", "META", "AMZN", "NVDA", "TSLA",
    # Harm exemplars (HD)
    "JNJ", "PFE", "MRK", "BMY",
    # Universal-recognition consumer
    "WMT", "COST", "TGT", "HD", "LOW",
    # Finance
    "JPM", "BAC", "WFC", "GS", "MS",
    # Energy
    "XOM", "CVX",
    # The marketed example tickers
    "RIVN", "NFLX", "DIS", "KO", "MCD",
}


# ════════════════════════════════════════════════════════════════════
# Pass 1: DEFENSIBILITY
# ════════════════════════════════════════════════════════════════════

def pass_defensibility(d):
    """Per-ticker defensibility checks. Returns list of (severity, msg)."""
    findings = []
    sources = d.get("data_sources", [])
    coverage = d.get("signal_coverage", "")
    spec_v = d.get("spec_version")

    if not sources:
        findings.append(("BLOCKER", "data_sources is empty"))
    elif len(sources) < 5:
        findings.append(("LAUNCH-OK", f"only {len(sources)} data sources (thin)"))

    # Parse signal_coverage. Two formats observed:
    #   "19/19 sub-signals with real data" → real
    #   "Estimated from public reporting"  → seed/fallback
    if not coverage:
        findings.append(("BLOCKER", "signal_coverage is empty"))
    elif "/" in coverage:
        try:
            parts = coverage.split("/")
            num = int(parts[0])
            denom_str = parts[1].split()[0]
            denom = int(denom_str)
            # v1.2.0: thresholds calibrated for sector-thin reporting.
            # Utilities/transport/energy legitimately have ~9/19 because
            # ~10 sub-signals (HRC, DEI, B Corp, USDA Organic, etc.) don't apply.
            # < 6 = genuinely insufficient. < 9 = defensible sector-thin.
            if num < 6:
                findings.append(("BLOCKER", f"signal_coverage insufficient: {num}/{denom}"))
            elif num < 9:
                findings.append(("LAUNCH-OK", f"signal_coverage sector-thin: {num}/{denom}"))
        except (ValueError, IndexError):
            findings.append(("LAUNCH-OK", f"signal_coverage unparseable: {coverage!r}"))
    else:
        # Seed-source format
        findings.append(("LAUNCH-OK", f"seed-source coverage format: {coverage!r}"))

    if spec_v != "1.2.0":
        findings.append(("BLOCKER", f"spec_version is {spec_v!r}, expected '1.2.0'"))

    # HD/AHI integrity
    hd = d.get("harm_documentation") or {}
    if hd.get("has_harm"):
        if not hd.get("sources"):
            findings.append(("BLOCKER", "harm_documentation.has_harm but no sources"))
        if not hd.get("flags"):
            findings.append(("BLOCKER", "harm_documentation.has_harm but no flags"))

    ah = d.get("algo_harm") or {}
    if ah.get("has_harm"):
        if not ah.get("flags"):
            findings.append(("BLOCKER", "algo_harm.has_harm but no flags"))
        comps = ah.get("components") or {}
        if not comps:
            findings.append(("BLOCKER", "algo_harm.has_harm but no components"))
        elif all(v == 0 for v in comps.values()):
            findings.append(("LAUNCH-OK", "algo_harm components all zero"))

    return findings


# ════════════════════════════════════════════════════════════════════
# Pass 2: COVERAGE — accumulated across all tickers
# ════════════════════════════════════════════════════════════════════

def pass_coverage(d, ticker):
    """Per-ticker coverage check. Returns list of findings."""
    findings = []
    if d is None:
        if ticker in TIER_1:
            findings.append(("BLOCKER", f"Tier-1 ticker {ticker} has no API response"))
        else:
            findings.append(("KNOWN-DEFERRED", f"{ticker} not in API (may be v1.2.1 backend coverage gap)"))
        return findings

    # Score must exist
    if d.get("composite") is None:
        findings.append(("BLOCKER", f"{ticker}: composite is None"))

    # All 5 dimensions must exist
    for dim in ("D_H", "D_U", "D_M", "D_A", "D_N"):
        v = d.get(dim)
        if v is None:
            findings.append(("BLOCKER", f"{ticker}: {dim} is None"))

    return findings


# ════════════════════════════════════════════════════════════════════
# Pass 3: CONSISTENCY — math correctness
# ════════════════════════════════════════════════════════════════════

def pass_consistency(d):
    """Per-ticker math/floor-rule checks. Returns list of findings."""
    findings = []

    composite = d.get("composite")
    if composite is None:
        return findings  # already flagged in pass 2

    dims = {dim: d.get(dim) for dim in ("D_H", "D_U", "D_M", "D_A", "D_N")}
    if any(v is None for v in dims.values()):
        return findings  # already flagged

    # Range checks
    if not (0 <= composite <= 100):
        findings.append(("BLOCKER", f"composite out of [0,100]: {composite}"))
    for k, v in dims.items():
        if not (0 <= v <= 100):
            findings.append(("BLOCKER", f"{k} out of [0,100]: {v}"))

    floor_triggered = bool(d.get("floor_triggered"))
    triggering_dim = d.get("triggering_dimension")  # 'H'/'U'/'M'/'A'/'N' or None

    # Find lowest dim
    dim_letters = ("H", "U", "M", "A", "N")
    dim_pairs = [(L, dims[f"D_{L}"]) for L in dim_letters]
    min_letter, min_val = min(dim_pairs, key=lambda x: x[1])

    # Floor logic: any dim < 30 → composite ≤ 50 AND floor_triggered=True
    if min_val < 30:
        if not floor_triggered:
            findings.append(("BLOCKER",
                f"floor should fire (D_{min_letter}={min_val} < 30) but floor_triggered=False"))
        if composite > 50:
            findings.append(("BLOCKER",
                f"floor should cap composite at 50 (D_{min_letter}={min_val} < 30) but composite={composite}"))
        if triggering_dim != min_letter:
            # Allow tie cases (multiple dims < 30)
            tied = [L for L, v in dim_pairs if v == min_val]
            if len(tied) == 1 or triggering_dim not in tied:
                findings.append(("LAUNCH-OK",
                    f"triggering_dimension={triggering_dim} but lowest dim is D_{min_letter}={min_val}"))
    else:
        # No dim < 30 → floor should NOT fire
        if floor_triggered:
            findings.append(("BLOCKER",
                f"floor fired but no dim < 30 (lowest: D_{min_letter}={min_val})"))

    # Composite math: should be approximately mean of 5 dims (with floor cap)
    expected_mean = sum(dims.values()) / 5
    if floor_triggered:
        # Floor fires: composite ≈ min(50, mean) ±1 for rounding
        expected = min(50, round(expected_mean))
        if abs(composite - expected) > 2:
            findings.append(("LAUNCH-OK",
                f"composite={composite} but expected min(50, mean(dims))={expected} (mean={expected_mean:.1f})"))
    else:
        # No floor: composite ≈ mean ±1 for rounding
        expected = round(expected_mean)
        if abs(composite - expected) > 2:
            findings.append(("LAUNCH-OK",
                f"composite={composite} but expected mean(dims)={expected} (mean={expected_mean:.1f})"))

    return findings


# ════════════════════════════════════════════════════════════════════
# Driver
# ════════════════════════════════════════════════════════════════════

def fetch_api(ticker, timeout=10):
    """Hit the API for one ticker. Returns dict or None on failure."""
    url = API_BASE + ticker
    req = Request(url, headers={"User-Agent": "audit_v120/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            return json.loads(resp.read())
    except (URLError, HTTPError, json.JSONDecodeError, TimeoutError) as e:
        return None


def main():
    if not SCORES_FILE.exists():
        sys.exit(f"NOT FOUND: {SCORES_FILE}")

    with open(SCORES_FILE) as f:
        all_scores = json.load(f)

    if not isinstance(all_scores, list):
        sys.exit(f"Expected list in {SCORES_FILE}, got {type(all_scores).__name__}")

    print(f"Auditing {len(all_scores)} companies via {API_BASE}...")
    print("(Each request ~0.3s; total ~2-3 min)")
    print()

    # Aggregate findings
    all_findings = []  # list of (ticker, severity, category, msg)
    api_failures = 0
    audit_start = time.time()

    for i, entry in enumerate(all_scores):
        ticker = entry.get("ticker")
        company = entry.get("company", "?")
        if not ticker:
            continue

        # Progress every 20
        if i % 20 == 0 and i > 0:
            elapsed = time.time() - audit_start
            rate = i / elapsed
            eta = (len(all_scores) - i) / rate
            print(f"  [{i}/{len(all_scores)}] {rate:.1f} req/s, ETA {eta:.0f}s, "
                  f"{len(all_findings)} findings so far")

        d = fetch_api(ticker)
        if d is None:
            api_failures += 1
            all_findings.append((ticker, "BLOCKER", "API",
                f"{ticker} ({company}): API request failed"))
            continue

        # Pass 1
        for sev, msg in pass_defensibility(d):
            all_findings.append((ticker, sev, "DEFENSIBILITY", msg))

        # Pass 2
        for sev, msg in pass_coverage(d, ticker):
            all_findings.append((ticker, sev, "COVERAGE", msg))

        # Pass 3
        for sev, msg in pass_consistency(d):
            all_findings.append((ticker, sev, "CONSISTENCY", msg))

    elapsed = time.time() - audit_start
    print()
    print(f"Audit complete in {elapsed:.0f}s")
    print(f"  {len(all_scores)} tickers checked")
    print(f"  {api_failures} API failures")
    print(f"  {len(all_findings)} total findings")

    # Tally by severity & category
    sev_counts = {}
    cat_counts = {}
    for _, sev, cat, _ in all_findings:
        sev_counts[sev] = sev_counts.get(sev, 0) + 1
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    blocker_n = sev_counts.get("BLOCKER", 0)
    launch_ok_n = sev_counts.get("LAUNCH-OK", 0)
    deferred_n = sev_counts.get("KNOWN-DEFERRED", 0)

    print()
    print("Severity breakdown:")
    print(f"  🔴 BLOCKER:        {blocker_n}")
    print(f"  🟡 LAUNCH-OK:      {launch_ok_n}")
    print(f"  🟢 KNOWN-DEFERRED: {deferred_n}")
    print()
    print("Category breakdown:")
    for cat in ("DEFENSIBILITY", "COVERAGE", "CONSISTENCY", "API"):
        print(f"  {cat:<14} {cat_counts.get(cat, 0)}")

    # Write report
    sev_order = {"BLOCKER": 0, "LAUNCH-OK": 1, "KNOWN-DEFERRED": 2}
    all_findings.sort(key=lambda x: (sev_order.get(x[1], 9), x[2], x[0]))

    sev_emoji = {"BLOCKER": "🔴", "LAUNCH-OK": "🟡", "KNOWN-DEFERRED": "🟢"}

    with open(OUTPUT, "w") as f:
        f.write(f"# v1.2.0 Score Audit\n\n")
        f.write(f"_Generated {time.strftime('%Y-%m-%d %H:%M')} · "
                f"{len(all_scores)} companies · "
                f"{elapsed:.0f}s elapsed_\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"| Severity | Count |\n|---|---|\n")
        f.write(f"| 🔴 BLOCKER | {blocker_n} |\n")
        f.write(f"| 🟡 LAUNCH-OK | {launch_ok_n} |\n")
        f.write(f"| 🟢 KNOWN-DEFERRED | {deferred_n} |\n\n")
        f.write(f"## By Category\n\n")
        f.write(f"| Category | Count |\n|---|---|\n")
        for cat in ("DEFENSIBILITY", "COVERAGE", "CONSISTENCY", "API"):
            f.write(f"| {cat} | {cat_counts.get(cat, 0)} |\n")
        f.write("\n")

        # Findings, severity-sorted
        last_sev = None
        last_cat = None
        for ticker, sev, cat, msg in all_findings:
            if sev != last_sev:
                f.write(f"\n## {sev_emoji[sev]} {sev}\n\n")
                last_sev = sev
                last_cat = None
            if cat != last_cat:
                f.write(f"\n### {cat}\n\n")
                last_cat = cat
            f.write(f"- **{ticker}** — {msg}\n")

    print()
    print(f"✓ Report written: {OUTPUT}")
    print()
    if blocker_n > 0:
        print(f"⚠️  {blocker_n} BLOCKER findings. Review {OUTPUT.name} before launch.")
        sys.exit(1)
    print("✅ No blockers. Launch-eligible per audit.")


if __name__ == "__main__":
    main()
