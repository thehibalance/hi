#!/usr/bin/env python3
"""
HI. — REST API
Phase 2, Track C: API layer serving HI Grades.

Security:
  - CORS whitelist: thehibalance.org, extension, localhost
  - Rate limiting: 100 req/min per IP, 20 req/min on search
  - Input sanitization: query length caps, character filtering
  - Read-only: no write endpoints exposed

Endpoints:
  GET  /api/v1/score/<domain>         — Score by domain (extension uses this)
  GET  /api/v1/score/ticker/<ticker>  — Score by ticker
  GET  /api/v1/search?q=             — Search companies by name
  GET  /api/v1/grades                 — List all scored companies
  GET  /api/v1/grades/top             — Top 10 companies
  GET  /api/v1/grades/bottom          — Bottom 10 companies
  GET  /api/v1/stats                  — Database statistics
  GET  /api/v1/health                 — Health check

Run:
  pip install flask flask-cors flask-limiter
  python api_server.py
  python api_server.py --port 8080
"""

import json, os, sys, re, html as html_lib
from pathlib import Path
from datetime import datetime

try:
    from flask import Flask, jsonify, request
    from flask_cors import CORS
except ImportError:
    print("Install: pip install flask flask-cors")
    sys.exit(1)

# Optional: rate limiting (graceful if not installed)
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    HAS_LIMITER = True
except ImportError:
    HAS_LIMITER = False
    print("Warning: flask-limiter not installed. Rate limiting disabled.")
    print("Install: pip install flask-limiter")

app = Flask(__name__)

# ═══ CORS WHITELIST ═══
# Only allow requests from our domains + extension + localhost dev
ALLOWED_ORIGINS = [
    "https://thehibalance.org",
    "https://www.thehibalance.org",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:8080",
    "chrome-extension://*",
]
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=False)

# ═══ RATE LIMITING ═══
if HAS_LIMITER:
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["100 per minute", "1000 per hour"],
        storage_uri="memory://",
    )
else:
    # No-op decorator if limiter not available
    class FakeLimiter:
        def limit(self, *args, **kwargs):
            def decorator(f): return f
            return decorator
    limiter = FakeLimiter()

# ═══ API KEY AUTHENTICATION ═══
try:
    from api_keys import validate_key, TIERS
    HAS_KEYS = True
except ImportError:
    HAS_KEYS = False
    print("Warning: api_keys module not found. Key authentication disabled.")

# ═══ STRIPE INTEGRATION ═══
try:
    from stripe_integration import register_stripe_routes
    register_stripe_routes(app)
except ImportError:
    print("  Stripe: not loaded (stripe_integration.py missing or stripe not installed)")
except Exception as e:
    print(f"  Stripe: error loading — {e}")

@app.before_request
def check_api_key():
    """Validate API key on every request. Free tier = no key needed."""
    # Skip key check for non-API routes
    path = request.path
    if not path.startswith("/api/") or path in ["/api/v1/stats", "/api/v1/health", "/api/v1/pricing"]:
        return
    # Skip for Stripe routes
    if path.startswith("/stripe/"):
        return
    
    if not HAS_KEYS:
        return
    
    key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "")
    result = validate_key(key)
    
    if result is None:
        return jsonify({"error": "invalid_api_key", "message": "Invalid API key. Get one at thehibalance.org/api"}), 401
    
    if isinstance(result, dict) and result.get("error") == "daily_limit":
        return jsonify({
            "error": "daily_limit_exceeded",
            "message": f"Daily limit of {result['limit']} calls reached for {result['tier']} tier.",
            "upgrade": "https://thehibalance.org/api#pricing"
        }), 429
    
    # Store tier on request for downstream use
    request.api_tier = result

# ═══ INPUT SANITIZATION ═══
MAX_QUERY_LENGTH = 100
MAX_PARAM_LENGTH = 50

def sanitize_input(text, max_len=MAX_QUERY_LENGTH):
    """Sanitize user input: strip dangerous chars, cap length, escape HTML."""
    if not text:
        return ""
    text = str(text)[:max_len]
    text = html_lib.escape(text)
    # Strip control characters and null bytes
    text = re.sub(r'[\x00-\x1f\x7f]', '', text)
    # Strip potential SQL/NoSQL injection patterns
    text = re.sub(r'[;{}$]', '', text)
    return text.strip()

def sanitize_domain(domain):
    """Sanitize domain input."""
    if not domain:
        return ""
    domain = str(domain)[:MAX_PARAM_LENGTH].lower().strip()
    # Only allow valid domain characters
    domain = re.sub(r'[^a-z0-9.\-]', '', domain)
    return domain

def sanitize_ticker(ticker):
    """Sanitize ticker input."""
    if not ticker:
        return ""
    ticker = str(ticker)[:10].upper().strip()
    # Only allow alphanumeric + dots (for BRK.B style)
    ticker = re.sub(r'[^A-Z0-9.]', '', ticker)
    return ticker

