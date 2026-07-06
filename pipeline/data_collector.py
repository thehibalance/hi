#!/usr/bin/env python3
"""
HI. Data Collector — All 34 Sources in One Command
Fetches fresh data from all free/public/government APIs.

Usage:
  python3 data_collector.py --all                    # Fetch everything
  python3 data_collector.py --core                   # Core 6 only (SEC, EPA, BLS, CDP, Jobs, Glassdoor)
  python3 data_collector.py --subsignals             # 6 subsignal sources
  python3 data_collector.py --extended               # 12 extended sources
  python3 data_collector.py --company "Apple Inc"    # Single company

API Keys (put in data/ directory or set env vars):
  - FINNHUB_KEY: finnhub.io (free 60 calls/min)
  - FMP_KEY: financialmodelingprep.com (free 250 calls/day)
  - ALPHA_VANTAGE_KEY: alphavantage.co (free 25 calls/day)
  - FRED_KEY: fred.stlouisfed.org (free)
  - NEWSAPI_KEY: newsapi.org (free 100 calls/day)
"""

import json, os, time, re, math, sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

try:
    import requests
except ImportError:
    print("pip install requests --break-system-packages")
    sys.exit(1)

DATA_DIR = Path("data")
RATE_LIMIT_PAUSE = 0.3  # seconds between API calls


def load_key(name):
    """Load API key. Env vars preferred (checks 3 naming conventions), files as fallback."""
    base = name.upper().replace(".", "_")
    # Try env vars: FINNHUB_API_KEY, FINNHUB_KEY, FINNHUB
    for env_name in [f"{base}_API_KEY", f"{base}_KEY", base]:
        if os.environ.get(env_name):
            return os.environ[env_name]
    # Fall back to files (for local dev)
    for path in [DATA_DIR / f"{name}_key.txt", DATA_DIR / f"{name}.txt", Path(f"{name}_key.txt")]:
        if path.exists():
            return path.read_text().strip()
    return None


