#!/usr/bin/env python3
"""
HI. — HUMAN Scoring Engine v2.1
Merges signals from 24 sub-signals across 40 data sources into HUMAN dimension scores.

Follows HUMAN_Grade_Methodology_Spec v1.1
3 gates: Score, Balance, Integrity
Floor rule: any dimension < 10 caps composite at 40.
Balance floor: any dimension < 42 flags balance. 2+ dims below 42 caps at 41. 1 dim below 42 caps at 49.
Defaults: All sub-signals default to 50 (neutral) when no data is available.
Rounding: down unless decimal is .6 or higher (whole numbers only).

Key fixes in v2.1:
  - 3-gate system (Score, Balance, Integrity) replaces 10-gate system
  - All defaults set to 50 (neutral) — no generous defaults
  - HW.1 humanwashing now industry-normalized (4x industry median, not flat $2M)
  - CDP non-disclosure penalty only for companies with >$1B revenue or >10K employees
  - Glassdoor confidence weighted by review count
  - AHI weights aligned with spec v1.1
"""

import json, os, sys
from pathlib import Path

# Canonical names for companies known by multiple names
CANONICAL_NAMES = {
    # Tech
    "google": "Alphabet Inc.",
    "alphabet": "Alphabet Inc.",
    "amazon": "Amazon.com, Inc.",
    "amazon.com": "Amazon.com, Inc.",
    "meta": "Meta Platforms, Inc.",
    "meta platforms": "Meta Platforms, Inc.",
    "facebook": "Meta Platforms, Inc.",
    "microsoft": "Microsoft Corporation",
    "apple": "Apple Inc.",
    # Consumer
    "coca-cola": "Coca-Cola Company",
    "coca cola": "Coca-Cola Company",
    "the coca-cola": "Coca-Cola Company",
    "coca-cola company (the)": "Coca-Cola Company",
    "pepsi": "PepsiCo, Inc.",
    "pepsico": "PepsiCo, Inc.",
    "walmart": "Walmart Inc.",
    "starbucks": "Starbucks Corporation",
    "mcdonald's": "McDonald's Corporation",
    "mcdonalds": "McDonald's Corporation",
    "nike": "Nike, Inc.",
    "disney": "Walt Disney Company",
    "the walt disney": "Walt Disney Company",
    "walt disney": "Walt Disney Company",
    "walt disney company (the)": "Walt Disney Company",
    "walt disney co": "Walt Disney Company",
    # Finance
    "jpmorgan": "JPMorgan Chase & Co.",
    "jp morgan": "JPMorgan Chase & Co.",
    "jp morgan chase": "JPMorgan Chase & Co.",
    "jpmorgan chase": "JPMorgan Chase & Co.",
    "goldman sachs": "Goldman Sachs Group, Inc.",
    "the goldman sachs group": "Goldman Sachs Group, Inc.",
    "bank of america": "Bank of America Corporation",
    "wells fargo": "Wells Fargo & Company",
    "morgan stanley": "Morgan Stanley",
    # Healthcare
    "johnson & johnson": "Johnson & Johnson",
    "johnson and johnson": "Johnson & Johnson",
    "j&j": "Johnson & Johnson",
    "pfizer": "Pfizer, Inc.",
    "unitedhealth": "UnitedHealth Group Incorporated",
    "unitedhealth group": "UnitedHealth Group Incorporated",
    # Defense
    "lockheed martin": "Lockheed Martin Corporation",
    "boeing": "Boeing Company",
    "the boeing": "Boeing Company",
    "boeing company (the)": "Boeing Company",
    # Retail
    "target": "Target Corporation",
    "home depot": "Home Depot, Inc.",
    "the home depot": "Home Depot, Inc.",
    "home depot, inc. (the)": "Home Depot, Inc.",
    "costco": "Costco Wholesale Corporation",
    "costco wholesale": "Costco Wholesale Corporation",
    # Auto
    "general motors": "General Motors Company",
    "ford": "Ford Motor Company",
    "ford motor": "Ford Motor Company",
    # Energy
    "nextera energy": "NextEra Energy, Inc.",
    "chevron": "Chevron Corporation",
    "exxon": "Exxon Mobil Corporation",
    "exxon mobil": "Exxon Mobil Corporation",
    "exxonmobil": "Exxon Mobil Corporation",
    # Other
    "dr. bronner's": "Dr. Bronner's",
    "dr bronner": "Dr. Bronner's",
    "at&t": "AT&T Inc.",
    "procter & gamble": "Procter & Gamble Company",
    "procter and gamble": "Procter & Gamble Company",
    "the procter & gamble": "Procter & Gamble Company",
}

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
    displacement = sec_h.get("displacement_signal")
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
    
    # H.3 Human Decision Depth — deterministic heuristic
    # More humans per $B revenue = more human decisions. Deeper org = more human judgment.
    h3 = 50
    h3_sources = []
    if rpe:
        # Lower revenue-per-employee = more humans in the loop = more human decisions
        rpe_ratio = industry_median / max(rpe, 1)
        h3 = clamp(40 + rpe_ratio * 30)  # Range: ~40-70 from RPE alone
        h3_sources.append("SEC")
    
    # Adjust by headcount — larger workforces have deeper decision chains
    headcount = sec_h.get("headcount")
    if isinstance(headcount, dict):
        headcount = headcount.get("value", 0)
    headcount = headcount or 0
    if headcount:
        if headcount > 200000: h3 = min(100, h3 + 15)
        elif headcount > 50000: h3 = min(100, h3 + 10)
        elif headcount > 10000: h3 = min(100, h3 + 5)
        if "SEC" not in h3_sources: h3_sources.append("SEC")
    
    # Industry baseline — healthcare/defense require more human judgment
    h3_industry = {"healthcare": 10, "defense": 8, "food": 5, "manufacturing": 5,
                   "finance": 3, "media": 3, "auto": 0, "retail": -5,
                   "tech": -8, "telecom": -5, "energy": 0, "default": 0}
    h3 = clamp(h3 + h3_industry.get(industry, 0))
    
    # Penalty if AI displacement is high — fewer human decisions
    if displacement is not None and displacement > 20:
        h3 = clamp(h3 - displacement * 0.3)
    
    scores["H.3"] = round(h3, 1)
    sources_used.extend([s for s in h3_sources if s not in sources_used])
    
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

    D_H = 0.20*scores["H.1"] + 0.20*scores["H.2"] + 0.20*scores["H.3"] + 0.20*scores["H.4"] + 0.20*scores["H.5"]
    return round_score(D_H), scores, list(set(sources_used))


