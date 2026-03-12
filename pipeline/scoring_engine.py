#!/usr/bin/env python3
"""
HI. — HUMAN Scoring Engine v2
Merges signals from ALL data sources into HUMAN dimension scores.

Data sources:
  1. SEC EDGAR  — headcount, revenue, R&D, litigation, filing frequency
  2. EPA ECHO   — environmental violations, penalties, inspections
  3. BLS        — industry wage/employment benchmarks
  4. CDP        — climate disclosure scores
  5. Job Boards — AI hiring velocity
  6. Glassdoor  — employee ratings, CEO approval, culture

Follows HUMAN_Grade_Methodology_Spec v1.0
Floor rule: any dimension < 10 caps composite at 40.

Usage:
  python scoring_engine.py
  python scoring_engine.py --sec data/sec --epa data/epa --cdp data/cdp
"""

import json, os, sys
from pathlib import Path

INDUSTRY_RPE_MEDIANS = {
    "tech": 500000, "retail": 200000, "finance": 600000,
    "healthcare": 250000, "energy": 1500000, "manufacturing": 300000,
    "food": 150000, "media": 400000, "telecom": 500000,
    "defense": 350000, "auto": 300000, "default": 350000,
}

SIC_TO_INDUSTRY = {
    "35": "tech", "36": "tech", "37": "manufacturing", "38": "tech",
    "73": "tech", "48": "telecom", "49": "energy",
    "52": "retail", "53": "retail", "54": "retail", "56": "retail", "57": "retail", "59": "retail",
    "60": "finance", "61": "finance", "62": "finance", "63": "finance", "64": "finance",
    "20": "food", "21": "food", "51": "food", "58": "food",
    "28": "healthcare", "80": "healthcare", "50": "retail",
    "13": "energy", "29": "energy", "27": "media", "78": "media",
    "45": "defense", "55": "auto",
}

def get_industry(sic_code):
    if not sic_code: return "default"
    return SIC_TO_INDUSTRY.get(str(sic_code)[:2], "default")

def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))

def normalize(v, v_min, v_max):
    if v_max == v_min: return 50
    return clamp((v - v_min) / (v_max - v_min) * 100)

def load_source(directory, filename="all_companies.json"):
    path = Path(directory) / filename
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []

def normalize_name(name):
    """Normalize company name for matching: strip Inc, Corp, LLC, etc."""
    n = name.lower().strip()
    for suffix in [' inc.', ' inc', ' corp.', ' corp', ' llc', ' ltd.', ' ltd',
                   ' co.', ' co', ' plc', ' sa', ' ag', ' nv', ' se',
                   ' holdings', ' group', ' international', ' company',
                   ' technologies', ' technology', ' enterprises', ' solutions',
                   ' platforms', ' (google)', ' (alphabet)', ' (facebook)',
                   ' (square)', ' (raytheon)']:
        if n.endswith(suffix):
            n = n[:-len(suffix)].strip()
    # Remove trailing punctuation
    n = n.rstrip('.,')
    return n

def index_by_company(records, key="company"):
    idx = {}
    for r in records:
        name = r.get(key, "").lower().strip()
        if name: idx[name] = r
        # Also index by normalized name
        norm = normalize_name(name)
        if norm and norm != name: idx[norm] = r
        ticker = r.get("ticker", "")
        if ticker: idx[f"ticker:{ticker.upper()}"] = r
    return idx

def find_match(company_name, ticker, index):
    # 1. Exact name match
    result = index.get(company_name.lower().strip())
    if result: return result
    # 2. Normalized name match
    norm = normalize_name(company_name)
    result = index.get(norm)
    if result: return result
    # 3. Ticker match (most reliable cross-source link)
    if ticker:
        result = index.get(f"ticker:{ticker.upper()}")
        if result: return result
    # No partial/substring matching — too many false positives
    return None


# ── Dimension Scoring ─────────────────────────────────────────────────