def safe_get(url, params=None, headers=None, timeout=15, _retry_count=0):
    """Rate-limited GET with bounded retry.
    
    Previously had an infinite retry loop on 429 that could deadlock threads
    when a daily quota was exhausted. Now caps at 2 retries total, then returns
    None and lets the caller fall back gracefully.
    """
    time.sleep(RATE_LIMIT_PAUSE)
    try:
        r = requests.get(url, params=params, headers=headers, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 429:
            if _retry_count >= 2:
                # Give up and let caller handle None — don't block the thread forever
                return None
            print(f"    Rate limited, waiting 15s (retry {_retry_count + 1}/2)...")
            time.sleep(15)
            return safe_get(url, params, headers, timeout, _retry_count + 1)
        else:
            return None
    except Exception as e:
        return None


def load_company_list():
    """Load master company list from scores + universe tickers."""
    companies = []
    seen_tickers = set()
    
    # Load existing scores first
    scores_file = DATA_DIR / "scores" / "all_scores.json"
    if scores_file.exists():
        scores = json.load(open(scores_file))
        for s in scores:
            if s.get("error"):
                continue
            t = s.get("ticker", "").upper()
            companies.append({
                "name": s.get("company", ""),
                "ticker": s.get("ticker", ""),
                "industry": s.get("industry", ""),
                "sic": s.get("sic", ""),
                "domains": s.get("domains", []),
            })
            if t:
                seen_tickers.add(t)
    
    # v1.2.0 fix: build a ticker→name lookup from authoritative sources before
    # iterating universe tickers. This ensures we never pass an empty name to
    # fetch_sec(), which previously caused 353 ghost records (empty company
    # field in SEC aggregate) that scoring engine silently dropped.
    name_lookup = {}

    # Primary source: sp500_companies.SP500 — (ticker, name) tuples for full S&P 500
    try:
        from sp500_companies import SP500 as _SP500
        for _t, _n in _SP500:
            if _t and _n:
                name_lookup[_t.upper()] = _n
    except ImportError:
        pass

    # ADR fallback: major foreign filers not in sp500_companies (different SEC filing format)
    # v1.2.0 final polish: extended with UK/Asian/Indian ADRs that audit found missing
    ADR_NAMES = {
        # Asia/Pacific
        "TSM":  "Taiwan Semiconductor Manufacturing Company Limited",
        "BABA": "Alibaba Group Holding Limited",
        "PDD":  "PDD Holdings Inc.",
        "JD":   "JD.com, Inc.",
        "NTES": "NetEase, Inc.",
        "BIDU": "Baidu, Inc.",
        "TCOM": "Trip.com Group Limited",
        "TM":   "Toyota Motor Corporation",
        "SONY": "Sony Group Corporation",
        "SHOP": "Shopify Inc.",
        "SE":   "Sea Limited",
        # Indian ADRs
        "INFY": "Infosys Limited",
        "HDB":  "HDFC Bank Limited",
        "WIT":  "Wipro Limited",
        # European ADRs
        "ASML": "ASML Holding N.V.",
        "SAP":  "SAP SE",
        "STM":  "STMicroelectronics N.V.",
        "NVO":  "Novo Nordisk A/S",
        "NVS":  "Novartis AG",
        "BUD":  "Anheuser-Busch InBev SA/NV",
        # UK ADRs
        "AZN":  "AstraZeneca plc",
        "GSK":  "GSK plc",
        "SHEL": "Shell plc",
        "BP":   "BP p.l.c.",
        "BTI":  "British American Tobacco p.l.c.",
        "DEO":  "Diageo plc",
        "UL":   "Unilever PLC",
        "VOD":  "Vodafone Group Plc",
        "LYG":  "Lloyds Banking Group plc",
        "BCS":  "Barclays PLC",
        "NWG":  "NatWest Group plc",
        "WPP":  "WPP plc",
        "HSBC": "HSBC Holdings plc",
        # Australian/Mining
        "BHP":  "BHP Group Limited",
        "RIO":  "Rio Tinto plc",
        # North American
        "TD":   "Toronto-Dominion Bank",
        "RY":   "Royal Bank of Canada",
    }
    for _t, _n in ADR_NAMES.items():
        if _t not in name_lookup:
            name_lookup[_t] = _n

    # Add universe tickers not already in scores
    try:
        from universe_tickers import get_all_tickers
        universe = get_all_tickers()
        new_count = 0
        unresolved_count = 0
        for ticker in universe:
            if ticker.upper() not in seen_tickers:
                # v1.2.0: lookup authoritative name; empty only if truly unknown
                resolved_name = name_lookup.get(ticker.upper(), "")
                if not resolved_name:
                    unresolved_count += 1
                companies.append({
                    "name": resolved_name,  # populated from sp500_companies + ADR fallback
                    "ticker": ticker,
                    "industry": "",
                    "sic": "",
                    "domains": [],
                })
                seen_tickers.add(ticker.upper())
                new_count += 1
        if new_count:
            print(f"  Universe tickers: {new_count} new tickers added (total: {len(companies)})")
        if unresolved_count:
            print(f"    ⚠ {unresolved_count} of those have no name in sp500_companies or ADR_NAMES — SEC will try to resolve at fetch time")
    except ImportError:
        print("  No universe_tickers.py found, using existing scores only.")

    # Also backfill any name='' entries that came from existing scores
    backfilled = 0
    for c in companies:
        if not c.get("name") and c.get("ticker"):
            resolved = name_lookup.get(c["ticker"].upper(), "")
            if resolved:
                c["name"] = resolved
                backfilled += 1
    if backfilled:
        print(f"  Name backfill: {backfilled} companies got names from sp500_companies/ADR list")
    
    if not companies:
        print("  No existing scores or universe tickers found.")
    
    return companies


# ═══════════════════════════════════════════════════════════════════════
# SOURCE 1: SEC EDGAR (free, no key, 10 req/sec)
# ═══════════════════════════════════════════════════════════════════════

SEC_HEADERS = {"User-Agent": "HI Score Bot hi@thehibalance.org", "Accept": "application/json"}

# Module-level circuit breaker flag for Finnhub daily quota exhaustion.
# When True, fetch_finnhub short-circuits to (None, None) without network calls.
_FINNHUB_EXHAUSTED = False

def fetch_sec(company_name, ticker):
    """Fetch SEC EDGAR data: 10-K headcount, revenue, R&D, filings."""
    if not ticker:
        return None
    
    result = {"company": company_name, "ticker": ticker}
    
    # Get CIK from ticker
    try:
        r = requests.get(f"https://efts.sec.gov/LATEST/search-index?q={ticker}&dateRange=custom&startdt=2020-01-01&forms=10-K",
                        headers=SEC_HEADERS, timeout=10)
        # Try company tickers endpoint
        tickers_url = "https://efts.sec.gov/LATEST/search-index?q=\"{}\"&forms=10-K".format(ticker)
    except:
        pass
    
    # EDGAR full-text search for recent 10-K
    try:
        search = safe_get(
            "https://efts.sec.gov/LATEST/search-index",
            params={"q": f'"{ticker}"', "forms": "10-K", "dateRange": "custom",
                    "startdt": "2023-01-01", "enddt": datetime.now().strftime("%Y-%m-%d")},
            headers=SEC_HEADERS
        )
    except:
        search = None
    
    # Get company facts (structured data)
    try:
        # First get CIK
        ticker_map = safe_get("https://www.sec.gov/files/company_tickers.json", headers=SEC_HEADERS)
        cik = None
        if ticker_map:
            # v1.2.0 fix: SEC uses HYPHEN for class shares (BRK-B, BF-B) while
            # everyone else uses DOT (BRK.B, BF.B). Try both forms in lookup.
            ticker_upper = ticker.upper()
            ticker_hyphen = ticker_upper.replace(".", "-")
            for entry in ticker_map.values():
                entry_ticker = entry.get("ticker", "").upper()
                if entry_ticker == ticker_upper or entry_ticker == ticker_hyphen:
                    cik = str(entry["cik_str"]).zfill(10)
                    result["company"] = entry.get("title", company_name)
                    break
        
        if cik:
            facts = safe_get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", headers=SEC_HEADERS)
            if facts:
                us_gaap = facts.get("facts", {}).get("us-gaap", {})
                
                # Revenue
                rev_data = us_gaap.get("Revenues", us_gaap.get("RevenueFromContractWithCustomerExcludingAssessedTax", {}))
                rev_units = rev_data.get("units", {}).get("USD", [])
                annual_revs = [r for r in rev_units if r.get("form") == "10-K" and r.get("fy", 0) >= 2022]
                if annual_revs:
                    latest_rev = sorted(annual_revs, key=lambda x: x.get("fy", 0), reverse=True)[0]
                    result["revenue"] = latest_rev.get("val", 0)
                
                # Headcount (NumberOfEmployees)
                emp_data = us_gaap.get("EntityNumberOfEmployees", us_gaap.get("NumberOfEmployees", {}))
                if not emp_data:
                    # Try dei namespace
                    emp_data = facts.get("facts", {}).get("dei", {}).get("EntityNumberOfEmployees", {})
                emp_units = emp_data.get("units", {}).get("pure", emp_data.get("units", {}).get("employee", []))
                annual_emp = [e for e in emp_units if e.get("form") == "10-K" and e.get("fy", 0) >= 2021]
                if annual_emp:
                    sorted_emp = sorted(annual_emp, key=lambda x: x.get("fy", 0), reverse=True)
                    result["headcount"] = {"value": sorted_emp[0].get("val", 0)}
                    if len(sorted_emp) >= 2:
                        prev = float(sorted_emp[1].get("val", 0) or 0)
                        curr = float(sorted_emp[0].get("val", 0) or 0)
                        if prev > 0:
                            result["headcount_change_pct"] = round((curr - prev) / prev * 100, 1)
                
                # R&D
                rd_data = us_gaap.get("ResearchAndDevelopmentExpense", {})
                rd_units = rd_data.get("units", {}).get("USD", [])
                annual_rd = [r for r in rd_units if r.get("form") == "10-K" and r.get("fy", 0) >= 2022]
                if annual_rd:
                    result["rd_expense"] = sorted(annual_rd, key=lambda x: x.get("fy", 0), reverse=True)[0].get("val", 0)
                
                # Compute derived signals
                rev = float(result.get("revenue", 0) or 0)
                hc = float(result.get("headcount", {}).get("value", 0) if isinstance(result.get("headcount"), dict) else result.get("headcount", 0) or 0)
                rd = float(result.get("rd_expense", 0) or 0)
                
                if hc > 0 and rev > 0:
                    result["revenue_per_employee"] = round(rev / hc)
                if hc > 0 and rd > 0:
                    result["rd_per_employee"] = round(rd / hc)
                    if rev > 0:
                        result["displacement_signal"] = round((rd / rev * 100) - (hc / (rev / 200000)) * 5, 1)
                
                # Filing count
                filings = safe_get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=SEC_HEADERS)
                if filings:
                    recent = filings.get("filings", {}).get("recent", {})
                    forms = recent.get("form", [])
                    dates = recent.get("filingDate", [])
                    cutoff = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
                    recent_count = sum(1 for d in dates if d >= cutoff)
                    result["total_recent_filings"] = recent_count
                    result["category"] = filings.get("category", "")
                    result["sic"] = filings.get("sic", "")
                    result["sic_description"] = filings.get("sicDescription", "")
    except Exception as e:
        pass
    
    if len(result) <= 2:
        return None
    
    # Structure for scoring engine
    return {
        "company": company_name, "ticker": ticker,
        "h_signals": {
            "revenue_per_employee": result.get("revenue_per_employee"),
            "headcount": result.get("headcount"),
            "headcount_change_pct": result.get("headcount_change_pct"),
            "displacement_signal": result.get("displacement_signal"),
            "rd_per_employee": result.get("rd_per_employee"),
        },
        "m_signals": {
            "litigation": {"value": 0},
            "rd_expense": result.get("rd_expense", 0),
            "revenue": result.get("revenue", 0),  # Stored so downstream merge can compute RPE
        },
        "n_signals": {
            "total_recent_filings": result.get("total_recent_filings", 0),
            "category": result.get("category", ""),
            "sic": result.get("sic", ""),
            "sic_description": result.get("sic_description", ""),
        },
        "u_signals": {},
        "a_signals": {},
    }