def score_u_dimension(sec_u, glassdoor_data, industry, subsignals=None):
    scores = {}
    sources_used = []
    gd = glassdoor_data.get("u_signals", {}) if glassdoor_data else {}
    # Normalize Glassdoor field names (1-5 scale → 0-100)
    if gd.get("overall_rating") is not None and gd.get("overall_score") is None:
        gd["overall_score"] = round(gd["overall_rating"] * 20, 1)
        gd["culture_score"] = round(gd.get("culture_rating", 3.0) * 20, 1)
        gd["worklife_score"] = round(gd.get("work_life_rating", gd.get("overall_rating", 3.0)) * 20, 1)
        gd["recommend_pct"] = gd.get("recommend_pct", round(gd["overall_rating"] * 15, 1))
        gd["review_count"] = gd.get("review_count", 500)
    ss = subsignals or {}

    # U.1 Customer Empathy — CFPB data if available, else Glassdoor
    cfpb_u1 = ss.get("cfpb", {}).get("U.1")
    if cfpb_u1 is not None:
        scores["U.1"] = cfpb_u1
        sources_used.append("CFPB")
    elif gd.get("overall_score") is not None:
        scores["U.1"] = round(gd.get("overall_score", 50) * 0.5 + gd.get("culture_score", 50) * 0.5, 1)
        sources_used.append("Glassdoor")
    else:
        scores["U.1"] = 50

    # U.2 Worker Empathy — Glassdoor (weighted by review count for confidence)
    if gd.get("worklife_score") is not None:
        raw_u2 = round(gd.get("worklife_score", 50) * 0.5 + gd.get("recommend_pct", 50) * 0.5, 1)
        # Low review count = less confidence, blend toward neutral
        review_count = gd.get("review_count", 500)
        if review_count < 50:
            confidence = 0.3  # Very low confidence
        elif review_count < 100:
            confidence = 0.5
        elif review_count < 500:
            confidence = 0.8
        else:
            confidence = 1.0
        scores["U.2"] = round(raw_u2 * confidence + 50 * (1 - confidence), 1)
        if "Glassdoor" not in sources_used: sources_used.append("Glassdoor")
    else:
        scores["U.2"] = 50

    # U.3 Relational Integrity — Glassdoor culture
    if gd.get("culture_score") is not None:
        scores["U.3"] = gd["culture_score"]
        if "Glassdoor" not in sources_used: sources_used.append("Glassdoor")
    else:
        scores["U.3"] = 50

    # U.4 Simulated Empathy Detection — deterministic heuristic
    # Proxy: Glassdoor ratings + industry automation baseline + worker empathy signals
    u4 = 50
    
    # Industry baseline — some industries are inherently more automated in customer facing
    u4_industry = {"finance": 35, "tech": 38, "telecom": 32, "insurance": 30,
                   "healthcare": 65, "food": 70, "retail": 55, "hospitality": 72,
                   "manufacturing": 50, "media": 45, "apparel": 65, "auto": 50,
                   "energy": 50, "defense": 55, "default": 50}
    u4 = u4_industry.get(industry, 50)
    
    # Glassdoor culture + overall as empathy proxy — high scores = genuine human care
    if gd.get("culture_score") is not None and gd.get("overall_score") is not None:
        culture = gd["culture_score"]
        overall = gd["overall_score"]
        # Blend industry baseline with actual employee sentiment
        u4 = round(u4 * 0.4 + culture * 0.3 + overall * 0.3, 1)
    elif gd.get("overall_score") is not None:
        u4 = round(u4 * 0.5 + gd["overall_score"] * 0.5, 1)
    
    scores["U.4"] = round(clamp(u4), 1)

    # U.5 Moral Courage — placeholder
    scores["U.5"] = 50

    D_U = 0.20*scores["U.1"] + 0.20*scores["U.2"] + 0.20*scores["U.3"] + 0.20*scores["U.4"] + 0.20*scores["U.5"]
    return round_score(D_U), scores, sources_used


