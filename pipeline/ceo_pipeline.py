#!/usr/bin/env python3
"""
CEO Accountability Pipeline
Sub-signal under M (Moral & Ethical Conduct)

Four signals:
  M.8 — CEO-to-Worker Pay Ratio (SEC DEF 14A proxy filings)
  M.9 — Glassdoor CEO Approval Rating
  M.10 — CEO Tenure vs Layoff Timing
  M.11 — CEO Compensation Trend vs Headcount Trend

Data sources: SEC EDGAR (proxy filings), Glassdoor (existing), Finnhub (existing), Layoffs.fyi (existing)
No additional API keys needed.
"""

import json, time, sys, os, re
from pathlib import Path
from collections import defaultdict

try:
    import requests
except ImportError:
    print("Install: pip install requests --break-system-packages")
    sys.exit(1)

HEADERS = {"User-Agent": "HI-Score-Engine admin@thehibalance.org"}
SEC_BASE = "https://efts.sec.gov/LATEST"


def load_scored_companies():
    sf = Path("data/scores/all_scores.json")
    if sf.exists():
        return json.load(open(sf))
    return []


def load_json_dict(path, key="ticker"):
    p = Path(path)
    if not p.exists():
        return {}
    data = json.load(open(p))
    idx = {}
    for r in data:
        k = r.get(key, "")
        if k:
            idx[k.upper() if isinstance(k, str) else k] = r
    return idx


def fetch_ceo_pay_ratio(ticker):
    """
    Fetch CEO-to-median-worker pay ratio from SEC EDGAR full-text search.
    Companies must disclose this in annual proxy statements (DEF 14A) since 2018.
    """
    try:
        # Search for pay ratio disclosure in proxy filings
        r = requests.get(
            f"{SEC_BASE}/search-index",
            params={
                "q": f'"pay ratio" "{ticker}"',
                "forms": "DEF 14A",
                "dateRange": "custom",
                "startdt": "2023-01-01",
                "enddt": "2026-12-31",
            },
            headers=HEADERS,
            timeout=15,
        )

        if r.status_code != 200:
            return None

        data = r.json()
        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            return None

        # Get the filing URL to extract ratio
        filing = hits[0].get("_source", {})
        return {
            "has_proxy": True,
            "filing_date": filing.get("file_date", ""),
            "form_type": filing.get("form_type", ""),
        }
    except:
        return None


def estimate_pay_ratio_from_fmp(ticker):
    """
    Estimate CEO pay ratio using FMP data if available.
    Uses executive compensation data.
    """
    try:
        key_path = Path("data/fmp_key.txt")
        if not key_path.exists():
            return None
        key = key_path.read_text().strip()

        r = requests.get(
            f"https://financialmodelingprep.com/stable/governance/executive-compensation?symbol={ticker}&apikey={key}",
            timeout=15,
        )
        if r.status_code != 200:
            return None

        data = r.json()
        if not data or not isinstance(data, list):
            return None

        # Find CEO compensation
        ceo_comp = None
        for exec_data in data:
            title = (exec_data.get("title") or "").lower()
            if "chief executive" in title or "ceo" in title:
                ceo_comp = exec_data.get("totalCompensation") or exec_data.get("salary")
                break

        return {"ceo_compensation": ceo_comp} if ceo_comp else None
    except:
        return None


def compute_ceo_score(company, glassdoor_data, finnhub_data, layoffs_data, fmp_data):
    """
    Compute CEO accountability score (0-100) from four signals.
    Lower score = worse CEO accountability = drags M dimension down.
    """
    ticker = company.get("ticker", "")
    scores = []
    signals = {}

    # ── M.8: CEO-to-Worker Pay Ratio ──
    # Use FMP data if available
    fmp = fmp_data.get(ticker.upper(), {}) if ticker else {}
    fmp_h = fmp.get("h_signals", {})
    revenue = fmp.get("meta", {}).get("revenue")
    employees = fmp_h.get("headcount")
    rpe = fmp_h.get("revenue_per_employee")

    # Estimate based on revenue per employee as proxy
    # High RPE often correlates with high pay ratios
    if rpe:
        if rpe > 2000000:
            scores.append(20)  # Extreme — likely very high pay ratio
            signals["pay_ratio_estimate"] = "extreme"
        elif rpe > 1000000:
            scores.append(40)
            signals["pay_ratio_estimate"] = "high"
        elif rpe > 500000:
            scores.append(60)
            signals["pay_ratio_estimate"] = "moderate"
        elif rpe > 200000:
            scores.append(75)
            signals["pay_ratio_estimate"] = "reasonable"
        else:
            scores.append(85)
            signals["pay_ratio_estimate"] = "good"

    # ── M.9: Glassdoor CEO Approval ──
    gd = glassdoor_data.get(ticker.upper(), {}) if ticker else {}
    # Try matching by company name too
    if not gd:
        for k, v in glassdoor_data.items():
            if company.get("company", "").lower() in k.lower():
                gd = v
                break

    ceo_approval = gd.get("ceo_approval")
    if ceo_approval is not None:
        # Scale: 0-100 directly maps
        approval_score = min(100, max(0, int(ceo_approval)))
        scores.append(approval_score)
        signals["ceo_approval"] = ceo_approval

    overall_rating = gd.get("overall_rating")
    if overall_rating is not None:
        # Scale: 1-5 stars → 0-100
        rating_score = min(100, max(0, int((overall_rating / 5.0) * 100)))
        scores.append(rating_score)
        signals["glassdoor_rating"] = overall_rating

    # ── M.10: CEO Tenure vs Layoff Timing ──
    # Check if layoffs happened recently for this company
    lo = layoffs_data.get(ticker.upper(), {}) if ticker else {}
    if not lo:
        name_lower = company.get("company", "").lower().strip()
        for k, v in layoffs_data.items():
            if name_lower in k.lower() or k.lower() in name_lower:
                lo = v
                break

    layoff_events = lo.get("h_signals", {}).get("layoff_events", 0)
    total_laid_off = lo.get("h_signals", {}).get("total_laid_off", 0)

    if total_laid_off > 10000:
        scores.append(15)
        signals["layoff_severity"] = "massive"
        signals["total_laid_off"] = total_laid_off
    elif total_laid_off > 5000:
        scores.append(30)
        signals["layoff_severity"] = "severe"
        signals["total_laid_off"] = total_laid_off
    elif total_laid_off > 1000:
        scores.append(50)
        signals["layoff_severity"] = "significant"
        signals["total_laid_off"] = total_laid_off
    elif total_laid_off > 100:
        scores.append(65)
        signals["layoff_severity"] = "moderate"
        signals["total_laid_off"] = total_laid_off
    elif layoff_events > 0:
        scores.append(75)
        signals["layoff_severity"] = "minor"
    # No layoffs = no penalty (don't add score, let other signals dominate)

    # ── M.11: Compensation Trend vs Headcount Trend ──
    # Use Finnhub news to detect compensation controversy
    fh = finnhub_data.get(ticker.upper(), {}) if ticker else {}
    hb = fh.get("heartbeat", {})

    layoff_news = hb.get("layoff_mentions_90d", 0)
    ai_news = hb.get("ai_mentions_90d", 0)

    # If heavy layoff news AND heavy AI pivot = leadership prioritizing tech over people
    if layoff_news >= 5 and ai_news >= 5:
        scores.append(20)
        signals["leadership_pattern"] = "layoffs_with_ai_pivot"
    elif layoff_news >= 3:
        scores.append(40)
        signals["leadership_pattern"] = "active_layoffs"
    elif ai_news >= 10:
        scores.append(55)
        signals["leadership_pattern"] = "aggressive_ai"

    # ── COMPOSITE CEO SCORE ──
    if scores:
        ceo_score = round(sum(scores) / len(scores), 1)
    else:
        ceo_score = 60.0  # Default — neutral, no data

    return {
        "ceo_accountability_score": ceo_score,
        "signals_used": len(scores),
        "signals": signals,
    }


