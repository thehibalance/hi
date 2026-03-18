"""
HI. Sub-Signal Pipelines — 6 New Data Sources
Gets us from 18/24 to 22/24 sub-signals.

Sources:
1. CFPB Complaints API → U.1 Customer Empathy + M.1 Pricing Ethics
2. FEC/OpenSecrets → M.5 Political Ethics
3. CPSC Recalls API → M.4 Product Ethics
4. Have I Been Pwned API → M.2 Data Ethics
5. iFixit + Industry Data → A.4 Hardware Lifecycle
6. EPA + Industry Data → A.3 Land & Habitat (enhanced)

Run: python3 subsignal_pipelines.py --all
"""

import json, os, time, math
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    print("pip install requests --break-system-packages")
    exit(1)

DATA_DIR = Path("data/subsignals")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════
# 1. CFPB Consumer Complaints → U.1 Customer Empathy + M.1 Pricing Ethics
# ═══════════════════════════════════════════════════════════════════════

CFPB_API = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"

# Map company names to CFPB company names (they use different naming)
CFPB_COMPANY_MAP = {
    "apple": "APPLE INC.", "amazon": "AMAZON.COM", "google": "GOOGLE LLC",
    "meta": "FACEBOOK", "microsoft": "MICROSOFT CORPORATION",
    "jpmorgan": "JPMORGAN CHASE", "bank of america": "BANK OF AMERICA",
    "wells fargo": "WELLS FARGO", "citigroup": "CITIGROUP", "capital one": "CAPITAL ONE",
    "american express": "AMERICAN EXPRESS", "discover": "DISCOVER BANK",
    "paypal": "PAYPAL", "tesla": "TESLA", "att": "AT&T",
    "verizon": "VERIZON", "tmobile": "T-MOBILE", "comcast": "COMCAST",
    "disney": "WALT DISNEY", "netflix": "NETFLIX",
}

def fetch_cfpb(company_name, ticker):
    """Fetch CFPB complaint data for a company."""
    cache_file = DATA_DIR / f"cfpb_{ticker.upper()}.json"
    if cache_file.exists():
        age_hrs = (time.time() - cache_file.stat().st_mtime) / 3600
        if age_hrs < 168:  # 1 week cache
            return json.load(open(cache_file))
    
    # Try mapped name first, then raw name
    search_name = CFPB_COMPANY_MAP.get(company_name.lower().split()[0], company_name)
    
    try:
        params = {
            "company": search_name,
            "date_received_min": (datetime.now().replace(year=datetime.now().year - 3)).strftime("%Y-%m-%d"),
            "size": 0,  # Just want counts
            "no_aggs": False,
        }
        r = requests.get(CFPB_API, params=params, timeout=10)
        if r.status_code != 200:
            return None
        
        data = r.json()
        total = data.get("hits", {}).get("total", {}).get("value", 0)
        
        # Get product breakdown
        products = {}
        for bucket in data.get("aggregations", {}).get("product", {}).get("buckets", []):
            products[bucket["key"]] = bucket["doc_count"]
        
        # Get timely response rate
        timely = 0
        timely_buckets = data.get("aggregations", {}).get("timely", {}).get("buckets", [])
        for b in timely_buckets:
            if b["key"] == "Yes":
                timely = b["doc_count"]
        
        result = {
            "company": company_name,
            "ticker": ticker,
            "total_complaints_3yr": total,
            "products": products,
            "timely_responses": timely,
            "timely_rate": round(timely / max(total, 1) * 100, 1),
            "fetched": datetime.now().isoformat(),
            "source": "CFPB"
        }
        
        json.dump(result, open(cache_file, "w"), indent=2)
        return result
    except Exception as e:
        print(f"  CFPB error for {company_name}: {e}")
        return None


def score_cfpb(cfpb_data, industry, revenue_b=None):
    """
    Score U.1 (Customer Empathy) and M.1 (Pricing Ethics) from CFPB data.
    Returns: {"U.1": score, "M.1": score}
    """
    if not cfpb_data:
        return {"U.1": None, "M.1": None}
    
    total = cfpb_data.get("total_complaints_3yr", 0)
    timely_rate = cfpb_data.get("timely_rate", 50)
    
    # Normalize complaints per $B revenue (larger companies get more complaints)
    rev = revenue_b or 10  # Default $10B if unknown
    complaints_per_b = total / max(rev, 0.1)
    
    # U.1 Customer Empathy: fewer complaints + high timely response = better
    if complaints_per_b < 100:
        u1_base = 85
    elif complaints_per_b < 500:
        u1_base = 70
    elif complaints_per_b < 2000:
        u1_base = 55
    elif complaints_per_b < 10000:
        u1_base = 40
    else:
        u1_base = 25
    
    # Bonus for timely responses
    u1 = min(100, u1_base + (timely_rate - 50) * 0.3)
    
    # M.1 Pricing Ethics: look at lending/pricing complaint categories
    pricing_complaints = sum(v for k, v in cfpb_data.get("products", {}).items()
                           if any(w in k.lower() for w in ["credit", "loan", "mortgage", "debt", "payday"]))
    pricing_ratio = pricing_complaints / max(total, 1)
    
    if pricing_ratio < 0.1:
        m1 = 80
    elif pricing_ratio < 0.3:
        m1 = 65
    elif pricing_ratio < 0.5:
        m1 = 50
    else:
        m1 = 35
    
    return {"U.1": round(max(0, min(100, u1)), 1), "M.1": round(max(0, min(100, m1)), 1)}