def score_m_dimension(sec_m, epa_data, glassdoor_data, industry, subsignals=None):
    scores = {}
    sources_used = []
    ss = subsignals or {}

    # M.1 Pricing Ethics — CFPB if available
    cfpb_m1 = ss.get("cfpb", {}).get("M.1")
    if cfpb_m1 is not None:
        scores["M.1"] = cfpb_m1
        sources_used.append("CFPB")
    else:
        scores["M.1"] = 50  # No data = neutral, not generous

    # M.2 Data Ethics — HIBP breach data
    hibp_m2 = ss.get("hibp", {}).get("M.2")
    if hibp_m2 is not None:
        scores["M.2"] = hibp_m2
        sources_used.append("HIBP")
    else:
        scores["M.2"] = 50  # No breach data ≠ good data ethics

    # M.3 Market Ethics — SEC + EPA
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

    # M.4 Product Ethics — CPSC recalls if available, else Glassdoor as proxy
    cpsc_m4 = ss.get("cpsc", {}).get("M.4")
    if cpsc_m4 is not None:
        scores["M.4"] = cpsc_m4
        sources_used.append("CPSC")
    else:
        gd_u = glassdoor_data.get("u_signals", {}) if glassdoor_data else {}
        overall = gd_u.get("overall_rating")
        if overall is not None:
            # Use overall rating as management/product proxy (1-5 → 0-100)
            scores["M.4"] = round(overall * 20, 1)
            sources_used.append("Glassdoor")
        else:
            scores["M.4"] = 50  # No data = neutral

    # M.5 Political Ethics — FEC data if available, else Glassdoor CEO approval
    fec_m5 = ss.get("fec", {}).get("M.5")
    if fec_m5 is not None:
        scores["M.5"] = fec_m5
        sources_used.append("FEC")
    else:
        gd_u = glassdoor_data.get("u_signals", {}) if glassdoor_data else {}
        ceo = gd_u.get("ceo_approval")
        if ceo is not None:
            scores["M.5"] = round(ceo, 1)  # Already 0-100
            if "Glassdoor" not in sources_used: sources_used.append("Glassdoor")
        else:
            scores["M.5"] = 50  # No data = neutral

    D_M = 0.20*scores["M.1"] + 0.20*scores["M.2"] + 0.20*scores["M.3"] + 0.20*scores["M.4"] + 0.20*scores["M.5"]
    return round_score(D_M), scores, list(set(sources_used))


def score_a_dimension(sec_a, epa_data, cdp_data, industry, subsignals=None):
    scores = {}
    sources_used = []
    ss = subsignals or {}
    cdp_a = cdp_data.get("a_signals", {}) if cdp_data else {}

    # A.1 Energy — CDP climate
    if cdp_a.get("cdp_climate_score") is not None:
        scores["A.1"] = cdp_a["cdp_climate_score"]
        sources_used.append("CDP")
    else:
        defaults = {"energy": 30, "manufacturing": 45, "tech": 50, "finance": 65,
                    "healthcare": 55, "retail": 50, "food": 55, "media": 60,
                    "telecom": 45, "defense": 40, "auto": 40, "default": 50}
        scores["A.1"] = defaults.get(industry, 50)

    # A.2 Water — CDP water
    if cdp_a.get("cdp_water_score") is not None:
        scores["A.2"] = cdp_a["cdp_water_score"]
        if "CDP" not in sources_used: sources_used.append("CDP")
    else:
        scores["A.2"] = 50

    # A.3 Land & Habitat — Enhanced with industry deforestation risk
    land_score = ss.get("land", {}).get("A.3")
    if land_score is not None:
        scores["A.3"] = land_score
        sources_used.append("Industry+EPA")
    else:
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

    # A.4 Hardware Lifecycle — iFixit + industry data
    hw_score = ss.get("hardware", {}).get("A.4")
    if hw_score is not None:
        scores["A.4"] = hw_score
        hw_src = ss.get("hardware", {}).get("source", "iFixit")
        if hw_src not in sources_used: sources_used.append(hw_src)
    else:
        if cdp_a.get("cdp_forests_score") is not None:
            scores["A.4"] = cdp_a["cdp_forests_score"]
        else:
            hw_defaults = {"tech": 40, "telecom": 45, "manufacturing": 50, "default": 55}
            scores["A.4"] = hw_defaults.get(industry, 55)

    # A.5 Resource Stewardship — CDP forests + industry baseline
    if cdp_a.get("cdp_forests_score") is not None and scores["A.4"] != cdp_a.get("cdp_forests_score"):
        scores["A.5"] = cdp_a["cdp_forests_score"]
        if "CDP" not in sources_used: sources_used.append("CDP")
    else:
        rs_defaults = {"food": 40, "manufacturing": 45, "retail": 50, "energy": 35,
                       "tech": 60, "finance": 65, "healthcare": 55, "default": 50}
        scores["A.5"] = rs_defaults.get(industry, 50)

    D_A = 0.20*scores["A.1"] + 0.20*scores["A.2"] + 0.20*scores["A.3"] + 0.20*scores["A.4"] + 0.20*scores["A.5"]
    return round_score(D_A), scores, list(set(sources_used))


def score_n_dimension(sec_n, cdp_data, epa_data, industry):
    scores = {}
    sources_used = []
    scores["N.1"] = 40

    cdp_n = cdp_data.get("n_signals", {}) if cdp_data else {}
    if cdp_n.get("cdp_non_responder") is True:
        # Only penalize large companies — small companies may not have resources for CDP
        scores["N.2"] = 30  # Mild penalty, not 5
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
    scores["N.4"] = 50  # No data = neutral (humanwashing detection requires evidence)

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

    D_N = 0.20*scores["N.1"] + 0.20*scores["N.2"] + 0.20*scores["N.3"] + 0.20*scores["N.4"] + 0.20*scores["N.5"]
    return round_score(D_N), scores, sources_used


def round_score(val):
    """Round down unless decimal is .6 or higher."""
    import math
    remainder = round(val - math.floor(val), 4)  # Avoid float precision issues
    return int(math.ceil(val)) if remainder >= 0.6 else int(math.floor(val))


