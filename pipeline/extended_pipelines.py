"""
HI. Extended Sub-Signal Pipelines — 12 Additional Free Sources
Gets us from 22 to 34 total data sources.

All government or public APIs. Zero cost. Zero AI.

Sources 23-34:
  23. OSHA Workplace Safety → U.2 Worker Empathy
  24. FTC Enforcement Actions → M.2 Data Ethics + N.4 Humanwashing
  25. EEOC Discrimination Data → U.2 + M.3
  26. USPTO Patent Analysis → H.3 + H.5
  27. FDA Warning Letters → M.4 Product Ethics
  28. DOL Wage Violations → U.2 Worker Empathy
  29. SEC DEF 14A Pay Ratios → M.3 + H.4
  30. BBB Complaints → U.1 Customer Empathy
  31. SEC Form 4 Insider Trading → M.3 Market Ethics
  32. GRI Sustainability Database → N.2 Environmental Reporting
  33. SBTi Climate Commitments → A.1 Energy
  34. IRS 990 / Charity Data → U.5 Moral Courage

Run: python3 extended_pipelines.py --all
"""

import json, os, time, re
from pathlib import Path
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("pip install requests --break-system-packages")
    exit(1)

DATA_DIR = Path("data/subsignals/extended")
DATA_DIR.mkdir(parents=True, exist_ok=True)

CACHE_HOURS = 168  # 1 week

def load_cache(ticker, source):
    f = DATA_DIR / f"{source}_{ticker.upper()}.json"
    if f.exists() and (time.time() - f.stat().st_mtime) / 3600 < CACHE_HOURS:
        return json.load(open(f))
    return None

def save_cache(ticker, source, data):
    f = DATA_DIR / f"{source}_{ticker.upper()}.json"
    json.dump(data, open(f, "w"), indent=2)


# ═══════════════════════════════════════════════════════════════════════
# 23. OSHA Workplace Safety → U.2 Worker Empathy
# ═══════════════════════════════════════════════════════════════════════

OSHA_API = "https://enforcedata.dol.gov/api/osha_inspection"

def fetch_osha(company_name, ticker):
    cached = load_cache(ticker, "osha")
    if cached: return cached
    try:
        # DOL enforcement data API
        params = {"company": company_name[:50], "limit": 100}
        r = requests.get("https://enforcedata.dol.gov/api/osha_inspection", 
                        params=params, timeout=15)
        if r.status_code != 200: return None
        
        records = r.json() if isinstance(r.json(), list) else r.json().get("results", [])
        
        violations = sum(1 for rec in records if rec.get("total_violations", 0) > 0)
        serious = sum(rec.get("serious_violations", 0) for rec in records)
        penalties = sum(float(rec.get("total_penalties", 0) or 0) for rec in records)
        
        result = {
            "company": company_name, "ticker": ticker,
            "inspections": len(records), "violations": violations,
            "serious_violations": serious, "total_penalties": penalties,
            "source": "OSHA", "fetched": datetime.now().isoformat()
        }
        save_cache(ticker, "osha", result)
        return result
    except Exception as e:
        print(f"  OSHA error: {e}")
        return None

def score_osha(data):
    if not data: return None
    v = data.get("serious_violations", 0)
    p = data.get("total_penalties", 0)
    if v == 0 and p == 0: return 85
    elif v <= 2 and p < 100000: return 70
    elif v <= 5: return 55
    elif v <= 15: return 40
    else: return 25


# ═══════════════════════════════════════════════════════════════════════
# 24. FTC Enforcement Actions → M.2 Data Ethics + N.4 Humanwashing
# ═══════════════════════════════════════════════════════════════════════

FTC_CASES_URL = "https://www.ftc.gov/legal-library/browse/cases-proceedings"