# ═══════════════════════════════════════════════════════════════════════
# SOURCE 2: EPA ECHO (free, no key)
# ═══════════════════════════════════════════════════════════════════════

def fetch_epa(company_name, ticker):
    """Fetch EPA ECHO data: violations, penalties, inspections."""
    clean_name = company_name.split(",")[0].split("(")[0].strip()
    data = safe_get("https://echodata.epa.gov/echo/dfr_rest_services.get_facility_info",
                    params={"p_fn": clean_name, "output": "JSON"})
    if not data:
        return None
    
    facilities = data.get("Results", {}).get("FacilityInfo", [])
    if not facilities:
        return None
    
    total_violations = 0
    total_penalties = 0
    total_inspections = 0
    
    for f in facilities[:5]:  # Top 5 facilities
        total_violations += int(f.get("CurrVioStatus", "0") or "0") if f.get("CurrVioStatus", "").isdigit() else (1 if f.get("CurrVioStatus") == "Y" else 0)
        total_inspections += int(f.get("InspCount", "0") or "0")
    
    return {
        "company": company_name, "ticker": ticker,
        "a_signals": {
            "total_violations_3yr": total_violations,
            "total_inspections": total_inspections,
            "facility_count": len(facilities),
        },
        "m_signals": {
            "total_penalties": total_penalties,
            "formal_actions": total_violations,
        },
    }


