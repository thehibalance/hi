#!/usr/bin/env python3
"""
HI. — REST API
Phase 2, Track C: API layer serving HI Grades.

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
  pip install flask flask-cors
  python api_server.py
  python api_server.py --port 8080
"""

import json, os, sys, re
from pathlib import Path
from datetime import datetime

try:
    from flask import Flask, jsonify, request
    from flask_cors import CORS
except ImportError:
    print("Install: pip install flask flask-cors")
    sys.exit(1)

app = Flask(__name__)
CORS(app)

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
    if score >= 90: return "HI Certified"
    if score >= 80: return "A"
    if score >= 60: return "B"
    if score >= 42: return "C"
    return "F"

SATIRES = {
    "HI Certified": "Humans and tech, in harmony. This is what balance looks like.",
    "A": "AI does the math. Humans do the handshakes. Nailed it.",
    "B": "Humans and machines, learning to share the remote.",
    "C": "42. The answer to everything. Now what's the question?",
    "F": "Don't panic. Every journey starts somewhere.",
}


def seed_to_record(s):
    composite = round((s["h"] + s["u"] + s["m"] + s["a"] + s["n"]) / 5, 1)
    if min(s["h"], s["u"], s["m"], s["a"], s["n"]) < 10:
        composite = min(composite, 40.0)
    grade = get_grade(composite)
    return {
        "company": s["name"], "ticker": None,
        "domains": s.get("domains", []), "tags": s.get("tags", []),
        "D_H": s["h"], "D_U": s["u"], "D_M": s["m"], "D_A": s["a"], "D_N": s["n"],
        "composite": composite, "hi_grade": grade, "satire": SATIRES.get(grade, ""),
        "floor_triggered": min(s["h"], s["u"], s["m"], s["a"], s["n"]) < 10,
        "confidence": "Estimated", "data_sources": ["Manual Scoring"],
        "notes": s.get("notes", ""), "spec_version": "1.0.0",
        "industry": s["tags"][0] if s.get("tags") else "",
        "humanwashing_flags": [],
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

    # Load HUMAN 100 Index
    h100_dir = DATA_DIR.parent / "human100"
    if (h100_dir / "index.json").exists():
        HUMAN100 = json.load(open(h100_dir / "index.json"))
        print(f"  HUMAN 100: {len(HUMAN100)} constituents")
    if (h100_dir / "metadata.json").exists():
        HUMAN100_META = json.load(open(h100_dir / "metadata.json"))

    # Load HUMAN Lens data
    arb_dir = DATA_DIR.parent / "arbitrage"
    if (arb_dir / "all_arbitrage.json").exists():
        ARBITRAGE = json.load(open(arb_dir / "all_arbitrage.json"))
        print(f"  Arbitrage: {len(ARBITRAGE)} companies analyzed")
    if (arb_dir / "metadata.json").exists():
        ARBITRAGE_META = json.load(open(arb_dir / "metadata.json"))

    # Load HUMAN Shield data
    moat_dir = DATA_DIR.parent / "ethical_moat"
    if (moat_dir / "all_moats.json").exists():
        MOATS = json.load(open(moat_dir / "all_moats.json"))
        print(f"  HUMAN Shield: {len(MOATS)} companies analyzed")
    if (moat_dir / "metadata.json").exists():
        MOATS_META = json.load(open(moat_dir / "metadata.json"))

    # Load HUMAN Contagion
    cont_dir = DATA_DIR.parent / "contagion"
    if (cont_dir / "all_contagion.json").exists():
        CONTAGION = json.load(open(cont_dir / "all_contagion.json"))
        print(f"  Contagion: {len(CONTAGION)} companies")

    # Load Empathy Watermark
    ew_dir = DATA_DIR.parent / "empathy_watermark"
    if (ew_dir / "all_watermarks.json").exists():
        EMPATHY_WM = json.load(open(ew_dir / "all_watermarks.json"))
        print(f"  Empathy Watermark: {len(EMPATHY_WM)} companies")

    # Load HUMAN Consciousness
    cc_dir = DATA_DIR.parent / "consumer_consciousness"
    if (cc_dir / "benchmarks.json").exists():
        CONSUMER_BENCH = json.load(open(cc_dir / "benchmarks.json"))
        print(f"  HUMAN Consciousness: benchmarks loaded")

    # Load HUMAN Wave
    cb_dir = DATA_DIR.parent / "collective_bargaining"
    if (cb_dir / "signals.json").exists():
        COLLECTIVE = json.load(open(cb_dir / "signals.json"))
        print(f"  HUMAN Wave: signals loaded")

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
            if t and t.upper() in sp500_domains and not c.get("domains"):
                c["domains"] = sp500_domains[t.upper()]
            
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
            
            # Index by domain
            for d in c.get("domains", []):
                d = d.lower().strip()
                if d and d not in COMPANIES:
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

    ALL_COMPANIES.sort(key=lambda x: x.get("composite", 0), reverse=True)
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
    domain = re.sub(r"^(https?://)?(www\.)?", "", domain.lower().strip()).split("/")[0]

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
    ticker = ticker.upper().strip()
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
def search():
    q = request.args.get("q", "").lower().strip()
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
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 50)), 200)
    grade_filter = request.args.get("grade", "").upper()

    filtered = ALL_COMPANIES
    if grade_filter:
        gmap = {"HI": "HI Certified", "A": "A", "B": "B", "C": "C", "F": "F"}
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
    limit = min(int(request.args.get("limit", 10)), 100)
    results = []
    for i, c in enumerate(ALL_COMPANIES[:limit]):
        rec = dict(c)
        rec["rank"] = i + 1
        results.append(rec)
    return jsonify({"count": len(results), "results": results})


@app.route("/api/v1/grades/bottom")
def bottom_grades():
    limit = min(int(request.args.get("limit", 10)), 100)
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
    avg = round(sum(composites) / len(composites), 1) if composites else 0

    return jsonify({
        "total_companies": len(ALL_COMPANIES),
        "domains_indexed": len(COMPANIES),
        "tickers_indexed": len(TICKERS),
        "grade_distribution": grades,
        "average_composite": avg,
        "humanwashing_flagged": sum(1 for c in ALL_COMPANIES if c.get("humanwashing_flags")),
        "floor_rule_triggered": sum(1 for c in ALL_COMPANIES if c.get("floor_triggered")),
        "data_sources": 18,
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
    level = request.args.get("level", "")  # fortress, strong, moderate, thin, none
    limit = min(int(request.args.get("limit", 50)), 200)
    results = MOATS
    if level:
        results = [r for r in results if r.get("moat_level") == level]
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
    vuln = [r for r in MOATS if r.get("moat_level") in ("thin", "none")]
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
    args = parser.parse_args()

    # Railway/Render/Fly set PORT env var automatically
    port = args.port or int(os.environ.get("PORT", 5000))

    global DATA_DIR
    DATA_DIR = Path(args.data)

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