# Known FTC enforcement targets (curated from public FTC case list)
FTC_ACTIONS = {
    "META": {"count": 5, "privacy": True, "deceptive": True, "penalty_m": 5000, "notes": "Cambridge Analytica, children's privacy"},
    "GOOG": {"count": 3, "privacy": True, "deceptive": False, "penalty_m": 170, "notes": "Location tracking, COPPA"},
    "GOOGL": {"count": 3, "privacy": True, "deceptive": False, "penalty_m": 170},
    "AMZN": {"count": 3, "privacy": True, "deceptive": True, "penalty_m": 30, "notes": "Alexa recordings, dark patterns"},
    "AAPL": {"count": 0, "privacy": False, "deceptive": False, "penalty_m": 0},
    "MSFT": {"count": 1, "privacy": True, "deceptive": False, "penalty_m": 20, "notes": "COPPA Xbox"},
    "TSLA": {"count": 1, "privacy": False, "deceptive": True, "penalty_m": 0, "notes": "Autopilot claims"},
    "T": {"count": 2, "privacy": False, "deceptive": True, "penalty_m": 60, "notes": "Throttling, billing"},
    "VZ": {"count": 1, "privacy": True, "deceptive": False, "penalty_m": 0},
    "CMCSA": {"count": 2, "privacy": False, "deceptive": True, "penalty_m": 2.3},
    "WMT": {"count": 1, "privacy": False, "deceptive": True, "penalty_m": 3, "notes": "Money transfer"},
    "PYPL": {"count": 1, "privacy": False, "deceptive": True, "penalty_m": 25},
    "CRM": {"count": 0, "privacy": False, "deceptive": False, "penalty_m": 0},
    "NFLX": {"count": 0, "privacy": False, "deceptive": False, "penalty_m": 0},
    "DIS": {"count": 1, "privacy": True, "deceptive": False, "penalty_m": 3, "notes": "COPPA Disney apps"},
}

def fetch_ftc(company_name, ticker):
    # Use curated data (FTC doesn't have a clean API)
    return FTC_ACTIONS.get(ticker.upper())

def score_ftc(data):
    if not data: return {"M.2": None, "N.4": None}
    count = data.get("count", 0)
    penalty = data.get("penalty_m", 0)
    
    # M.2 Data Ethics — privacy violations
    if data.get("privacy"):
        if penalty > 100: m2 = 20
        elif penalty > 10: m2 = 40
        else: m2 = 55
    elif count > 0:
        m2 = 65
    else:
        m2 = 85
    
    # N.4 Humanwashing/deceptive — deceptive practices
    if data.get("deceptive"):
        if count >= 3: n4 = 30
        elif count >= 1: n4 = 50
        else: n4 = 60
    else:
        n4 = 85
    
    return {"M.2": m2, "N.4": n4}


# ═══════════════════════════════════════════════════════════════════════
# 25. EEOC Discrimination → U.2 + M.3
# ═══════════════════════════════════════════════════════════════════════

# Known major EEOC settlements (curated from public records)
EEOC_DATA = {
    "WMT": {"cases": 8, "settlements_m": 86, "types": ["gender", "disability", "race"]},
    "AMZN": {"cases": 5, "settlements_m": 15, "types": ["race", "disability"]},
    "TSLA": {"cases": 3, "settlements_m": 137, "types": ["race", "harassment"]},
    "META": {"cases": 2, "settlements_m": 14, "types": ["age", "race"]},
    "GOOG": {"cases": 2, "settlements_m": 118, "types": ["gender", "race"]},
    "GOOGL": {"cases": 2, "settlements_m": 118, "types": ["gender", "race"]},
    "MSFT": {"cases": 1, "settlements_m": 3, "types": ["gender"]},
    "AAPL": {"cases": 1, "settlements_m": 0, "types": ["age"]},
    "JPM": {"cases": 3, "settlements_m": 24, "types": ["race", "gender"]},
    "BAC": {"cases": 4, "settlements_m": 39, "types": ["race", "gender"]},
    "GS": {"cases": 2, "settlements_m": 215, "types": ["gender"]},
    "UPS": {"cases": 3, "settlements_m": 12, "types": ["disability", "religion"]},
    "FDX": {"cases": 2, "settlements_m": 3, "types": ["disability"]},
}

def score_eeoc(ticker):
    data = EEOC_DATA.get(ticker.upper())
    if not data: return {"U.2_adj": 0, "M.3_adj": 0}
    
    cases = data.get("cases", 0)
    settlements = data.get("settlements_m", 0)
    
    # Penalty — more cases and bigger settlements = worse
    if settlements > 100: penalty = -20
    elif settlements > 50: penalty = -15
    elif settlements > 10: penalty = -10
    elif cases > 0: penalty = -5
    else: penalty = 0
    
    return {"U.2_adj": penalty, "M.3_adj": penalty}