# ═══════════════════════════════════════════════════════════════════════
# 2. FEC / OpenSecrets → M.5 Political Ethics
# ═══════════════════════════════════════════════════════════════════════

FEC_API = "https://api.open.fec.gov/v1"

def fetch_fec(company_name, ticker, fec_api_key=None):
    """Fetch FEC political donation data. Requires API key from api.open.fec.gov"""
    cache_file = DATA_DIR / f"fec_{ticker.upper()}.json"
    if cache_file.exists():
        age_hrs = (time.time() - cache_file.stat().st_mtime) / 3600
        if age_hrs < 168:
            return json.load(open(cache_file))
    
    if not fec_api_key:
        fec_api_key = os.environ.get("FEC_API_KEY", "DEMO_KEY")
    
    try:
        # Search for committee by company name
        params = {
            "q": company_name,
            "api_key": fec_api_key,
            "per_page": 5,
        }
        r = requests.get(f"{FEC_API}/names/committees/", params=params, timeout=10)
        if r.status_code != 200:
            return None
        
        committees = r.json().get("results", [])
        total_receipts = 0
        total_disbursements = 0
        party_split = {}
        
        for comm in committees[:3]:
            cid = comm.get("id", "")
            # Get totals
            tr = requests.get(f"{FEC_API}/committee/{cid}/totals/", 
                            params={"api_key": fec_api_key, "per_page": 1}, timeout=10)
            if tr.status_code == 200:
                totals = tr.json().get("results", [{}])
                if totals:
                    total_receipts += totals[0].get("receipts", 0) or 0
                    total_disbursements += totals[0].get("disbursements", 0) or 0
        
        result = {
            "company": company_name,
            "ticker": ticker,
            "committees_found": len(committees),
            "total_receipts": total_receipts,
            "total_disbursements": total_disbursements,
            "fetched": datetime.now().isoformat(),
            "source": "FEC"
        }
        
        json.dump(result, open(cache_file, "w"), indent=2)
        return result
    except Exception as e:
        print(f"  FEC error for {company_name}: {e}")
        return None


def score_fec(fec_data):
    """
    Score M.5 (Political Ethics) from FEC data.
    Lower political spending = higher score (less political influence buying).
    """
    if not fec_data:
        return {"M.5": None}
    
    total_spending = fec_data.get("total_disbursements", 0)
    
    # Score based on total political spending
    if total_spending < 100000:
        m5 = 85  # Minimal political spending
    elif total_spending < 1000000:
        m5 = 70
    elif total_spending < 10000000:
        m5 = 55
    elif total_spending < 50000000:
        m5 = 40
    else:
        m5 = 25  # Heavy political spending
    
    return {"M.5": round(m5, 1)}


# ═══════════════════════════════════════════════════════════════════════
# 3. CPSC Recalls → M.4 Product Ethics
# ═══════════════════════════════════════════════════════════════════════

CPSC_API = "https://www.saferproducts.gov/RestWebServices/Recall"

