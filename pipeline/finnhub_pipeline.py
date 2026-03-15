#!/usr/bin/env python3
"""
Finnhub Pipeline — ESG Scores + Company News
Source: https://finnhub.io
Free tier: 60 requests/minute

Pulls: ESG scores (total, E, S, G), company news (layoffs, AI, restructuring)
Maps to: U (social score), M (governance), A (environmental), N (transparency)
Also feeds: HUMAN Heartbeat (real-time event detection)

Get free API key: https://finnhub.io/register
"""

import json, time, sys, os, re
from pathlib import Path
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("Install: pip install requests --break-system-packages")
    sys.exit(1)

BASE = "https://finnhub.io/api/v1"

# Keywords that signal HUMAN-relevant events
LAYOFF_KEYWORDS = ["layoff", "laid off", "layoffs", "workforce reduction", "job cuts", "restructuring", "downsizing", "eliminating positions", "staff cuts"]
AI_KEYWORDS = ["artificial intelligence", "ai strategy", "machine learning", "automation", "replacing workers", "ai-powered", "generative ai"]
ETHICS_KEYWORDS = ["lawsuit", "fine", "penalty", "fraud", "scandal", "investigation", "violation", "settlement"]
ENV_KEYWORDS = ["emissions", "carbon", "climate", "pollution", "environmental", "sustainability"]


def get_api_key():
    key = os.environ.get("FINNHUB_KEY", "")
    if not key:
        kf = Path("data/finnhub_key.txt")
        if kf.exists(): key = kf.read_text().strip()
    if not key:
        print("No Finnhub API key. Get free key at:")
        print("  https://finnhub.io/register")
        print("Then: echo YOUR_KEY > data/finnhub_key.txt")
        sys.exit(1)
    return key


def load_tickers():
    tickers = set()
    sf = Path("data/scores/all_scores.json")
    if sf.exists():
        for c in json.load(open(sf)):
            t = c.get("ticker", "")
            if t and isinstance(t, str) and len(t) <= 5:
                tickers.add(t.upper())
    return sorted(tickers)


def fetch_esg(ticker, key):
    try:
        r = requests.get(f"{BASE}/stock/esg?symbol={ticker}&token={key}", timeout=15)
        d = r.json()
        if d and isinstance(d, dict) and d.get("data"):
            latest = d["data"][-1] if isinstance(d["data"], list) else d["data"]
            return latest
        return None
    except:
        return None


def fetch_news(ticker, key, days=90):
    try:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        r = requests.get(f"{BASE}/company-news?symbol={ticker}&from={start}&to={end}&token={key}", timeout=15)
        d = r.json()
        return d if isinstance(d, list) else []
    except:
        return []


def analyze_news(articles):
    """Analyze news for HUMAN-relevant signals."""
    signals = {
        "layoff_mentions": 0,
        "ai_mentions": 0,
        "ethics_mentions": 0,
        "env_mentions": 0,
        "total_articles": len(articles),
        "layoff_headlines": [],
        "ai_headlines": [],
    }

    for a in articles:
        text = (a.get("headline", "") + " " + a.get("summary", "")).lower()

        for kw in LAYOFF_KEYWORDS:
            if kw in text:
                signals["layoff_mentions"] += 1
                if len(signals["layoff_headlines"]) < 3:
                    signals["layoff_headlines"].append(a.get("headline", "")[:100])
                break

        for kw in AI_KEYWORDS:
            if kw in text:
                signals["ai_mentions"] += 1
                if len(signals["ai_headlines"]) < 3:
                    signals["ai_headlines"].append(a.get("headline", "")[:100])
                break

        for kw in ETHICS_KEYWORDS:
            if kw in text:
                signals["ethics_mentions"] += 1
                break

        for kw in ENV_KEYWORDS:
            if kw in text:
                signals["env_mentions"] += 1
                break

    return signals