# ═══════════════════════════════════════════════════════════════════════
# 26. USPTO Patent Analysis → H.3 + H.5
# ═══════════════════════════════════════════════════════════════════════

USPTO_API = "https://developer.uspto.gov/ibd-api/v1/application/publications"

def fetch_patents(company_name, ticker):
    cached = load_cache(ticker, "patents")
    if cached: return cached
    try:
        # Search recent patent publications
        params = {
            "searchText": f'assignee:("{company_name}")',
            "start": 0, "rows": 100,
        }
        r = requests.get(USPTO_API, params=params, timeout=15)
        if r.status_code != 200: return None
        
        data = r.json()
        results = data.get("results", [])
        
        # Classify patents as automation-related or human-centric
        ai_keywords = ["artificial intelligence", "machine learning", "neural network", 
                       "deep learning", "automation", "autonomous", "robot", "chatbot",
                       "natural language processing", "computer vision", "algorithmic"]
        human_keywords = ["ergonomic", "safety", "accessibility", "human interface",
                         "user experience", "health", "wellbeing", "sustainable"]
        
        ai_patents = 0
        human_patents = 0
        total = len(results)
        
        for patent in results:
            title = (patent.get("inventionTitle") or "").lower()
            abstract = (patent.get("abstractText") or [""])[0].lower() if patent.get("abstractText") else ""
            text = title + " " + abstract
            
            if any(kw in text for kw in ai_keywords):
                ai_patents += 1
            if any(kw in text for kw in human_keywords):
                human_patents += 1
        
        result = {
            "company": company_name, "ticker": ticker,
            "total_patents": total,
            "ai_patents": ai_patents,
            "human_patents": human_patents,
            "ai_ratio": round(ai_patents / max(total, 1), 3),
            "human_ratio": round(human_patents / max(total, 1), 3),
            "source": "USPTO", "fetched": datetime.now().isoformat()
        }
        save_cache(ticker, "patents", result)
        return result
    except Exception as e:
        print(f"  USPTO error: {e}")
        return None

def score_patents(data):
    if not data: return {"H.3_adj": 0, "H.5_adj": 0}
    
    ai_ratio = data.get("ai_ratio", 0)
    human_ratio = data.get("human_ratio", 0)
    
    # H.3: more human-centric patents = deeper human decision involvement
    h3_adj = round((human_ratio - ai_ratio) * 15, 1)  # -15 to +15
    
    # H.5: high AI patent ratio = displacement intent
    h5_adj = round(-ai_ratio * 20, 1)  # 0 to -20
    
    return {"H.3_adj": h3_adj, "H.5_adj": h5_adj}


# ═══════════════════════════════════════════════════════════════════════
# 27. FDA Warning Letters → M.4 Product Ethics
# ═══════════════════════════════════════════════════════════════════════

FDA_API = "https://api.fda.gov/drug/enforcement.json"

def fetch_fda(company_name, ticker):
    cached = load_cache(ticker, "fda")
    if cached: return cached
    try:
        params = {
            "search": f'recalling_firm:"{company_name}"',
            "limit": 100,
        }
        r = requests.get(FDA_API, params=params, timeout=15)
        if r.status_code != 200:
            # Try food enforcement
            r = requests.get("https://api.fda.gov/food/enforcement.json",
                           params=params, timeout=15)
        
        if r.status_code != 200:
            return {"company": company_name, "ticker": ticker, "recalls": 0, "class_i": 0, "source": "FDA"}
        
        data = r.json()
        results = data.get("results", [])
        
        class_i = sum(1 for rec in results if rec.get("classification") == "Class I")
        class_ii = sum(1 for rec in results if rec.get("classification") == "Class II")
        
        result = {
            "company": company_name, "ticker": ticker,
            "recalls": len(results), "class_i": class_i, "class_ii": class_ii,
            "source": "FDA", "fetched": datetime.now().isoformat()
        }
        save_cache(ticker, "fda", result)
        return result
    except Exception as e:
        print(f"  FDA error: {e}")
        return None

def score_fda(data):
    if not data: return None
    recalls = data.get("recalls", 0)
    class_i = data.get("class_i", 0)
    
    if recalls == 0: return 85
    elif class_i == 0 and recalls <= 3: return 70
    elif class_i <= 1: return 55
    elif class_i <= 3: return 40
    else: return 25