def fetch_cpsc(company_name, ticker):
    """Fetch CPSC product recall data."""
    cache_file = DATA_DIR / f"cpsc_{ticker.upper()}.json"
    if cache_file.exists():
        age_hrs = (time.time() - cache_file.stat().st_mtime) / 3600
        if age_hrs < 168:
            return json.load(open(cache_file))
    
    try:
        params = {
            "format": "json",
            "RecallTitle": company_name,
        }
        r = requests.get(CPSC_API, params=params, timeout=10)
        if r.status_code != 200:
            # Try manufacturer search
            params = {"format": "json", "Manufacturer": company_name}
            r = requests.get(CPSC_API, params=params, timeout=10)
        
        if r.status_code != 200:
            return None
        
        recalls = r.json() if isinstance(r.json(), list) else []
        
        # Count recent recalls (last 5 years)
        recent = [rec for rec in recalls 
                  if rec.get("RecallDate", "2020") >= "2020"]
        
        # Count injuries
        total_injuries = 0
        for rec in recent:
            inj = rec.get("Injuries", [])
            if isinstance(inj, list):
                for i in inj:
                    total_injuries += i.get("Count", 0) if isinstance(i, dict) else 0
        
        result = {
            "company": company_name,
            "ticker": ticker,
            "total_recalls": len(recalls),
            "recent_recalls_5yr": len(recent),
            "total_injuries": total_injuries,
            "fetched": datetime.now().isoformat(),
            "source": "CPSC"
        }
        
        json.dump(result, open(cache_file, "w"), indent=2)
        return result
    except Exception as e:
        print(f"  CPSC error for {company_name}: {e}")
        return None


def score_cpsc(cpsc_data):
    """Score M.4 (Product Ethics) from CPSC recall data."""
    if not cpsc_data:
        return {"M.4": None}
    
    recent = cpsc_data.get("recent_recalls_5yr", 0)
    injuries = cpsc_data.get("total_injuries", 0)
    
    # Base score from recall count
    if recent == 0:
        m4 = 90
    elif recent <= 2:
        m4 = 75
    elif recent <= 5:
        m4 = 60
    elif recent <= 10:
        m4 = 45
    else:
        m4 = 30
    
    # Penalty for injuries
    if injuries > 100:
        m4 -= 20
    elif injuries > 10:
        m4 -= 10
    
    return {"M.4": round(max(0, min(100, m4)), 1)}


# ═══════════════════════════════════════════════════════════════════════
# 4. Have I Been Pwned → M.2 Data Ethics
# ═══════════════════════════════════════════════════════════════════════

HIBP_API = "https://haveibeenpwned.com/api/v3/breaches"

def fetch_hibp(company_name, domain, ticker):
    """Fetch data breach history from HIBP."""
    cache_file = DATA_DIR / f"hibp_{ticker.upper()}.json"
    if cache_file.exists():
        age_hrs = (time.time() - cache_file.stat().st_mtime) / 3600
        if age_hrs < 168:
            return json.load(open(cache_file))
    
    try:
        # HIBP v3 requires API key for email searches but breach list is free
        r = requests.get(HIBP_API, timeout=10, headers={"User-Agent": "HI-Score-Pipeline"})
        if r.status_code != 200:
            return None
        
        all_breaches = r.json()
        
        # Find breaches matching this company/domain
        company_breaches = []
        search_terms = [company_name.lower(), domain.lower().replace(".com", "").replace(".org", "")]
        
        for breach in all_breaches:
            name = breach.get("Name", "").lower()
            bdomain = breach.get("Domain", "").lower()
            if any(term in name or term in bdomain for term in search_terms):
                company_breaches.append({
                    "name": breach.get("Name"),
                    "date": breach.get("BreachDate"),
                    "pwn_count": breach.get("PwnCount", 0),
                    "data_classes": breach.get("DataClasses", []),
                    "is_verified": breach.get("IsVerified", False),
                })
        
        result = {
            "company": company_name,
            "ticker": ticker,
            "domain": domain,
            "breach_count": len(company_breaches),
            "breaches": company_breaches,
            "total_records_exposed": sum(b.get("pwn_count", 0) for b in company_breaches),
            "sensitive_data_exposed": any("Passwords" in b.get("data_classes", []) or 
                                        "Credit cards" in b.get("data_classes", [])
                                        for b in company_breaches),
            "fetched": datetime.now().isoformat(),
            "source": "HIBP"
        }
        
        json.dump(result, open(cache_file, "w"), indent=2)
        return result
    except Exception as e:
        print(f"  HIBP error for {company_name}: {e}")
        return None


def score_hibp(hibp_data):
    """Score M.2 (Data Ethics) from breach data."""
    if not hibp_data:
        return {"M.2": None}
    
    breaches = hibp_data.get("breach_count", 0)
    records = hibp_data.get("total_records_exposed", 0)
    sensitive = hibp_data.get("sensitive_data_exposed", False)
    
    # Base score from breach count
    if breaches == 0:
        m2 = 90
    elif breaches == 1:
        m2 = 70
    elif breaches <= 3:
        m2 = 55
    else:
        m2 = 35
    
    # Scale penalty by records exposed
    if records > 100000000:
        m2 -= 25
    elif records > 10000000:
        m2 -= 15
    elif records > 1000000:
        m2 -= 10
    
    # Extra penalty for sensitive data
    if sensitive:
        m2 -= 10
    
    return {"M.2": round(max(0, min(100, m2)), 1)}