# ═══ SECURITY HEADERS ═══
@app.after_request
def add_security_headers(response):
    """Add security headers to every response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Cache-Control'] = 'public, max-age=300'  # 5 min cache
    response.headers['X-Powered-By'] = 'HI.'
    return response

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({
        "error": "rate_limit_exceeded",
        "message": "Too many requests. Please slow down.",
        "retry_after": "60 seconds"
    }), 429

# In-memory indexes
COMPANIES = {}       # domain -> record
TICKERS = {}         # ticker -> record
NAME_INDEX = {}      # lowercase name -> record
ALL_COMPANIES = []   # sorted by composite desc
HEARTBEAT = {}       # ticker -> heartbeat data
HEARTBEAT_ALERTS = []
HEARTBEAT_PULSE = {}
HUMAN100 = []        # HUMAN 100 Index constituents
HUMAN100_META = {}   # Index metadata
ARBITRAGE = []       # HUMAN Lens results
ARBITRAGE_META = {}  # Arbitrage metadata
MOATS = []           # HUMAN Shield results
MOATS_META = {}      # Moat metadata
CONTAGION = []       # HUMAN Contagion results
EMPATHY_WM = []      # Empathy Watermark results
CONSUMER_BENCH = {}  # HUMAN Consciousness benchmarks
COLLECTIVE = {}      # HUMAN Wave signals
DATA_DIR = Path("data/scores")


def get_grade(score):
    """Score-only system. Returns 'HI Balanced' or 'scored'."""
    return "scored"

THRESHOLD_FLOOR = 55  # Hard minimum — never drops below this
THRESHOLD_HIGH_WATER = THRESHOLD_FLOOR  # In-memory ratchet (persists per deploy)

def compute_hi_balanced_threshold(companies):
    """
    Adaptive threshold: mean + 2 SD of pipeline-scored composites.
    
    Failsafes:
    1. Hard floor: never below THRESHOLD_FLOOR (55)
    2. Ratchet: can only go UP, never down (persisted to file)
    
    Only recalculates when --quarterly flag is passed.
    Daily runs use the saved threshold.
    """
    global THRESHOLD_HIGH_WATER
    composites = [c.get("composite", 0) for c in companies 
                  if c.get("composite", 0) > 0 
                  and c.get("data_sources") 
                  and c.get("data_sources") not in [["Manual Scoring"], ["Public Reporting"]]]
    if len(composites) < 10:
        composites = [c.get("composite", 0) for c in companies if c.get("composite", 0) > 0]
    if len(composites) < 10:
        return 62  # Default
    import math
    mean = sum(composites) / len(composites)
    variance = sum((x - mean) ** 2 for x in composites) / len(composites)
    stdev = math.sqrt(variance)
    computed = round(mean + 2 * stdev, 1)
    
    # Failsafe 1: Hard floor
    computed = max(computed, THRESHOLD_FLOOR)
    
    # Failsafe 2: Ratchet — can only go up
    THRESHOLD_HIGH_WATER = max(computed, THRESHOLD_HIGH_WATER)
    
    return THRESHOLD_HIGH_WATER

THRESHOLD_FILE = Path("data/threshold.json")

def load_saved_threshold():
    """Load the last quarterly threshold from file."""
    if THRESHOLD_FILE.exists():
        try:
            data = json.load(open(THRESHOLD_FILE))
            return data.get("threshold", 62)
        except:
            pass
    return None

def save_threshold(threshold):
    """Save the quarterly threshold to file."""
    THRESHOLD_FILE.parent.mkdir(parents=True, exist_ok=True)
    json.dump({
        "threshold": threshold,
        "updated": datetime.now().isoformat(),
        "type": "quarterly"
    }, open(THRESHOLD_FILE, "w"), indent=2)

def check_hi_balanced(company, threshold):
    """
    Check 3 gates for Gold HI Grade status.
    Gate 1 — SCORE: Composite ≥ adaptive threshold
    Gate 2 — BALANCE: All 5 dimensions ≥ 42
    Gate 3 — INTEGRITY: No Humanwashing™ flags AND Algorithmic Harm Index™ < 30
    
    Score, balance, and integrity. That's it.
    """
    dims = [company.get("D_H", 0), company.get("D_U", 0), company.get("D_M", 0), company.get("D_A", 0), company.get("D_N", 0)]
    below_42 = sum(1 for d in dims if d < 42)
    
    no_humanwashing = len(company.get("humanwashing_flags", [])) == 0
    ahi_score = company.get("algorithmic_harm_score") or company.get("algo_harm_score") or 0
    ahi_clean = ahi_score < 30
    
    gates = {
        "score": company.get("composite", 0) >= threshold,
        "balance": below_42 == 0,
        "integrity": no_humanwashing and ahi_clean,
    }
    
    return all(gates.values()), gates

SATIRES = {
    "scored": "",
}


def seed_to_record(s):
    composite = round((s["h"] + s["u"] + s["m"] + s["a"] + s["n"]) / 5)
    dims = [s["h"], s["u"], s["m"], s["a"], s["n"]]
    below_42 = sum(1 for d in dims if d < 42)
    if min(dims) < 10:
        composite = min(composite, 40.0)
    # Balance floor: 2+ below 42 = cap 41, 1 below 42 = cap 49
    balance_floor = False
    if below_42 >= 2:
        composite = min(composite, 41)
        balance_floor = True
    elif below_42 == 1:
        composite = min(composite, 49)
        balance_floor = True
    return {
        "company": s["name"], "ticker": None,
        "domains": s.get("domains", []), "tags": s.get("tags", []),
        "D_H": s["h"], "D_U": s["u"], "D_M": s["m"], "D_A": s["a"], "D_N": s["n"],
        "composite": composite, "hi_grade": "scored", "hi_balanced": False,
        "satire": "",
        "floor_triggered": min(dims) < 10,
        "balance_floor": balance_floor,
        "confidence": "Baseline", "data_sources": ["Public Reporting"],
        "notes": s.get("notes", ""), "spec_version": "1.1.0",
        "industry": s["tags"][0] if s.get("tags") else "",
        "humanwashing_flags": [],
        "algorithmic_harm_score": s.get("algorithmic_harm_score", 0),
        "subsidiaries": s.get("subsidiaries", []),
        "primary_contractors": s.get("primary_contractors", []),
        "key_signals": {
            "headcount": None, "headcount_change_pct": None,
            "revenue_per_employee": None, "displacement_signal": None,
            "ai_hiring_ratio": None, "glassdoor_rating": None,
            "cdp_climate": None, "epa_violations": None,
        },
    }


def normalize_name(name):
    """Aggressively normalize company name for dedup matching."""
    if not name:
        return ""
    n = name.lower().strip()
    # Normalize & to and, then strip "and" later if between words
    n = n.replace('&', ' and ')
    # Strip punctuation first so suffixes match cleanly
    n = re.sub(r'[,.\-\'\"()\[\]]', ' ', n)
    n = re.sub(r'\s+', ' ', n).strip()
    # Strip possessive
    if n.endswith(' s'): n = n[:-2].strip()
    # Strip common prefixes
    for prefix in ['the ', 'a ']:
        if n.startswith(prefix):
            n = n[len(prefix):]
    # Strip common suffixes — run twice to catch chained suffixes
    for _pass in range(2):
        for suffix in [' incorporated', ' corporation', ' international', ' technologies', ' technology',
                       ' enterprises', ' solutions', ' platforms', ' provisions', ' holdings', ' group',
                       ' company', ' inc', ' corp', ' llc', ' ltd', ' co', ' plc', ' sa', ' ag', ' nv', ' se']:
            if n.endswith(suffix):
                n = n[:-len(suffix)].strip()
    return n.strip()

def build_index():
    global COMPANIES, TICKERS, NAME_INDEX, ALL_COMPANIES, HEARTBEAT, HEARTBEAT_ALERTS, HEARTBEAT_PULSE, HUMAN100, HUMAN100_META, ARBITRAGE, ARBITRAGE_META, MOATS, MOATS_META, CONTAGION, EMPATHY_WM, CONSUMER_BENCH, COLLECTIVE
    COMPANIES, TICKERS, NAME_INDEX, ALL_COMPANIES = {}, {}, {}, []
    HEARTBEAT, HEARTBEAT_ALERTS, HEARTBEAT_PULSE = {}, [], {}
    HUMAN100, HUMAN100_META = [], {}
    ARBITRAGE, ARBITRAGE_META = [], {}
    MOATS, MOATS_META = [], {}
    CONTAGION, EMPATHY_WM, CONSUMER_BENCH, COLLECTIVE = [], [], {}, {}
    NORM_INDEX = {}  # normalized name index for dedup

    # Load heartbeat data
    hb_dir = DATA_DIR.parent / "heartbeat"
    try:
        if (hb_dir / "heartbeats.json").exists():
            for hb in json.load(open(hb_dir / "heartbeats.json")):
                t = hb.get("ticker", "")
                if t: HEARTBEAT[t.upper()] = hb
            print(f"  Heartbeat: {len(HEARTBEAT)} companies")
        if (hb_dir / "alerts.json").exists():
            HEARTBEAT_ALERTS = json.load(open(hb_dir / "alerts.json"))
            print(f"  Heartbeat alerts: {len(HEARTBEAT_ALERTS)}")
        if (hb_dir / "pulse.json").exists():
            HEARTBEAT_PULSE = json.load(open(hb_dir / "pulse.json"))
            print(f"  Heartbeat pulse: {HEARTBEAT_PULSE.get('pulse', 'unknown')}")
    except Exception as e:
        print(f"  Heartbeat: skipped (corrupt data: {e})")

    # Load HUMAN 100 Index
    h100_dir = DATA_DIR.parent / "human100"
    try:
        if (h100_dir / "index.json").exists():
            HUMAN100 = json.load(open(h100_dir / "index.json"))
            print(f"  HUMAN 100: {len(HUMAN100)} constituents")
        if (h100_dir / "metadata.json").exists():
            HUMAN100_META = json.load(open(h100_dir / "metadata.json"))
    except Exception as e:
        print(f"  HUMAN 100: skipped ({e})")

    # Load HUMAN Lens data
    try:
        arb_dir = DATA_DIR.parent / "arbitrage"
        if (arb_dir / "all_arbitrage.json").exists():
            ARBITRAGE = json.load(open(arb_dir / "all_arbitrage.json"))
            print(f"  Arbitrage: {len(ARBITRAGE)} companies analyzed")
        if (arb_dir / "metadata.json").exists():
            ARBITRAGE_META = json.load(open(arb_dir / "metadata.json"))
    except Exception as e:
        print(f"  Arbitrage: skipped ({e})")

    # Load HUMAN Shield data
    try:
        moat_dir = DATA_DIR.parent / "ethical_moat"
        if (moat_dir / "all_moats.json").exists():
            MOATS = json.load(open(moat_dir / "all_moats.json"))
            print(f"  HUMAN Shield: {len(MOATS)} companies analyzed")
        if (moat_dir / "metadata.json").exists():
            MOATS_META = json.load(open(moat_dir / "metadata.json"))
    except Exception as e:
        print(f"  HUMAN Shield: skipped ({e})")

    # Load HUMAN Contagion
    try:
        cont_dir = DATA_DIR.parent / "contagion"
        if (cont_dir / "all_contagion.json").exists():
            CONTAGION = json.load(open(cont_dir / "all_contagion.json"))
            print(f"  Contagion: {len(CONTAGION)} companies")
    except Exception as e:
        print(f"  Contagion: skipped ({e})")

    # Load Empathy Watermark
    try:
        ew_dir = DATA_DIR.parent / "empathy_watermark"
        if (ew_dir / "all_watermarks.json").exists():
            EMPATHY_WM = json.load(open(ew_dir / "all_watermarks.json"))
            print(f"  Empathy Watermark: {len(EMPATHY_WM)} companies")
    except Exception as e:
        print(f"  Empathy Watermark: skipped ({e})")

    # Load HUMAN Consciousness
    try:
        cc_dir = DATA_DIR.parent / "consumer_consciousness"
        if (cc_dir / "benchmarks.json").exists():
            CONSUMER_BENCH = json.load(open(cc_dir / "benchmarks.json"))
            print(f"  HUMAN Consciousness: benchmarks loaded")
    except Exception as e:
        print(f"  Consciousness: skipped ({e})")

    # Load HUMAN Wave
    try:
        cb_dir = DATA_DIR.parent / "collective_bargaining"
        if (cb_dir / "signals.json").exists():
            COLLECTIVE = json.load(open(cb_dir / "signals.json"))
            print(f"  HUMAN Wave: signals loaded")
    except Exception as e:
        print(f"  HUMAN Wave: skipped ({e})")

    # Load S&P 500 domain mappings
    sp500_domains = {}
    try:
        from sp500_domains import DOMAIN_MAP
        sp500_domains = DOMAIN_MAP
        print(f"  S&P 500 domains: {sum(len(d) for d in sp500_domains.values())} domains for {len(sp500_domains)} companies")
    except ImportError:
        pass

    # Load scoring engine output
    if DATA_DIR.exists():
        sf = DATA_DIR / "all_scores.json"
        scored = json.load(open(sf)) if sf.exists() else []
        seen_norm = {}  # Track normalized names to prevent dupes
        for c in scored:
            if c.get("error"): continue
            t = c.get("ticker", "")
            n = c.get("company", "")
            norm = normalize_name(n)
            
            # Skip duplicates by normalized name — keep the one with more sources
            if norm in seen_norm:
                existing = seen_norm[norm]
                if len(c.get("data_sources", [])) > len(existing.get("data_sources", [])):
                    # Replace existing with this better record
                    if existing in ALL_COMPANIES:
                        ALL_COMPANIES.remove(existing)
                    seen_norm[norm] = c
                else:
                    continue  # Skip this record, existing is better
            else:
                seen_norm[norm] = c
            
            # Inject domains from S&P 500 mapping if not already present
            # Merge S&P 500 domains (add missing ones, don't replace)
            if t and t.upper() in sp500_domains:
                existing = set(d.lower() for d in c.get("domains", []))
                for d in sp500_domains[t.upper()]:
                    if d.lower() not in existing:
                        c.setdefault("domains", []).append(d)
            
            # Inject heartbeat data
            if t and t.upper() in HEARTBEAT:
                hb = HEARTBEAT[t.upper()]
                c["decay_index"] = hb.get("decay_index", 0)
                c["decay_level"] = hb.get("decay_level", "stable")
                c["decay_factors"] = hb.get("factors", [])
            
            if t: TICKERS[t.upper()] = c
            if n: NAME_INDEX[n.lower()] = c
            if norm: NORM_INDEX[norm] = c
            ALL_COMPANIES.append(c)
            
            # Index by domain — prefer company whose name matches the domain
            for d in c.get("domains", []):
                d = d.lower().strip()
                if not d: continue
                if d not in COMPANIES:
                    COMPANIES[d] = c
                else:
                    # Domain conflict — prefer the company whose name matches
                    base = d.split(".")[0].lower()
                    existing_name = COMPANIES[d].get("company", "").lower()
                    new_name = c.get("company", "").lower()
                    if base in new_name and base not in existing_name:
                        COMPANIES[d] = c
                    elif len(c.get("data_sources", [])) > len(COMPANIES[d].get("data_sources", [])):
                        COMPANIES[d] = c

    # Load seed database
    seed_candidates = [
        "human-edge/lib/seed-data.js",
        "../human-edge/lib/seed-data.js",
        "lib/seed-data.js",
        "seed-data.js",
    ]
    seed_added = 0
    seed_skipped = 0
    for seed_path in seed_candidates:
        if os.path.exists(seed_path):
            content = open(seed_path).read()
            start = content.index("const SEED_COMPANIES = ") + len("const SEED_COMPANIES = ")
            end = content.index("];", start) + 1
            for s in json.loads(content[start:end]):
                rec = seed_to_record(s)
                norm = normalize_name(rec["company"])
                
                # Check 1: Exact name match
                if rec["company"].lower() in NAME_INDEX:
                    existing = NAME_INDEX[rec["company"].lower()]
                    for d in rec.get("domains", []):
                        d = d.lower().strip()
                        if d and d not in COMPANIES:
                            COMPANIES[d] = existing
                    seed_skipped += 1
                    continue
                
                # Check 2: Normalized name match
                if norm in NORM_INDEX:
                    existing = NORM_INDEX[norm]
                    for d in rec.get("domains", []):
                        d = d.lower().strip()
                        if d and d not in COMPANIES:
                            COMPANIES[d] = existing
                    seed_skipped += 1
                    continue
                
                # Check 3: Domain overlap — if any seed domain already maps to a scored company
                domain_match = False
                for d in rec.get("domains", []):
                    d = d.lower().strip()
                    if d in COMPANIES:
                        # This domain already has a scored company — skip seed, add remaining domains
                        existing = COMPANIES[d]
                        for d2 in rec.get("domains", []):
                            d2 = d2.lower().strip()
                            if d2 and d2 not in COMPANIES:
                                COMPANIES[d2] = existing
                        domain_match = True
                        seed_skipped += 1
                        break
                if domain_match:
                    continue
                
                # Check 4: Partial name match — "patagonia" matches "patagonia provisions"
                partial_match = False
                for existing_norm in NORM_INDEX:
                    if norm in existing_norm or existing_norm in norm:
                        if abs(len(norm) - len(existing_norm)) < 15:  # Close enough
                            existing = NORM_INDEX[existing_norm]
                            for d in rec.get("domains", []):
                                d = d.lower().strip()
                                if d and d not in COMPANIES:
                                    COMPANIES[d] = existing
                            partial_match = True
                            seed_skipped += 1
                            break
                if partial_match:
                    continue
                
                # No match found — add as seed-only company
                NAME_INDEX[rec["company"].lower()] = rec
                NORM_INDEX[norm] = rec
                ALL_COMPANIES.append(rec)
                for d in rec.get("domains", []):
                    d = d.lower().strip()
                    if d and d not in COMPANIES:
                        COMPANIES[d] = rec
                seed_added += 1
            print(f"  Seed data: {seed_added} added, {seed_skipped} skipped (already scored)")
            break

    # Sort: verified first, then estimated, then pending. Within each tier, by composite desc.
    status_priority = {"verified": 0, "estimated": 1, "pending": 2}
    ALL_COMPANIES.sort(key=lambda x: (status_priority.get(x.get("score_status", "pending"), 2), -x.get("composite", 0)))
    
    # Add score_status: "verified" (5+ real), "estimated" (1-4 real), "pending" (seed only)
    BASELINE_SOURCES = {"Defaults", "Manual Scoring", "Seed Estimate", "Public Reporting"}
    for c in ALL_COMPANIES:
        real = [s for s in c.get("data_sources", []) if s not in BASELINE_SOURCES]
        if len(real) >= 5:
            c["score_status"] = "verified"
        elif len(real) >= 1:
            c["score_status"] = "estimated"
        else:
            c["score_status"] = "pending"
    
    pending_count = sum(1 for c in ALL_COMPANIES if c.get("score_status") == "pending")
    print(f"  Score status: {len(ALL_COMPANIES) - pending_count} active, {pending_count} pending verification")
    
    # Compute HI Balanced threshold
    # Daily: use saved threshold. Quarterly: recalculate.
    saved = load_saved_threshold()
    if saved and not getattr(app, '_quarterly_mode', False):
        threshold = saved
        print(f"  Using saved quarterly threshold: {threshold}")
    else:
        threshold = compute_hi_balanced_threshold(ALL_COMPANIES)
        save_threshold(threshold)
        print(f"  {'Quarterly recalculated' if getattr(app, '_quarterly_mode', False) else 'Initial'} threshold: {threshold}")
    balanced_count = 0
    for c in ALL_COMPANIES:
        passed, gates = check_hi_balanced(c, threshold)
        # Pending companies cannot earn Gold — must have real data
        if c.get("score_status") == "pending":
            passed = False
        c["hi_balanced"] = passed
        c["hi_balanced_gates"] = gates
        c["hi_balanced_threshold"] = threshold
        if passed:
            c["hi_grade"] = "scored"
            c["satire"] = ""
            balanced_count += 1
    print(f"  HI Balanced threshold: {threshold} | {balanced_count} companies qualified")
    
    # Generate/refresh HUMAN 100 from live data (always use ALL_COMPANIES for freshness)
    eligible = [c for c in ALL_COMPANIES if c.get("composite", 0) > 0 and not c.get("humanwashing_flags") and c.get("ticker")]
    eligible.sort(key=lambda x: (x.get("hi_balanced", False), x.get("composite", 0)), reverse=True)
    HUMAN100 = []
    for rank, c in enumerate(eligible[:100], 1):
        entry = {
            "rank": rank,
            "company": c.get("company", ""),
            "ticker": c.get("ticker", ""),
            "composite": c.get("composite", 0),
            "D_H": c.get("D_H", 0), "D_U": c.get("D_U", 0), "D_M": c.get("D_M", 0),
            "D_A": c.get("D_A", 0), "D_N": c.get("D_N", 0),
            "industry": c.get("industry", ""),
            "hi_balanced": c.get("hi_balanced", False),
            "hi_grade": c.get("hi_grade", "scored"),
            "decay_index": c.get("decay_index", 0),
            "decay_level": c.get("decay_level", "stable"),
            "balance_floor": c.get("balance_floor", False),
        }
        HUMAN100.append(entry)
    
    # Compute HUMAN 100 metadata
    if HUMAN100:
        h100_composites = [c["composite"] for c in HUMAN100]
        h100_avg = round(sum(h100_composites) / len(h100_composites))
        dim_avgs = {}
        for dim in ["D_H", "D_U", "D_M", "D_A", "D_N"]:
            vals = [c.get(dim, 0) for c in HUMAN100 if c.get(dim, 0) > 0]
            dim_avgs[dim] = round(sum(vals) / len(vals)) if vals else 0
        HUMAN100_META = {
            "average_composite": h100_avg,
            "dimension_averages": dim_avgs,
            "rebalance_date": "Quarterly",
            "watchlist_count": sum(1 for c in HUMAN100 if c.get("decay_index", 0) >= 30),
            "hi_balanced_count": sum(1 for c in HUMAN100 if c.get("hi_balanced")),
        }
    print(f"  HUMAN 100: {len(HUMAN100)} constituents")
    
    # Inject hi_balanced into all feature lists (they load from pre-generated files)
    try:
        balanced_tickers = {c.get("ticker", "").upper() for c in ALL_COMPANIES if c.get("hi_balanced") and c.get("ticker")}
        balanced_names = {c.get("company", "").strip() for c in ALL_COMPANIES if c.get("hi_balanced") and c.get("company")}
        for feature_list in [CONTAGION, EMPATHY_WM, MOATS, ARBITRAGE]:
            if isinstance(feature_list, list):
                for item in feature_list:
                    t = (item.get("ticker") or "").upper()
                    n = (item.get("company") or "").strip()
                    if (t and t in balanced_tickers) or (n and n in balanced_names):
                        item["hi_balanced"] = True
                    else:
                        item["hi_balanced"] = False
    except Exception as e:
        print(f"  Warning: hi_balanced injection error: {e}")
    print(f"  {len(ALL_COMPANIES)} companies | {len(COMPANIES)} domains | {len(TICKERS)} tickers")


# ── Endpoints ─────────────────────────────────────────────────────────

@app.route("/")
def root():
    return jsonify({
        "service": "HI. Score API", "tagline": "Find the HI balance.",
        "version": "1.0.0", "website": "https://thehibalance.org",
        "endpoints": {
            "score_by_domain": "GET /api/v1/score/{domain}",
            "score_by_ticker": "GET /api/v1/score/ticker/{ticker}",
            "search": "GET /api/v1/search?q={query}",
            "list_grades": "GET /api/v1/grades?page=1&per_page=50&grade=A",
            "top": "GET /api/v1/grades/top?limit=10",
            "bottom": "GET /api/v1/grades/bottom?limit=10",
            "stats": "GET /api/v1/stats",
            "health": "GET /api/v1/health",
        },
    })


@app.route("/api/v1/health")
def health():
    return jsonify({
        "status": "ok", "service": "HI. Score API", "version": "1.0.0",
        "companies": len(ALL_COMPANIES), "domains": len(COMPANIES),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


@app.route("/api/v1/score/<path:domain>")
def score_by_domain(domain):
    """Primary endpoint for browser extension."""
    domain = sanitize_domain(re.sub(r"^(https?://)?(www\.)?", "", domain.lower().strip()).split("/")[0])

    # Direct match
    if domain in COMPANIES:
        return jsonify(COMPANIES[domain])

    # Try base domain
    parts = domain.split(".")
    if len(parts) > 2:
        base = ".".join(parts[-2:])
        if base in COMPANIES:
            return jsonify(COMPANIES[base])

    # Try adding TLDs
    if "." not in domain:
        for tld in [".com", ".org", ".net", ".io"]:
            if domain + tld in COMPANIES:
                return jsonify(COMPANIES[domain + tld])

    return jsonify({
        "error": "not_found", "domain": domain,
        "message": f"No HI Grade found for {domain}.",
        "suggestion": "Submit for scoring at thehibalance.org/submit"
    }), 404


@app.route("/api/v1/score/ticker/<ticker>")
def score_by_ticker(ticker):
    ticker = sanitize_ticker(ticker)
    if ticker in TICKERS:
        return jsonify(TICKERS[ticker])
    return jsonify({"error": "not_found", "ticker": ticker}), 404


SEARCH_ALIASES = {
    "google": "alphabet", "youtube": "alphabet", "gmail": "alphabet", "android": "alphabet",
    "facebook": "meta", "instagram": "meta", "whatsapp": "meta",
    "iphone": "apple", "ipad": "apple", "macbook": "apple",
    "windows": "microsoft", "xbox": "microsoft", "linkedin": "microsoft",
    "aws": "amazon", "alexa": "amazon", "kindle": "amazon", "prime": "amazon",
    "gmail": "alphabet", "chrome": "alphabet", "waymo": "alphabet",
    "tesla": "tesla", "spacex": "tesla",
    "tiktok": "bytedance",
    "snapchat": "snap",
    "uber eats": "uber",
    "venmo": "paypal",
    "cashapp": "block", "square": "block",
    "jet blue": "jetblue",
}

@app.route("/api/v1/search")
@limiter.limit("30 per minute")
def search():
    q = sanitize_input(request.args.get("q", ""), MAX_QUERY_LENGTH).lower().strip()
    if len(q) < 2:
        return jsonify({"error": "Query too short (min 2 chars)"}), 400

    # Expand query with aliases
    search_terms = [q]
    if q in SEARCH_ALIASES:
        search_terms.append(SEARCH_ALIASES[q])

    limit = min(int(request.args.get("limit", 20)), 100)
    results = []
    seen_norms = set()
    for c in ALL_COMPANIES:
        try:
            name = (c.get("company") or "").lower()
            tags = " ".join(c.get("tags") or []).lower()
            ticker = (c.get("ticker") or "").lower()
            domains = " ".join(c.get("domains") or []).lower()
            matched = any(term in name or term in tags or term == ticker or term in domains for term in search_terms)
            if matched:
                norm = normalize_name(c.get("company") or "")
                if norm in seen_norms:
                    continue
                seen_norms.add(norm)
                results.append(c)
            if len(results) >= limit:
                break
        except Exception:
            continue

    # Sort: scored companies (with data_sources) before seed
    results.sort(key=lambda x: (len(x.get("data_sources") or []) > 1, x.get("composite") or 0), reverse=True)
    return jsonify({"query": q, "count": len(results), "results": results})


@app.route("/api/v1/grades")
def list_grades():
    page = max(1, min(int(request.args.get("page", 1) or 1), 100))
    per_page = max(1, min(int(request.args.get("per_page", 50) or 50), 200))
    grade_filter = sanitize_input(request.args.get("grade", ""), 10).upper()

    filtered = ALL_COMPANIES
    if grade_filter:
        gmap = {"A": "A", "B": "B", "C": "C", "D": "D", "F": "F"}
        target = gmap.get(grade_filter, grade_filter)
        filtered = [c for c in ALL_COMPANIES if c.get("hi_grade") == target]

    total = len(filtered)
    start = (page - 1) * per_page
    results = [{
        "company": c["company"], "ticker": c.get("ticker"),
        "composite": c["composite"], "hi_grade": c["hi_grade"], "satire": c.get("satire"),
        "D_H": c["D_H"], "D_U": c["D_U"], "D_M": c["D_M"], "D_A": c["D_A"], "D_N": c["D_N"],
    } for c in filtered[start:start + per_page]]

    return jsonify({
        "total": total, "page": page, "per_page": per_page,
        "pages": (total + per_page - 1) // per_page, "results": results,
    })


@app.route("/api/v1/grades/top")
def top_grades():
    limit = min(int(request.args.get("limit", 10)), 1000)
    results = []
    for i, c in enumerate(ALL_COMPANIES[:limit]):
        rec = dict(c)
        rec["rank"] = i + 1
        results.append(rec)
    return jsonify({"count": len(results), "results": results})


@app.route("/api/v1/grades/bottom")
def bottom_grades():
    limit = min(int(request.args.get("limit", 10)), 1000)
    bottom = list(reversed(ALL_COMPANIES[-limit:]))
    results = []
    for i, c in enumerate(bottom):
        rec = dict(c)
        rec["rank"] = i + 1
        results.append(rec)
    return jsonify({"count": len(results), "results": results})


@app.route("/api/v1/stats")
def stats():
    grades = {}
    for c in ALL_COMPANIES:
        g = c.get("hi_grade", "?")
        grades[g] = grades.get(g, 0) + 1

    composites = [c["composite"] for c in ALL_COMPANIES if c.get("composite")]
    avg = round(sum(composites) / len(composites)) if composites else 0
    threshold = load_saved_threshold() or compute_hi_balanced_threshold(ALL_COMPANIES)
    certified_count = sum(1 for c in ALL_COMPANIES if c.get("hi_balanced"))

    return jsonify({
        "total_companies": len(ALL_COMPANIES),
        "domains_indexed": len(COMPANIES),
        "tickers_indexed": len(TICKERS),
        "grade_distribution": grades,
        "average_composite": avg,
        "hi_balanced_threshold": threshold,
        "hi_balanced_count": certified_count,
        "humanwashing_flagged": sum(1 for c in ALL_COMPANIES if c.get("humanwashing_flags")),
        "floor_rule_triggered": sum(1 for c in ALL_COMPANIES if c.get("floor_triggered")),
        "balance_floor_triggered": sum(1 for c in ALL_COMPANIES if c.get("balance_floor")),
        "data_sources": 42,
        "spec_version": "1.0.0",
        "brand": {
            "name": "HI.", "tagline": "Find the HI balance.",
            "domain": "thehibalance.org", "foundation": "The HI Balance",
        },
    })


@app.route("/api/v1/heartbeat/pulse")
def heartbeat_pulse():
    """Ecosystem pulse — overall health of the HI balance."""
    return jsonify(HEARTBEAT_PULSE or {
        "pulse": "unknown", "average_decay": 0,
        "companies_analyzed": 0, "alerts_count": 0,
    })


@app.route("/api/v1/heartbeat/alerts")
def heartbeat_alerts():
    """Companies with elevated decay risk."""
    limit = min(int(request.args.get("limit", 20)), 100)
    level = request.args.get("level", "")  # critical, warning
    alerts = HEARTBEAT_ALERTS
    if level:
        alerts = [a for a in alerts if a.get("decay_level") == level]
    return jsonify({
        "count": len(alerts[:limit]),
        "total": len(alerts),
        "results": alerts[:limit],
    })


@app.route("/api/v1/heartbeat/<ticker>")
def heartbeat_company(ticker):
    """Heartbeat data for a specific company."""
    ticker = ticker.upper().strip()
    if ticker in HEARTBEAT:
        return jsonify(HEARTBEAT[ticker])
    return jsonify({"error": "not_found", "ticker": ticker}), 404


# ═══ HUMAN 100 INDEX — Patent Feature ═══

@app.route("/api/v1/human100")
def human100_index():
    """The full HUMAN 100 Index."""
    limit = min(int(request.args.get("limit", 100)), 100)
    return jsonify({
        "index_name": "HUMAN 100",
        "constituents_count": len(HUMAN100),
        "metadata": HUMAN100_META,
        "constituents": HUMAN100[:limit],
    })


@app.route("/api/v1/human100/metadata")
def human100_metadata():
    """Index metadata — stats, methodology, rebalance info."""
    return jsonify(HUMAN100_META or {"error": "Index not yet generated"})


@app.route("/api/v1/human100/check/<ticker>")
def human100_check(ticker):
    """Check if a company is in the HUMAN 100."""
    ticker = ticker.upper().strip()
    for c in HUMAN100:
        if c.get("ticker", "").upper() == ticker:
            return jsonify({"in_index": True, **c})
    return jsonify({"in_index": False, "ticker": ticker})


# ═══ GRADE ARBITRAGE — Patent Feature ═══

@app.route("/api/v1/arbitrage")
def arbitrage_all():
    """All grade arbitrage results."""
    arb_type = request.args.get("type", "")  # esg_washing, hidden_gem, aligned, double_risk
    limit = min(int(request.args.get("limit", 50)), 200)
    results = ARBITRAGE
    if arb_type:
        results = [r for r in results if r.get("arbitrage_type") == arb_type]
    return jsonify({
        "total": len(results),
        "metadata": ARBITRAGE_META,
        "results": results[:limit],
    })


@app.route("/api/v1/arbitrage/washers")
def arbitrage_washers():
    """Companies where ESG overrates vs HI."""
    limit = min(int(request.args.get("limit", 20)), 100)
    washers = [r for r in ARBITRAGE if r.get("arbitrage_type") == "esg_washing"]
    return jsonify({"count": len(washers), "results": washers[:limit]})


@app.route("/api/v1/arbitrage/gems")
def arbitrage_gems():
    """Companies where HI outperforms ESG."""
    limit = min(int(request.args.get("limit", 20)), 100)
    gems = [r for r in ARBITRAGE if r.get("arbitrage_type") == "hidden_gem"]
    return jsonify({"count": len(gems), "results": gems[:limit]})


@app.route("/api/v1/arbitrage/<ticker>")
def arbitrage_company(ticker):
    """Arbitrage data for a specific company."""
    ticker = ticker.upper().strip()
    for r in ARBITRAGE:
        if r.get("ticker", "").upper() == ticker:
            return jsonify(r)
    return jsonify({"error": "not_found", "ticker": ticker}), 404


# ═══ ETHICAL MOAT — Patent Feature ═══

@app.route("/api/v1/moat")
def moat_all():
    """All ethical moat results."""
    level = request.args.get("level", "")
    limit = min(int(request.args.get("limit", 50)), 1000)
    results = MOATS
    if level:
        # Handle both old and new level names
        aliases = {"developing": ["developing", "moderate"], "vulnerable": ["vulnerable", "thin"],
                   "moderate": ["moderate", "developing"], "thin": ["thin", "vulnerable"]}
        match_levels = aliases.get(level, [level])
        results = [r for r in results if r.get("moat_level") in match_levels]
    return jsonify({
        "total": len(results),
        "metadata": MOATS_META,
        "results": results[:limit],
    })


@app.route("/api/v1/moat/fortresses")
def moat_fortresses():
    """Companies with fortress-level AI displacement resistance."""
    limit = min(int(request.args.get("limit", 20)), 100)
    forts = [r for r in MOATS if r.get("moat_level") == "fortress"]
    return jsonify({"count": len(forts), "results": forts[:limit]})


@app.route("/api/v1/moat/vulnerable")
def moat_vulnerable():
    """Companies most vulnerable to AI displacement."""
    limit = min(int(request.args.get("limit", 20)), 100)
    vuln = [r for r in MOATS if r.get("moat_level") in ("vulnerable", "none")]
    return jsonify({"count": len(vuln), "results": vuln[:limit]})


@app.route("/api/v1/moat/<ticker>")
def moat_company(ticker):
    """Ethical moat data for a specific company."""
    ticker = ticker.upper().strip()
    for r in MOATS:
        if r.get("ticker", "").upper() == ticker:
            return jsonify(r)
    return jsonify({"error": "not_found", "ticker": ticker}), 404


# ═══ CONTAGION EFFECT — Patent Feature ═══

@app.route("/api/v1/contagion")
def contagion_all():
    """Supply chain ethics ripple scores."""
    ctype = request.args.get("type", "")
    limit = min(int(request.args.get("limit", 50)), 200)
    results = CONTAGION
    if ctype:
        results = [r for r in results if r.get("contagion_type") == ctype]
    return jsonify({"total": len(results), "results": results[:limit]})


@app.route("/api/v1/contagion/<ticker>")
def contagion_company(ticker):
    ticker = ticker.upper().strip()
    for r in CONTAGION:
        if r.get("ticker", "").upper() == ticker:
            return jsonify(r)
    return jsonify({"error": "not_found", "ticker": ticker}), 404


# ═══ EMPATHY WATERMARK — Patent Feature ═══

@app.route("/api/v1/empathy")
def empathy_all():
    """Empathy authenticity watermarks."""
    wm = request.args.get("watermark", "")
    limit = min(int(request.args.get("limit", 50)), 200)
    results = EMPATHY_WM
    if wm:
        results = [r for r in results if r.get("watermark") == wm]
    return jsonify({"total": len(results), "results": results[:limit]})


@app.route("/api/v1/empathy/performative")
def empathy_performative():
    """Companies with performative empathy."""
    limit = min(int(request.args.get("limit", 20)), 100)
    perf = [r for r in EMPATHY_WM if r.get("watermark") == "performative"]
    return jsonify({"count": len(perf), "results": perf[:limit]})


@app.route("/api/v1/empathy/<ticker>")
def empathy_company(ticker):
    ticker = ticker.upper().strip()
    for r in EMPATHY_WM:
        if r.get("ticker", "").upper() == ticker:
            return jsonify(r)
    return jsonify({"error": "not_found", "ticker": ticker}), 404


# ═══ CONSUMER CONSCIOUSNESS — Patent Feature ═══

@app.route("/api/v1/consciousness")
def consciousness_benchmarks():
    """Consumer consciousness benchmarks and tiers."""
    return jsonify(CONSUMER_BENCH or {"error": "Benchmarks not yet generated"})


@app.route("/api/v1/consciousness/industry/<industry>")
def consciousness_industry(industry):
    """Benchmark for a specific industry."""
    benchmarks = CONSUMER_BENCH.get("industry_benchmarks", {})
    ind = industry.lower().strip()
    if ind in benchmarks:
        return jsonify({"industry": ind, **benchmarks[ind]})
    return jsonify({"error": "not_found", "industry": ind}), 404


# ═══ COLLECTIVE BARGAINING — Patent Feature ═══

@app.route("/api/v1/collective")
def collective_signals():
    """Collective bargaining signals — market pressure data."""
    return jsonify(COLLECTIVE or {"error": "Signals not yet generated"})


@app.route("/api/v1/collective/pressure")
def collective_pressure():
    """Industry pressure rankings."""
    return jsonify({
        "industry_pressure": COLLECTIVE.get("industry_pressure", []),
        "dimension_pressure": COLLECTIVE.get("dimension_pressure", {}),
    })


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HI. Score API")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--data", default="data/scores")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--quarterly", action="store_true", help="Recalculate HI Balanced threshold (run quarterly only)")
    args = parser.parse_args()

    # Railway/Render/Fly set PORT env var automatically
    port = args.port or int(os.environ.get("PORT", 5000))

    global DATA_DIR
    DATA_DIR = Path(args.data)
    
    if args.quarterly:
        app._quarterly_mode = True
        print("🔄 QUARTERLY MODE — Threshold will be recalculated")

    print("HI. Score API — Find the HI balance.")
    print("thehibalance.org | The HI Balance")
    print("=" * 50)
    build_index()
    print("=" * 50)
    print(f"http://localhost:{port}/")
    print("=" * 50)

    app.run(host=args.host, port=port, debug=args.debug)


if __name__ == "__main__":
    main()
else:
    print("HI. Score API starting under gunicorn")
    build_index()