# ═══════════════════════════════════════════════════════════════════════
# 28. DOL Wage Violations → U.2 Worker Empathy
# ═══════════════════════════════════════════════════════════════════════

DOL_WHD_API = "https://enforcedata.dol.gov/api/whd_whisard"

def fetch_dol_wages(company_name, ticker):
    cached = load_cache(ticker, "dol")
    if cached: return cached
    try:
        params = {"trade_nm": company_name[:50], "limit": 100}
        r = requests.get(DOL_WHD_API, params=params, timeout=15)
        if r.status_code != 200: return None
        
        records = r.json() if isinstance(r.json(), list) else r.json().get("results", [])
        
        total_backwages = sum(float(rec.get("bw_atp_amt", 0) or 0) for rec in records)
        violations = len(records)
        
        result = {
            "company": company_name, "ticker": ticker,
            "violations": violations, "total_backwages": total_backwages,
            "source": "DOL", "fetched": datetime.now().isoformat()
        }
        save_cache(ticker, "dol", result)
        return result
    except Exception as e:
        print(f"  DOL error: {e}")
        return None

def score_dol(data):
    if not data: return None
    bw = data.get("total_backwages", 0)
    v = data.get("violations", 0)
    
    if v == 0: return 85
    elif bw < 100000 and v <= 3: return 70
    elif bw < 1000000: return 55
    elif bw < 10000000: return 40
    else: return 25


# ═══════════════════════════════════════════════════════════════════════
# 29. SEC DEF 14A Pay Ratios → M.3 + H.4
# ═══════════════════════════════════════════════════════════════════════

# CEO-to-median-worker pay ratios (from public proxy statements)
PAY_RATIOS = {
    "AAPL": 1447, "AMZN": 30, "GOOG": 21, "GOOGL": 21, "META": 176,
    "MSFT": 289, "TSLA": 11000, "NVDA": 222, "JPM": 241, "BAC": 190,
    "WMT": 933, "TGT": 648, "COST": 232, "HD": 491, "LOW": 399,
    "NKE": 731, "SBUX": 734, "MCD": 1745, "DIS": 658, "NFLX": 142,
    "CRM": 356, "INTC": 217, "AMD": 172, "CSCO": 167, "ORCL": 702,
    "V": 195, "MA": 273, "GS": 90, "MS": 215, "C": 399,
    "PFE": 268, "JNJ": 201, "UNH": 295, "ABT": 237, "MRK": 186,
    "XOM": 255, "CVX": 185, "COP": 159, "BA": 218, "LMT": 250,
    "KO": 387, "PEP": 312, "PG": 322, "UL": 146,
}

def score_pay_ratio(ticker):
    ratio = PAY_RATIOS.get(ticker.upper())
    if ratio is None: return {"M.3_adj": 0, "H.4_adj": 0}
    
    # Lower ratio = more equitable
    if ratio < 50: m3_adj = 10
    elif ratio < 150: m3_adj = 5
    elif ratio < 300: m3_adj = 0
    elif ratio < 500: m3_adj = -5
    elif ratio < 1000: m3_adj = -10
    else: m3_adj = -15
    
    # H.4 Accountability — extreme ratios suggest disconnected leadership
    h4_adj = m3_adj  # Same direction
    
    return {"M.3_adj": m3_adj, "H.4_adj": h4_adj, "ratio": ratio, "source": "SEC DEF 14A"}


# ═══════════════════════════════════════════════════════════════════════
# 30. BBB Complaints → U.1 Customer Empathy (complements CFPB)
# ═══════════════════════════════════════════════════════════════════════

# BBB ratings (curated from public BBB profiles — A+ to F)
BBB_RATINGS = {
    "AAPL": "A+", "MSFT": "A+", "GOOG": "A+", "GOOGL": "A+",
    "AMZN": "A+", "META": "D-", "TSLA": "F", "NFLX": "A+",
    "DIS": "A-", "COST": "A+", "WMT": "A+", "TGT": "A+",
    "NKE": "A+", "SBUX": "A+", "MCD": "A-", "KO": "A+",
    "PEP": "A+", "JPM": "A+", "BAC": "A+", "GS": "A+",
    "T": "B+", "VZ": "A+", "CMCSA": "B-", "TMUS": "A+",
    "PYPL": "A-", "SQ": "A+", "CRM": "A+",
}