def compute_composite(D_H, D_U, D_M, D_A, D_N):
    composite = (D_H + D_U + D_M + D_A + D_N) / 5
    floor_triggered = False
    balance_floor_triggered = False
    triggering_dimension = None
    dims = {"H": D_H, "U": D_U, "M": D_M, "A": D_A, "N": D_N}
    min_dim = min(dims.values())
    below_42 = sum(1 for v in dims.values() if v < 42)
    
    # Hard floor: any dimension < 10 caps composite at 40
    if min_dim < 10:
        composite = min(composite, 40)
        floor_triggered = True
        triggering_dimension = min(dims, key=dims.get)
    
    # Balance floor: 2+ dimensions below 42 = F (cap at 41)
    elif below_42 >= 2:
        balance_floor_triggered = True
        triggering_dimension = min(dims, key=dims.get)
        if composite > 41:
            composite = 41.0
    
    # Balance floor: 1 dimension below 42 = D cap (cap at 49)
    elif below_42 == 1:
        balance_floor_triggered = True
        triggering_dimension = min(dims, key=dims.get)
        if composite > 49:
            composite = 49.0
    
    return round_score(composite), floor_triggered, balance_floor_triggered, triggering_dimension

def get_hi_grade(composite, verified=False):
    """Score-only system. All companies return 'scored'. Gold HI Grade is checked separately."""
    return "scored", ""


def compute_gold_threshold(all_scores):
    """Adaptive threshold: mean + 2 SD of all composites."""
    composites = [s.get("composite", 0) for s in all_scores if s.get("composite", 0) > 0]
    if len(composites) < 10:
        return 62
    import math
    mean = sum(composites) / len(composites)
    variance = sum((x - mean) ** 2 for x in composites) / len(composites)
    stdev = math.sqrt(variance)
    return round(mean + 2 * stdev, 1)


def check_hi_certified(record, threshold):
    """Check all 3 gates for Gold HI Grade status.
    Gate 1: Score — composite >= threshold
    Gate 2: Balance — all 5 dimensions >= 42
    Gate 3: Integrity — no humanwashing flags AND AHI < 30
    """
    dims = [record.get("D_H", 0), record.get("D_U", 0), record.get("D_M", 0), record.get("D_A", 0), record.get("D_N", 0)]
    algo_harm_score = record.get("algo_harm", {}).get("algo_harm_score", 0)
    # Filter out AH: flags from humanwashing count — those are informational, not gate-blocking
    hw_flags = [f for f in record.get("humanwashing_flags", []) if not f.startswith("AH:")]
    gates = {
        "score": record.get("composite", 0) >= threshold,
        "balance": all(d >= 42 for d in dims),
        "integrity": len(hw_flags) == 0 and algo_harm_score < 30,
    }
    return all(gates.values()), gates


# ═══════════════════════════════════════════════════════════════════════
# ALGORITHMIC HARM INDEX — Cross-cutting penalty
# Measures whether a company's algorithms empower or exploit humans.
# Hits M, U, H, N — like humanwashing detection, but for algorithms.
# ═══════════════════════════════════════════════════════════════════════

# Curated from FTC actions, congressional testimony, academic research,
# platform transparency reports, and documented harm events.
# 5 factors (0-100, higher = more harmful):
#   division:       amplifies outrage, tribalism, polarization
#   addiction:       dopamine loops, infinite scroll, dark patterns
#   manipulation:    exploits vulnerable users (kids, mental health, financial stress)
#   transparency:    discloses how algorithms work (inverted: lower = less transparent)
#   human_override:  users can opt out or control the algorithm (inverted)