def score_h_dimension(sec_h, job_data, bls_data, industry):
    scores = {}
    sources_used = []

    rpe = sec_h.get("revenue_per_employee")
    industry_median = INDUSTRY_RPE_MEDIANS.get(industry, INDUSTRY_RPE_MEDIANS["default"])
    ai_ratio = job_data.get("h_signals", {}).get("ai_ratio") if job_data else None

    if rpe and ai_ratio is not None:
        rpe_score = clamp((industry_median / rpe) * 65) if rpe > 0 else 50
        ai_score = job_data["h_signals"].get("adjusted_score", 50)
        scores["H.1"] = round(rpe_score * 0.5 + ai_score * 0.5, 1)
        sources_used.extend(["SEC", "Jobs"])
    elif rpe:
        scores["H.1"] = clamp((industry_median / rpe) * 65) if rpe > 0 else 50
        sources_used.append("SEC")
    elif ai_ratio is not None:
        scores["H.1"] = job_data["h_signals"].get("adjusted_score", 50)
        sources_used.append("Jobs")
    else:
        scores["H.1"] = 50

    craft_defaults = {"food": 65, "manufacturing": 60, "healthcare": 70, "defense": 55,
                      "auto": 55, "retail": 45, "tech": 40, "finance": 45,
                      "media": 55, "telecom": 40, "energy": 50, "default": 50}
    base_craft = craft_defaults.get(industry, 50)
    if bls_data:
        ind_data = bls_data.get("industries", {}).get(industry, {})
        wage_ratio = ind_data.get("wage_vs_national")
        if wage_ratio:
            base_craft = clamp(base_craft + (wage_ratio - 1.0) * 20)
            sources_used.append("BLS")
    scores["H.2"] = round(base_craft, 1)
    scores["H.3"] = 50
    scores["H.4"] = 50

    displacement = sec_h.get("displacement_signal")
    job_trend = job_data.get("h_signals", {}).get("ai_hiring_trend") if job_data else None
    if displacement is not None:
        scores["H.5"] = clamp(80 - displacement * 1.0)
        sources_used.append("SEC")
        if job_trend == "surging": scores["H.5"] = clamp(scores["H.5"] - 10)
        elif job_trend == "growing": scores["H.5"] = clamp(scores["H.5"] - 5)
    elif job_data and job_data.get("h_signals", {}).get("adjusted_score") is not None:
        scores["H.5"] = job_data["h_signals"]["adjusted_score"]
        sources_used.append("Jobs")
    else:
        hc_change = sec_h.get("headcount_change_pct")
        if hc_change is not None:
            scores["H.5"] = clamp(60 + hc_change * 2)
            sources_used.append("SEC")
        else:
            scores["H.5"] = 50

    D_H = 0.25*scores["H.1"] + 0.20*scores["H.2"] + 0.20*scores["H.3"] + 0.15*scores["H.4"] + 0.20*scores["H.5"]
    return round(D_H, 1), scores, list(set(sources_used))


def score_u_dimension(sec_u, glassdoor_data, industry):
    scores = {}
    sources_used = []
    gd = glassdoor_data.get("u_signals", {}) if glassdoor_data else {}

    if gd.get("overall_score") is not None:
        scores["U.1"] = round(gd.get("overall_score", 50) * 0.5 + gd.get("culture_score", 50) * 0.5, 1)
        scores["U.2"] = round(gd.get("worklife_score", 50) * 0.5 + gd.get("recommend_pct", 50) * 0.5, 1)
        scores["U.3"] = gd.get("culture_score", 50)
        sources_used.append("Glassdoor")
    else:
        scores["U.1"] = 50
        scores["U.2"] = 50
        scores["U.3"] = 50

    scores["U.4"] = 50
    scores["U.5"] = 50

    D_U = 0.25*scores["U.1"] + 0.25*scores["U.2"] + 0.20*scores["U.3"] + 0.15*scores["U.4"] + 0.15*scores["U.5"]
    return round(D_U, 1), scores, sources_used