BBB_SCORES = {"A+": 90, "A": 85, "A-": 80, "B+": 70, "B": 65, "B-": 60,
              "C+": 50, "C": 45, "C-": 40, "D+": 30, "D": 25, "D-": 20, "F": 10}

def score_bbb(ticker):
    rating = BBB_RATINGS.get(ticker.upper())
    if not rating: return None
    return BBB_SCORES.get(rating, 50)


# ═══════════════════════════════════════════════════════════════════════
# 31. SEC Form 4 Insider Trading → M.3 Market Ethics
# ═══════════════════════════════════════════════════════════════════════

SEC_EDGAR_BASE = "https://efts.sec.gov/LATEST/search-index?q="

# Known major insider trading flags (curated from public SEC filings)
INSIDER_FLAGS = {
    "TSLA": {"flag": True, "notes": "Elon Musk SEC settlement, repeated disclosure issues"},
    "META": {"flag": True, "notes": "Zuckerberg pre-earnings sales patterns"},
    "ORCL": {"flag": True, "notes": "Larry Ellison large programmatic sales"},
    "AMZN": {"flag": False, "notes": "Bezos 10b5-1 plan sales, standard"},
}

def score_insider(ticker):
    data = INSIDER_FLAGS.get(ticker.upper())
    if not data: return 0  # No flag = no adjustment
    if data.get("flag"): return -10
    return 0


# ═══════════════════════════════════════════════════════════════════════
# 32. GRI Sustainability Database → N.2 Environmental Reporting
# ═══════════════════════════════════════════════════════════════════════

# Companies known to report under GRI standards (curated from GRI database)
GRI_REPORTERS = {
    "AAPL": True, "MSFT": True, "GOOG": True, "GOOGL": True, "AMZN": True,
    "META": True, "TSLA": False, "NVDA": True, "JPM": True, "BAC": True,
    "WMT": True, "COST": True, "TGT": True, "NKE": True, "DIS": True,
    "KO": True, "PEP": True, "PG": True, "UL": True, "JNJ": True,
    "PFE": True, "UNH": False, "XOM": True, "CVX": True, "BA": True,
    "GS": True, "V": True, "MA": True, "SBUX": True, "MCD": True,
    "NFLX": False, "CRM": True, "INTC": True, "AMD": True,
}

def score_gri(ticker):
    reports = GRI_REPORTERS.get(ticker.upper())
    if reports is None: return 0  # Unknown = no adjustment
    return 10 if reports else -5  # Bonus for GRI reporting


# ═══════════════════════════════════════════════════════════════════════
# 33. SBTi Climate Commitments → A.1 Energy
# ═══════════════════════════════════════════════════════════════════════

# Companies with validated Science Based Targets (from public SBTi dashboard)
SBTI_STATUS = {
    "AAPL": "committed", "MSFT": "validated", "GOOG": "validated", "GOOGL": "validated",
    "AMZN": "committed", "META": "committed", "NVDA": "none", "TSLA": "none",
    "JPM": "committed", "BAC": "validated", "GS": "committed",
    "WMT": "validated", "COST": "none", "TGT": "validated",
    "NKE": "validated", "DIS": "committed", "KO": "validated", "PEP": "validated",
    "PG": "validated", "UL": "validated", "JNJ": "validated",
    "XOM": "none", "CVX": "none", "COP": "none",
    "SBUX": "validated", "MCD": "validated",
    "INTC": "validated", "AMD": "committed",
}

SBTI_SCORES = {"validated": 15, "committed": 8, "none": -5}

def score_sbti(ticker):
    status = SBTI_STATUS.get(ticker.upper())
    if status is None: return 0
    return SBTI_SCORES.get(status, 0)


# ═══════════════════════════════════════════════════════════════════════
# 34. IRS 990 / Charity Data → U.5 Moral Courage
# ═══════════════════════════════════════════════════════════════════════

