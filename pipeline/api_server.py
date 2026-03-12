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


def build_index():
    global COMPANIES, TICKERS, NAME_INDEX, ALL_COMPANIES
    COMPANIES, TICKERS, NAME_INDEX, ALL_COMPANIES = {}, {}, {}, []

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
        for c in scored:
            if c.get("error"): continue
            t = c.get("ticker", "")
            
            # Inject domains from S&P 500 mapping if not already present
            if t and t.upper() in sp500_domains and not c.get("domains"):
                c["domains"] = sp500_domains[t.upper()]
            
            if t: TICKERS[t.upper()] = c
            n = c.get("company", "")
            if n: NAME_INDEX[n.lower()] = c
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
    for seed_path in seed_candidates:
        if os.path.exists(seed_path):
            content = open(seed_path).read()
            start = content.index("const SEED_COMPANIES = ") + len("const SEED_COMPANIES = ")
            end = content.index("];", start) + 1
            for s in json.loads(content[start:end]):
                rec = seed_to_record(s)
                if rec["company"].lower() not in NAME_INDEX:
                    NAME_INDEX[rec["company"].lower()] = rec
                    ALL_COMPANIES.append(rec)
                for d in rec.get("domains", []):
                    d = d.lower().strip()
                    if d and d not in COMPANIES:
                        COMPANIES[d] = rec
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


@app.route("/api/v1/search")
def search():
    q = request.args.get("q", "").lower().strip()
    if len(q) < 2:
        return jsonify({"error": "Query too short (min 2 chars)"}), 400

    limit = min(int(request.args.get("limit", 20)), 100)
    results = []
    for c in ALL_COMPANIES:
        name = c.get("company", "").lower()
        tags = " ".join(c.get("tags", [])).lower()
        if q in name or q in tags:
            results.append(c)
        if len(results) >= limit:
            break

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
        "spec_version": "1.0.0",
        "brand": {
            "name": "HI.", "tagline": "Find the HI balance.",
            "domain": "thehibalance.org", "foundation": "The Deep Thought Foundation",
        },
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
    print("thehibalance.org | The Deep Thought Foundation")
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
