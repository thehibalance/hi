#!/usr/bin/env python3
"""
HI. — HUMAN Scoring Engine
Phase 2, Track B: Convert raw data signals into HUMAN dimension scores.

Takes JSON output from data pipelines (SEC EDGAR, EPA, etc.) and computes:
  D_H  — Human Consciousness (0-100)
  D_U  — Understanding & Empathy (0-100)
  D_M  — Moral & Ethical Conduct (0-100)
  D_A  — Alive & Environmental (0-100)
  D_N  — Natural Transparency (0-100)
  HUMAN — Composite score (0-100)
  HI Grade — Letter grade (HI Certified, A, B, C, F)

Follows HUMAN_Grade_Methodology_Spec v1.0
Floor rule: any dimension < 10 caps composite at 40.
"""

import json, os, sys
from pathlib import Path

# ── Industry Benchmarks ───────────────────────────────────────────────
# Revenue per employee medians by SIC code group (approximate)
# Used for industry normalization per spec Section 10
INDUSTRY_RPE_MEDIANS = {
    "tech": 500000,         # Software, internet
    "retail": 200000,       # Retail trade
    "finance": 600000,      # Financial services
    "healthcare": 250000,   # Healthcare
    "energy": 1500000,      # Oil, gas, energy
    "manufacturing": 300000,# Manufacturing
    "food": 150000,         # Food & beverage
    "media": 400000,        # Media & entertainment
    "telecom": 500000,      # Telecommunications
    "defense": 350000,      # Aerospace & defense
    "auto": 300000,         # Automotive
    "default": 350000,      # Fallback
}

SIC_TO_INDUSTRY = {
    "35": "tech", "36": "tech", "37": "manufacturing", "38": "tech",
    "73": "tech", "48": "telecom", "49": "energy",
    "52": "retail", "53": "retail", "54": "retail", "56": "retail", "57": "retail", "59": "retail",
    "60": "finance", "61": "finance", "62": "finance", "63": "finance", "64": "finance",
    "20": "food", "21": "food", "51": "food", "58": "food",
    "28": "healthcare", "80": "healthcare", "50": "retail",
    "13": "energy", "29": "energy",
    "27": "media", "78": "media",
    "45": "defense",
    "55": "auto",
}


def get_industry(sic_code):
    """Map SIC code to industry group."""
    if not sic_code:
        return "default"
    prefix = str(sic_code)[:2]
    return SIC_TO_INDUSTRY.get(prefix, "default")


def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def normalize(v, v_min, v_max):
    """Normalize value to 0-100 scale. Per spec Section 1.5."""
    if v_max == v_min:
        return 50
    return clamp((v - v_min) / (v_max - v_min) * 100)


# ── Dimension Scoring Functions ───────────────────────────────────────

def score_h_dimension(h_signals, industry):
    """
    H — Human Consciousness (20%)
    Sub-signals per spec:
      H.1 Creative Agency Ratio (0.25) — proxied by inverse automation signal
      H.2 Craft & Tacit Knowledge (0.20) — proxied by industry type
      H.3 Human Decision Depth (0.20) — default 50 (needs operational data)
      H.4 Accountability Chain (0.15) — default 50 (needs governance data)
      H.5 AI Displacement Trajectory (0.20) — from SEC headcount vs R&D
    """
    scores = {}

    # H.1 Creative Agency Ratio — proxy from revenue/employee
    # High RPE relative to industry = more automation = lower human agency
    rpe = h_signals.get("revenue_per_employee")
    industry_median = INDUSTRY_RPE_MEDIANS.get(industry, INDUSTRY_RPE_MEDIANS["default"])
    if rpe:
        # Ratio of industry median to actual RPE
        # If RPE = median, score ~60. If RPE = 3x median, score ~20. If RPE = 0.5x median, score ~90.
        ratio = industry_median / rpe if rpe > 0 else 1.0
        scores["H.1"] = clamp(ratio * 65)  # Scale so median = ~65
    else:
        scores["H.1"] = 50  # Default per spec Section 10.4

    # H.2 Craft & Tacit Knowledge — proxy from industry type
    craft_scores = {
        "food": 65, "manufacturing": 60, "healthcare": 70, "defense": 55,
        "auto": 55, "retail": 45, "tech": 40, "finance": 45,
        "media": 55, "telecom": 40, "energy": 50, "default": 50,
    }
    scores["H.2"] = craft_scores.get(industry, 50)

    # H.3 Human Decision Depth — default (needs operational disclosure data)
    scores["H.3"] = 50

    # H.4 Accountability Chain — default (needs governance data)
    scores["H.4"] = 50

    # H.5 AI Displacement Trajectory — from SEC data
    displacement = h_signals.get("displacement_signal")
    if displacement is not None:
        # Per spec: S_H5 = clamp(100 - displacement_signal * 100, 0, 100)
        # But our displacement is already (rd_change - hc_change) as percentage points
        # Normalize: 0 displacement = score 80, +50 displacement = score 30, -20 = score 100
        scores["H.5"] = clamp(80 - displacement * 1.0)
    else:
        # Use headcount change alone if available
        hc_change = h_signals.get("headcount_change_pct")
        if hc_change is not None:
            # Growing headcount = good. Shrinking = bad.
            # +10% growth = score 80, 0% = score 60, -20% = score 20
            scores["H.5"] = clamp(60 + hc_change * 2)
        else:
            scores["H.5"] = 50

    # Weighted average per spec: D_H = Σ(W_i × S_i)
    D_H = (
        0.25 * scores["H.1"] +
        0.20 * scores["H.2"] +
        0.20 * scores["H.3"] +
        0.15 * scores["H.4"] +
        0.20 * scores["H.5"]
    )

    return round(D_H, 1), scores


