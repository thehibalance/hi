#!/usr/bin/env python3
"""
HUMAN Heartbeat — Real-Time Score Event Monitor
Patent Feature: Consciousness Decay Index + HUMAN Heartbeat

The Heartbeat aggregates signals from multiple pipelines to detect:
1. Layoff surges (H dimension at risk)
2. AI acceleration (H dimension changing)
3. Ethics/legal events (M dimension at risk)
4. Environmental events (A dimension at risk)
5. Leadership changes (all dimensions)
6. Score trajectory (is the company improving or declining?)

Inputs: Finnhub news, Layoffs.fyi, SEC 8-K, all scored data
Output: heartbeat.json with alerts, decay index, and recommendations

This is the first patent feature to go live.
"""

import json, sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def load_json(path):
    if Path(path).exists():
        return json.load(open(path))
    return []


def load_dict(path, key="ticker"):
    data = load_json(path)
    idx = {}
    for r in data:
        k = r.get(key, "")
        if k: idx[k.upper() if isinstance(k, str) else k] = r
    return idx


def compute_heartbeat():
    print(f"\n{'='*60}")
    print(f"  HUMAN Heartbeat — Score Event Monitor")
    print(f"  Patent Feature: Consciousness Decay Index")
    print(f"{'='*60}\n")

    # Load all data sources
    scores = load_json("data/scores/all_scores.json")
    finnhub = load_dict("data/finnhub/all_companies.json")
    layoffs = load_dict("data/layoffs/all_companies.json", key="company")
    sec_8k = load_dict("data/sec_8k/all_companies.json")

    # Normalize layoffs keys for matching
    layoffs_lower = {}
    for k, v in layoffs.items():
        layoffs_lower[k.lower().strip()] = v

    output_dir = Path("data/heartbeat")
    output_dir.mkdir(parents=True, exist_ok=True)

    alerts = []
    company_heartbeats = []

    for company in scores:
        ticker = company.get("ticker", "")
        name = company.get("company", "")
        composite = company.get("composite", 50)
        grade = company.get("hi_grade", "?")

        # Gather signals
        fh = finnhub.get(ticker.upper(), {}) if ticker else {}
        lo = layoffs_lower.get(name.lower().strip(), {})
        sk = sec_8k.get(ticker.upper(), {}) if ticker else {}

        hb_signals = fh.get("heartbeat", {})
        lo_signals = lo.get("h_signals", {})
        sk_signals = sk.get("heartbeat", {})

        # ── DECAY INDEX ──
        # Score risk factors (each adds to decay probability)
        decay_factors = []
        decay_score = 0

        # Layoff activity from Finnhub news
        layoff_news = hb_signals.get("layoff_mentions_90d", 0)
        if layoff_news >= 5:
            decay_factors.append(f"Heavy layoff coverage ({layoff_news} articles)")
            decay_score += 20
        elif layoff_news >= 2:
            decay_factors.append(f"Layoff mentions ({layoff_news} articles)")
            decay_score += 10

        # AI acceleration from Finnhub news
        ai_news = hb_signals.get("ai_mentions_90d", 0)
        if ai_news >= 10:
            decay_factors.append(f"Aggressive AI pivot ({ai_news} articles)")
            decay_score += 15
        elif ai_news >= 5:
            decay_factors.append(f"AI acceleration ({ai_news} articles)")
            decay_score += 8

        # Layoffs.fyi data
        total_displaced = lo_signals.get("total_laid_off", 0)
        if total_displaced > 10000:
            decay_factors.append(f"Massive layoffs ({total_displaced:,} total)")
            decay_score += 25
        elif total_displaced > 1000:
            decay_factors.append(f"Significant layoffs ({total_displaced:,} total)")
            decay_score += 15
        elif total_displaced > 100:
            decay_factors.append(f"Layoffs recorded ({total_displaced:,})")
            decay_score += 5

        # SEC 8-K activity
        material_events = sk_signals.get("material_events_180d", 0)
        if material_events > 8:
            decay_factors.append(f"High 8-K activity ({material_events} filings)")
            decay_score += 10

        # Ethics mentions from Finnhub
        ethics_news = hb_signals.get("ethics_mentions_90d", 0)
        if ethics_news >= 5:
            decay_factors.append(f"Ethics/legal issues ({ethics_news} articles)")
            decay_score += 15

        # Humanwashing flags from existing score
        hw_flags = company.get("humanwashing_flags", [])
        if hw_flags:
            decay_factors.append(f"{len(hw_flags)} humanwashing flag(s)")
            decay_score += len(hw_flags) * 5

        # ── DECAY INDEX CLASSIFICATION ──
        decay_score = min(decay_score, 100)
        if decay_score >= 50:
            decay_level = "critical"
        elif decay_score >= 30:
            decay_level = "warning"
        elif decay_score >= 10:
            decay_level = "watch"
        else:
            decay_level = "stable"

        # ── GENERATE ALERTS ──
        if decay_level in ["critical", "warning"]:
            alert = {
                "ticker": ticker,
                "company": name,
                "current_grade": grade,
                "composite": composite,
                "decay_index": decay_score,
                "decay_level": decay_level,
                "factors": decay_factors,
                "timestamp": datetime.now().isoformat(),
            }
            alerts.append(alert)

        # ── COMPANY HEARTBEAT ──
        company_heartbeats.append({
            "company": name,
            "ticker": ticker,
            "hi_grade": grade,
            "composite": composite,
            "decay_index": decay_score,
            "decay_level": decay_level,
            "factors": decay_factors,
            "signals": {
                "layoff_news_90d": layoff_news,
                "ai_news_90d": ai_news,
                "ethics_news_90d": ethics_news,
                "total_displaced": total_displaced,
                "material_events_180d": material_events,
                "humanwashing_flags": len(hw_flags),
            },
        })

    # Sort alerts by severity
    alerts.sort(key=lambda x: x["decay_index"], reverse=True)
    company_heartbeats.sort(key=lambda x: x["decay_index"], reverse=True)

    # Save outputs
    with open(output_dir / "alerts.json", "w") as f:
        json.dump(alerts, f, indent=2)

    with open(output_dir / "heartbeats.json", "w") as f:
        json.dump(company_heartbeats, f, indent=2)

    # Summary stats
    levels = defaultdict(int)
    for hb in company_heartbeats:
        levels[hb["decay_level"]] += 1

    print(f"  Companies analyzed: {len(company_heartbeats)}")
    print(f"  Decay levels:")
    print(f"    Critical: {levels['critical']}")
    print(f"    Warning:  {levels['warning']}")
    print(f"    Watch:    {levels['watch']}")
    print(f"    Stable:   {levels['stable']}")

    if alerts:
        print(f"\n  ⚠ TOP ALERTS ({len(alerts)} total):")
        for a in alerts[:15]:
            icon = "🔴" if a["decay_level"] == "critical" else "🟡"
            print(f"    {icon} {a['company'][:25]:25s} {a['current_grade']:12s} Decay: {a['decay_index']:>3d}  {', '.join(a['factors'][:2])}")

    # HUMAN Heartbeat pulse — overall ecosystem health
    avg_decay = sum(hb["decay_index"] for hb in company_heartbeats) / len(company_heartbeats) if company_heartbeats else 0
    pulse = "healthy" if avg_decay < 10 else "elevated" if avg_decay < 20 else "stressed" if avg_decay < 35 else "critical"

    print(f"\n  {'='*40}")
    print(f"  HUMAN HEARTBEAT PULSE: {pulse.upper()}")
    print(f"  Average decay index: {avg_decay:.1f}")
    print(f"  {'='*40}")

    pulse_data = {
        "timestamp": datetime.now().isoformat(),
        "pulse": pulse,
        "average_decay": round(avg_decay, 1),
        "companies_analyzed": len(company_heartbeats),
        "alerts_count": len(alerts),
        "levels": dict(levels),
    }

    with open(output_dir / "pulse.json", "w") as f:
        json.dump(pulse_data, f, indent=2)

    print(f"\n  Outputs:")
    print(f"    {output_dir / 'alerts.json'} — {len(alerts)} alerts")
    print(f"    {output_dir / 'heartbeats.json'} — {len(company_heartbeats)} company heartbeats")
    print(f"    {output_dir / 'pulse.json'} — ecosystem pulse")
    print(f"{'='*60}\n")

    return alerts, company_heartbeats, pulse_data


if __name__ == "__main__":
    compute_heartbeat()