# ═══════════════════════════════════════════════════════════════════════
# SOURCE 3: BLS (free, no key for public data)
# ═══════════════════════════════════════════════════════════════════════

def fetch_bls_benchmarks():
    """Fetch BLS industry benchmarks (run once, not per-company)."""
    benchmarks = {}
    # Use pre-compiled industry data
    # BLS API is series-based, not company-based
    # We use industry averages for normalization
    benchmarks = {
        "Technology": {"avg_wage": 120000, "employment_growth": 3.2},
        "Retail": {"avg_wage": 35000, "employment_growth": -1.1},
        "Healthcare": {"avg_wage": 75000, "employment_growth": 5.8},
        "Financial Services": {"avg_wage": 95000, "employment_growth": 1.5},
        "Manufacturing": {"avg_wage": 55000, "employment_growth": -0.8},
        "Energy": {"avg_wage": 85000, "employment_growth": -2.1},
        "Consumer Goods": {"avg_wage": 45000, "employment_growth": 0.3},
        "Telecommunications": {"avg_wage": 80000, "employment_growth": -1.5},
    }
    return benchmarks


# ═══════════════════════════════════════════════════════════════════════
# SOURCE 4-5: Finnhub (ESG + News + Glassdoor proxy)
# ═══════════════════════════════════════════════════════════════════════