def score_u_dimension(u_signals, industry):
    """
    U — Understanding & Empathy (20%)
    Requires Glassdoor, customer service data, layoff tracking.
    With SEC data only, we use defaults + any available signals.
    """
    scores = {}

    # U.1 Empathy Expression — default (needs customer service data)
    scores["U.1"] = 50

    # U.2 Worker Empathy — default (needs Glassdoor/employee data)
    scores["U.2"] = 50

    # U.3 Relational Integrity — default (needs marketing/product analysis)
    scores["U.3"] = 50

    # U.4 Moral Courage — default
    scores["U.4"] = 50

    # U.5 Simulated Empathy Detection — default
    scores["U.5"] = 50

    D_U = (
        0.25 * scores["U.1"] +
        0.25 * scores["U.2"] +
        0.20 * scores["U.3"] +
        0.15 * scores["U.4"] +
        0.15 * scores["U.5"]
    )

    return round(D_U, 1), scores


def score_m_dimension(m_signals, industry):
    """
    M — Moral & Ethical Conduct (20%)
    Deduction-based per spec: start at 100, subtract for violations.
    """
    score = 100
    scores = {}

    # M.1 Pricing Ethics — default (needs pricing analysis)
    scores["M.1"] = 80  # Assume decent unless flagged

    # M.2 Data Ethics — default
    scores["M.2"] = 70  # Moderate concern for most public companies

    # M.3 Market Ethics — check for litigation
    litigation = m_signals.get("litigation", {}).get("value")
    if litigation and litigation > 0:
        # Deduction based on litigation amount relative to assets
        # Major litigation = bigger deduction
        if litigation > 1000000000:  # >$1B
            scores["M.3"] = 30
        elif litigation > 100000000:  # >$100M
            scores["M.3"] = 50
        elif litigation > 10000000:  # >$10M
            scores["M.3"] = 65
        else:
            scores["M.3"] = 75
    else:
        scores["M.3"] = 85

    # M.4 Product Ethics — default
    scores["M.4"] = 70

    # M.5 Political Ethics — default (needs lobbying data)
    scores["M.5"] = 60

    D_M = (
        0.20 * scores["M.1"] +
        0.20 * scores["M.2"] +
        0.20 * scores["M.3"] +
        0.25 * scores["M.4"] +
        0.15 * scores["M.5"]
    )

    return round(D_M, 1), scores


def score_a_dimension(a_signals, industry):
    """
    A — Alive & Environmental (20%)
    Limited from SEC data alone. Capex trends can proxy infrastructure investment.
    """
    scores = {}

    # A.1 Energy Score — default (needs CDP/EPA data)
    # Industry-adjusted defaults
    energy_defaults = {
        "energy": 30, "manufacturing": 45, "tech": 50, "finance": 65,
        "healthcare": 55, "retail": 50, "food": 55, "media": 60,
        "telecom": 45, "defense": 40, "auto": 40, "default": 50,
    }
    scores["A.1"] = energy_defaults.get(industry, 50)

    # A.2 Water Score — default (needs CDP water data)
    scores["A.2"] = 50

    # A.3 Land & Habitat — default
    scores["A.3"] = 50

    # A.4 Hardware Lifecycle — default (needs iFixit/Boavizta data)
    # Tech companies get lower default (more e-waste)
    hw_defaults = {
        "tech": 40, "telecom": 45, "manufacturing": 50, "default": 55,
    }
    scores["A.4"] = hw_defaults.get(industry, 55)

    D_A = (
        0.30 * scores["A.1"] +
        0.25 * scores["A.2"] +
        0.20 * scores["A.3"] +
        0.25 * scores["A.4"]
    )

    return round(D_A, 1), scores