def score_m_dimension(sec_m, epa_data, glassdoor_data, industry):
    scores = {}
    sources_used = []
    scores["M.1"] = 80
    scores["M.2"] = 70

    litigation = sec_m.get("litigation", {}).get("value")
    epa_penalties = epa_data.get("m_signals", {}).get("total_penalties", 0) if epa_data else 0
    epa_actions = epa_data.get("m_signals", {}).get("formal_actions", 0) if epa_data else 0
    total_legal = (litigation or 0) + epa_penalties

    if total_legal > 1000000000: scores["M.3"] = 20
    elif total_legal > 100000000: scores["M.3"] = 40
    elif total_legal > 10000000: scores["M.3"] = 55
    elif total_legal > 1000000: scores["M.3"] = 65
    elif total_legal > 0: scores["M.3"] = 75
    else: scores["M.3"] = 85

    if litigation: sources_used.append("SEC")
    if epa_penalties > 0 or epa_actions > 0: sources_used.append("EPA")

    gd_m = glassdoor_data.get("m_signals", {}) if glassdoor_data else {}
    if gd_m.get("mgmt_score") is not None:
        scores["M.4"] = round(gd_m["mgmt_score"] * 0.6 + gd_m.get("comp_score", 50) * 0.4, 1)
        sources_used.append("Glassdoor")
    else:
        scores["M.4"] = 70

    if gd_m.get("ceo_score") is not None:
        scores["M.5"] = gd_m["ceo_score"]
    else:
        scores["M.5"] = 60

    D_M = 0.20*scores["M.1"] + 0.20*scores["M.2"] + 0.20*scores["M.3"] + 0.25*scores["M.4"] + 0.15*scores["M.5"]
    return round(D_M, 1), scores, list(set(sources_used))


def score_a_dimension(sec_a, epa_data, cdp_data, industry):
    scores = {}
    sources_used = []
    cdp_a = cdp_data.get("a_signals", {}) if cdp_data else {}

    if cdp_a.get("cdp_climate_score") is not None:
        scores["A.1"] = cdp_a["cdp_climate_score"]
        sources_used.append("CDP")
    else:
        defaults = {"energy": 30, "manufacturing": 45, "tech": 50, "finance": 65,
                    "healthcare": 55, "retail": 50, "food": 55, "media": 60,
                    "telecom": 45, "defense": 40, "auto": 40, "default": 50}
        scores["A.1"] = defaults.get(industry, 50)

    if cdp_a.get("cdp_water_score") is not None:
        scores["A.2"] = cdp_a["cdp_water_score"]
        if "CDP" not in sources_used: sources_used.append("CDP")
    else:
        scores["A.2"] = 50

    epa_a = epa_data.get("a_signals", {}) if epa_data else {}
    if epa_a.get("total_violations_3yr") is not None:
        v = epa_a["total_violations_3yr"]
        if v == 0: scores["A.3"] = 85
        elif v <= 3: scores["A.3"] = 65
        elif v <= 10: scores["A.3"] = 45
        elif v <= 20: scores["A.3"] = 30
        else: scores["A.3"] = 15
        sources_used.append("EPA")
    else:
        scores["A.3"] = 50

    if cdp_a.get("cdp_forests_score") is not None:
        scores["A.4"] = cdp_a["cdp_forests_score"]
    else:
        hw_defaults = {"tech": 40, "telecom": 45, "manufacturing": 50, "default": 55}
        scores["A.4"] = hw_defaults.get(industry, 55)

    D_A = 0.30*scores["A.1"] + 0.25*scores["A.2"] + 0.20*scores["A.3"] + 0.25*scores["A.4"]
    return round(D_A, 1), scores, list(set(sources_used))