def fetch_finnhub(ticker, finnhub_key):
    """Fetch Finnhub ESG scores. Returns (esg, None).
    
    Note: Previously returned a fake Glassdoor proxy with hardcoded 3.5/3.3/70
    ratings, which was a stub that was never completed. The scoring engine
    already detects this proxy signature and clears it (score_u_dimension
    lines 355-359), so removing it here is a no-op on actual scores but:
      1. Saves Finnhub API quota (free tier = 60 calls/min + daily cap)
      2. Eliminates misleading fake data in raw SEC records
      3. Makes the U dimension's fallback to CFPB/DEI/industry defaults
         explicit instead of going through a scoring-engine workaround
    
    Circuit breaker: once a 429 is observed, subsequent calls short-circuit
    to (None, None) without attempting the network call. This prevents the
    collection from wasting hours retrying an exhausted daily quota.
    
    Real Glassdoor replacement (paid Finnhub tier, Comparably, Indeed scraping,
    or equivalent) is a post-launch v1.1 task.
    """
    global _FINNHUB_EXHAUSTED
    if _FINNHUB_EXHAUSTED:
        return None, None
    if not finnhub_key or not ticker:
        return None, None
    
    # ESG scores — real data, keep
    esg = safe_get(f"https://finnhub.io/api/v1/stock/esg", params={"symbol": ticker, "token": finnhub_key})
    
    # If the ESG call returned None AND we haven't already tripped the breaker,
    # it might be a rate-limit. Verify with a cheap HEAD check before tripping.
    if esg is None:
        try:
            import requests
            r = requests.head(f"https://finnhub.io/api/v1/stock/esg",
                              params={"symbol": ticker, "token": finnhub_key}, timeout=5)
            if r.status_code == 429:
                _FINNHUB_EXHAUSTED = True
                print(f"    ⚠ Finnhub daily quota exhausted — skipping for rest of run")
        except Exception:
            pass
    
    return esg, None


# ═══════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════
# SOURCE 6-8: Yahoo/FMP/Alpha Vantage (financial data)
# ═══════════════════════════════════════════════════════════════════════

def fetch_fmp(ticker, fmp_key):
    """Fetch FMP financial data.
    
    Note: FMP deprecated /api/v3/profile/{ticker} in August 2025.
    Now uses /stable/profile?symbol={ticker} which returns the same fields.
    """
    if not fmp_key or not ticker:
        return None
    data = safe_get(f"https://financialmodelingprep.com/stable/profile",
                    params={"symbol": ticker, "apikey": fmp_key})
    if data and isinstance(data, list) and len(data) > 0:
        p = data[0]
        return {
            "market_cap": p.get("marketCap", 0),
            "employees": p.get("fullTimeEmployees", 0),
            "industry": p.get("industry", ""),
            "sector": p.get("sector", ""),
            "price": p.get("price", 0),
        }
    return None


def fetch_yfinance(ticker):
    """Fetch headcount + revenue from Yahoo Finance via yfinance library.
    
    Free, no API key, no rate limits as aggressive as FMP. Reliably returns
    fullTimeEmployees and totalRevenue for the vast majority of US listed
    companies. This is the primary fallback when SEC XBRL doesn't have
    employee data (which is most companies — SEC tagging is voluntary).
    """
    if not ticker:
        return None
    try:
        import yfinance as yf
    except ImportError:
        # yfinance not installed; caller will fall back to other sources
        return None
    
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        employees = info.get("fullTimeEmployees")
        revenue = info.get("totalRevenue")
        
        # Only return a result if we have at least one useful field
        if employees or revenue:
            return {
                "employees": employees if employees else None,
                "revenue": revenue if revenue else None,
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
            }
    except Exception:
        # yfinance can throw various errors (network, parsing, ticker not found)
        # Silently return None and let caller try other sources
        pass
    return None


# ═══════════════════════════════════════════════════════════════════════
# SOURCE 9-10: CDP + DEI/HRC (public indices)
# ═══════════════════════════════════════════════════════════════════════

# CDP and DEI/HRC are published as annual reports — we maintain curated data
# These are loaded from existing data files if available

def load_cdp_data():
    """Load CDP climate scores from curated data."""
    cdp_file = DATA_DIR / "cdp" / "all_companies.json"
    if cdp_file.exists():
        return json.load(open(cdp_file))
    return []

def load_dei_hrc_data():
    """Load DEI/HRC inclusion indices from curated data."""
    dei_file = DATA_DIR / "dei" / "all_companies.json"
    hrc_file = DATA_DIR / "hrc" / "all_companies.json"
    dei = json.load(open(dei_file)) if dei_file.exists() else []
    hrc = json.load(open(hrc_file)) if hrc_file.exists() else []
    return dei, hrc


# ═══════════════════════════════════════════════════════════════════════
# SOURCE 11-14: NewsAPI + Layoffs + WARN + CEO signals
# ═══════════════════════════════════════════════════════════════════════