def score_n_dimension(n_signals, industry):
    """
    N — Natural Transparency (20%)
    SEC filing frequency is a direct transparency signal.
    """
    scores = {}

    # N.1 AI Disclosure Quality — default (needs NLP analysis of filings)
    scores["N.1"] = 40  # Most companies poor at AI disclosure

    # N.2 Environmental Reporting — proxy from filing presence
    scores["N.2"] = 50

    # N.3 Labor Practice Auditability — default
    scores["N.3"] = 45

    # N.4 Humanwashing Detection — default (no flags without full analysis)
    scores["N.4"] = 80  # Start at 80 (no detected humanwashing)

    # N.5 Disclosure Completeness — from SEC filing frequency
    total_filings = n_signals.get("total_recent_filings", 0)
    if total_filings >= 8:
        scores["N.5"] = 90  # Very active filer
    elif total_filings >= 5:
        scores["N.5"] = 75
    elif total_filings >= 3:
        scores["N.5"] = 60
    elif total_filings >= 1:
        scores["N.5"] = 40
    else:
        scores["N.5"] = 20  # Very low disclosure

    # Bonus: Large accelerated filers have more disclosure requirements
    category = n_signals.get("category", "")
    if "Large Accelerated" in str(category):
        scores["N.5"] = min(100, scores["N.5"] + 5)

    D_N = (
        0.25 * scores["N.1"] +
        0.20 * scores["N.2"] +
        0.20 * scores["N.3"] +
        0.20 * scores["N.4"] +
        0.15 * scores["N.5"]
    )

    return round(D_N, 1), scores


# ── Composite Score & Grade ───────────────────────────────────────────

def compute_composite(D_H, D_U, D_M, D_A, D_N):
    """Compute composite HUMAN score with floor rule. Per spec Section 2."""
    composite = (D_H + D_U + D_M + D_A + D_N) / 5
    floor_triggered = False
    triggering_dimension = None

    # Floor rule: any dimension < 10 caps composite at 40
    min_dim = min(D_H, D_U, D_M, D_A, D_N)
    if min_dim < 10:
        composite = min(composite, 40)
        floor_triggered = True
        dims = {"H": D_H, "U": D_U, "M": D_M, "A": D_A, "N": D_N}
        triggering_dimension = min(dims, key=dims.get)

    return round(composite, 1), floor_triggered, triggering_dimension


def get_hi_grade(composite, verified=False):
    """Classify composite into HI Grade. Per spec Section 2.3."""
    if composite >= 90 and verified:
        return "HI Certified", "Humans and tech, in harmony. This is what balance looks like."
    elif composite >= 90:
        return "A", "AI does the math. Humans do the handshakes. Nailed it."  # Capped at A without verification
    elif composite >= 80:
        return "A", "AI does the math. Humans do the handshakes. Nailed it."
    elif composite >= 60:
        return "B", "Humans and machines, learning to share the remote."
    elif composite >= 42:
        return "C", "42. The answer to everything. Now what's the question?"
    else:
        return "F", "Don't panic. Every journey starts somewhere."


# ── Full Scoring Pipeline ─────────────────────────────────────────────