def score_n_dimension(sec_n, cdp_data, epa_data, industry):
    scores = {}
    sources_used = []
    scores["N.1"] = 40

    cdp_n = cdp_data.get("n_signals", {}) if cdp_data else {}
    if cdp_n.get("cdp_non_responder") is True:
        scores["N.2"] = 5
        sources_used.append("CDP")
    elif cdp_n.get("disclosure_quality"):
        q = cdp_n["disclosure_quality"]
        if "EXCELLENT" in q: scores["N.2"] = 90
        elif "GOOD" in q: scores["N.2"] = 70
        elif "PARTIAL" in q: scores["N.2"] = 45
        else: scores["N.2"] = 25
        sources_used.append("CDP")
    else:
        scores["N.2"] = 50

    scores["N.3"] = 45
    scores["N.4"] = 80

    total_filings = sec_n.get("total_recent_filings", 0)
    if total_filings >= 8: scores["N.5"] = 90
    elif total_filings >= 5: scores["N.5"] = 75
    elif total_filings >= 3: scores["N.5"] = 60
    elif total_filings >= 1: scores["N.5"] = 40
    else: scores["N.5"] = 20
    if total_filings > 0: sources_used.append("SEC")

    epa_a = epa_data.get("a_signals", {}) if epa_data else {}
    if epa_a.get("inspections_5yr", 0) > 10:
        scores["N.5"] = min(100, scores["N.5"] + 5)
        if "EPA" not in sources_used: sources_used.append("EPA")

    if "Large Accelerated" in str(sec_n.get("category", "")):
        scores["N.5"] = min(100, scores["N.5"] + 5)

    D_N = 0.25*scores["N.1"] + 0.20*scores["N.2"] + 0.20*scores["N.3"] + 0.20*scores["N.4"] + 0.15*scores["N.5"]
    return round(D_N, 1), scores, sources_used


def compute_composite(D_H, D_U, D_M, D_A, D_N):
    composite = (D_H + D_U + D_M + D_A + D_N) / 5
    floor_triggered = False
    triggering_dimension = None
    min_dim = min(D_H, D_U, D_M, D_A, D_N)
    if min_dim < 10:
        composite = min(composite, 40)
        floor_triggered = True
        dims = {"H": D_H, "U": D_U, "M": D_M, "A": D_A, "N": D_N}
        triggering_dimension = min(dims, key=dims.get)
    return round(composite, 1), floor_triggered, triggering_dimension

def get_hi_grade(composite, verified=False):
    if composite >= 90 and verified:
        return "HI Certified", "Humans and tech, in harmony. This is what balance looks like."
    elif composite >= 90:
        return "A", "AI does the math. Humans do the handshakes. Nailed it."
    elif composite >= 80:
        return "A", "AI does the math. Humans do the handshakes. Nailed it."
    elif composite >= 60:
        return "B", "Humans and machines, learning to share the remote."
    elif composite >= 42:
        return "C", "42. The answer to everything. Now what's the question?"
    else:
        return "F", "Don't panic. Every journey starts somewhere."


