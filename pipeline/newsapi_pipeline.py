#!/usr/bin/env python3
"""
NewsAPI Pipeline — Broad Media Monitoring
Source: https://newsapi.org
Free tier: 100 requests/day, 1 month of articles

Pulls: Company news from 150K+ sources (CNN, BBC, NYT, TechCrunch, etc.)
Catches: Layoff announcements, CEO controversies, environmental disasters,
         ethics violations, AI pivots, employee treatment stories
Maps to: All dimensions via Heartbeat, M (ethics news), H (layoff news)

Get free API key: https://newsapi.org/register
"""

import json, time, sys, os, re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

try:
    import requests
except ImportError:
    print("Install: pip install requests --break-system-packages")
    sys.exit(1)

BASE = "https://newsapi.org/v2"

# HUMAN-relevant keyword categories
CATEGORIES = {
    "layoff": {
        "keywords": ["layoff", "laid off", "layoffs", "job cuts", "workforce reduction",
                     "downsizing", "restructuring", "mass firing", "eliminating positions",
                     "staff cuts", "headcount reduction"],
        "dimension": "H",
        "severity_weight": 3,
    },
    "ai_pivot": {
        "keywords": ["artificial intelligence", "ai strategy", "ai-powered", "generative ai",
                     "replacing workers with ai", "automation replacing", "machine learning deployment",
                     "ai workforce", "chatbot replacing"],
        "dimension": "H",
        "severity_weight": 2,
    },
    "ethics": {
        "keywords": ["lawsuit", "sued", "fraud", "scandal", "investigation", "SEC investigation",
                     "fine", "penalty", "settlement", "whistleblower", "discrimination",
                     "harassment", "cover-up", "data breach", "privacy violation"],
        "dimension": "M",
        "severity_weight": 3,
    },
    "ceo_controversy": {
        "keywords": ["ceo fired", "ceo resigned", "ceo controversy", "executive pay",
                     "ceo compensation", "golden parachute", "pay ratio",
                     "ceo under fire", "leadership change", "board ousted"],
        "dimension": "M",
        "severity_weight": 2,
    },
    "environment": {
        "keywords": ["pollution", "emissions scandal", "oil spill", "environmental damage",
                     "carbon footprint", "toxic waste", "contamination", "epa violation",
                     "climate pledge", "deforestation"],
        "dimension": "A",
        "severity_weight": 3,
    },
    "employee_treatment": {
        "keywords": ["unsafe working conditions", "worker exploitation", "union busting",
                     "employee walkout", "worker strike", "forced overtime",
                     "warehouse conditions", "worker safety", "labor violation"],
        "dimension": "U",
        "severity_weight": 3,
    },
    "transparency": {
        "keywords": ["cover up", "misleading investors", "greenwashing", "fake reviews",
                     "hidden fees", "deceptive practices", "ai-generated without disclosure"],
        "dimension": "N",
        "severity_weight": 2,
    },
    "positive": {
        "keywords": ["living wage", "employee owned", "paid family leave", "carbon neutral",
                     "b corp", "fair trade", "worker cooperative", "profit sharing",
                     "community investment", "sustainability achievement"],
        "dimension": "ALL",
        "severity_weight": -2,  # Positive signal — boosts score
    },
}


def get_api_key():
    key = os.environ.get("NEWSAPI_KEY", "")
    if not key:
        kf = Path("data/newsapi_key.txt")
        if kf.exists(): key = kf.read_text().strip()
    if not key:
        print("No NewsAPI key. Get free key at:")
        print("  https://newsapi.org/register")
        print("Then: echo YOUR_KEY > data/newsapi_key.txt")
        sys.exit(1)
    return key


def load_companies():
    """Load top companies to monitor (prioritize by score and data)."""
    companies = []
    sf = Path("data/scores/all_scores.json")
    if sf.exists():
        seen = set()
        for c in json.load(open(sf)):
            name = c.get("company", "")
            ticker = c.get("ticker", "")
            # Deduplicate by ticker
            key = ticker.upper() if ticker else name.lower()
            if key in seen:
                continue
            seen.add(key)
            companies.append({"company": name, "ticker": ticker})
    return companies


def search_company_news(company_name, key, days=30):
    """Search NewsAPI for recent articles about a company."""
    try:
        # Simplify company name for search
        simple = re.sub(r',?\s+(Inc\.?|Corp\.?|LLC|Ltd\.?|Co\.?|PLC|SA|AG|Company|Corporation|Incorporated)\.?\s*$',
                       '', company_name, flags=re.IGNORECASE).strip()
        # Remove parentheticals
        simple = re.sub(r'\s*[\(\[].*?[\)\]]', '', simple).strip()

        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        r = requests.get(f"{BASE}/everything", params={
            "q": f'"{simple}"',
            "sortBy": "relevancy",
            "pageSize": 20,
            "language": "en",
            "apiKey": key,
        }, timeout=15)

        if r.status_code == 429:
            print("    Rate limited — stopping")
            return None
        if r.status_code != 200:
            print(f"    API status {r.status_code}")
            return []

        data = r.json()
        return data.get("articles", [])
    except Exception as e:
        print(f"    Error: {e}")
        return []


def analyze_articles(articles, company_name):
    """Analyze articles for HUMAN-relevant signals."""
    signals = defaultdict(lambda: {
        "count": 0,
        "headlines": [],
        "sources": [],
    })

    total = len(articles) if articles else 0

    if not articles:
        return {"total_articles": 0, "categories": {}}

    for article in articles:
        title = (article.get("title") or "").lower()
        desc = (article.get("description") or "").lower()
        source = article.get("source", {}).get("name", "")
        text = f"{title} {desc}"

        for category, config in CATEGORIES.items():
            for kw in config["keywords"]:
                if kw in text:
                    sig = signals[category]
                    sig["count"] += 1
                    if len(sig["headlines"]) < 3:
                        sig["headlines"].append(article.get("title", "")[:120])
                    if source and source not in sig["sources"]:
                        sig["sources"].append(source)
                    break  # Only count once per category per article

    return {
        "total_articles": total,
        "categories": {k: dict(v) for k, v in signals.items()},
    }