def fetch_news(company_name, newsapi_key):
    """Fetch recent news for decay detection."""
    if not newsapi_key:
        return []
    data = safe_get("https://newsapi.org/v2/everything",
                    params={"q": f'"{company_name}" AND (layoff OR AI OR ethics OR scandal)',
                            "sortBy": "publishedAt", "pageSize": 5, "apiKey": newsapi_key,
                            "from": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")})
    if data:
        return data.get("articles", [])
    return []


def fetch_layoffs(company_name):
    """Check layoffs.fyi data (scraped, cached)."""
    # Layoffs.fyi doesn't have a public API — we use cached CSV
    layoffs_file = DATA_DIR / "layoffs" / "layoffs_data.json"
    if layoffs_file.exists():
        data = json.load(open(layoffs_file))
        for entry in data:
            if company_name.lower() in entry.get("company", "").lower():
                return entry
    return None


# ═══════════════════════════════════════════════════════════════════════
# SOURCES 15-26: Subsignal + Extended (already built)
# ═══════════════════════════════════════════════════════════════════════

def fetch_subsignals(company_name, ticker, domain=None, industry=None):
    """Delegate to subsignal_pipelines.py"""
    try:
        from subsignal_pipelines import fetch_all_subsignals
        return fetch_all_subsignals(company_name, ticker, domain, industry)
    except ImportError:
        return {}

def fetch_extended(company_name, ticker, domain=None, industry=None):
    """Delegate to extended_pipelines.py"""
    try:
        from extended_pipelines import fetch_all_extended
        return fetch_all_extended(company_name, ticker, domain, industry)
    except ImportError:
        return {}


# ═══════════════════════════════════════════════════════════════════════
# MASTER COLLECTOR
# ═══════════════════════════════════════════════════════════════════════

def safe_filename(name, ticker):
    """Sanitize a company name/ticker for use as a filename."""
    raw = ticker or name.replace(' ', '_')
    return raw.replace('/','_').replace('\\','_').replace(':','_').replace('*','_').replace('?','_').replace('"','_').replace('<','_').replace('>','_').replace('|','_').upper()


def is_stale(filepath, max_age_hours=24):
    """Check if a file is older than max_age_hours."""
    if not filepath.exists():
        return True
    age = time.time() - filepath.stat().st_mtime
    return age > (max_age_hours * 3600)


def collect_one(company, keys, core, subsignals, extended, data_dir, incremental_hours=0):
    """Collect all data for a single company. Thread-safe."""
    name = company["name"]
    ticker = company.get("ticker", "")
    industry = company.get("industry", "")
    domain = company.get("domains", [""])[0] if company.get("domains") else ""
    
    if not name and not ticker:
        return None
    
    safe = safe_filename(name, ticker)
    
    # Incremental: skip if data is fresh
    if incremental_hours > 0:
        ss_file = data_dir / "subsignals" / f"{safe}.json"
        ext_file = data_dir / "extended" / f"{safe}.json"
        if not is_stale(ss_file, incremental_hours) and not is_stale(ext_file, incremental_hours):
            return {"skipped": True, "name": name, "ticker": ticker}
    
    result = {"name": name, "ticker": ticker, "sec": None, "epa": None, "glassdoor": None}
    
    finnhub_key = keys.get("finnhub")
    fmp_key = keys.get("fmp")
    
    if core:
        sec = fetch_sec(name, ticker)
        if sec:
            result["sec"] = sec
        
        epa = fetch_epa(name, ticker)
        if epa:
            result["epa"] = epa
        
        if finnhub_key and ticker:
            esg, gd = fetch_finnhub(ticker, finnhub_key)
            if gd:
                result["glassdoor"] = gd
        
        # ─── HEADCOUNT + REVENUE FALLBACK CHAIN ───────────────────────────
        # SEC XBRL rarely has tagged employee counts (voluntary disclosure).
        # Chain: SEC primary → Yahoo Finance (free) → FMP (paid) → leave None
        # We try to populate BOTH headcount and revenue from whichever source
        # provides them, then compute revenue_per_employee at the end.
        if result.get("sec"):
            sec_data = result["sec"]
            h_sigs = sec_data.setdefault("h_signals", {})
            m_sigs = sec_data.setdefault("m_signals", {})
            
            # Extract current state from SEC fetch
            current_hc = h_sigs.get("headcount")
            if isinstance(current_hc, dict):
                current_hc = current_hc.get("value")
            current_rev = m_sigs.get("revenue", 0)
            
            need_hc = not current_hc
            need_rev = not current_rev
            
            # Fallback 1: Yahoo Finance (free, no key)
            if need_hc or need_rev:
                yf_data = fetch_yfinance(ticker)
                if yf_data:
                    if need_hc and yf_data.get("employees"):
                        h_sigs["headcount"] = {"value": yf_data["employees"]}
                        current_hc = yf_data["employees"]
                        need_hc = False
                    if need_rev and yf_data.get("revenue"):
                        m_sigs["revenue"] = yf_data["revenue"]
                        current_rev = yf_data["revenue"]
                        need_rev = False
            
            # Fallback 2: FMP (paid, requires key)
            if (need_hc or need_rev) and fmp_key and ticker:
                fmp = fetch_fmp(ticker, fmp_key)
                if fmp:
                    if need_hc and fmp.get("employees"):
                        h_sigs["headcount"] = {"value": fmp["employees"]}
                        current_hc = fmp["employees"]
                        need_hc = False
                    # FMP profile doesn't include revenue; that field stays missing
            
            # Compute revenue_per_employee from whatever we have
            if current_hc and current_rev:
                h_sigs["revenue_per_employee"] = round(current_rev / current_hc)
        # ──────────────────────────────────────────────────────────────────
    
    if subsignals:
        ss = fetch_subsignals(name, ticker, domain, industry)
        if ss:
            ss_dir = data_dir / "subsignals"
            ss_dir.mkdir(parents=True, exist_ok=True)
            ss_file = ss_dir / f"{safe}.json"
            json.dump(ss, open(ss_file, "w"), indent=2)
            result["subsignals"] = sum(1 for v in ss.values() if v)
    
    if extended:
        ext = fetch_extended(name, ticker, domain, industry)
        if ext:
            ext_dir = data_dir / "extended"
            ext_dir.mkdir(parents=True, exist_ok=True)
            ext_file = ext_dir / f"{safe}.json"
            json.dump({ticker.upper(): ext} if ticker else {name: ext}, open(ext_file, "w"), indent=2)
            result["extended"] = sum(1 for v in ext.values() if v)
    
    return result


def collect_all(companies, keys, core=True, subsignals=True, extended=True, workers=8, incremental_hours=0):
    """Collect data from all 34 sources for all companies. Parallel + incremental."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    sec_results = []
    epa_results = []
    glassdoor_results = []
    cdp_results = load_cdp_data()
    
    total = len(companies)
    skipped = 0
    completed = 0
    
    print(f"\n  Workers: {workers} threads | Incremental: {'ON (' + str(incremental_hours) + 'h)' if incremental_hours else 'OFF (full refresh)'}")
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for i, company in enumerate(companies):
            future = executor.submit(
                collect_one, company, keys, core, subsignals, extended, 
                DATA_DIR, incremental_hours
            )
            futures[future] = (i, company)
        
        for future in as_completed(futures):
            i, company = futures[future]
            try:
                result = future.result()
                if result is None:
                    continue
                
                if result.get("skipped"):
                    skipped += 1
                    continue
                
                completed += 1
                name = result["name"]
                ticker = result["ticker"]
                
                # Collect core results
                if result.get("sec"):
                    sec_results.append(result["sec"])
                if result.get("epa"):
                    epa_results.append(result["epa"])
                if result.get("glassdoor"):
                    glassdoor_results.append(result["glassdoor"])
                
                # Progress
                ss_count = result.get("subsignals", 0)
                ext_count = result.get("extended", 0)
                status = []
                if result.get("sec"): status.append("SEC")
                if result.get("glassdoor"): status.append("Finnhub")
                if ss_count: status.append(f"{ss_count}ss")
                if ext_count: status.append(f"{ext_count}ext")
                
                print(f"  [{completed + skipped}/{total}] {name or ticker} {'· ' + ', '.join(status) if status else ''}")
                
            except Exception as e:
                name = company.get("name", "?")
                ticker = company.get("ticker", "?")
                print(f"  [{completed + skipped}/{total}] {name} ({ticker}) ERROR: {e}")
    
    # Save all core data
    if core:
        save_dir = lambda name: (DATA_DIR / name).mkdir(parents=True, exist_ok=True) or DATA_DIR / name
        
        def _merge_save(fresh_records, source_dir, source_label):
            """Merge fresh records with existing all_companies.json by ticker.
            
            Critical for incremental runs: companies skipped due to fresh data
            (--incremental N) must NOT be removed from the combined file.
            Without this merge, incremental runs would wipe data for any
            company not freshly collected in that run.
            """
            combined_path = source_dir / "all_companies.json"
            existing = []
            if combined_path.exists():
                try:
                    with open(combined_path) as f:
                        existing = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"  ⚠ Could not read existing {source_label} all_companies.json: {e}")
                    existing = []
            
            # Index existing by ticker for fast overlay
            by_ticker = {}
            for r in existing:
                t = r.get("ticker")
                if t:
                    by_ticker[t] = r
            
            # Overlay fresh records (these replace existing entries by ticker)
            fresh_count = 0
            for r in fresh_records:
                t = r.get("ticker")
                if t:
                    by_ticker[t] = r
                    fresh_count += 1
            
            merged = list(by_ticker.values())
            with open(combined_path, "w") as f:
                json.dump(merged, f, indent=2)
            
            preserved = len(merged) - fresh_count
            if preserved > 0:
                print(f"  {source_label}: {fresh_count} freshly collected, {preserved} preserved from previous runs, {len(merged)} total saved")
            else:
                print(f"  {source_label}: {len(merged)} companies saved")
        
        if sec_results:
            d = save_dir("sec")
            _merge_save(sec_results, d, "SEC EDGAR")
        
        if epa_results:
            d = save_dir("epa")
            _merge_save(epa_results, d, "EPA ECHO")
        
        if glassdoor_results:
            d = save_dir("glassdoor")
            _merge_save(glassdoor_results, d, "Glassdoor (via Finnhub)")
        
        # BLS benchmarks (run once)
        bls_dir = save_dir("bls")
        bls = fetch_bls_benchmarks()
        json.dump(bls, open(bls_dir / "industry_benchmarks.json", "w"), indent=2)
        print(f"  BLS: {len(bls)} industry benchmarks saved")
    
    if skipped:
        print(f"\n  ⏭ Skipped {skipped} companies (data fresh within {incremental_hours}h)")
    
    return {
        "sec": len(sec_results),
        "epa": len(epa_results),
        "glassdoor": len(glassdoor_results),
        "cdp": len(cdp_results),
        "bls": "loaded",
        "skipped": skipped,
        "collected": completed,
    }


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="HI. Data Collector — All 34 Sources")
    parser.add_argument("--all", action="store_true", help="Fetch all 34 sources")
    parser.add_argument("--core", action="store_true", help="Core 6 only")
    parser.add_argument("--subsignals", action="store_true", help="6 subsignal sources")
    parser.add_argument("--extended", action="store_true", help="12 extended sources")
    parser.add_argument("--company", help="Single company name")
    parser.add_argument("--data", default="data", help="Data directory")
    parser.add_argument("--workers", type=int, default=8, help="Parallel threads (default: 8)")
    parser.add_argument("--incremental", type=int, default=0, help="Skip companies with data fresher than N hours (0=full refresh)")
    args = parser.parse_args()
    
    global DATA_DIR
    DATA_DIR = Path(args.data)
    
    # Default to --all if nothing specified
    if not any([args.all, args.core, args.subsignals, args.extended]):
        args.all = True
    
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  HI. Data Collector — 34 Free Public Sources           ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # Load API keys
    keys = {
        "finnhub": load_key("finnhub"),
        "fmp": load_key("fmp"),
        "alpha_vantage": load_key("alpha_vantage"),
        "fred": load_key("fred"),
        "newsapi": load_key("newsapi"),
    }
    
    found_keys = [k for k, v in keys.items() if v]
    missing_keys = [k for k, v in keys.items() if not v]
    print(f"\n  API keys found: {', '.join(found_keys) or 'none'}")
    if missing_keys:
        print(f"  API keys missing: {', '.join(missing_keys)} (some sources will be skipped)")
    
    # Load companies
    companies = load_company_list()
    if args.company:
        companies = [{"name": args.company, "ticker": "", "industry": "", "domains": []}]
    
    if not companies:
        print("\n  No companies to collect. Run scoring engine first or use --company.")
        return
    
    print(f"\n  Collecting data for {len(companies)} companies...")
    start = time.time()
    
    results = collect_all(
        companies, keys,
        core=args.all or args.core,
        subsignals=args.all or args.subsignals,
        extended=args.all or args.extended,
        workers=args.workers,
        incremental_hours=args.incremental,
    )
    
    elapsed = round(time.time() - start, 1)
    print(f"\n{'═' * 60}")
    print(f"  ✓ Data collection complete in {elapsed}s")
    print(f"  Next: python3 run_all.py")
    print(f"{'═' * 60}")


if __name__ == "__main__":
    main()