ALGO_HARM_DATA = {
    # Social media — highest harm
    "META":  {"division": 85, "addiction": 90, "manipulation": 80, "transparency": 25, "human_override": 30,
              "flags": ["Instagram teen mental health crisis", "Engagement algorithm amplifies outrage", "Algorithmic feed replaced chronological", "Whistleblower confirmed harm awareness"]},
    "SNAP":  {"division": 40, "addiction": 75, "manipulation": 70, "transparency": 30, "human_override": 35,
              "flags": ["Streaks create artificial social pressure", "Discover feed optimizes engagement over wellbeing"]},
    # Video platforms
    "GOOG":  {"division": 70, "addiction": 75, "manipulation": 55, "transparency": 40, "human_override": 45,
              "flags": ["YouTube autoplay radicalization pipeline", "Kids content algorithm failures", "Search ranking manipulation for ad revenue"]},
    "GOOGL": {"division": 70, "addiction": 75, "manipulation": 55, "transparency": 40, "human_override": 45,
              "flags": ["YouTube autoplay radicalization pipeline", "Kids content algorithm failures"]},
    "NFLX":  {"division": 15, "addiction": 60, "manipulation": 30, "transparency": 35, "human_override": 50,
              "flags": ["Autoplay next episode", "Algorithmic thumbnails personalized to maximize clicks"]},
    # E-commerce / marketplace
    "AMZN":  {"division": 15, "addiction": 45, "manipulation": 55, "transparency": 20, "human_override": 30,
              "flags": ["Dynamic pricing algorithms", "Dark patterns in Prime cancellation", "Buy Box manipulation"]},
    "BKNG":  {"division": 10, "addiction": 40, "manipulation": 60, "transparency": 25, "human_override": 30,
              "flags": ["Fake urgency dark patterns", "Hidden fees revealed late", "Pressure-based conversion"]},
    # Ride-hailing / gig economy
    "UBER":  {"division": 10, "addiction": 30, "manipulation": 55, "transparency": 25, "human_override": 20,
              "flags": ["Surge pricing exploits demand spikes", "Driver gamification manipulation", "Algorithmic wage suppression"]},
    "LYFT":  {"division": 10, "addiction": 25, "manipulation": 45, "transparency": 30, "human_override": 25,
              "flags": ["Surge pricing", "Driver earnings opacity"]},
    # Social / messaging
    "PINS":  {"division": 20, "addiction": 55, "manipulation": 35, "transparency": 40, "human_override": 50,
              "flags": ["Infinite scroll feed", "Body image content concerns"]},
    "RDDT":  {"division": 55, "addiction": 50, "manipulation": 30, "transparency": 50, "human_override": 60,
              "flags": ["Recommendation algo can push extreme communities", "Strong community moderation helps"]},
    # Tech platforms
    "AAPL":  {"division": 5, "addiction": 20, "manipulation": 15, "transparency": 45, "human_override": 70,
              "flags": ["Screen Time tools show commitment", "App Store ranking opacity"]},
    "MSFT":  {"division": 10, "addiction": 25, "manipulation": 20, "transparency": 50, "human_override": 60,
              "flags": ["LinkedIn feed engagement-driven", "Copilot dependency concerns"]},
    # Fintech / payments
    "PYPL":  {"division": 5, "addiction": 20, "manipulation": 35, "transparency": 30, "human_override": 40,
              "flags": ["BNPL algorithms target financially vulnerable"]},
    "SQ":    {"division": 5, "addiction": 30, "manipulation": 35, "transparency": 30, "human_override": 40,
              "flags": ["Cash App gambling-like features", "Algorithmic lending"]},
    "AFRM":  {"division": 5, "addiction": 25, "manipulation": 50, "transparency": 30, "human_override": 35,
              "flags": ["BNPL targets impulse purchases", "Algorithmic credit scoring"]},
    # Gaming
    "EA":    {"division": 15, "addiction": 70, "manipulation": 65, "transparency": 20, "human_override": 25,
              "flags": ["Loot box algorithms designed for addiction", "Pay-to-win mechanics", "Targets minors"]},
    "TTWO":  {"division": 15, "addiction": 60, "manipulation": 55, "transparency": 25, "human_override": 30,
              "flags": ["GTA Online shark cards", "NBA 2K microtransaction pressure"]},
    "ATVI":  {"division": 10, "addiction": 55, "manipulation": 45, "transparency": 30, "human_override": 35,
              "flags": ["Matchmaking patents designed to push purchases", "Engagement optimization"]},
    # Telecom
    "T":     {"division": 5, "addiction": 10, "manipulation": 30, "transparency": 25, "human_override": 35,
              "flags": ["Algorithmic throttling", "Opaque data pricing"]},
    "CMCSA": {"division": 10, "addiction": 15, "manipulation": 35, "transparency": 20, "human_override": 25,
              "flags": ["Data cap algorithms", "Bundle pricing dark patterns"]},
    # Retail — low harm
    "WMT":   {"division": 5, "addiction": 15, "manipulation": 20, "transparency": 40, "human_override": 60, "flags": []},
    "COST":  {"division": 0, "addiction": 5, "manipulation": 5, "transparency": 60, "human_override": 80, "flags": []},
    "TGT":   {"division": 5, "addiction": 15, "manipulation": 15, "transparency": 45, "human_override": 60, "flags": []},
}

def compute_algo_harm(ticker):
    """
    Compute Algorithmic Harm Index — cross-cutting penalty.
    Returns harm score + per-dimension penalties + flags.
    """
    data = ALGO_HARM_DATA.get(ticker.upper())
    if not data:
        return {"algo_harm_score": 0, "penalties": {"H": 0, "U": 0, "M": 0, "N": 0}, "flags": [], "has_harm": False}
    
    # Composite harm score: weighted average of 5 factors (matches spec v1.1)
    harm = (
        data["division"] * 0.25 +
        data["addiction"] * 0.25 +
        data["manipulation"] * 0.20 +
        (100 - data["transparency"]) * 0.15 +
        (100 - data["human_override"]) * 0.15
    )
    
    # Only apply penalties if harm > 30
    if harm <= 30:
        return {"algo_harm_score": round(harm, 1), "penalties": {"H": 0, "U": 0, "M": 0, "N": 0}, "flags": data.get("flags", []), "has_harm": False}
    
    # Penalties scale: max -15 per dimension at harm=100
    pf = (harm - 30) / 70  # 0 to 1
    penalties = {
        "H": round(-pf * 10, 1),   # H.1 — algo replaces human editorial judgment
        "U": round(-pf * 15, 1),   # U.1 + U.4 — exploiting users isn't empathy
        "M": round(-pf * 15, 1),   # M.4 — dark patterns, addiction, manipulation
        "N": round(-pf * 10, 1),   # N.4 — claiming to "connect" while dividing
    }
    
    return {"algo_harm_score": round(harm, 1), "penalties": penalties, "flags": data.get("flags", []), "has_harm": True}