def process_company(ticker, key):
    esg = fetch_esg(ticker, key)
    time.sleep(1.1)  # 60 req/min limit
    news = fetch_news(ticker, key)
    time.sleep(1.1)

    news_signals = analyze_news(news)

    esg_total = None
    esg_e = None
    esg_s = None
    esg_g = None

    if esg:
        esg_total = esg.get("totalESG")
        esg_e = esg.get("environmentalScore")
        esg_s = esg.get("socialScore")
        esg_g = esg.get("governanceScore")

    return {
        "company": None,  # Filled by scoring engine
        "ticker": ticker,
        "u_signals": {
            "esg_social": esg_s,
        },
        "m_signals": {
            "esg_governance": esg_g,
            "ethics_news_count": news_signals["ethics_mentions"],
        },
        "a_signals": {
            "esg_environmental": esg_e,
            "env_news_count": news_signals["env_mentions"],
        },
        "n_signals": {
            "esg_total": esg_total,
        },
        "heartbeat": {
            "layoff_mentions_90d": news_signals["layoff_mentions"],
            "ai_mentions_90d": news_signals["ai_mentions"],
            "ethics_mentions_90d": news_signals["ethics_mentions"],
            "env_mentions_90d": news_signals["env_mentions"],
            "total_articles_90d": news_signals["total_articles"],
            "layoff_headlines": news_signals["layoff_headlines"],
            "ai_headlines": news_signals["ai_headlines"],
        },
        "source": "Finnhub",
    }


def run_pipeline(limit=None):
    key = get_api_key()
    output_dir = Path("data/finnhub")
    output_dir.mkdir(parents=True, exist_ok=True)

    tickers = load_tickers()

    output_file = output_dir / "all_companies.json"
    existing = {}
    if output_file.exists():
        for c in json.load(open(output_file)):
            existing[c["ticker"]] = c

    to_fetch = [t for t in tickers if t not in existing]
    if limit: to_fetch = to_fetch[:limit]

    # 2 calls per company, 60/min = ~25 companies/min
    max_batch = min(len(to_fetch), 500)
    to_fetch = to_fetch[:max_batch]

    print(f"\n{'='*60}")
    print(f"  Finnhub Pipeline — ESG + News")
    print(f"{'='*60}")
    print(f"  API key: {key[:4]}...{key[-4:]}")
    print(f"  New to fetch: {len(to_fetch)}")
    print(f"  Rate: 2 calls/company, 60/min")
    print(f"  Est. time: {len(to_fetch) * 2.5 // 60:.0f} minutes")
    print(f"{'='*60}\n")

    records = list(existing.values())
    errors = 0

    for i, ticker in enumerate(to_fetch):
        result = process_company(ticker, key)
        if result:
            records.append(result)
            existing[ticker] = result
            esg = result["n_signals"]["esg_total"]
            layoffs = result["heartbeat"]["layoff_mentions_90d"]
            ai = result["heartbeat"]["ai_mentions_90d"]
            esg_s = f"{esg:.1f}" if esg else "—"
            print(f"  [{i+1}/{len(to_fetch)}] {ticker:6s} ESG: {esg_s:>6s}  Layoff news: {layoffs:>3d}  AI news: {ai:>3d}")
        else:
            errors += 1
            print(f"  [{i+1}/{len(to_fetch)}] {ticker:6s} — skipped")

    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)

    # Heartbeat alerts
    heartbeat_dir = Path("data/heartbeat")
    heartbeat_dir.mkdir(parents=True, exist_ok=True)

    alerts = []
    for r in records:
        hb = r.get("heartbeat", {})
        if hb.get("layoff_mentions_90d", 0) >= 3:
            alerts.append({
                "ticker": r["ticker"],
                "type": "layoff_surge",
                "count": hb["layoff_mentions_90d"],
                "headlines": hb.get("layoff_headlines", []),
                "severity": "high" if hb["layoff_mentions_90d"] >= 5 else "medium",
            })
        if hb.get("ai_mentions_90d", 0) >= 5:
            alerts.append({
                "ticker": r["ticker"],
                "type": "ai_acceleration",
                "count": hb["ai_mentions_90d"],
                "headlines": hb.get("ai_headlines", []),
                "severity": "high" if hb["ai_mentions_90d"] >= 10 else "medium",
            })

    with open(heartbeat_dir / "alerts.json", "w") as f:
        json.dump(alerts, f, indent=2)

    has_esg = sum(1 for r in records if r["n_signals"]["esg_total"])
    has_news = sum(1 for r in records if r["heartbeat"]["total_articles_90d"] > 0)

    print(f"\n{'='*60}")
    print(f"  COMPLETE — {len(records)} total ({len(to_fetch)-errors} new)")
    print(f"  With ESG scores: {has_esg}")
    print(f"  With news data:  {has_news}")
    print(f"  Heartbeat alerts: {len(alerts)}")
    if alerts:
        print(f"\n  \u26a0 HEARTBEAT ALERTS:")
        for a in alerts[:10]:
            print(f"    {a['ticker']:6s} {a['type']:20s} ({a['count']} mentions, {a['severity']})")
    print(f"\n  Output: {output_file}")
    print(f"  Alerts: {heartbeat_dir / 'alerts.json'}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    run_pipeline(limit=p.parse_args().limit)