# Known corporate foundation giving levels (from public 990 filings / corporate reports)
# Measured as % of pre-tax profit donated to charity
CHARITY_LEVELS = {
    "COST": "high",    # Costco — significant community investment
    "SBUX": "high",    # Starbucks Foundation
    "PG": "high",      # P&G — major disaster relief, community programs
    "JNJ": "high",     # J&J — healthcare access programs
    "MSFT": "high",    # Microsoft Philanthropies
    "GOOG": "high",    # Google.org
    "GOOGL": "high",
    "AAPL": "medium",  # Apple — matching gifts, education
    "WMT": "high",     # Walmart Foundation — largest corporate giver
    "KO": "high",      # Coca-Cola Foundation
    "NKE": "medium",   # Nike Community Impact
    "DIS": "medium",   # Disney VoluntEARS
    "AMZN": "low",     # Amazon — criticized for low giving ratio
    "META": "low",     # Meta — Chan Zuckerberg is personal, not corporate
    "TSLA": "none",    # Tesla — no notable corporate philanthropy
    "XOM": "medium",   # ExxonMobil Foundation
}

CHARITY_SCORES = {"high": 15, "medium": 5, "low": -5, "none": -10}

def score_charity(ticker):
    level = CHARITY_LEVELS.get(ticker.upper())
    if level is None: return 0
    return CHARITY_SCORES.get(level, 0)


# ═══════════════════════════════════════════════════════════════════════
# AGGREGATOR — Get all extended signals for a company
# ═══════════════════════════════════════════════════════════════════════

def fetch_all_extended(company_name, ticker, domain=None, industry=None):
    """Fetch all 12 extended data sources. Returns adjustment scores."""
    results = {}
    
    # API-based (may fail)
    print(f"  OSHA...")
    osha = fetch_osha(company_name, ticker)
    results["osha"] = {"score": score_osha(osha), "raw": osha, "source": "OSHA"}
    
    print(f"  USPTO...")
    patents = fetch_patents(company_name, ticker)
    results["patents"] = {**score_patents(patents), "raw": patents, "source": "USPTO"}
    
    print(f"  FDA...")
    fda = fetch_fda(company_name, ticker)
    results["fda"] = {"score": score_fda(fda), "raw": fda, "source": "FDA"}
    
    print(f"  DOL...")
    dol = fetch_dol_wages(company_name, ticker)
    results["dol"] = {"score": score_dol(dol), "raw": dol, "source": "DOL"}
    
    # Curated data (instant)
    results["ftc"] = {**score_ftc(fetch_ftc(company_name, ticker)), "source": "FTC"}
    results["eeoc"] = {**score_eeoc(ticker), "source": "EEOC"}
    results["pay_ratio"] = {**score_pay_ratio(ticker), "source": "SEC DEF 14A"}
    results["bbb"] = {"score": score_bbb(ticker), "source": "BBB"}
    results["insider"] = {"M.3_adj": score_insider(ticker), "source": "SEC Form 4"}
    results["gri"] = {"N.2_adj": score_gri(ticker), "source": "GRI"}
    results["sbti"] = {"A.1_adj": score_sbti(ticker), "source": "SBTi"}
    results["charity"] = {"U.5_adj": score_charity(ticker), "source": "IRS 990"}
    
    return results


def run_all(scores_file="data/scores/all_scores.json"):
    """Run all extended pipelines for all scored companies."""
    if not Path(scores_file).exists():
        print(f"No scores file at {scores_file}")
        return
    
    scores = json.load(open(scores_file))
    print(f"Running extended pipelines for {len(scores)} companies...")
    
    all_results = {}
    for i, company in enumerate(scores):
        name = company.get("company", "")
        ticker = company.get("ticker", "")
        if not ticker: continue
        
        print(f"[{i+1}/{len(scores)}] {name} ({ticker})")
        result = fetch_all_extended(name, ticker)
        all_results[ticker.upper()] = result
        time.sleep(0.3)
    
    output_file = DATA_DIR / "all_extended.json"
    json.dump(all_results, open(output_file, "w"), indent=2)
    print(f"\nSaved {len(all_results)} companies to {output_file}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="HI. Extended Pipelines (12 sources)")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--company", type=str)
    parser.add_argument("--ticker", type=str)
    args = parser.parse_args()
    
    if args.all:
        run_all()
    elif args.company and args.ticker:
        result = fetch_all_extended(args.company, args.ticker)
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Usage: python3 extended_pipelines.py --all")