def score_company(company_name, ticker="", sec_data=None, epa_data=None,
                  bls_data=None, cdp_data=None, job_data=None, glassdoor_data=None,
                  subsignal_data=None):
    sic = sec_data.get("n_signals", {}).get("sic", "") if sec_data else ""
    industry = get_industry(sic)
    
    # Load subsignal data if available
    ss = subsignal_data or {}
    if not ss and ticker:
        try:
            ss_file = Path("data/subsignals/all_subsignals.json")
            if ss_file.exists():
                all_ss = json.load(open(ss_file))
                ss = all_ss.get(ticker.upper(), {})
        except:
            pass

    sec_h = sec_data.get("h_signals", {}) if sec_data else {}
    sec_m = sec_data.get("m_signals", {}) if sec_data else {}
    sec_n = sec_data.get("n_signals", {}) if sec_data else {}
    sec_u = sec_data.get("u_signals", {}) if sec_data else {}

    D_H, h_detail, h_src = score_h_dimension(sec_h, job_data, bls_data, industry)
    D_U, u_detail, u_src = score_u_dimension(sec_u, glassdoor_data, industry, ss)
    D_M, m_detail, m_src = score_m_dimension(sec_m, epa_data, glassdoor_data, industry, ss)
    D_A, a_detail, a_src = score_a_dimension(sec_data.get("a_signals", {}) if sec_data else {}, epa_data, cdp_data, industry, ss)
    D_N, n_detail, n_src = score_n_dimension(sec_n, cdp_data, epa_data, industry)

    # ═══ EXTENDED SIGNALS (sources 23-34) ═══
    # Load extended pipeline data and apply adjustments
    ext = {}
    if ticker:
        try:
            ext_file = Path("data/subsignals/extended/all_extended.json")
            if ext_file.exists():
                all_ext = json.load(open(ext_file))
                ext = all_ext.get(ticker.upper(), {})
        except:
            pass
    
    if ext:
        # ═══ UPGRADE HARDCODED SUB-SIGNALS WITH REAL DATA ═══
        
        # H.4 CEO Accountability — use pay ratio + insider trading
        pay = ext.get("pay_ratio", {})
        pay_ratio = pay.get("ratio")
        if pay_ratio is not None:
            if pay_ratio > 500: h_detail["H.4"] = 20
            elif pay_ratio > 300: h_detail["H.4"] = 35
            elif pay_ratio > 200: h_detail["H.4"] = 45
            elif pay_ratio > 100: h_detail["H.4"] = 55
            elif pay_ratio > 50: h_detail["H.4"] = 70
            else: h_detail["H.4"] = 85
            if "SEC DEF 14A" not in h_src: h_src.append("SEC DEF 14A")
        insider_adj = ext.get("insider", {}).get("M.3_adj", 0)
        if insider_adj != 0:
            h_detail["H.4"] = clamp(h_detail["H.4"] + insider_adj)
            if "SEC Form 4" not in h_src: h_src.append("SEC Form 4")
        
        # U.5 Moral Courage — use charity (IRS 990) + BBB
        charity_adj = ext.get("charity", {}).get("U.5_adj", 0)
        bbb_score = ext.get("bbb", {}).get("score")
        if charity_adj != 0 or bbb_score is not None:
            u5 = 50
            if charity_adj > 0: u5 = clamp(u5 + charity_adj * 3)
            if bbb_score is not None: u5 = round(u5 * 0.6 + bbb_score * 0.4)
            u_detail["U.5"] = round(clamp(u5), 1)
            if charity_adj != 0 and "IRS 990" not in u_src: u_src.append("IRS 990")
            if bbb_score is not None and "BBB" not in u_src: u_src.append("BBB")
        
        # N.1 AI Disclosure — use GRI alignment + SBTi as transparency proxies
        gri_adj = ext.get("gri", {}).get("N.2_adj", 0)
        sbti_adj = ext.get("sbti", {}).get("A.1_adj", 0)
        if gri_adj != 0 or sbti_adj != 0:
            n1 = 40
            if gri_adj > 0: n1 = clamp(n1 + 20)  # GRI aligned = more transparent
            if sbti_adj > 0: n1 = clamp(n1 + 15)  # SBTi target = more transparent
            n_detail["N.1"] = round(clamp(n1), 1)
            if "GRI" not in n_src: n_src.append("GRI")
        
        # N.3 Labor Auditability — use OSHA inspections + DOL data
        osha_score = ext.get("osha", {}).get("score")
        dol_score = ext.get("dol", {}).get("score")
        if osha_score is not None or dol_score is not None:
            n3 = 45
            if osha_score is not None:
                # More OSHA inspections = more auditable (govt is watching)
                n3 = round(osha_score * 0.4 + n3 * 0.6)
            if dol_score is not None:
                n3 = round(dol_score * 0.3 + n3 * 0.7)
            n_detail["N.3"] = round(clamp(n3), 1)
            if "OSHA" not in n_src: n_src.append("OSHA")
            if dol_score is not None and "DOL" not in n_src: n_src.append("DOL")
        
        # N.4 Humanwashing Detection — compute from inputs we already have
        rpe = sec_h.get("revenue_per_employee")
        displacement = sec_h.get("displacement_signal")
        ai_ratio = job_data.get("h_signals", {}).get("ai_ratio") if job_data else None
        n4 = 50  # Start neutral
        if rpe and rpe > INDUSTRY_RPE_MEDIANS.get(industry, 350000) * 3:
            n4 -= 20  # High automation signal
        if displacement is not None and displacement > 20:
            n4 -= 15  # Active displacement
        if ai_ratio is not None and ai_ratio > 0.35:
            n4 -= 10  # AI-dominated hiring
        ftc_n4 = ext.get("ftc", {}).get("N.4")
        if ftc_n4 is not None:
            n4 = round(n4 * 0.6 + ftc_n4 * 0.4)
        n_detail["N.4"] = round(clamp(n4), 1)
        
        # ═══ RECALCULATE DIMENSIONS from updated sub-signals ═══
        D_H = round_score(0.20*h_detail["H.1"] + 0.20*h_detail["H.2"] + 0.20*h_detail["H.3"] + 0.20*h_detail["H.4"] + 0.20*h_detail["H.5"])
        D_U = round_score(0.20*u_detail["U.1"] + 0.20*u_detail["U.2"] + 0.20*u_detail["U.3"] + 0.20*u_detail["U.4"] + 0.20*u_detail["U.5"])
        D_N = round_score(0.20*n_detail["N.1"] + 0.20*n_detail["N.2"] + 0.20*n_detail["N.3"] + 0.20*n_detail["N.4"] + 0.20*n_detail["N.5"])
        
        # ═══ THEN APPLY EXTENDED ADJUSTMENTS on top ═══
        
        # OSHA → U.2 blend
        osha_score = ext.get("osha", {}).get("score")
        if osha_score is not None:
            D_U = round_score(D_U * 0.85 + osha_score * 0.15)
            if "OSHA" not in n_src: n_src.append("OSHA")
        
        # DOL wages → U.2 blend
        dol_score = ext.get("dol", {}).get("score")
        if dol_score is not None:
            D_U = round_score(D_U * 0.9 + dol_score * 0.1)
            if "DOL" not in n_src: n_src.append("DOL")
        
        # BBB → U.1 blend (into U dimension)
        bbb_score = ext.get("bbb", {}).get("score")
        if bbb_score is not None:
            D_U = round_score(D_U * 0.9 + bbb_score * 0.1)
            if "BBB" not in n_src: n_src.append("BBB")
        
        # FTC → M.2 + N.4
        ftc = ext.get("ftc", {})
        if ftc.get("M.2") is not None:
            D_M = round_score(D_M * 0.9 + ftc["M.2"] * 0.1)
            if "FTC" not in n_src: n_src.append("FTC")
        if ftc.get("N.4") is not None:
            D_N = round_score(D_N * 0.9 + ftc["N.4"] * 0.1)
        
        # EEOC → U.2 + M.3 adjustments
        eeoc = ext.get("eeoc", {})
        D_U = clamp(D_U + eeoc.get("U.2_adj", 0))
        D_M = clamp(D_M + eeoc.get("M.3_adj", 0))
        if eeoc.get("U.2_adj", 0) != 0 and "EEOC" not in n_src: n_src.append("EEOC")
        
        # USPTO patents → H.3 + H.5 adjustments
        patents = ext.get("patents", {})
        D_H = clamp(D_H + patents.get("H.3_adj", 0) + patents.get("H.5_adj", 0))
        if patents.get("H.3_adj", 0) != 0 and "USPTO" not in n_src: n_src.append("USPTO")
        
        # FDA → M.4 blend
        fda_score = ext.get("fda", {}).get("score")
        if fda_score is not None:
            D_M = round_score(D_M * 0.9 + fda_score * 0.1)
            if "FDA" not in n_src: n_src.append("FDA")
        
        # Pay ratio → M.3 + H.4
        pay = ext.get("pay_ratio", {})
        D_M = clamp(D_M + pay.get("M.3_adj", 0))
        D_H = clamp(D_H + pay.get("H.4_adj", 0))
        if pay.get("ratio") and "SEC DEF 14A" not in n_src: n_src.append("SEC DEF 14A")
        
        # Insider trading → M.3
        D_M = clamp(D_M + ext.get("insider", {}).get("M.3_adj", 0))
        if ext.get("insider", {}).get("M.3_adj", 0) != 0 and "SEC Form 4" not in n_src: n_src.append("SEC Form 4")
        
        # GRI → N.2
        D_N = clamp(D_N + ext.get("gri", {}).get("N.2_adj", 0))
        if ext.get("gri", {}).get("N.2_adj", 0) != 0 and "GRI" not in n_src: n_src.append("GRI")
        
        # SBTi → A.1
        D_A = clamp(D_A + ext.get("sbti", {}).get("A.1_adj", 0))
        if ext.get("sbti", {}).get("A.1_adj", 0) != 0 and "SBTi" not in n_src: n_src.append("SBTi")
        
        # Charity → U.5
        D_U = clamp(D_U + ext.get("charity", {}).get("U.5_adj", 0))
        if ext.get("charity", {}).get("U.5_adj", 0) != 0 and "IRS 990" not in n_src: n_src.append("IRS 990")
    
    # ═══ ALGORITHMIC HARM INDEX — Cross-cutting penalty ═══
    algo_harm = compute_algo_harm(ticker)
    if algo_harm["has_harm"]:
        p = algo_harm["penalties"]
        D_H = clamp(D_H + p["H"])
        D_U = clamp(D_U + p["U"])
        D_M = clamp(D_M + p["M"])
        D_N = clamp(D_N + p["N"])

    # Round dimensions after all adjustments
    D_H, D_U, D_M, D_A, D_N = round_score(D_H), round_score(D_U), round_score(D_M), round_score(D_A), round_score(D_N)

    composite, floor_triggered, balance_floor_triggered, triggering_dim = compute_composite(D_H, D_U, D_M, D_A, D_N)
    grade, satire = get_hi_grade(composite)
    all_sources = sorted(set(h_src + u_src + m_src + a_src + n_src)) or ["Defaults"]

    all_details = {**h_detail, **u_detail, **m_detail, **a_detail, **n_detail}
    real_count = sum(1 for v in all_details.values() if v != 50)

    hw_flags = []
    rpe = sec_h.get("revenue_per_employee")
    industry_rpe_median = INDUSTRY_RPE_MEDIANS.get(industry, INDUSTRY_RPE_MEDIANS["default"])
    if rpe and rpe > industry_rpe_median * 4:
        hw_flags.append(f"HW.1: Revenue/employee ${rpe:,.0f} is >4x industry median (${industry_rpe_median:,.0f})")
    displacement = sec_h.get("displacement_signal")
    if displacement and displacement > 30:
        hw_flags.append("HW.2: R&D growth significantly outpacing headcount")
    if job_data and job_data.get("h_signals", {}).get("ai_ratio", 0) >= 0.35:
        hw_flags.append("HW.3: AI roles dominate job postings (>35%)")
    if epa_data and epa_data.get("a_signals", {}).get("total_violations_3yr", 0) > 20:
        hw_flags.append("HW.4: Significant environmental violations")
    if cdp_data and cdp_data.get("n_signals", {}).get("cdp_non_responder"):
        # Only penalize companies large enough that CDP disclosure is expected
        headcount_val = sec_h.get("headcount")
        if isinstance(headcount_val, dict): headcount_val = headcount_val.get("value", 0)
        rpe_val = sec_h.get("revenue_per_employee") or 0
        est_revenue = (headcount_val or 0) * rpe_val
        if est_revenue > 1_000_000_000 or (headcount_val or 0) > 10000:
            hw_flags.append("HW.5: Refuses CDP climate disclosure (large company)")
    
    # Add algo harm flags
    algo_flags = []
    if algo_harm["has_harm"]:
        algo_flags = [f"AH: {f}" for f in algo_harm["flags"][:3]]  # Top 3 flags
        hw_flags.extend(algo_flags)

    # Confidence tier based on real data sources
    real_sources = [s for s in all_sources if s not in ["Defaults", "Manual Scoring", "Seed Estimate", "Public Reporting"]]
    if len(real_sources) >= 5:
        confidence = "Verified"
    elif len(real_sources) >= 2:
        confidence = "Estimated"
    else:
        confidence = "Baseline"

    return {
        "company": company_name, "ticker": ticker, "industry": industry, "sic": sic,
        "sic_description": sec_data.get("n_signals", {}).get("sic_description", "") if sec_data else "",
        "D_H": D_H, "D_U": D_U, "D_M": D_M, "D_A": D_A, "D_N": D_N,
        "composite": composite, "hi_grade": grade, "satire": satire,
        "floor_triggered": floor_triggered, "balance_floor": balance_floor_triggered, "triggering_dimension": triggering_dim,
        "confidence": confidence, "spec_version": "1.1.0",
        "data_sources": all_sources,
        "signal_coverage": f"{real_count}/{len(all_details)} sub-signals with real data",
        "humanwashing_flags": hw_flags,
        "algo_harm": algo_harm,
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

        # Apply canonical name for known duplicates
        name_check = name.lower().strip()
        # Try progressively shorter versions
        for check in [
            name_check,
            name_check.split(',')[0].strip(),
            name_check.replace(' inc.', '').replace(' inc', '').replace(' corp.', '').replace(' corp', '').replace(' llc', '').replace(' ltd', '').replace(' company', '').replace(' corporation', '').replace(' incorporated', '').strip(),
            name_check.replace('(the)', '').replace('the ', '').strip().rstrip('.,'),
        ]:
            check = check.strip().rstrip('.,')
            if check in CANONICAL_NAMES:
                name = CANONICAL_NAMES[check]
                break

        if sec and sec.get("error") and not any([epa, cdp, job, gd]):
            continue

        result = score_company(name, ticker, sec, epa, bls_data, cdp, job, gd)
        all_scores.append(result)
        sources = ", ".join(result["data_sources"])
        print(f"  {result['hi_grade']:12s} {result['composite']:5.1f}  {name:30s}  [{sources}]")

    all_scores.sort(key=lambda x: x.get("composite", 0), reverse=True)

    # Deduplicate by ticker AND normalized name — keep the record with the most data sources
    import re
    def norm_for_dedup(name):
        n = name.lower().strip()
        n = n.replace('&', ' and ')
        n = re.sub(r'[,.\-\'\"()\[\]]', ' ', n)
        n = re.sub(r'\s+', ' ', n).strip()
        if n.endswith(' s'): n = n[:-2].strip()
        if n.startswith('the '): n = n[4:]
        for _pass in range(2):
            for s in [' incorporated', ' corporation', ' international', ' technologies', ' technology',
                      ' enterprises', ' solutions', ' platforms', ' provisions', ' holdings', ' group',
                      ' company', ' inc', ' corp', ' llc', ' ltd', ' co', ' plc', ' sa', ' ag', ' nv', ' se']:
                if n.endswith(s): n = n[:-len(s)].strip()
        return n

    seen_tickers = {}
    seen_names = {}
    deduped = []
    dupes_removed = 0

    for s in all_scores:
        t = s.get("ticker", "")
        name = s.get("company", "")
        norm = norm_for_dedup(name)
        is_dupe = False

        # Check ticker dupe
        if t and t in seen_tickers:
            existing = seen_tickers[t]
            if len(s.get("data_sources", [])) > len(existing.get("data_sources", [])):
                deduped.remove(existing)
                seen_tickers[t] = s
                seen_names[norm] = s
                deduped.append(s)
            dupes_removed += 1
            is_dupe = True
        # Check name dupe
        elif norm and norm in seen_names:
            existing = seen_names[norm]
            if len(s.get("data_sources", [])) > len(existing.get("data_sources", [])):
                deduped.remove(existing)
                seen_names[norm] = s
                if t: seen_tickers[t] = s
                deduped.append(s)
            dupes_removed += 1
            is_dupe = True

        if not is_dupe:
            if t: seen_tickers[t] = s
            if norm: seen_names[norm] = s
            deduped.append(s)
    
    all_scores = deduped
    if dupes_removed:
        print(f"\n  Deduplication: removed {dupes_removed} duplicate records")

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
    for g in ["A", "B", "C", "D", "F"]:
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

    balance_capped = [s for s in all_scores if s.get("balance_floor")]
    if balance_capped:
        print(f"\n  ⚖ Balance floor (capped at C): {len(balance_capped)} companies")
        for s in balance_capped[:10]:
            print(f"    {s['company']}: {s['triggering_dimension']} below 42")

    print(f"\n  Output: {outfile}")


if __name__ == "__main__":
    main()