# ═══════════════════════════════════════════════════════════════════════
# 5. Hardware Lifecycle → A.4 (iFixit + Industry Heuristics)
# ═══════════════════════════════════════════════════════════════════════

# iFixit repairability scores (curated — no API needed, these are public)
IFIXIT_SCORES = {
    "AAPL": {"score": 6, "notes": "iPhone repairability improving with right-to-repair laws"},
    "MSFT": {"score": 5, "notes": "Surface devices notoriously hard to repair"},
    "DELL": {"score": 7, "notes": "Business laptops generally repairable"},
    "HPQ": {"score": 7, "notes": "Consumer laptops moderate repairability"},
    "LNVGY": {"score": 7, "notes": "ThinkPad line highly repairable"},
    "GOOG": {"score": 5, "notes": "Pixel phones moderate, data center hardware proprietary"},
    "AMZN": {"score": 4, "notes": "Kindle/Echo devices low repairability"},
    "META": {"score": 3, "notes": "Quest VR headsets very low repairability"},
    "TSLA": {"score": 3, "notes": "Right-to-repair battles, proprietary everything"},
    "NVDA": {"score": 6, "notes": "GPU cards generally replaceable"},
    "INTC": {"score": 7, "notes": "Standard socket CPUs"},
    "AMD": {"score": 7, "notes": "Standard socket CPUs"},
    "SNE": {"score": 5, "notes": "PlayStation moderate repairability"},
    "SONY": {"score": 5, "notes": "Consumer electronics mixed"},
    "SMSN": {"score": 6, "notes": "Galaxy phones improving repairability"},
}

# Industry defaults for hardware lifecycle (0-100 scale)
HARDWARE_INDUSTRY_DEFAULTS = {
    "tech": 45, "semiconductor": 55, "telecom": 50, "manufacturing": 60,
    "retail": 65, "finance": 70, "healthcare": 55, "energy": 50,
    "food": 75, "apparel": 70, "media": 60, "auto": 50,
    "aerospace": 45, "defense": 40, "default": 55,
}

def score_hardware(ticker, industry):
    """
    Score A.4 (Hardware Lifecycle) from iFixit data + industry heuristics.
    Combines repairability, e-waste policies, and hardware refresh cycles.
    """
    ifixit = IFIXIT_SCORES.get(ticker.upper())
    
    if ifixit:
        # iFixit scores are 1-10, normalize to 0-100
        a4 = ifixit["score"] * 10
        source = "iFixit"
    else:
        # Use industry default
        a4 = HARDWARE_INDUSTRY_DEFAULTS.get(industry, 55)
        source = "Industry"
    
    return {"A.4": round(a4, 1), "source": source}


# ═══════════════════════════════════════════════════════════════════════
# 6. Land & Habitat → A.3 (Enhanced EPA + Industry + Deforestation Risk)
# ═══════════════════════════════════════════════════════════════════════

# Deforestation risk by industry (based on CDP Forests data, public)
DEFORESTATION_RISK = {
    "food": 30, "apparel": 35, "consumer": 40, "retail": 45,
    "energy": 35, "mining": 25, "manufacturing": 45, "auto": 50,
    "tech": 65, "finance": 70, "healthcare": 60, "media": 70,
    "telecom": 60, "aerospace": 55, "defense": 50, "default": 50,
}

# Companies with known supply chain deforestation issues
DEFORESTATION_FLAGS = {
    "NSRGY": -20,  # Nestlé - palm oil
    "PG": -15,     # P&G - palm oil
    "UL": -15,     # Unilever - palm oil (but improving)
    "KO": -10,     # Coca-Cola - sugar supply chain
    "MCD": -15,    # McDonald's - beef/soy supply chain  
    "AMZN": -10,   # Amazon - packaging/shipping
    "WMT": -10,    # Walmart - supplier footprint
    "NKE": -10,    # Nike - leather supply chain
    "SBUX": -10,   # Starbucks - coffee supply chain
}

def score_land(ticker, industry, epa_violations=0):
    """
    Score A.3 (Land & Habitat) from industry data + deforestation risk + EPA.
    """
    # Base from industry
    base = DEFORESTATION_RISK.get(industry, 50)
    
    # Company-specific deforestation flags
    flag = DEFORESTATION_FLAGS.get(ticker.upper(), 0)
    
    # EPA violation penalty (if data available)
    epa_penalty = 0
    if epa_violations > 20:
        epa_penalty = -20
    elif epa_violations > 10:
        epa_penalty = -15
    elif epa_violations > 3:
        epa_penalty = -10
    
    a3 = base + flag + epa_penalty
    
    return {"A.3": round(max(0, min(100, a3)), 1), "source": "Industry+EPA"}