def compute_news_impact(analysis):
    """Compute impact score from news analysis. Higher = more concerning."""
    impact = 0
    details = {}

    for category, config in CATEGORIES.items():
        count = analysis.get("categories", {}).get(category, {}).get("count", 0)
        if count > 0:
            weight = config["severity_weight"]
            category_impact = count * weight
            impact += category_impact
            details[category] = {
                "count": count,
                "impact": category_impact,
                "dimension": config["dimension"],
            }

    return {
        "total_impact": impact,
        "details": details,
        "risk_level": "critical" if impact > 15 else "high" if impact > 8 else "medium" if impact > 3 else "low",
    }


def run_pipeline(limit=None):
    key = get_api_key()
    output_dir = Path("data/newsapi")
    output_dir.mkdir(parents=True, exist_ok=True)

    companies = load_companies()

    # Load existing to append
    output_file = output_dir / "all_companies.json"
    existing = {}
    if output_file.exists():
        for c in json.load(open(output_file)):
            k = c.get("ticker", "") or c.get("company", "")
            if k: existing[k.upper() if isinstance(k, str) else k] = c

    to_fetch = [c for c in companies
                if (c.get("ticker", "") or c.get("company", "")).upper() not in existing]

    # Free tier: 100 requests/day
    max_daily = min(len(to_fetch), 90) if not limit else limit
    to_fetch = to_fetch[:max_daily]

    print(f"\n{'='*60}")
    print(f"  NewsAPI Pipeline — Broad Media Monitoring")
    print(f"{'='*60}")
    print(f"  API key: {key[:4]}...{key[-4:]}")
    print(f"  Companies to scan: {len(to_fetch)}")
    print(f"  Free tier: 100 req/day (1 req per company)")
    print(f"  Coverage: 150K+ sources, last 30 days")
    print(f"{'='*60}\n")

    records = list(existing.values())
    errors = 0
    alerts = []

    for i, comp in enumerate(to_fetch):
        name = comp["company"]
        ticker = comp.get("ticker", "")

        articles = search_company_news(name, key)

        if articles is None:
            # Rate limited
            print(f"  Rate limited at {i+1}/{len(to_fetch)} — saving progress")
            break

        analysis = analyze_articles(articles, name)
        impact = compute_news_impact(analysis)

        record = {
            "company": name,
            "ticker": ticker,
            "news_signals": {
                "total_articles_30d": analysis["total_articles"],
                "risk_level": impact["risk_level"],
                "total_impact": impact["total_impact"],
                "categories": {k: v["count"] for k, v in analysis.get("categories", {}).items()},
            },
            "heartbeat": {
                "news_risk_level": impact["risk_level"],
                "news_impact": impact["total_impact"],
                "news_details": impact["details"],
                "news_headlines": {
                    cat: data.get("headlines", [])
                    for cat, data in analysis.get("categories", {}).items()
                    if data.get("headlines")
                },
            },
            "source": "NewsAPI",
        }

        records.append(record)
        k = ticker.upper() if ticker else name.upper()
        existing[k] = record

        # Print summary
        total = analysis["total_articles"]
        risk = impact["risk_level"]
        cats = analysis.get("categories", {})
        cat_str = ", ".join(f"{k}:{v['count']}" for k, v in cats.items() if v["count"] > 0)
        icon = "🔴" if risk == "critical" else "🟡" if risk == "high" else "🟠" if risk == "medium" else "⚪"

        print(f"  [{i+1}/{len(to_fetch)}] {icon} {name[:30]:30s} Articles: {total:>3d}  Risk: {risk:8s}  {cat_str}")

        if risk in ["critical", "high"]:
            alerts.append({
                "company": name,
                "ticker": ticker,
                "risk": risk,
                "impact": impact["total_impact"],
                "details": impact["details"],
                "headlines": {
                    cat: data.get("headlines", [])
                    for cat, data in analysis.get("categories", {}).items()
                    if data.get("headlines")
                },
            })

        time.sleep(1.0)  # Be nice to the API

    # Save
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)

    # Save alerts
    if alerts:
        with open(output_dir / "alerts.json", "w") as f:
            json.dump(alerts, f, indent=2)

    # Stats
    risk_counts = defaultdict(int)
    for r in records:
        risk_counts[r["news_signals"]["risk_level"]] += 1

    print(f"\n{'='*60}")
    print(f"  COMPLETE — {len(records)} companies monitored")
    print(f"  Risk levels:")
    print(f"    Critical: {risk_counts['critical']}")
    print(f"    High:     {risk_counts['high']}")
    print(f"    Medium:   {risk_counts['medium']}")
    print(f"    Low:      {risk_counts['low']}")
    print(f"  Alerts: {len(alerts)}")

    if alerts:
        print(f"\n  ⚠ NEWS ALERTS:")
        for a in alerts[:10]:
            t = a["ticker"] or "—"
            details = ", ".join(f"{k}: {v['count']}" for k, v in a["details"].items())
            print(f"    🔴 {a['company'][:25]:25s} {t:>6s}  Impact: {a['impact']:>3d}  {details}")

    print(f"\n  Output: {output_file}")
    print(f"  Feeds into: Heartbeat monitor, M/H/A/U/N dimensions")
    print(f"  Run daily to catch breaking news (appends, skips fetched)")
    print(f"{'='*60}\n")

    return records


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    run_pipeline(limit=p.parse_args().limit)