def score_company(company_name, ticker="", sec_data=None, epa_data=None,
                  bls_data=None, cdp_data=None, job_data=None, glassdoor_data=None):
    sic = sec_data.get("n_signals", {}).get("sic", "") if sec_data else ""
    industry = get_industry(sic)

    sec_h = sec_data.get("h_signals", {}) if sec_data else {}
    sec_m = sec_data.get("m_signals", {}) if sec_data else {}
    sec_n = sec_data.get("n_signals", {}) if sec_data else {}
    sec_u = sec_data.get("u_signals", {}) if sec_data else {}

    D_H, h_detail, h_src = score_h_dimension(sec_h, job_data, bls_data, industry)
    D_U, u_detail, u_src = score_u_dimension(sec_u, glassdoor_data, industry)
    D_M, m_detail, m_src = score_m_dimension(sec_m, epa_data, glassdoor_data, industry)
    D_A, a_detail, a_src = score_a_dimension(sec_data.get("a_signals", {}) if sec_data else {}, epa_data, cdp_data, industry)
    D_N, n_detail, n_src = score_n_dimension(sec_n, cdp_data, epa_data, industry)

    composite, floor_triggered, triggering_dim = compute_composite(D_H, D_U, D_M, D_A, D_N)
    grade, satire = get_hi_grade(composite)
    all_sources = sorted(set(h_src + u_src + m_src + a_src + n_src)) or ["Defaults"]

    all_details = {**h_detail, **u_detail, **m_detail, **a_detail, **n_detail}
    real_count = sum(1 for v in all_details.values() if v != 50)

    hw_flags = []
    rpe = sec_h.get("revenue_per_employee")
    if rpe and rpe > 2000000:
        hw_flags.append("HW.1: Revenue/employee >$2M suggests high automation")
    displacement = sec_h.get("displacement_signal")
    if displacement and displacement > 30:
        hw_flags.append("HW.2: R&D growth significantly outpacing headcount")
    if job_data and job_data.get("h_signals", {}).get("ai_ratio", 0) >= 0.35:
        hw_flags.append("HW.3: AI roles dominate job postings (>35%)")
    if epa_data and epa_data.get("a_signals", {}).get("total_violations_3yr", 0) > 20:
        hw_flags.append("HW.4: Significant environmental violations")
    if cdp_data and cdp_data.get("n_signals", {}).get("cdp_non_responder"):
        hw_flags.append("HW.5: Refuses CDP climate disclosure")

    return {
        "company": company_name, "ticker": ticker, "industry": industry, "sic": sic,
        "sic_description": sec_data.get("n_signals", {}).get("sic_description", "") if sec_data else "",
        "D_H": D_H, "D_U": D_U, "D_M": D_M, "D_A": D_A, "D_N": D_N,
        "composite": composite, "hi_grade": grade, "satire": satire,
        "floor_triggered": floor_triggered, "triggering_dimension": triggering_dim,
        "confidence": "Estimated", "spec_version": "1.0.0",
        "data_sources": all_sources,
        "signal_coverage": f"{real_count}/{len(all_details)} sub-signals with real data",
        "humanwashing_flags": hw_flags,
        "genome": {
            "H": {"scores": h_detail, "sources": h_src},
            "U": {"scores": u_detail, "sources": u_src},
            "M": {"scores": m_detail, "sources": m_src},
            "A": {"scores": a_detail, "sources": a_src},
            "N": {"scores": n_detail, "sources": n_src},
        },
        "key_signals": {
            "headcount": sec_h.get("headcount", {}).get("value") if isinstance(sec_h.get("headcount"), dict) else None,
            "headcount_change_pct": sec_h.get("headcount_change_pct"),
            "revenue_per_employee": rpe,
            "displacement_signal": displacement,
            "ai_hiring_ratio": job_data.get("h_signals", {}).get("ai_ratio") if job_data else None,
            "glassdoor_rating": glassdoor_data.get("u_signals", {}).get("overall_rating") if glassdoor_data else None,
            "cdp_climate": cdp_data.get("a_signals", {}).get("cdp_climate_letter") if cdp_data else None,
            "epa_violations": epa_data.get("a_signals", {}).get("total_violations_3yr") if epa_data else None,
        },
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HI. HUMAN Scoring Engine v2")
    parser.add_argument("--sec", default="data/sec")
    parser.add_argument("--epa", default="data/epa")
    parser.add_argument("--bls", default="data/bls")
    parser.add_argument("--cdp", default="data/cdp")
    parser.add_argument("--jobs", default="data/jobs")
    parser.add_argument("--glassdoor", default="data/glassdoor")
    parser.add_argument("--output", default="data/scores")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("HI. Scoring Engine v2 — Loading data sources")
    print("=" * 60)

    sec_records = load_source(args.sec)
    epa_records = load_source(args.epa)
    bls_data = None
    bls_path = Path(args.bls) / "industry_benchmarks.json"
    if bls_path.exists():
        with open(bls_path) as f: bls_data = json.load(f)
    cdp_records = load_source(args.cdp)
    job_records = load_source(args.jobs)
    gd_records = load_source(args.glassdoor)

    print(f"  SEC EDGAR:  {len(sec_records)} companies")
    print(f"  EPA ECHO:   {len(epa_records)} companies")
    print(f"  BLS:        {'loaded' if bls_data else 'not found'}")
    print(f"  CDP:        {len(cdp_records)} companies")
    print(f"  Job Boards: {len(job_records)} companies")
    print(f"  Glassdoor:  {len(gd_records)} companies")

    sec_idx = index_by_company(sec_records)
    epa_idx = index_by_company(epa_records)
    cdp_idx = index_by_company(cdp_records)
    job_idx = index_by_company(job_records)
    gd_idx = index_by_company(gd_records)

    # Build master company list using normalized names to prevent duplicates
    all_companies = set()
    for idx in [sec_idx, epa_idx, cdp_idx, job_idx, gd_idx]:
        for key in idx:
            if not key.startswith("ticker:"):
                all_companies.add(normalize_name(key))

    print(f"\n  Total unique companies: {len(all_companies)}")
    print("=" * 60)

    all_scores = []
    for company_lower in sorted(all_companies):
        # Get ticker from any source
        ticker = ""
        norm = normalize_name(company_lower)
        for idx in [sec_idx, epa_idx, cdp_idx, job_idx, gd_idx]:
            for key in [company_lower, norm]:
                if key in idx and idx[key].get("ticker"):
                    ticker = idx[key]["ticker"]
                    break
            if ticker: break

        sec = find_match(company_lower, ticker, sec_idx)
        epa = find_match(company_lower, ticker, epa_idx)
        cdp = find_match(company_lower, ticker, cdp_idx)
        job = find_match(company_lower, ticker, job_idx)
        gd = find_match(company_lower, ticker, gd_idx)

        name = company_lower.title()
        for source in [sec, epa, cdp, job, gd]:
            if source:
                name = source.get("company", name)
                ticker = source.get("ticker", ticker) or ticker

        if sec and sec.get("error") and not any([epa, cdp, job, gd]):
            continue

        result = score_company(name, ticker, sec, epa, bls_data, cdp, job, gd)
        all_scores.append(result)
        sources = ", ".join(result["data_sources"])
        print(f"  {result['hi_grade']:12s} {result['composite']:5.1f}  {name:30s}  [{sources}]")

    all_scores.sort(key=lambda x: x.get("composite", 0), reverse=True)

    outfile = output_dir / "all_scores.json"
    with open(outfile, "w") as f:
        json.dump(all_scores, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"SCORING COMPLETE — {len(all_scores)} companies")
    print(f"{'=' * 60}")

    grades = {}
    for s in all_scores:
        g = s.get("hi_grade", "?")
        grades[g] = grades.get(g, 0) + 1
    for g in ["HI Certified", "A", "B", "C", "F"]:
        if g in grades: print(f"  {g}: {grades[g]}")

    source_counts = {}
    for s in all_scores:
        for src in s.get("data_sources", []):
            source_counts[src] = source_counts.get(src, 0) + 1
    print(f"\n  Data source coverage:")
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        print(f"    {src}: {count} companies")

    flagged = [s for s in all_scores if s.get("humanwashing_flags")]
    if flagged:
        print(f"\n  Humanwashing flags: {len(flagged)} companies")
        for s in flagged[:10]:
            print(f"    {s['company']}: {'; '.join(s['humanwashing_flags'][:2])}")

    print(f"\n  Output: {outfile}")


if __name__ == "__main__":
    main()
