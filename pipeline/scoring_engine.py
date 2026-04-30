#!/usr/bin/env python3
"""
HI. — HUMAN Scoring Engine v2.1
Merges signals from 24 sub-signals across 40 data sources into HUMAN dimension scores.

Follows HUMAN_Grade_Methodology_Spec v1.1
3 gates: Score, Balance, Integrity
Floor rule (v1.2.0): any HUMAN dimension < 30 caps composite at 50.
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

# v1.7.1-industry-classification: applied 20260423-085434
SIC_TO_INDUSTRY = {
    # Technology / electronics (SIC 35-38, 73)
    "35": "tech", "36": "tech", "38": "tech", "73": "tech",
    # Defense / aerospace (SIC 37 split — auto in 371x, defense/aerospace in 372x-379x)
    # Note: SIC 37 prefix matches both; weapons detection in HARM_DATA catches the real defense cos.
    "37": "manufacturing",
    # Telecom, energy, utilities
    "48": "telecom", "49": "energy",
    # Retail (SIC 52-59 except 58 which is food service)
    "52": "retail", "53": "retail", "54": "retail", "56": "retail", "57": "retail", "59": "retail",
    "50": "retail", "51": "retail",
    # Finance (SIC 60-64)
    "60": "finance", "61": "finance", "62": "finance", "63": "finance", "64": "finance", "67": "finance",
    # Food & beverage (SIC 20-21, food service 58)
    "20": "food", "21": "food", "58": "food",
    # Healthcare / pharma (SIC 28 chemicals/pharma, 80 health services)
    "28": "healthcare", "80": "healthcare", "87": "healthcare",
    # Energy (SIC 13 oil/gas extraction, 29 refining)
    "13": "energy", "29": "energy",
    # Media / entertainment (SIC 27 publishing, 78 motion pictures, 79 amusement)
    "27": "media", "78": "media",
    # v1.7.1: Corrections + new categories
    "45": "transportation",  # was "defense" — SIC 45xx is Transportation by Air
    "40": "transportation",  # rail transport
    "41": "transportation",  # passenger transit
    "42": "transportation",  # motor freight / trucking (ODFL)
    "44": "transportation",  # water transport / cruises (CCL, RCL, NCLH)
    "47": "transportation",  # transportation services
    "55": "auto",            # auto dealers (5500 series)
    "30": "apparel",         # rubber/plastic footwear (Nike)
    "31": "apparel",         # leather goods
    "23": "apparel",         # apparel manufacturing
    "79": "hospitality",     # amusement / casinos (Wynn, LVS)
    "70": "hospitality",     # hotels (Hilton, Marriott)
    "72": "services",        # personal services (Cintas industrial laundry)
    "76": "services",        # repair services
    "81": "services",        # legal services
    "82": "services",        # education
    "86": "services",        # membership organizations
    "89": "services",        # miscellaneous services
    # (end v1.7.1)
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


# ── HRC & DEI data (Pass 2D Tier 0 wiring per API_SHOPPING_LIST) ──────
# Authoritative external sources for U.3 Relational Integrity:
#   HRC Corporate Equality Index — LGBTQ+ workplace inclusion
#   Disability:IN Disability Equality Index — disability workplace inclusion

_HRC_INDEX = None  # {ticker: cei_score, ...}  # lazy-loaded
_DEI_INDEX = None  # {ticker: dei_score, ...}  # lazy-loaded
_HRC_NAME_INDEX = None
_DEI_NAME_INDEX = None

# ── B Corp data (Pass 3 Tier 0 wiring — certification-grounded) ──────
# B Lab Certified B Corporations: authoritative third-party social/environmental
# performance verification. B Impact score >=80 required for certification.
# Maps to: M.5 (Stakeholder Governance), U.3 (Relational Integrity), A.4 (Product Lifecycle)
_BCORP_INDEX = None  # {ticker: record, ...}
_BCORP_NAME_INDEX = None  # {name_lower: record, ...}

# ── Fair Trade data (Pass 3 Tier 0 wiring — supply chain integrity) ──
# Fair Trade USA + Fairtrade International: rigorous supply chain certification
# ensuring fair compensation, safe working conditions, and traceability.
# Maps to: M.3 (Market Ethics — supply chain), A.4 (Product Lifecycle)
_FAIRTRADE_INDEX = None
_FAIRTRADE_NAME_INDEX = None

# ── USDA Organic data (Pass 3 Tier 0 wiring — federal agricultural certification) ──
# USDA Organic: federal standard for organic food/fiber/livestock. No synthetic
# inputs, no GMOs, soil health requirements, documented traceability.
# Maps to: A.3 (Land & Habitat), A.4 (Product Lifecycle), M.3 (Market Ethics)
_USDA_ORGANIC_INDEX = None
_USDA_ORGANIC_NAME_INDEX = None

# ── Climate Neutral data (Pass 3 Tier 0 wiring — carbon accounting certification) ──
# Climate Neutral / The Climate Label: annual measurement + offset of cradle-to-customer
# greenhouse gas emissions (Scope 1, 2, 3) with reduction plans.
# Maps to: A.1 (Energy & Emissions), A.4 (Product Lifecycle)
_CLIMATE_NEUTRAL_INDEX = None
_CLIMATE_NEUTRAL_NAME_INDEX = None

# ── 1% for the Planet data (Pass 3 Tier 0 wiring — revenue-bound environmental commitment) ──
# 1% for the Planet: members pledge 1%+ of annual revenue to environmental nonprofits,
# verified annually. Founded by Patagonia's Yvon Chouinard in 2002.
# Maps to: A.1 (Energy & Emissions), M.5 (Stakeholder Governance)
_ONE_PERCENT_INDEX = None
_ONE_PERCENT_NAME_INDEX = None


def _load_inclusion_data():
    """Load HRC and DEI score indexes from pipeline output. Idempotent."""
    global _HRC_INDEX, _DEI_INDEX, _HRC_NAME_INDEX, _DEI_NAME_INDEX
    if _HRC_INDEX is not None and _DEI_INDEX is not None:
        return
    _HRC_INDEX, _DEI_INDEX = {}, {}
    _HRC_NAME_INDEX, _DEI_NAME_INDEX = {}, {}
    
    # HRC
    hrc_path = Path("data/hrc/all_companies.json")
    if hrc_path.exists():
        try:
            for r in json.load(open(hrc_path)):
                t = (r.get("ticker") or "").upper().strip()
                n = (r.get("company") or "").lower().strip()
                if t: _HRC_INDEX[t] = r.get("cei_score")
                if n: _HRC_NAME_INDEX[n] = r.get("cei_score")
        except Exception:
            pass
    
    # DEI
    dei_path = Path("data/dei/all_companies.json")
    if dei_path.exists():
        try:
            for r in json.load(open(dei_path)):
                t = (r.get("ticker") or "").upper().strip()
                n = (r.get("company") or "").lower().strip()
                if t: _DEI_INDEX[t] = r.get("dei_score")
                if n: _DEI_NAME_INDEX[n] = r.get("dei_score")
        except Exception:
            pass


def _load_bcorp_data():
    """Load B Corp certification index from pipeline output. Idempotent."""
    global _BCORP_INDEX, _BCORP_NAME_INDEX
    if _BCORP_INDEX is not None:
        return
    _BCORP_INDEX, _BCORP_NAME_INDEX = {}, {}
    
    bcorp_path = Path("data/bcorp/all_companies.json")
    if bcorp_path.exists():
        try:
            for r in json.load(open(bcorp_path)):
                t = (r.get("ticker") or "").upper().strip()
                n = (r.get("company") or "").lower().strip()
                if t: _BCORP_INDEX[t] = r
                if n: _BCORP_NAME_INDEX[n] = r
        except Exception:
            pass


def _get_bcorp_record(ticker, company_name):
    """Return B Corp record for a company if certified, else None."""
    _load_bcorp_data()
    if ticker and ticker.upper() in _BCORP_INDEX:
        return _BCORP_INDEX[ticker.upper()]
    if company_name:
        return _BCORP_NAME_INDEX.get(company_name.lower().strip())
    return None


def _score_from_bcorp(record):
    """Map B Corp tier → sub-signal contribution.
    
    B Impact Assessment ladder (per B Lab methodology):
      130+ (elite, top ~5% of B Corps)     → 90
      100-129 (strong)                     → 80
      80-99 (certified, entry-level)       → 70
      certified without public score       → 65 (minimum credible certification)
    
    Non-certified companies return None — no signal from B Corp for them.
    """
    if not record or not record.get("bcorp_certified"):
        return None
    score = record.get("bcorp_score")
    tier = record.get("bcorp_tier", "certified_unscored")
    if tier == "elite" or (score and score >= 130): return 90
    if tier == "strong" or (score and score >= 100): return 80
    if tier == "certified" or (score and score >= 80): return 70
    return 65  # certified_unscored or defensive fallback


def _load_fairtrade_data():
    """Load Fair Trade certification index from pipeline output. Idempotent."""
    global _FAIRTRADE_INDEX, _FAIRTRADE_NAME_INDEX
    if _FAIRTRADE_INDEX is not None:
        return
    _FAIRTRADE_INDEX, _FAIRTRADE_NAME_INDEX = {}, {}
    
    ft_path = Path("data/fairtrade/all_companies.json")
    if ft_path.exists():
        try:
            for r in json.load(open(ft_path)):
                t = (r.get("ticker") or "").upper().strip()
                n = (r.get("company") or "").lower().strip()
                if t: _FAIRTRADE_INDEX[t] = r
                if n: _FAIRTRADE_NAME_INDEX[n] = r
        except Exception:
            pass


def _get_fairtrade_record(ticker, company_name):
    """Return Fair Trade record for a company if certified, else None."""
    _load_fairtrade_data()
    if ticker and ticker.upper() in _FAIRTRADE_INDEX:
        return _FAIRTRADE_INDEX[ticker.upper()]
    if company_name:
        return _FAIRTRADE_NAME_INDEX.get(company_name.lower().strip())
    return None


def _score_from_fairtrade(record):
    """Map Fair Trade tier → sub-signal contribution.
    
    Tier ladder (matching Fair Trade USA partner categories):
      full (entire company or 100% product line certified)   → 85
      partial (specific product lines certified)             → 70
      licensed (documented sourcing program)                 → 65
    
    Non-certified companies return None.
    """
    if not record or not record.get("fairtrade_certified"):
        return None
    tier = record.get("fairtrade_tier", "partial")
    if tier == "full": return 85
    if tier == "partial": return 70
    if tier == "licensed": return 65
    return 65


def _load_usda_organic_data():
    """Load USDA Organic certification index from pipeline output. Idempotent."""
    global _USDA_ORGANIC_INDEX, _USDA_ORGANIC_NAME_INDEX
    if _USDA_ORGANIC_INDEX is not None:
        return
    _USDA_ORGANIC_INDEX, _USDA_ORGANIC_NAME_INDEX = {}, {}
    
    usda_path = Path("data/usda_organic/all_companies.json")
    if usda_path.exists():
        try:
            for r in json.load(open(usda_path)):
                t = (r.get("ticker") or "").upper().strip()
                n = (r.get("company") or "").lower().strip()
                if t: _USDA_ORGANIC_INDEX[t] = r
                if n: _USDA_ORGANIC_NAME_INDEX[n] = r
        except Exception:
            pass


def _get_usda_organic_record(ticker, company_name):
    """Return USDA Organic record for a company if certified, else None."""
    _load_usda_organic_data()
    if ticker and ticker.upper() in _USDA_ORGANIC_INDEX:
        return _USDA_ORGANIC_INDEX[ticker.upper()]
    if company_name:
        return _USDA_ORGANIC_NAME_INDEX.get(company_name.lower().strip())
    return None


def _score_from_usda_organic(record):
    """Map USDA Organic tier → sub-signal contribution.
    
    Tier ladder:
      100_percent (entire company/product organic)     → 85
      made_with (70-94% organic)                       → 70
      ingredients (specific ingredients organic)       → 60
    
    Non-certified return None.
    """
    if not record or not record.get("usda_organic_certified"):
        return None
    tier = record.get("usda_organic_tier", "ingredients")
    if tier == "100_percent": return 85
    if tier == "made_with": return 70
    if tier == "ingredients": return 60
    return 60


def _load_climate_neutral_data():
    """Load Climate Neutral certification index. Idempotent."""
    global _CLIMATE_NEUTRAL_INDEX, _CLIMATE_NEUTRAL_NAME_INDEX
    if _CLIMATE_NEUTRAL_INDEX is not None:
        return
    _CLIMATE_NEUTRAL_INDEX, _CLIMATE_NEUTRAL_NAME_INDEX = {}, {}
    
    cn_path = Path("data/climate_neutral/all_companies.json")
    if cn_path.exists():
        try:
            for r in json.load(open(cn_path)):
                t = (r.get("ticker") or "").upper().strip()
                n = (r.get("company") or "").lower().strip()
                if t: _CLIMATE_NEUTRAL_INDEX[t] = r
                if n: _CLIMATE_NEUTRAL_NAME_INDEX[n] = r
        except Exception:
            pass


def _get_climate_neutral_record(ticker, company_name):
    """Return Climate Neutral record if certified, else None."""
    _load_climate_neutral_data()
    if ticker and ticker.upper() in _CLIMATE_NEUTRAL_INDEX:
        return _CLIMATE_NEUTRAL_INDEX[ticker.upper()]
    if company_name:
        return _CLIMATE_NEUTRAL_NAME_INDEX.get(company_name.lower().strip())
    return None


def _score_from_climate_neutral(record):
    """Climate Neutral gives a single certification tier (not scored sub-tiers like B Corp).
    Currently-certified → 80, lapsed → 65 (was certified, monitor).
    """
    if not record or not record.get("climate_neutral_certified"):
        return None
    status = record.get("status", "certified")
    if status == "certified": return 80
    if status == "lapsed": return 65
    return 80


def _load_one_percent_data():
    """Load 1% for the Planet membership index. Idempotent."""
    global _ONE_PERCENT_INDEX, _ONE_PERCENT_NAME_INDEX
    if _ONE_PERCENT_INDEX is not None:
        return
    _ONE_PERCENT_INDEX, _ONE_PERCENT_NAME_INDEX = {}, {}
    
    op_path = Path("data/one_percent/all_companies.json")
    if op_path.exists():
        try:
            for r in json.load(open(op_path)):
                t = (r.get("ticker") or "").upper().strip()
                n = (r.get("company") or "").lower().strip()
                if t: _ONE_PERCENT_INDEX[t] = r
                if n: _ONE_PERCENT_NAME_INDEX[n] = r
        except Exception:
            pass


def _get_one_percent_record(ticker, company_name):
    """Return 1% for the Planet record if member, else None."""
    _load_one_percent_data()
    if ticker and ticker.upper() in _ONE_PERCENT_INDEX:
        return _ONE_PERCENT_INDEX[ticker.upper()]
    if company_name:
        return _ONE_PERCENT_NAME_INDEX.get(company_name.lower().strip())
    return None


def _score_from_one_percent(record):
    """1% for the Planet tier → sub-signal contribution.
    
    Full-company membership is structurally strongest (all revenue subject to pledge).
    Brand-level is specific brand only. Product line is single product minimum.
    
      full_company   → 80
      brand_level    → 70
      product_line   → 60
    """
    if not record or not record.get("one_percent_member"):
        return None
    tier = record.get("tier", "full_company")
    if tier == "full_company": return 80
    if tier == "brand_level": return 70
    if tier == "product_line": return 60
    return 70


def _get_hrc_score(ticker, company_name):
    _load_inclusion_data()
    if ticker and ticker.upper() in _HRC_INDEX:
        return _HRC_INDEX[ticker.upper()]
    if company_name:
        return _HRC_NAME_INDEX.get(company_name.lower().strip())
    return None


def _get_dei_score(ticker, company_name):
    _load_inclusion_data()
    if ticker and ticker.upper() in _DEI_INDEX:
        return _DEI_INDEX[ticker.upper()]
    if company_name:
        return _DEI_NAME_INDEX.get(company_name.lower().strip())
    return None


# ── Harm Documentation data (Pass 4 — public-record harm penalties) ──────
# Documents publicly verifiable harm to penalize M dimension.
# Principle: "Humans can still choose."
# - Sugar/alcohol/tobacco-as-product/gambling: NO penalty (consumer choice)
# - Hidden risk, deception, weapons: PENALTY (no consent possible)
# Maps to: M.3 (Market Ethics) + M.4 (Product Ethics)

_HARM_INDEX = None
_HARM_NAME_INDEX = None

def _load_harm_data():
    """Load harm documentation index from pipeline output. Idempotent."""
    global _HARM_INDEX, _HARM_NAME_INDEX
    if _HARM_INDEX is not None:
        return
    _HARM_INDEX, _HARM_NAME_INDEX = {}, {}

    harm_path = Path("data/harm/all_companies.json")
    if harm_path.exists():
        try:
            data = json.load(open(harm_path))
            companies = data.get("companies", []) if isinstance(data, dict) else data
            for r in companies:
                t = (r.get("ticker") or "").upper().strip()
                n = (r.get("company") or "").lower().strip()
                if t: _HARM_INDEX[t] = r
                if n: _HARM_NAME_INDEX[n] = r
        except Exception:
            pass


def _get_harm_record(ticker, company_name):
    _load_harm_data()
    if ticker and ticker.upper() in _HARM_INDEX:
        return _HARM_INDEX[ticker.upper()]
    if company_name:
        cn = company_name.lower().strip()
        if cn in _HARM_NAME_INDEX:
            return _HARM_NAME_INDEX[cn]
        for k, v in _HARM_NAME_INDEX.items():
            if cn and len(cn) > 5 and len(k) > 5 and (cn in k or k in cn):
                return v
    return None


def compute_harm_penalty(ticker, company_name=""):
    """Compute Harm Documentation penalty — applies to M dimension only."""
    record = _get_harm_record(ticker, company_name)
    if not record:
        return {
            "has_harm": False,
            "penalties": {"M": 0},
            "flags": [],
            "sources": []
        }
    # v1.2y-evidence-fixes: flatten "details" sub-dict if present for consistent API
    # Weapons companies (GD, NOC) may store rubric data nested under "details"
    details = record.get("details", {})
    return {
        "has_harm": True,
        "penalties": {"M": record.get("penalty_M_total", 0)},
        "flags": record.get("flags", []),
        "sources": (record.get("sources") or details.get("sources", []))[:3],
        "settlement_5yr": record.get("settlement_total_5yr") or details.get("settlement_total_5yr", 0),
        "deaths_attributed": record.get("deaths_attributed") or details.get("deaths_attributed", 0),
        "concealment_findings": record.get("concealment_findings") or details.get("concealment_findings", []),
        "remediation_status": record.get("remediation_status") or details.get("remediation_status", "active"),
        "review_date": record.get("review_date") or details.get("review_date", "")
    }


def _score_from_inclusion_tier(tier_score):
    """Map HRC CEI / DEI score to U.3 contribution using tier structure.
    
    HRC tiers (per HRC methodology):
      100 = Equality 100 Award (top)
      90-99 = high performer
      80-89 = notable improvement
      <80 = participant but behind
    
    DEI tiers: score 100, 90, or 80 are publicly listed tiers.
    
    Rubric ladder for U.3 contribution (each tier grounded in source tier):
      100 → 85  (Equality 100 / Best Place to Work)
      90-99 → 75
      80-89 → 65
      60-79 → 50 (baseline for participants)
      <60 → 40
    """
    if tier_score is None:
        return None
    if tier_score >= 100: return 85
    if tier_score >= 90: return 75
    if tier_score >= 80: return 65
    if tier_score >= 60: return 50
    return 40


# ── Dimension Scoring ─────────────────────────────────────────────────

def score_h_dimension(sec_h, job_data, bls_data, industry, patents=None):
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
    # v1.2v: defensive int coercion — some data sources return strings
    try:
        headcount = int(headcount) if not isinstance(headcount, (int, float)) else headcount
    except (ValueError, TypeError):
        headcount = 0
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

    # v1.2x Layered: fold USPTO.H.3_adj into H.3
    if patents:
        h3_adj = patents.get("H.3_adj", 0)
        if h3_adj != 0:
            scores["H.3"] = clamp(scores["H.3"] + h3_adj)
            if "USPTO" not in sources_used: sources_used.append("USPTO")

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

    # v1.2x Layered: fold USPTO.H.5_adj into H.5
    if patents:
        h5_adj = patents.get("H.5_adj", 0)
        if h5_adj != 0:
            scores["H.5"] = clamp(scores["H.5"] + h5_adj)
            if "USPTO" not in sources_used: sources_used.append("USPTO")

    # v1.2v UNIFORM: All 4 active sub-signals weighted equally at 0.25.
    # Restoration of original methodology design — every sub-signal in a
    # dimension contributes equally. Adjustments (USPTO patents, AHI penalty)
    # apply downstream in score_company().
    D_H = 0.25*scores["H.1"] + 0.25*scores["H.2"] + 0.25*scores["H.3"] + 0.25*scores["H.5"]
    return round_score(D_H), scores, list(set(sources_used))


def score_u_dimension(sec_u, glassdoor_data, industry, subsignals=None, ticker=None, company_name=None, osha=None, dol=None, bbb=None, eeoc=None):
    scores = {}
    sources_used = []
    gd = glassdoor_data.get("u_signals", {}) if glassdoor_data else {}
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

    # v1.2x Layered: fold BBB blend into U.1 (customer-facing complaints)
    if bbb is not None:
        bbb_score = bbb.get("score") if isinstance(bbb, dict) else None
        if bbb_score is not None:
            scores["U.1"] = round(scores["U.1"] * 0.9 + bbb_score * 0.1, 1)
            if "BBB" not in sources_used: sources_used.append("BBB")

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

    # v1.2x Layered: fold OSHA blend into U.2 (worker safety)
    if osha is not None:
        osha_score = osha.get("score") if isinstance(osha, dict) else None
        if osha_score is not None:
            scores["U.2"] = round(scores["U.2"] * 0.85 + osha_score * 0.15, 1)
            if "OSHA" not in sources_used: sources_used.append("OSHA")

    # v1.2x Layered: fold DOL wage blend into U.2
    if dol is not None:
        dol_score = dol.get("score") if isinstance(dol, dict) else None
        if dol_score is not None:
            scores["U.2"] = round(scores["U.2"] * 0.9 + dol_score * 0.1, 1)
            if "DOL" not in sources_used: sources_used.append("DOL")

    # v1.2x Layered: fold EEOC.U.2_adj into U.2
    if eeoc is not None:
        u2_adj = eeoc.get("U.2_adj", 0) if isinstance(eeoc, dict) else 0
        if u2_adj != 0:
            scores["U.2"] = clamp(scores["U.2"] + u2_adj)
            if "EEOC" not in sources_used: sources_used.append("EEOC")

    # U.3 Relational Integrity — authoritative inclusion sources (HRC CEI, DEI, B Corp) blend with Glassdoor.
    # Per API_SHOPPING_LIST Pass 2D T0.1/T0.2/T0.5: HRC is the recognized US authority on LGBTQ+
    # workplace inclusion; Disability:IN DEI for disability inclusion; B Corp certification
    # includes a Workers + Community assessment that's a broader inclusion signal. All use
    # published methodology. Ladder maps tier structure → U.3 contribution.
    hrc_raw = _get_hrc_score(ticker, company_name)
    dei_raw = _get_dei_score(ticker, company_name)
    bcorp_record = _get_bcorp_record(ticker, company_name)
    hrc_contrib = _score_from_inclusion_tier(hrc_raw)
    dei_contrib = _score_from_inclusion_tier(dei_raw)
    bcorp_contrib = _score_from_bcorp(bcorp_record)
    inclusion_signals = [s for s in (hrc_contrib, dei_contrib, bcorp_contrib) if s is not None]
    
    if inclusion_signals:
        # Authoritative signals present — average them for U.3.
        u3 = round(sum(inclusion_signals) / len(inclusion_signals), 1)
        if hrc_contrib is not None and "HRC CEI" not in sources_used:
            sources_used.append("HRC CEI")
        if dei_contrib is not None and "Disability:IN DEI" not in sources_used:
            sources_used.append("Disability:IN DEI")
        if bcorp_contrib is not None and "B Corp" not in sources_used:
            sources_used.append("B Corp")
        # Optional: blend in Glassdoor as tertiary signal at low weight (self-report corroboration)
        if gd.get("culture_score") is not None:
            u3 = round(u3 * 0.85 + gd["culture_score"] * 0.15, 1)
            if "Glassdoor" not in sources_used: sources_used.append("Glassdoor")
        scores["U.3"] = u3
    elif gd.get("culture_score") is not None:
        # Fallback to Glassdoor alone (self-reported, weakest source)
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

    # v1.2v UNIFORM: All 4 active sub-signals weighted equally at 0.25.
    # Adjustments (EEOC, OSHA, DOL, BBB, AHI penalty) apply downstream.
    D_U = 0.25*scores["U.1"] + 0.25*scores["U.2"] + 0.25*scores["U.3"] + 0.25*scores["U.4"]
    return round_score(D_U), scores, sources_used


def score_m_dimension(sec_m, epa_data, glassdoor_data, industry, subsignals=None, ticker=None, company_name=None, ftc=None, eeoc=None, fda=None, pay_ratio=None, insider=None):
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

    # v1.2x Layered: fold FTC.M.2 blend into M.2
    if ftc is not None and isinstance(ftc, dict) and ftc.get("M.2") is not None:
        scores["M.2"] = round(scores["M.2"] * 0.9 + ftc["M.2"] * 0.1, 1)
        if "FTC" not in sources_used: sources_used.append("FTC")

    # M.3 Market Ethics — SEC + EPA legal penalties (downward signal) blended with
    # Fair Trade certification (positive supply-chain evidence). Fair Trade is the
    # strongest positive M.3 signal available — certifies fair compensation, safe
    # working conditions, and traceability.
    litigation = sec_m.get("litigation", {}).get("value")
    epa_penalties = epa_data.get("m_signals", {}).get("total_penalties", 0) if epa_data else 0
    epa_actions = epa_data.get("m_signals", {}).get("formal_actions", 0) if epa_data else 0
    total_legal = (litigation or 0) + epa_penalties

    # Legal-penalty-based score (downward)
    if total_legal > 1000000000: legal_m3 = 20
    elif total_legal > 100000000: legal_m3 = 40
    elif total_legal > 10000000: legal_m3 = 55
    elif total_legal > 1000000: legal_m3 = 65
    elif total_legal > 0: legal_m3 = 75
    else: legal_m3 = 85

    # Fair Trade positive signal + USDA Organic (federal third-party supply-chain verification)
    ft_record = _get_fairtrade_record(ticker, company_name)
    ft_m3 = _score_from_fairtrade(ft_record)
    usda_record = _get_usda_organic_record(ticker, company_name)
    usda_m3 = _score_from_usda_organic(usda_record)
    
    # Gather positive certifications
    positive_signals = [s for s in (ft_m3, usda_m3) if s is not None]

    if positive_signals:
        # Average positive certification evidence, then blend with legal-penalty baseline.
        # Weight positive signals at 60%, legal at 40% — legal penalties can still drag
        # down a company with cert partials ($100M+ penalties matters even with Fair Trade coffee).
        cert_avg = sum(positive_signals) / len(positive_signals)
        scores["M.3"] = round(cert_avg * 0.6 + legal_m3 * 0.4, 1)
        if ft_m3 is not None and "Fair Trade" not in sources_used: sources_used.append("Fair Trade")
        if usda_m3 is not None and "USDA Organic" not in sources_used: sources_used.append("USDA Organic")
    else:
        scores["M.3"] = legal_m3

    if litigation: sources_used.append("SEC")
    if epa_penalties > 0 or epa_actions > 0: sources_used.append("EPA")

    # v1.2x Layered: fold EEOC.M.3_adj into M.3
    if eeoc is not None and isinstance(eeoc, dict):
        m3_adj = eeoc.get("M.3_adj", 0)
        if m3_adj != 0:
            scores["M.3"] = clamp(scores["M.3"] + m3_adj)
            if "EEOC" not in sources_used: sources_used.append("EEOC")

    # v1.2x Layered: fold pay_ratio.M.3_adj into M.3
    if pay_ratio is not None and isinstance(pay_ratio, dict):
        pr_adj = pay_ratio.get("M.3_adj", 0)
        if pr_adj != 0:
            scores["M.3"] = clamp(scores["M.3"] + pr_adj)
        if pay_ratio.get("ratio") and "SEC DEF 14A" not in sources_used:
            sources_used.append("SEC DEF 14A")

    # v1.2x Layered: fold insider.M.3_adj into M.3
    if insider is not None and isinstance(insider, dict):
        ins_adj = insider.get("M.3_adj", 0)
        if ins_adj != 0:
            scores["M.3"] = clamp(scores["M.3"] + ins_adj)
            if "SEC Form 4" not in sources_used: sources_used.append("SEC Form 4")

    # M.4 Product Ethics — CPSC recalls if available, else Glassdoor
    cpsc_m4 = ss.get("cpsc", {}).get("M.4")
    if cpsc_m4 is not None:
        scores["M.4"] = cpsc_m4
        sources_used.append("CPSC")
    else:
        gd_m = glassdoor_data.get("m_signals", {}) if glassdoor_data else {}
        if gd_m.get("mgmt_score") is not None:
            scores["M.4"] = round(gd_m["mgmt_score"] * 0.6 + gd_m.get("comp_score", 50) * 0.4, 1)
            sources_used.append("Glassdoor")
        else:
            scores["M.4"] = 50  # No data = neutral

    # v1.2x Layered: fold FDA blend into M.4
    if fda is not None and isinstance(fda, dict):
        fda_score = fda.get("score")
        if fda_score is not None:
            scores["M.4"] = round(scores["M.4"] * 0.9 + fda_score * 0.1, 1)
            if "FDA" not in sources_used: sources_used.append("FDA")

    # M.5 Stakeholder Governance — B Corp legal structure is strongest (stakeholder-centric
    # fiduciary duty). 1% for the Planet is secondary (revenue-bound environmental pledge
    # signals structural stakeholder alignment). Both average if present. Fall back to FEC,
    # then Glassdoor CEO score.
    bcorp_m5 = None
    bcorp_record_m5 = _get_bcorp_record(ticker, company_name)
    if bcorp_record_m5 and bcorp_record_m5.get("bcorp_certified"):
        bcorp_m5 = _score_from_bcorp(bcorp_record_m5)
    
    op_record_m5 = _get_one_percent_record(ticker, company_name)
    op_m5 = _score_from_one_percent(op_record_m5)
    
    stakeholder_signals = [s for s in (bcorp_m5, op_m5) if s is not None]
    fec_m5 = ss.get("fec", {}).get("M.5")
    
    if stakeholder_signals:
        # Average certification evidence for stakeholder governance
        scores["M.5"] = round(sum(stakeholder_signals) / len(stakeholder_signals), 1)
        if bcorp_m5 is not None and "B Corp" not in sources_used: sources_used.append("B Corp")
        if op_m5 is not None and "1% for the Planet" not in sources_used: sources_used.append("1% for the Planet")
    elif fec_m5 is not None:
        scores["M.5"] = fec_m5
        sources_used.append("FEC")
    else:
        gd_m = glassdoor_data.get("m_signals", {}) if glassdoor_data else {}
        if gd_m.get("ceo_score") is not None:
            scores["M.5"] = gd_m["ceo_score"]
        else:
            scores["M.5"] = 50  # No data = neutral

    # v1.2v UNIFORM: All 5 active sub-signals weighted equally at 0.20.
    # Was 0.20/0.20/0.20/0.25/0.15. Adjustments (FTC, EEOC, FDA, pay ratio,
    # insider, AHI penalty, HD penalty) apply downstream.
    D_M = 0.20*scores["M.1"] + 0.20*scores["M.2"] + 0.20*scores["M.3"] + 0.20*scores["M.4"] + 0.20*scores["M.5"]
    return round_score(D_M), scores, list(set(sources_used))


def score_a_dimension(sec_a, epa_data, cdp_data, industry, subsignals=None, ticker=None, company_name=None, sbti=None):
    scores = {}
    sources_used = []
    ss = subsignals or {}
    cdp_a = cdp_data.get("a_signals", {}) if cdp_data else {}

    # A.1 Energy & Emissions — CDP climate (strongest), then certification-grounded
    # signals (Climate Neutral = measured + offset emissions; 1% for the Planet = revenue
    # pledge to environmental causes), then industry default.
    cn_record = _get_climate_neutral_record(ticker, company_name)
    cn_a1 = _score_from_climate_neutral(cn_record)
    op_record = _get_one_percent_record(ticker, company_name)
    op_a1 = _score_from_one_percent(op_record)
    env_signals = [s for s in (cn_a1, op_a1) if s is not None]
    
    if cdp_a.get("cdp_climate_score") is not None:
        # CDP is authoritative — use it, optionally blend with cert signals if present
        cdp_score = cdp_a["cdp_climate_score"]
        if env_signals:
            # Weight CDP at 70%, certs at 30% (CDP is more specific to emissions; certs are
            # positive commitments but don't guarantee actual reduction achievement)
            scores["A.1"] = round(cdp_score * 0.7 + (sum(env_signals) / len(env_signals)) * 0.3, 1)
            if cn_a1 is not None and "Climate Neutral" not in sources_used: sources_used.append("Climate Neutral")
            if op_a1 is not None and "1% for the Planet" not in sources_used: sources_used.append("1% for the Planet")
        else:
            scores["A.1"] = cdp_score
        sources_used.append("CDP")
    elif env_signals:
        # No CDP data but certifications present — use their average
        scores["A.1"] = round(sum(env_signals) / len(env_signals), 1)
        if cn_a1 is not None and "Climate Neutral" not in sources_used: sources_used.append("Climate Neutral")
        if op_a1 is not None and "1% for the Planet" not in sources_used: sources_used.append("1% for the Planet")
    else:
        defaults = {"energy": 30, "manufacturing": 45, "tech": 50, "finance": 65,
                    "healthcare": 55, "retail": 50, "food": 55, "media": 60,
                    "telecom": 45, "defense": 40, "auto": 40, "default": 50}
        scores["A.1"] = defaults.get(industry, 50)

    # v1.2x Layered: fold SBTi.A.1_adj into A.1
    if sbti is not None and isinstance(sbti, dict):
        a1_adj = sbti.get("A.1_adj", 0)
        if a1_adj != 0:
            scores["A.1"] = clamp(scores["A.1"] + a1_adj)
            if "SBTi" not in sources_used: sources_used.append("SBTi")

    # A.2 Water — CDP water
    if cdp_a.get("cdp_water_score") is not None:
        scores["A.2"] = cdp_a["cdp_water_score"]
        if "CDP" not in sources_used: sources_used.append("CDP")
    else:
        scores["A.2"] = 50

    # A.3 Land & Habitat — USDA Organic is strongest signal (soil health + no synthetic chemicals
    # is literally the A.3 definition), then industry+EPA sub-signal, then EPA violations.
    usda_record = _get_usda_organic_record(ticker, company_name)
    usda_a3 = _score_from_usda_organic(usda_record)
    land_score = ss.get("land", {}).get("A.3")
    
    if usda_a3 is not None:
        # If we also have the industry/EPA sub-signal, blend for a more nuanced score
        if land_score is not None:
            scores["A.3"] = round(usda_a3 * 0.7 + land_score * 0.3, 1)
            sources_used.append("USDA Organic")
            if "Industry+EPA" not in sources_used: sources_used.append("Industry+EPA")
        else:
            scores["A.3"] = usda_a3
            sources_used.append("USDA Organic")
    elif land_score is not None:
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

    # A.4 Product Lifecycle — iFixit hardware scores (strongest), then certification-grounded
    # signals (B Corp Environment + Fair Trade + USDA Organic + Climate Neutral), then CDP forests, then default.
    hw_score = ss.get("hardware", {}).get("A.4")
    if hw_score is not None:
        scores["A.4"] = hw_score
        hw_src = ss.get("hardware", {}).get("source", "iFixit")
        if hw_src not in sources_used: sources_used.append(hw_src)
    else:
        # Certification signals: B Corp Environment + Fair Trade traceability + USDA Organic + Climate Neutral
        bcorp_record = _get_bcorp_record(ticker, company_name)
        bcorp_a4 = _score_from_bcorp(bcorp_record)
        ft_record = _get_fairtrade_record(ticker, company_name)
        ft_a4 = _score_from_fairtrade(ft_record)
        usda_record_a4 = _get_usda_organic_record(ticker, company_name)
        usda_a4 = _score_from_usda_organic(usda_record_a4)
        cn_record_a4 = _get_climate_neutral_record(ticker, company_name)
        cn_a4 = _score_from_climate_neutral(cn_record_a4)
        cert_signals = [s for s in (bcorp_a4, ft_a4, usda_a4, cn_a4) if s is not None]
        
        if cert_signals:
            scores["A.4"] = round(sum(cert_signals) / len(cert_signals), 1)
            if bcorp_a4 is not None and "B Corp" not in sources_used: sources_used.append("B Corp")
            if ft_a4 is not None and "Fair Trade" not in sources_used: sources_used.append("Fair Trade")
            if usda_a4 is not None and "USDA Organic" not in sources_used: sources_used.append("USDA Organic")
            if cn_a4 is not None and "Climate Neutral" not in sources_used: sources_used.append("Climate Neutral")
        elif cdp_a.get("cdp_forests_score") is not None:
            scores["A.4"] = cdp_a["cdp_forests_score"]
        else:
            hw_defaults = {"tech": 40, "telecom": 45, "manufacturing": 50, "default": 55}
            scores["A.4"] = hw_defaults.get(industry, 55)

    # v1.2v UNIFORM: All 4 active sub-signals weighted equally at 0.25.
    # Was 0.30/0.25/0.20/0.25. SBTi bonus applies downstream.
    D_A = 0.25*scores["A.1"] + 0.25*scores["A.2"] + 0.25*scores["A.3"] + 0.25*scores["A.4"]
    return round_score(D_A), scores, list(set(sources_used))


def score_n_dimension(sec_n, cdp_data, epa_data, industry, gri=None):
    scores = {}
    sources_used = []
    # v1.0.2 removed N.1 (Narrative Integrity), N.3 (Stakeholder Engagement), N.4 (Narrative Courage).
    # Only N.2 (Reporting Quality via CDP) and N.5 (Filing Discipline via SEC) remain.

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

    # v1.2x Layered: fold GRI.N.2_adj into N.2
    if gri is not None and isinstance(gri, dict):
        n2_adj = gri.get("N.2_adj", 0)
        if n2_adj != 0:
            scores["N.2"] = clamp(scores["N.2"] + n2_adj)
            if "GRI" not in sources_used: sources_used.append("GRI")

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

    # v1.2v UNIFORM: 2 active sub-signals weighted equally at 0.50.
    # Was 0.571/0.429. GRI bonus, AHI penalty apply downstream.
    # NOTE: N dimension still depends on just two grounded signals (N.2, N.5).
    # Three sub-signals deferred to v1.2 (N.1, N.3, N.4). Future pass should
    # add DSA transparency, 12b-25 late filings per API_SHOPPING_LIST T1.1, T1.3.
    D_N = 0.50*scores["N.2"] + 0.50*scores["N.5"]
    return round_score(D_N), scores, sources_used


def round_score(val):
    """Round down unless decimal is .6 or higher."""
    import math
    remainder = round(val - math.floor(val), 4)  # Avoid float precision issues
    return int(math.ceil(val)) if remainder >= 0.6 else int(math.floor(val))


def compute_composite(D_H, D_U, D_M, D_A, D_N):
    """v1.2.0: composite is the mean of the five HUMAN dimensions, with one floor rule.

    FLOOR RULE: if ANY dimension < 30, composite is capped at 50.
    Severe failure in any single HUMAN dimension means the company cannot earn a
    composite above 50, even if the other four dimensions average it higher. This
    protects users from companies with one severely failing dimension (e.g.,
    harm_documentation penalties zeroing out M for J&J / Bayer / Purdue-style cases).

    Returns 4-tuple (signature preserved for backward compatibility):
      (composite, floor_triggered, balance_floor_unused, triggering_dimension)

    The 3rd element (balance_floor_unused) is always False — the legacy multi-tier
    "balance floor" rule was removed in v1.1.0; the placeholder is retained so the
    api_server caller can serialize a stable schema without churn. Schedule for
    full removal in v1.3 once iOS / extension consumers are audited.

    floor_triggered fires whenever min_dim < 30, even if the mean was already ≤ 50
    (signals "severe single-dim failure" to UI consumers regardless of cap effect).
    """
    composite = (D_H + D_U + D_M + D_A + D_N) / 5
    dims = {"H": D_H, "U": D_U, "M": D_M, "A": D_A, "N": D_N}
    min_dim_value = min(dims.values())

    if min_dim_value < 30:
        composite = min(composite, 50)
        triggering_dimension = min(dims, key=dims.get)
        return round_score(composite), True, False, triggering_dimension

    return round_score(composite), False, False, None

def get_hi_grade(composite, verified=False):
    """Score-only system. All companies return 'scored'. Gold HI Grade is checked separately."""
    return "scored", ""


# ═══════════════════════════════════════════════════════════════════════
# GOLD HI GRADE GATE — v1.1.0 simplified rule
# ═══════════════════════════════════════════════════════════════════════
# Single rule: All 5 HUMAN dimensions ≥ 60, each backed by ≥1 real data source,
# AND no active warning/critical decay alert.
#
# v1.0.x had: composite threshold + balance floor + integrity gate (3 gates with
# adaptive threshold, ratchet, etc.). v1.1.0 supersedes all of that.
#
# Why simplified: humanwashing and algorithmic harm are absorbed *into* dimension
# scores via sub-signal pipelines (M.2 catches data-ethics violations, U.4 catches
# manipulative empathy, etc.), so they no longer need a separate gate. Decay
# remains a separate gate because it captures real-time signals that backward-
# looking dimension data can't see fast enough (Oracle layoffs ≠ caught by
# annual SEC filings).

GOLD_DIM_THRESHOLD = 60   # Each HUMAN dimension must score ≥ 60
GOLD_DECAY_BLOCKING = {"warning", "critical"}  # decay levels that block Gold


def check_hi_certified(record, decay_data=None):
    """Check Gold HI Grade eligibility per v1.1.0 rule.
    
    Returns (is_gold, gates_dict) where gates_dict reports per-gate pass/fail
    for use in audit drill-downs.
    
    Gate 1 — DIMENSIONS: All 5 dims (H/U/M/A/N) ≥ GOLD_DIM_THRESHOLD (60)
    Gate 2 — EVIDENCE:   Each dim has ≥1 real data source (not Seed/default)
    Gate 3 — MOMENTUM:   decay_level not in GOLD_DECAY_BLOCKING (warning/critical)
    """
    dims = {
        "H": record.get("D_H", 0),
        "U": record.get("D_U", 0),
        "M": record.get("D_M", 0),
        "A": record.get("D_A", 0),
        "N": record.get("D_N", 0),
    }
    
    # Gate 1: every dim ≥ 60
    dim_pass = {k: v >= GOLD_DIM_THRESHOLD for k, v in dims.items()}
    gate_dimensions = all(dim_pass.values())
    
    # Gate 2: every dim has ≥1 real source
    # Real source = anything that's NOT just ["Seed Estimate"] or empty.
    # Manual Scoring (seed) records explicitly fail this gate — Gold requires
    # pipeline-verified evidence per the B2B "no black boxes" claim.
    genome = record.get("genome", {})
    evidence_pass = {}
    for dim_key in "HUMAN":
        sources = genome.get(dim_key, {}).get("sources", [])
        # Exclude Seed Estimate and require at least one real source
        real = [s for s in sources if s and s != "Seed Estimate"]
        evidence_pass[dim_key] = len(real) >= 1
    gate_evidence = all(evidence_pass.values())
    
    # Gate 3: decay momentum check
    decay_level = "stable"  # default if no decay data
    if decay_data:
        decay_level = decay_data.get("decay_level", "stable")
    elif record.get("decay_level"):
        decay_level = record.get("decay_level")
    gate_momentum = decay_level not in GOLD_DECAY_BLOCKING
    
    gates = {
        "dimensions": gate_dimensions,
        "evidence": gate_evidence,
        "momentum": gate_momentum,
        "_detail": {
            "dim_pass": dim_pass,
            "evidence_pass": evidence_pass,
            "decay_level": decay_level,
        }
    }
    
    return all([gate_dimensions, gate_evidence, gate_momentum]), gates


# Legacy threshold function — kept as no-op shim for any caller that hasn't
# migrated to check_hi_certified yet. v1.1.0 has no adaptive threshold;
# Gold is determined per-company by the 3-gate rule above.
def compute_gold_threshold(all_scores):
    """DEPRECATED in v1.1.0. Returns GOLD_DIM_THRESHOLD for backward compat.
    Old callers expecting a composite threshold should be migrated to check_hi_certified."""
    return GOLD_DIM_THRESHOLD



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
    # ─── v1.2y-evidence-fixes: bottom-scorer AHI entries (public record) ───
    "BYTEDANCE": {"division": 80, "addiction": 95, "manipulation": 80, "transparency": 15, "human_override": 15,
                  "flags": ["For You algorithm optimized for session length (internal docs leak 2022)",
                            "Documented teen mental-health content promotion (WSJ investigation 2021)",
                            "Douyin (China) vs TikTok (West) show different content curation (Center for Humane Tech research 2022)",
                            "Opaque moderation escalation (Congressional testimony 2023)"]},
    "WISH":      {"division": 25, "addiction": 45, "manipulation": 85, "transparency": 10, "human_override": 15,
                  "flags": ["Dark patterns in pricing display (FTC consent order 2023)",
                            "Counterfeit product prevalence (Paris Commercial Court ruling 2020)",
                            "Misleading original-price strikethrough (class action 2022)",
                            "Opaque merchant moderation practices"]},
    "CVIEW":     {"division": 20, "addiction": 5, "manipulation": 75, "transparency": 5, "human_override": 5,
                  "flags": ["Non-consensual facial image scraping (3B+ images, ACLU v. Clearview settlement 2022)",
                            "Biometric database without subject consent (Illinois BIPA violations)",
                            "Sold to law enforcement without public oversight (NYT expose 2020)",
                            "Banned in Canada, UK, France, Italy, Australia (regulatory rulings 2021-2023)"]},
    "BABA":      {"division": 15, "addiction": 30, "manipulation": 60, "transparency": 20, "human_override": 25,
                  "flags": ["Algorithmic merchant ranking with paid placement opacity",
                            "Counterfeit goods platform moderation concerns (USTR Notorious Markets List)"]},
    # (end v1.2y-evidence-fixes additions)
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
        # v1.2y-ahi-components: even without penalty, expose components
        low_components = {
            "division": data["division"],
            "addiction": data["addiction"],
            "manipulation": data["manipulation"],
            "transparency": data["transparency"],
            "human_override": data["human_override"],
        }
        return {"algo_harm_score": round(harm, 1), "penalties": {"H": 0, "U": 0, "M": 0, "N": 0}, "flags": data.get("flags", []), "has_harm": False, "components": low_components}
    
    # Penalties scale: max -15 per dimension at harm=100
    pf = (harm - 30) / 70  # 0 to 1
    penalties = {
        "H": round(-pf * 10, 1),   # H.1 — algo replaces human editorial judgment
        "U": round(-pf * 15, 1),   # U.1 + U.4 — exploiting users isn't empathy
        "M": round(-pf * 15, 1),   # M.4 — dark patterns, addiction, manipulation
        "N": round(-pf * 10, 1),   # N.4 — claiming to "connect" while dividing
    }
    
    # v1.2y-ahi-components: expose the 5 factors that produce the AHI score for journalist/UI auditability
    components = {
        "division": data["division"],
        "addiction": data["addiction"],
        "manipulation": data["manipulation"],
        "transparency": data["transparency"],
        "human_override": data["human_override"],
    }
    return {"algo_harm_score": round(harm, 1), "penalties": penalties, "flags": data.get("flags", []), "has_harm": True, "components": components}


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

    # ═══ v1.2x LAYERED SCORING — Load ext BEFORE dimension calls ═══
    # Weak-source blends (OSHA, DOL, BBB, FTC, FDA, EEOC, USPTO, pay ratio,
    # insider, GRI, SBTi) are passed INTO their target sub-signal functions.
    # Cross-cutting modifiers (AHI, HD) remain applied AT DIMENSION LEVEL below.
    ext = {}
    if ticker:
        try:
            ext_file = Path("data/subsignals/extended/all_extended.json")
            if ext_file.exists():
                all_ext = json.load(open(ext_file))
                ext = all_ext.get(ticker.upper(), {})
        except:
            pass

    D_H, h_detail, h_src = score_h_dimension(
        sec_h, job_data, bls_data, industry,
        patents=ext.get("patents"))
    D_U, u_detail, u_src = score_u_dimension(
        sec_u, glassdoor_data, industry, ss,
        ticker=ticker, company_name=company_name,
        osha=ext.get("osha"),
        dol=ext.get("dol"),
        bbb=ext.get("bbb"),
        eeoc=ext.get("eeoc"))
    D_M, m_detail, m_src = score_m_dimension(
        sec_m, epa_data, glassdoor_data, industry, ss,
        ticker=ticker, company_name=company_name,
        ftc=ext.get("ftc"),
        eeoc=ext.get("eeoc"),
        fda=ext.get("fda"),
        pay_ratio=ext.get("pay_ratio"),
        insider=ext.get("insider"))
    D_A, a_detail, a_src = score_a_dimension(
        sec_data.get("a_signals", {}) if sec_data else {},
        epa_data, cdp_data, industry, ss,
        ticker=ticker, company_name=company_name,
        sbti=ext.get("sbti"))
    D_N, n_detail, n_src = score_n_dimension(
        sec_n, cdp_data, epa_data, industry,
        gri=ext.get("gri"))

    # v1.2x Layered: weak-blend adjustment block removed — folded into sub-signals.
    # Charity adjustment removed in v1.0.2 — U.5 removed, charity uses editorial
    # curator labels per Pass 2A. Will be reintroduced post-Pass-3 if grounded
    # moral-courage signal exists.
    
    # ═══ ALGORITHMIC HARM INDEX — Cross-cutting penalty ═══
    algo_harm = compute_algo_harm(ticker)
    if algo_harm["has_harm"]:
        p = algo_harm["penalties"]
        D_H = clamp(D_H + p["H"])
        D_U = clamp(D_U + p["U"])
        D_M = clamp(D_M + p["M"])
        D_N = clamp(D_N + p["N"])

    # ═══ HARM DOCUMENTATION — Direct M dimension penalty ═══
    # Public-record harm: settlements, deaths, concealment.
    # Same pattern as AHI but only M dimension (harm = market/product issue).
    harm_doc = compute_harm_penalty(ticker, company_name)
    if harm_doc["has_harm"]:
        D_M = clamp(D_M + harm_doc["penalties"]["M"])


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

    # Add harm documentation flags (v1.2y-hw-cleanup: filter out "Products:" — they're context, not harm evidence)
    if harm_doc.get("has_harm"):
        harm_flags = [f"HD: {f}" for f in harm_doc.get("flags", [])[:3]
                      if not f.strip().startswith("Products:")]
        hw_flags.extend(harm_flags)


    record = {
        "company": company_name, "ticker": ticker, "industry": industry, "sic": sic,
        "sic_description": sec_data.get("n_signals", {}).get("sic_description", "") if sec_data else "",
        "D_H": D_H, "D_U": D_U, "D_M": D_M, "D_A": D_A, "D_N": D_N,
        "composite": composite, "hi_grade": grade, "satire": satire,
        "floor_triggered": floor_triggered, "balance_floor": balance_floor_triggered, "triggering_dimension": triggering_dim,
        "confidence": "Estimated", "spec_version": "1.2.0",
        "data_sources": all_sources,
        "signal_coverage": f"{real_count}/{len(all_details)} sub-signals with real data",
        "humanwashing_flags": hw_flags,
        "algo_harm": algo_harm,
        "harm_documentation": harm_doc,
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
    
    # Compute Gold HI Grade per v1.1.0 rule. Decay data isn't available at record-build
    # time (engine runs before heartbeat_monitor); api_server attaches decay and re-evaluates
    # at serve time. Engine writes Gold based on dimensions+evidence only; momentum gate
    # passes by default and api_server may flip it to False if decay is warning/critical.
    is_gold, gates = check_hi_certified(record, decay_data=None)
    record["hi_balanced"] = is_gold
    record["hi_balanced_gates"] = gates  # for audit drill-down per AUDIT_TRAIL §2
    return record


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
            # v1.2.0 fix: prefer ticker-bearing entries over seed entries.
            # When a scored record (with ticker) collides on normalized name with
            # a seed record (no ticker), the ticker entry should ALWAYS win
            # regardless of raw data_sources count, otherwise we orphan the ticker
            # and drop a Tier-1 company from the scored universe.
            s_has_ticker = bool(s.get("ticker"))
            e_has_ticker = bool(existing.get("ticker"))
            s_sources = len(s.get("data_sources", []))
            e_sources = len(existing.get("data_sources", []))
            should_replace = False
            if s_has_ticker and not e_has_ticker:
                should_replace = True
            elif s_has_ticker == e_has_ticker and s_sources > e_sources:
                should_replace = True
            if should_replace:
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