def score_company(sec_data):
    """Score a single company from SEC pipeline output. Returns HUMAN Genome."""
    company = sec_data.get("company", "Unknown")
    ticker = sec_data.get("ticker", "")

    if sec_data.get("error"):
        return {
            "company": company,
            "ticker": ticker,
            "error": sec_data["error"],
            "confidence": "Unscored",
        }

    # Determine industry
    sic = sec_data.get("n_signals", {}).get("sic", "")
    industry = get_industry(sic)

    # Score each dimension
    D_H, h_detail = score_h_dimension(sec_data.get("h_signals", {}), industry)
    D_U, u_detail = score_u_dimension(sec_data.get("u_signals", {}), industry)
    D_M, m_detail = score_m_dimension(sec_data.get("m_signals", {}), industry)
    D_A, a_detail = score_a_dimension(sec_data.get("a_signals", {}), industry)
    D_N, n_detail = score_n_dimension(sec_data.get("n_signals", {}), industry)

    # Composite
    composite, floor_triggered, triggering_dim = compute_composite(D_H, D_U, D_M, D_A, D_N)
    grade, satire = get_hi_grade(composite)

    # Confidence level per spec Section 2.4
    h_has_data = sec_data.get("h_signals", {}).get("headcount") is not None
    n_has_data = sec_data.get("n_signals", {}).get("total_recent_filings", 0) > 0
    if h_has_data and n_has_data:
        confidence = "Estimated"  # Have real data but not verified
    else:
        confidence = "Estimated"  # All public companies have some SEC data

    # Humanwashing flags
    hw_flags = []
    rpe = sec_data.get("h_signals", {}).get("revenue_per_employee")
    if rpe and rpe > 2000000:
        hw_flags.append("HW.1: Revenue/employee >$2M suggests high automation")
    displacement = sec_data.get("h_signals", {}).get("displacement_signal")
    if displacement and displacement > 30:
        hw_flags.append("HW.2: R&D growth significantly outpacing headcount — possible rapid AI displacement")

    return {
        "company": company,
        "ticker": ticker,
        "industry": industry,
        "sic": sic,
        "sic_description": sec_data.get("n_signals", {}).get("sic_description", ""),

        # Dimension scores
        "D_H": D_H,
        "D_U": D_U,
        "D_M": D_M,
        "D_A": D_A,
        "D_N": D_N,

        # Composite
        "composite": composite,
        "hi_grade": grade,
        "satire": satire,
        "floor_triggered": floor_triggered,
        "triggering_dimension": triggering_dim,

        # Metadata
        "confidence": confidence,
        "spec_version": "1.0.0",
        "data_sources": ["SEC EDGAR"],
        "humanwashing_flags": hw_flags,

        # Sub-signal detail (the HUMAN Genome)
        "genome": {
            "H": h_detail,
            "U": u_detail,
            "M": m_detail,
            "A": a_detail,
            "N": n_detail,
        },

        # Key signals for display
        "key_signals": {
            "headcount": sec_data.get("h_signals", {}).get("headcount", {}).get("value"),
            "headcount_change_pct": sec_data.get("h_signals", {}).get("headcount_change_pct"),
            "revenue_per_employee": sec_data.get("h_signals", {}).get("revenue_per_employee"),
            "displacement_signal": displacement,
        },
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HI. HUMAN Scoring Engine")
    parser.add_argument("--input", default="data/sec", help="Input directory (SEC pipeline output)")
    parser.add_argument("--output", default="data/scores", help="Output directory")
    parser.add_argument("--file", help="Score a single JSON file")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.file:
        # Score single file
        with open(args.file) as f:
            sec_data = json.load(f)
        result = score_company(sec_data)
        print(json.dumps(result, indent=2))
        outfile = output_dir / f"{result['ticker']}_scored.json"
        with open(outfile, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved to {outfile}")
    else:
        # Score all companies from pipeline output
        input_dir = Path(args.input)
        combined_file = input_dir / "all_companies.json"

        if combined_file.exists():
            with open(combined_file) as f:
                all_sec = json.load(f)
        else:
            # Load individual files
            all_sec = []
            for jf in sorted(input_dir.glob("*.json")):
                if jf.name != "all_companies.json":
                    with open(jf) as f:
                        all_sec.append(json.load(f))

        print(f"HI. Scoring Engine — Processing {len(all_sec)} companies")
        print(f"Spec version: 1.0.0")
        print()

        all_scores = []
        for sec_data in all_sec:
            result = score_company(sec_data)
            all_scores.append(result)

            grade = result.get("hi_grade", "?")
            comp = result.get("composite", 0)
            company = result.get("company", "?")
            print(f"  {grade:12s} {comp:5.1f}  {company}")

        # Sort by composite descending
        all_scores.sort(key=lambda x: x.get("composite", 0), reverse=True)

        # Save
        outfile = output_dir / "all_scores.json"
        with open(outfile, "w") as f:
            json.dump(all_scores, f, indent=2)

        # Summary
        print(f"\n{'='*60}")
        print(f"SCORING COMPLETE")
        print(f"{'='*60}")

        grades = {}
        for s in all_scores:
            g = s.get("hi_grade", "?")
            grades[g] = grades.get(g, 0) + 1

        for g in ["HI Certified", "A", "B", "C", "F"]:
            if g in grades:
                print(f"  {g}: {grades[g]}")

        flagged = [s for s in all_scores if s.get("humanwashing_flags")]
        if flagged:
            print(f"\n  Humanwashing flags: {len(flagged)} companies")
            for s in flagged:
                print(f"    {s['company']}: {', '.join(s['humanwashing_flags'])}")

        print(f"\n  Output: {outfile}")


if __name__ == "__main__":
    main()