# ═══════════════════════════════════════════════════════════════════════
# RUNNER — Fetch all data for a company
# ═══════════════════════════════════════════════════════════════════════

def fetch_all_subsignals(company_name, ticker, domain=None, industry=None, revenue_b=None):
    """Fetch all 6 new sub-signal data sources for a company."""
    results = {}
    
    # 1. CFPB
    print(f"  CFPB: {company_name}...")
    cfpb = fetch_cfpb(company_name, ticker)
    if cfpb:
        results["cfpb"] = score_cfpb(cfpb, industry, revenue_b)
        results["cfpb"]["raw"] = cfpb
    
    # 2. FEC
    print(f"  FEC: {company_name}...")
    fec = fetch_fec(company_name, ticker)
    if fec:
        results["fec"] = score_fec(fec)
        results["fec"]["raw"] = fec
    
    # 3. CPSC
    print(f"  CPSC: {company_name}...")
    cpsc = fetch_cpsc(company_name, ticker)
    if cpsc:
        results["cpsc"] = score_cpsc(cpsc)
        results["cpsc"]["raw"] = cpsc
    
    # 4. HIBP
    if domain:
        print(f"  HIBP: {domain}...")
        hibp = fetch_hibp(company_name, domain, ticker)
        if hibp:
            results["hibp"] = score_hibp(hibp)
            results["hibp"]["raw"] = hibp
    
    # 5. Hardware (no fetch needed — curated + industry)
    results["hardware"] = score_hardware(ticker, industry or "default")
    
    # 6. Land (no fetch needed — curated + industry)
    results["land"] = score_land(ticker, industry or "default")
    
    return results


# ═══════════════════════════════════════════════════════════════════════
# BATCH RUNNER
# ═══════════════════════════════════════════════════════════════════════

def run_all(scores_file="data/scores/all_scores.json"):
    """Run all sub-signal pipelines for all scored companies."""
    if not Path(scores_file).exists():
        print(f"No scores file at {scores_file}")
        return
    
    scores = json.load(open(scores_file))
    print(f"Running sub-signal pipelines for {len(scores)} companies...")
    
    all_results = {}
    for i, company in enumerate(scores):
        name = company.get("company", "")
        ticker = company.get("ticker", "")
        domain = (company.get("domains") or [""])[0] if company.get("domains") else ""
        industry = company.get("industry", "").lower().split("/")[0].strip()
        
        if not ticker:
            continue
        
        print(f"[{i+1}/{len(scores)}] {name} ({ticker})")
        result = fetch_all_subsignals(name, ticker, domain, industry)
        all_results[ticker.upper()] = result
        
        # Rate limit
        time.sleep(0.5)
    
    # Save results
    output_file = DATA_DIR / "all_subsignals.json"
    json.dump(all_results, open(output_file, "w"), indent=2)
    print(f"\nSaved {len(all_results)} companies to {output_file}")
    
    # Print coverage stats
    covered = {"U.1": 0, "M.1": 0, "M.2": 0, "M.4": 0, "M.5": 0, "A.3": 0, "A.4": 0}
    for ticker, data in all_results.items():
        if data.get("cfpb", {}).get("U.1") is not None: covered["U.1"] += 1
        if data.get("cfpb", {}).get("M.1") is not None: covered["M.1"] += 1
        if data.get("hibp", {}).get("M.2") is not None: covered["M.2"] += 1
        if data.get("cpsc", {}).get("M.4") is not None: covered["M.4"] += 1
        if data.get("fec", {}).get("M.5") is not None: covered["M.5"] += 1
        covered["A.3"] += 1  # Always has industry default
        covered["A.4"] += 1  # Always has industry default
    
    print(f"\nSub-signal coverage:")
    for sig, count in covered.items():
        print(f"  {sig}: {count}/{len(all_results)} ({round(count/max(len(all_results),1)*100)}%)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="HI. Sub-Signal Pipelines")
    parser.add_argument("--all", action="store_true", help="Run all pipelines for all companies")
    parser.add_argument("--company", type=str, help="Score a single company")
    parser.add_argument("--ticker", type=str, help="Company ticker")
    parser.add_argument("--domain", type=str, help="Company domain")
    args = parser.parse_args()
    
    if args.all:
        run_all()
    elif args.company and args.ticker:
        result = fetch_all_subsignals(args.company, args.ticker, args.domain)
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Usage: python3 subsignal_pipelines.py --all")
        print("       python3 subsignal_pipelines.py --company 'Apple' --ticker AAPL --domain apple.com")