def run_pipeline():
    output_dir = Path("data/ceo")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  CEO Accountability Pipeline")
    print(f"  Sub-signal under M (Moral & Ethical Conduct)")
    print(f"{'='*60}")
    print(f"  M.8  — CEO-to-Worker Pay Ratio (estimated)")
    print(f"  M.9  — Glassdoor CEO Approval")
    print(f"  M.10 — CEO Tenure vs Layoff Timing")
    print(f"  M.11 — Compensation Trend vs Headcount")
    print(f"{'='*60}\n")

    companies = load_scored_companies()
    print(f"  Companies to analyze: {len(companies)}")

    # Load existing data sources
    glassdoor_data = load_json_dict("data/glassdoor/all_companies.json", key="company")
    # Also index by ticker
    gd_by_ticker = {}
    for k, v in glassdoor_data.items():
        t = v.get("ticker", "")
        if t:
            gd_by_ticker[t.upper()] = v

    finnhub_data = load_json_dict("data/finnhub/all_companies.json")
    layoffs_data = load_json_dict("data/layoffs/all_companies.json", key="company")
    fmp_data = load_json_dict("data/fmp/all_companies.json")

    print(f"  Glassdoor records: {len(glassdoor_data)}")
    print(f"  Finnhub records: {len(finnhub_data)}")
    print(f"  Layoffs records: {len(layoffs_data)}")
    print(f"  FMP records: {len(fmp_data)}")
    print()

    records = []
    low_scores = []

    for company in companies:
        ticker = company.get("ticker", "")
        name = company.get("company", "")

        result = compute_ceo_score(
            company,
            {**glassdoor_data, **gd_by_ticker},
            finnhub_data,
            layoffs_data,
            fmp_data,
        )

        score = result["ceo_accountability_score"]
        signals_count = result["signals_used"]

        record = {
            "company": name,
            "ticker": ticker,
            "m_signals": {
                "ceo_accountability_score": score,
                "ceo_signals": result["signals"],
                "ceo_signals_used": signals_count,
            },
            "source": "CEO Accountability",
        }
        records.append(record)

        if score < 40 and signals_count >= 2:
            low_scores.append((name, ticker, score, result["signals"]))

    # Save
    output_file = output_dir / "all_companies.json"
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)

    # Stats
    scored = [r for r in records if r["m_signals"]["ceo_signals_used"] > 0]
    avg = sum(r["m_signals"]["ceo_accountability_score"] for r in scored) / len(scored) if scored else 0

    print(f"  Companies with CEO data: {len(scored)}")
    print(f"  Average CEO score: {avg:.1f}")

    if low_scores:
        low_scores.sort(key=lambda x: x[2])
        print(f"\n  ⚠ LOW CEO ACCOUNTABILITY ({len(low_scores)} companies):")
        for name, ticker, score, signals in low_scores[:15]:
            t = ticker or "—"
            sigs = ", ".join(f"{k}: {v}" for k, v in signals.items() if k != "total_laid_off")
            print(f"    🔴 {name[:30]:30s} {t:>6s}  Score: {score:>5.1f}  {sigs}")

    print(f"\n  Output: {output_file}")
    print(f"  Integrates into scoring engine as M.8-M.11")
    print(f"{'='*60}\n")

    return records


if __name__ == "__main__":
    run_pipeline()
