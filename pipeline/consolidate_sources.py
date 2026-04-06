#!/usr/bin/env python3
"""
HI. — Source Consolidation
Reads standalone pipeline outputs (data/fmp/, data/ceo/, etc.) and merges
them into the subsignal/extended format the scoring engine consumes.

The scoring engine reads:
  - data/subsignals/all_subsignals.json   (keyed by ticker)
  - data/subsignals/extended/all_extended.json  (keyed by ticker)

This script bridges the gap between standalone pipelines and scoring.

Usage:
  python3 consolidate_sources.py
  python3 consolidate_sources.py --data data  --dry-run
"""

import json, os, sys, math
from pathlib import Path
from datetime import datetime


def load_json(path):
    """Load JSON file, return empty list/dict on failure."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        with open(p) as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"  ⚠ Failed to load {path}: {e}")
        return []


def index_by_ticker(records, ticker_key="ticker"):
    """Index a list of records by uppercase ticker."""
    idx = {}
    for r in records:
        t = r.get(ticker_key, "")
        if t and isinstance(t, str):
            idx[t.upper()] = r
    return idx


def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, round(v)))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HI. Source Consolidation")
    parser.add_argument("--data", default="data", help="Base data directory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be merged without writing")
    args = parser.parse_args()

    base = Path(args.data)
    ss_file = base / "subsignals" / "all_subsignals.json"
    ext_file = base / "subsignals" / "extended" / "all_extended.json"

    # Load existing subsignal and extended data
    all_ss = {}
    if ss_file.exists():
        try:
            all_ss = json.load(open(ss_file))
        except:
            pass

    all_ext = {}
    if ext_file.exists():
        try:
            all_ext = json.load(open(ext_file))
        except:
            pass

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  HI. — Source Consolidation                             ║")
    print("║  Merging standalone pipelines → scoring engine format   ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"\n  Existing subsignals: {len(all_ss)} tickers")
    print(f"  Existing extended:   {len(all_ext)} tickers")

    merged_count = 0
    sources_found = []

    # ─── FMP (Financial Modeling Prep) ───────────────────────────────
    # Maps: headcount → H.1/H.4, revenue growth → M signals, R&D → H.5
    fmp_data = load_json(base / "fmp" / "all_companies.json")
    fmp_idx = index_by_ticker(fmp_data)
    if fmp_idx:
        sources_found.append(f"FMP: {len(fmp_idx)} companies")
        for ticker, d in fmp_idx.items():
            if ticker not in all_ext:
                all_ext[ticker] = {}

            h_sig = d.get("h_signals", {})
            m_sig = d.get("m_signals", {})

            # Revenue growth → M adjustment
            rev_growth = m_sig.get("revenue_growth_pct")
            if rev_growth is not None:
                # Positive growth is good for M dimension
                adj = clamp(rev_growth * 0.3, -10, 10)
                all_ext[ticker]["fmp_growth"] = {
                    "M_adj": adj,
                    "revenue_growth_pct": rev_growth,
                    "source": "FMP"
                }

            # R&D spend → H.5 adjustment (higher R&D % = investing in people/innovation)
            rd_pct = h_sig.get("rd_pct_revenue")
            if rd_pct is not None:
                # Industry benchmarks: tech ~15%, pharma ~20%, others ~3-5%
                h5_adj = clamp((rd_pct - 5) * 0.5, -5, 10)
                all_ext[ticker]["fmp_rd"] = {
                    "H.5_adj": h5_adj,
                    "rd_pct_revenue": rd_pct,
                    "source": "FMP"
                }

            # Operating margin → financial health context
            op_margin = m_sig.get("operating_margin")
            if op_margin is not None:
                all_ext[ticker]["fmp_margin"] = {
                    "operating_margin": op_margin,
                    "source": "FMP"
                }

            # Headcount change → H.1 adjustment
            hc_change = h_sig.get("headcount_change_pct")
            if hc_change is not None:
                # Negative headcount change = layoffs = bad for H
                h1_adj = clamp(hc_change * 0.5, -15, 10)
                all_ext[ticker]["fmp_headcount"] = {
                    "H.1_adj": h1_adj,
                    "headcount_change_pct": hc_change,
                    "source": "FMP"
                }

            merged_count += 1
    print(f"\n  FMP:            {len(fmp_idx)} companies merged")

    # ─── Finnhub (ESG + Profile) ─────────────────────────────────────
    finnhub_data = load_json(base / "finnhub" / "all_companies.json")
    finnhub_idx = index_by_ticker(finnhub_data)
    if finnhub_idx:
        sources_found.append(f"Finnhub: {len(finnhub_idx)} companies")
        for ticker, d in finnhub_idx.items():
            if ticker not in all_ext:
                all_ext[ticker] = {}

            esg = d.get("esg", {})
            if esg:
                # Finnhub ESG total score (0-100 scale)
                total = esg.get("totalScore") or esg.get("total")
                if total is not None:
                    # Blend into multiple dimensions
                    env_score = esg.get("environmentScore") or esg.get("environment")
                    soc_score = esg.get("socialScore") or esg.get("social")
                    gov_score = esg.get("governanceScore") or esg.get("governance")

                    all_ext[ticker]["finnhub_esg"] = {
                        "A.1_adj": clamp((env_score - 50) * 0.15, -8, 8) if env_score else 0,
                        "U.2_adj": clamp((soc_score - 50) * 0.15, -8, 8) if soc_score else 0,
                        "N.2_adj": clamp((gov_score - 50) * 0.15, -8, 8) if gov_score else 0,
                        "total_esg": total,
                        "source": "Finnhub ESG"
                    }

            merged_count += 1
    print(f"  Finnhub:        {len(finnhub_idx)} companies merged")

    # ─── NewsAPI (Decay Detection) ───────────────────────────────────
    # NewsAPI feeds into heartbeat/decay, not directly into scoring.
    # But we track it as a source for the audit.
    newsapi_data = load_json(base / "newsapi" / "all_companies.json")
    newsapi_idx = index_by_ticker(newsapi_data)
    if newsapi_idx:
        sources_found.append(f"NewsAPI: {len(newsapi_idx)} companies")
        for ticker, d in newsapi_idx.items():
            if ticker not in all_ext:
                all_ext[ticker] = {}

            impact = d.get("impact", {})
            risk = impact.get("risk_level", "low")

            # High negative news = decay signal (small penalty)
            if risk in ("critical", "high"):
                total_impact = impact.get("total_impact", 0)
                penalty = clamp(-total_impact * 0.3, -10, 0)
                all_ext[ticker]["newsapi"] = {
                    "decay_adj": penalty,
                    "risk_level": risk,
                    "total_articles": d.get("total_articles", 0),
                    "source": "NewsAPI"
                }

            merged_count += 1
    print(f"  NewsAPI:        {len(newsapi_idx)} companies merged")

    # ─── Layoffs.fyi ─────────────────────────────────────────────────
    layoffs_data = load_json(base / "layoffs" / "all_companies.json")
    layoffs_idx = {}
    for r in layoffs_data:
        # Layoffs data may be keyed by company name, not ticker
        t = r.get("ticker", "") or ""
        name = r.get("company", "")
        if t:
            layoffs_idx[t.upper()] = r
        elif name:
            layoffs_idx[name.upper()] = r
    if layoffs_idx:
        sources_found.append(f"Layoffs.fyi: {len(layoffs_idx)} companies")
        for key, d in layoffs_idx.items():
            ticker = (d.get("ticker") or key or "").upper()
            if not ticker or len(ticker) > 5:
                continue
            if ticker not in all_ext:
                all_ext[ticker] = {}

            total_laid_off = d.get("total_laid_off", 0) or 0
            events = d.get("layoff_events", 0) or d.get("events", 0) or 0

            if total_laid_off > 0:
                # Scale: 100 layoffs = minor, 10K+ = severe
                severity = min(math.log10(max(total_laid_off, 1)) * 3, 15)
                all_ext[ticker]["layoffs"] = {
                    "H.1_adj": -round(severity, 1),
                    "total_laid_off": total_laid_off,
                    "events": events,
                    "source": "Layoffs.fyi"
                }

            merged_count += 1
    print(f"  Layoffs.fyi:    {len(layoffs_idx)} companies merged")

    # ─── WARN Act ────────────────────────────────────────────────────
    warn_data = load_json(base / "warn" / "all_companies.json")
    warn_idx = index_by_ticker(warn_data)
    if warn_idx:
        sources_found.append(f"WARN Act: {len(warn_idx)} companies")
        for ticker, d in warn_idx.items():
            if ticker not in all_ext:
                all_ext[ticker] = {}

            notices = d.get("total_notices", 0) or 0
            affected = d.get("total_affected", 0) or 0

            if notices > 0:
                severity = min(notices * 2, 10)
                all_ext[ticker]["warn"] = {
                    "H.1_adj": -round(severity, 1),
                    "total_notices": notices,
                    "total_affected": affected,
                    "source": "WARN Act"
                }

            merged_count += 1
    print(f"  WARN Act:       {len(warn_idx)} companies merged")

    # ─── CEO Pipeline ────────────────────────────────────────────────
    ceo_data = load_json(base / "ceo" / "all_companies.json")
    ceo_idx = index_by_ticker(ceo_data)
    if ceo_idx:
        sources_found.append(f"CEO Pipeline: {len(ceo_idx)} companies")
        for ticker, d in ceo_idx.items():
            if ticker not in all_ext:
                all_ext[ticker] = {}

            ceo_score = d.get("ceo_accountability_score")
            if ceo_score is not None:
                # CEO score is 0-100; deviation from 60 (neutral) = adjustment
                adj = clamp((ceo_score - 60) * 0.2, -10, 10)
                all_ext[ticker]["ceo"] = {
                    "M.3_adj": adj,
                    "ceo_score": ceo_score,
                    "signals_used": d.get("signals_used", 0),
                    "source": "CEO Pipeline"
                }

            merged_count += 1
    print(f"  CEO Pipeline:   {len(ceo_idx)} companies merged")

    # ─── DEI Reporting ───────────────────────────────────────────────
    dei_data = load_json(base / "dei" / "all_companies.json")
    dei_idx = index_by_ticker(dei_data)
    if dei_idx:
        sources_found.append(f"DEI: {len(dei_idx)} companies")
        for ticker, d in dei_idx.items():
            if ticker not in all_ss:
                all_ss[ticker] = {}

            dei_score = d.get("dei_score") or d.get("score")
            if dei_score is not None:
                # DEI feeds into U.3 (Inclusion & Belonging)
                all_ss[ticker]["dei"] = {
                    "U.3": clamp(dei_score),
                    "source": "DEI Index"
                }

            merged_count += 1
    print(f"  DEI:            {len(dei_idx)} companies merged")

    # ─── HRC Corporate Equality Index ────────────────────────────────
    hrc_data = load_json(base / "hrc" / "all_companies.json")
    hrc_idx = index_by_ticker(hrc_data)
    if hrc_idx:
        sources_found.append(f"HRC: {len(hrc_idx)} companies")
        for ticker, d in hrc_idx.items():
            if ticker not in all_ss:
                all_ss[ticker] = {}

            hrc_score = d.get("hrc_score") or d.get("score") or d.get("cei_score")
            if hrc_score is not None:
                # HRC CEI feeds into U.3 (Inclusion)
                existing_u3 = all_ss[ticker].get("dei", {}).get("U.3")
                if existing_u3 is not None:
                    # Average with DEI if both exist
                    blended = round((existing_u3 + clamp(hrc_score)) / 2)
                    all_ss[ticker]["hrc"] = {
                        "U.3": blended,
                        "source": "HRC CEI"
                    }
                else:
                    all_ss[ticker]["hrc"] = {
                        "U.3": clamp(hrc_score),
                        "source": "HRC CEI"
                    }

            merged_count += 1
    print(f"  HRC:            {len(hrc_idx)} companies merged")

    # ─── SEC 8-K Material Events ─────────────────────────────────────
    sec8k_data = load_json(base / "sec_8k" / "all_companies.json")
    sec8k_idx = index_by_ticker(sec8k_data)
    if sec8k_idx:
        sources_found.append(f"SEC 8-K: {len(sec8k_idx)} companies")
        for ticker, d in sec8k_idx.items():
            if ticker not in all_ext:
                all_ext[ticker] = {}

            filing_count = d.get("filing_count", 0) or d.get("total_filings", 0)
            material_events = d.get("material_events", [])

            # More 8-K filings = more transparency (N.1 adjustment)
            if filing_count > 0:
                n1_adj = clamp(min(filing_count, 10) * 0.5, 0, 5)
                all_ext[ticker]["sec_8k"] = {
                    "N.1_adj": n1_adj,
                    "filing_count": filing_count,
                    "source": "SEC 8-K"
                }

            merged_count += 1
    print(f"  SEC 8-K:        {len(sec8k_idx)} companies merged")

    # ─── Alpha Vantage ───────────────────────────────────────────────
    av_data = load_json(base / "alphavantage" / "all_companies.json")
    av_idx = index_by_ticker(av_data)
    if av_idx:
        sources_found.append(f"Alpha Vantage: {len(av_idx)} companies")
        for ticker, d in av_idx.items():
            if ticker not in all_ext:
                all_ext[ticker] = {}

            # Alpha Vantage provides overview/fundamentals
            pe_ratio = d.get("pe_ratio") or d.get("PERatio")
            profit_margin = d.get("profit_margin") or d.get("ProfitMargin")

            if pe_ratio is not None or profit_margin is not None:
                all_ext[ticker]["alpha_vantage"] = {
                    "pe_ratio": pe_ratio,
                    "profit_margin": profit_margin,
                    "source": "Alpha Vantage"
                }

            merged_count += 1
    print(f"  Alpha Vantage:  {len(av_idx)} companies merged")

    # ─── Yahoo Finance ───────────────────────────────────────────────
    yahoo_data = load_json(base / "yahoo" / "all_companies.json")
    yahoo_idx = index_by_ticker(yahoo_data)
    if yahoo_idx:
        sources_found.append(f"Yahoo Finance: {len(yahoo_idx)} companies")
        for ticker, d in yahoo_idx.items():
            if ticker not in all_ext:
                all_ext[ticker] = {}

            esg_score = d.get("esg_score") or d.get("sustainabilityScore")
            if esg_score is not None:
                all_ext[ticker]["yahoo_esg"] = {
                    "esg_score": esg_score,
                    "source": "Yahoo Finance"
                }

            merged_count += 1
    print(f"  Yahoo Finance:  {len(yahoo_idx)} companies merged")

    # ─── FRED (macro/industry-level) ─────────────────────────────────
    fred_file = base / "fred" / "industry_data.json"
    if not fred_file.exists():
        fred_file = base / "fred" / "all_data.json"
    fred_data = load_json(fred_file) if fred_file.exists() else {}
    if fred_data:
        sources_found.append(f"FRED: macro data loaded")
        # FRED is industry-level context, not per-company
        # Store as metadata for the scoring engine
        fred_out = base / "fred" / "macro_context.json"
        if not args.dry_run:
            Path(fred_out).parent.mkdir(parents=True, exist_ok=True)
            json.dump(fred_data, open(fred_out, "w"), indent=2)
    print(f"  FRED:           {'loaded' if fred_data else 'no data'}")

    # ─── OpenCorporates ──────────────────────────────────────────────
    oc_data = load_json(base / "opencorporates" / "all_companies.json")
    oc_idx = index_by_ticker(oc_data)
    if oc_idx:
        sources_found.append(f"OpenCorporates: {len(oc_idx)} companies")
        for ticker, d in oc_idx.items():
            if ticker not in all_ext:
                all_ext[ticker] = {}

            # Corporate structure complexity / subsidiary count
            subsidiaries = d.get("subsidiary_count", 0) or d.get("total_subsidiaries", 0)
            if subsidiaries > 0:
                # Many subsidiaries can indicate opacity
                n_adj = clamp(-min(subsidiaries / 50, 5), -5, 0)
                all_ext[ticker]["opencorporates"] = {
                    "N.3_adj": n_adj,
                    "subsidiaries": subsidiaries,
                    "source": "OpenCorporates"
                }

            merged_count += 1
    print(f"  OpenCorporates: {len(oc_idx)} companies merged")

    # ─── Write consolidated files ────────────────────────────────────
    print(f"\n{'═' * 60}")
    print(f"  CONSOLIDATION SUMMARY")
    print(f"{'═' * 60}")
    print(f"  Subsignals: {len(all_ss)} tickers")
    print(f"  Extended:   {len(all_ext)} tickers")
    print(f"  Total merges: {merged_count}")
    print(f"  Sources found: {len(sources_found)}")
    for s in sources_found:
        print(f"    ✓ {s}")

    if args.dry_run:
        print(f"\n  🔍 DRY RUN — no files written")
        return

    # Ensure directories exist
    ss_file.parent.mkdir(parents=True, exist_ok=True)
    ext_file.parent.mkdir(parents=True, exist_ok=True)

    # Write consolidated files
    with open(ss_file, "w") as f:
        json.dump(all_ss, f, indent=2)
    print(f"\n  ✓ Wrote {ss_file} ({len(all_ss)} tickers)")

    with open(ext_file, "w") as f:
        json.dump(all_ext, f, indent=2)
    print(f"  ✓ Wrote {ext_file} ({len(all_ext)} tickers)")

    print(f"\n  Next: python3 scoring_engine.py")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()
