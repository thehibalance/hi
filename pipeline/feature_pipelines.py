"""
HI. HUMAN Feature Pipelines
Computes Shield, Contagion, Lens, and Wave from scored company data.
Run after scoring engine: python3 feature_pipelines.py --data data/scores
"""

import json, math, os, sys
from pathlib import Path
from collections import defaultdict


def load_scores(data_dir):
    """Load all scored companies."""
    sf = Path(data_dir) / "all_scores.json"
    if not sf.exists():
        print(f"ERROR: {sf} not found. Run scoring engine first.")
        sys.exit(1)
    companies = [c for c in json.load(open(sf)) if not c.get("error") and c.get("composite", 0) > 0]
    print(f"Loaded {len(companies)} scored companies")
    return companies


# ═══════════════════════════════════════════════════════════════════════
# HUMAN SHIELD — AI Displacement Resistance
# 6 components, each 0-100, averaged to moat_score
# ═══════════════════════════════════════════════════════════════════════

def compute_shield(companies):
    """
    6-component moat score measuring resistance to AI displacement.
    Each component 0-100, weighted average = moat_score.
    """
    results = []
    
    for c in companies:
        genome = c.get("genome", {})
        ks = c.get("key_signals", {})
        dims = {d: c.get(f"D_{d}", 50) for d in "HUМАН"} if False else {
            "H": c.get("D_H", 50), "U": c.get("D_U", 50), "M": c.get("D_M", 50),
            "A": c.get("D_A", 50), "N": c.get("D_N", 50)
        }
        h_scores = genome.get("H", {}).get("scores", {})
        u_scores = genome.get("U", {}).get("scores", {})
        m_scores = genome.get("M", {}).get("scores", {})
        n_scores = genome.get("N", {}).get("scores", {})
        
        # Component 1: Craft Depth (25%) — How deep is human craft?
        # H.1 Creative Agency + H.2 Craft & Knowledge + H.3 Decision Depth
        craft = (
            h_scores.get("H.1", 50) * 0.4 +
            h_scores.get("H.2", 50) * 0.35 +
            h_scores.get("H.3", 50) * 0.25
        )
        
        # Component 2: Human Capital (20%) — Workforce investment
        # Headcount trends + headcount change + RPE inverse
        hc_change = ks.get("headcount_change_pct", 0) or 0
        rpe = ks.get("revenue_per_employee", 500000) or 500000
        hc_score = min(100, max(0, 50 + hc_change * 3))  # Growth = higher
        rpe_score = min(100, max(0, 100 - (rpe / 50000)))  # Lower RPE = more humans
        human_capital = hc_score * 0.5 + rpe_score * 0.3 + dims["H"] * 0.2
        
        # Component 3: Empathy Moat (20%) — Genuine empathy can't be replicated
        # U.1 Customer Empathy + U.4 Simulated Empathy Detection + Glassdoor
        glassdoor = ks.get("glassdoor_rating", 3.5) or 3.5
        glassdoor_norm = min(100, max(0, (glassdoor - 1) * 25))  # 1-5 → 0-100
        empathy = (
            u_scores.get("U.1", 50) * 0.35 +
            u_scores.get("U.4", 50) * 0.30 +
            glassdoor_norm * 0.20 +
            dims["U"] * 0.15
        )
        
        # Component 4: Ethics Shield (15%) — Principled companies resist pressure
        # M.1 Governance + M.3 Executive Ethics + humanwashing flags (penalty)
        hw_penalty = len(c.get("humanwashing_flags", [])) * 10
        ethics = max(0, (
            m_scores.get("M.1", 50) * 0.35 +
            m_scores.get("M.3", 50) * 0.30 +
            dims["M"] * 0.35
        ) - hw_penalty)
        
        # Component 5: Transparency Wall (10%) — Transparent companies are harder to disrupt
        # N.1 AI Disclosure + N.2 Reporting Quality + N.4 Integrity
        transparency = (
            n_scores.get("N.1", 50) * 0.35 +
            n_scores.get("N.2", 50) * 0.30 +
            n_scores.get("N.4", 50) * 0.20 +
            dims["N"] * 0.15
        )
        
        # Component 6: AI Resistance (10%) — Direct measure of AI displacement risk
        # H.5 Innovation Stewardship + displacement_signal (inverse) + ai_hiring_ratio (inverse)
        disp = ks.get("displacement_signal", 0) or 0
        ai_ratio = ks.get("ai_hiring_ratio", 0.1) or 0.1
        ai_resist = max(0, (
            h_scores.get("H.5", 50) * 0.40 +
            max(0, 100 - disp * 2) * 0.30 +  # Lower displacement = higher resistance
            max(0, 100 - ai_ratio * 200) * 0.30  # Lower AI ratio = higher resistance
        ))
        
        # Weighted composite
        moat_score = round(
            craft * 0.25 +
            human_capital * 0.20 +
            empathy * 0.20 +
            ethics * 0.15 +
            transparency * 0.10 +
            ai_resist * 0.10
        , 1)
        
        # Tier
        if moat_score >= 75:
            level, label = "fortress", "Fortress"
        elif moat_score >= 60:
            level, label = "strong", "Strong"
        elif moat_score >= 42:
            level, label = "moderate", "Moderate"
        elif moat_score >= 25:
            level, label = "thin", "Thin"
        else:
            level, label = "none", "None"
        
        # Reasons
        reasons = []
        if craft >= 70: reasons.append(f"Deep human craft (craft depth: {craft:.0f})")
        if empathy >= 70: reasons.append(f"Strong empathy moat (empathy: {empathy:.0f})")
        if ethics >= 70: reasons.append(f"Principled ethics shield (ethics: {ethics:.0f})")
        if ai_resist < 30: reasons.append(f"High AI displacement risk (resistance: {ai_resist:.0f})")
        if hw_penalty > 0: reasons.append(f"Humanwashing penalty reduces shield (-{hw_penalty})")
        
        results.append({
            "company": c["company"], "ticker": c.get("ticker", ""),
            "industry": c.get("industry", ""),
            "composite": c.get("composite", 0),
            "moat_score": moat_score, "moat_level": level, "moat_label": label,
            "components": {
                "craft_depth": round(craft, 1),
                "human_capital": round(human_capital, 1),
                "empathy_moat": round(empathy, 1),
                "ethics_shield": round(ethics, 1),
                "transparency_wall": round(transparency, 1),
                "ai_resistance": round(ai_resist, 1),
            },
            "reasons": reasons[:3],
        })
    
    results.sort(key=lambda x: x["moat_score"], reverse=True)
    
    dist = defaultdict(int)
    for r in results:
        dist[r["moat_level"]] += 1
    
    meta = {
        "total": len(results),
        "distribution": dict(dist),
        "average_moat": round(sum(r["moat_score"] for r in results) / len(results), 1) if results else 0,
    }
    
    return results, meta


# ═══════════════════════════════════════════════════════════════════════
# HUMAN CONTAGION — Industry Ethics Ripple Effect
# How a company's behavior spreads through its industry
# ═══════════════════════════════════════════════════════════════════════

def compute_contagion(companies):
    """
    Measures ethical contagion — how company behavior ripples through industry.
    High-influence companies with low scores drag industries down.
    High-influence companies with high scores lift industries up.
    """
    # Build industry groups
    industries = defaultdict(list)
    for c in companies:
        ind = c.get("industry", "Other") or "Other"
        industries[ind].append(c)
    
    # Compute industry averages
    ind_avgs = {}
    for ind, members in industries.items():
        composites = [m.get("composite", 0) for m in members]
        ind_avgs[ind] = sum(composites) / len(composites) if composites else 50
    
    results = []
    for c in companies:
        ind = c.get("industry", "Other") or "Other"
        members = industries.get(ind, [])
        if len(members) < 2:
            continue  # Need peers to measure contagion
        
        comp = c.get("composite", 0)
        ind_avg = ind_avgs.get(ind, 50)
        ks = c.get("key_signals", {})
        
        # Influence weight — larger companies have more contagion
        headcount = ks.get("headcount") or 1000
        rpe = ks.get("revenue_per_employee", 200000) or 200000
        est_revenue = headcount * rpe
        
        # Normalize influence within industry (0-1)
        ind_revenues = []
        for m in members:
            mks = m.get("key_signals", {})
            mhc = mks.get("headcount") or 1000
            mrpe = mks.get("revenue_per_employee", 200000) or 200000
            ind_revenues.append(mhc * mrpe)
        
        max_rev = max(ind_revenues) if ind_revenues else 1
        influence = est_revenue / max_rev if max_rev > 0 else 0.1
        influence = min(1.0, max(0.05, influence))
        
        # Contagion direction: positive (lifting) or negative (dragging)
        gap = comp - ind_avg
        
        # Contagion score: influence * gap magnitude
        contagion_magnitude = abs(gap) * influence
        
        # Is this company a leader or a dragger?
        is_negative_leader = gap < -10 and influence > 0.3
        is_positive_leader = gap > 10 and influence > 0.3
        
        # Dimension breakdown — which dimensions deviate most from industry
        dim_gaps = {}
        for d in ["H", "U", "M", "A", "N"]:
            company_dim = c.get(f"D_{d}", 50)
            ind_dim_vals = [m.get(f"D_{d}", 50) for m in members]
            ind_dim_avg = sum(ind_dim_vals) / len(ind_dim_vals) if ind_dim_vals else 50
            dim_gaps[d] = round(company_dim - ind_dim_avg, 1)
        
        # Worst dimension gap (most negative = dragging industry down most)
        worst_dim = min(dim_gaps, key=dim_gaps.get)
        best_dim = max(dim_gaps, key=dim_gaps.get)
        
        results.append({
            "company": c["company"], "ticker": c.get("ticker", ""),
            "industry": ind,
            "composite": comp,
            "industry_average": round(ind_avg, 1),
            "gap_from_industry": round(gap, 1),
            "influence_weight": round(influence, 3),
            "contagion_magnitude": round(contagion_magnitude, 1),
            "is_positive_leader": is_positive_leader,
            "is_negative_leader": is_negative_leader,
            "negative_contagion_leader": is_negative_leader,
            "dimension_gaps": dim_gaps,
            "worst_dimension": worst_dim,
            "best_dimension": best_dim,
            "industry_peer_count": len(members),
        })
    
    results.sort(key=lambda x: x["contagion_magnitude"], reverse=True)
    return results


# ═══════════════════════════════════════════════════════════════════════
# HUMAN LENS — HI vs ESG Gap Detection
# Compares HI Grade against estimated Finnhub ESG
# ═══════════════════════════════════════════════════════════════════════

def compute_lens(companies):
    """
    Detects discrepancies between HI Grade and traditional ESG.
    ESG Washing: ESG high but HI low (hiding human displacement behind green metrics)
    Hidden Gem: ESG low but HI high (genuinely human but not ESG-recognized)
    Aligned: Both agree
    Double Risk: Both low
    """
    results = []
    
    for c in companies:
        comp = c.get("composite", 0)
        genome = c.get("genome", {})
        ks = c.get("key_signals", {})
        
        # Estimate ESG composite from available signals
        # Real ESG scores come from Finnhub/MSCI — we approximate from our data
        cdp = ks.get("cdp_climate")
        epa_violations = ks.get("epa_violations", 0) or 0
        glassdoor = ks.get("glassdoor_rating", 3.0) or 3.0
        
        # E component: A dimension + CDP + EPA inverse
        e_score = c.get("D_A", 50)
        if cdp and cdp in ["A", "A-"]:
            e_score = min(100, e_score + 15)
        elif cdp and cdp in ["B", "B-"]:
            e_score = min(100, e_score + 5)
        if epa_violations > 10:
            e_score = max(0, e_score - 15)
        
        # S component: U dimension + Glassdoor
        glassdoor_norm = min(100, max(0, (glassdoor - 1) * 25))
        s_score = c.get("D_U", 50) * 0.6 + glassdoor_norm * 0.4
        
        # G component: M dimension + N dimension blend
        g_score = c.get("D_M", 50) * 0.5 + c.get("D_N", 50) * 0.5
        
        # ESG composite (traditional weighting: E=35%, S=30%, G=35%)
        esg_composite = round(e_score * 0.35 + s_score * 0.30 + g_score * 0.35, 1)
        
        # Gap analysis
        gap = round(comp - esg_composite, 1)
        
        # Classification
        hi_high = comp >= 55
        esg_high = esg_composite >= 55
        
        if esg_high and not hi_high:
            arb_type = "esg_washing"
            label = "ESG Washing"
            gap_reasons = []
            # Find which HI dimensions ESG misses
            if c.get("D_H", 50) < 42:
                gap_reasons.append(f"H dimension at {c.get('D_H', 50)} — ESG ignores human consciousness")
            if c.get("algo_harm", {}).get("has_harm"):
                gap_reasons.append(f"Algorithmic Harm score {c['algo_harm']['algo_harm_score']} — ESG doesn't measure this")
            if c.get("humanwashing_flags"):
                gap_reasons.append(f"{len(c['humanwashing_flags'])} humanwashing flags — ESG misses performative claims")
            if c.get("D_U", 50) < 42:
                gap_reasons.append(f"U dimension at {c.get('D_U', 50)} — simulated empathy undetected by ESG")
        elif hi_high and not esg_high:
            arb_type = "hidden_gem"
            label = "Hidden Gem"
            gap_reasons = [
                f"HI composite {comp} but ESG only {esg_composite}",
                "Genuinely human company not recognized by traditional ESG",
            ]
            if c.get("D_H", 50) >= 60:
                gap_reasons.append(f"Strong human consciousness ({c.get('D_H', 50)}) — invisible to ESG")
        elif hi_high and esg_high:
            arb_type = "aligned"
            label = "Aligned"
            gap_reasons = ["HI and ESG agree — strong across both frameworks"]
        else:
            arb_type = "double_risk"
            label = "Double Risk"
            gap_reasons = ["Low on both HI and ESG — significant risk across all dimensions"]
        
        results.append({
            "company": c["company"], "ticker": c.get("ticker", ""),
            "industry": c.get("industry", ""),
            "hi_composite": comp,
            "esg_composite": esg_composite,
            "esg_components": {
                "environmental": round(e_score, 1),
                "social": round(s_score, 1),
                "governance": round(g_score, 1),
            },
            "gap": gap,
            "arbitrage_type": arb_type,
            "arbitrage_label": label,
            "gap_reasons": gap_reasons[:3],
            "composite": comp,
        })
    
    results.sort(key=lambda x: abs(x["gap"]), reverse=True)
    
    dist = defaultdict(int)
    for r in results:
        dist[r["arbitrage_type"]] += 1
    
    meta = {
        "total": len(results),
        "arbitrage_distribution": dict(dist),
        "average_gap": round(sum(r["gap"] for r in results) / len(results), 1) if results else 0,
    }
    
    return results, meta


# ═══════════════════════════════════════════════════════════════════════
# HUMAN WAVE — Collective Market Pressure Signals
# Which industries and dimensions are under the most pressure?
# ═══════════════════════════════════════════════════════════════════════

def compute_wave(companies, threshold=64.6):
    """
    Aggregates scoring data into market pressure signals.
    Identifies which industries and dimensions are failing system-wide.
    Uses HI Balanced threshold as the bar — not the floor.
    """
    # Load saved threshold if available
    try:
        import os
        t_path = os.path.join("data", "threshold.json")
        if os.path.exists(t_path):
            import json as _json
            threshold = _json.load(open(t_path)).get("threshold", threshold)
    except:
        pass
    
    # Industry pressure
    industries = defaultdict(lambda: {"scores": [], "dims": defaultdict(list), "hw_flags": 0, "algo_harm": 0, "below_threshold": 0})
    
    for c in companies:
        ind = c.get("industry", "Other") or "Other"
        comp = c.get("composite", 0)
        industries[ind]["scores"].append(comp)
        
        for d in ["H", "U", "M", "A", "N"]:
            val = c.get(f"D_{d}", 50)
            industries[ind]["dims"][d].append(val)
            if val < threshold:
                industries[ind]["below_threshold"] += 1
        
        industries[ind]["hw_flags"] += len(c.get("humanwashing_flags", []))
        if c.get("algo_harm", {}).get("has_harm"):
            industries[ind]["algo_harm"] += 1
    
    # Dimension-level market pressure
    dim_totals = defaultdict(list)
    for c in companies:
        for d in ["H", "U", "M", "A", "N"]:
            dim_totals[d].append(c.get(f"D_{d}", 50))
    
    dim_pressure = {}
    for d, vals in dim_totals.items():
        avg = sum(vals) / len(vals) if vals else 50
        below_threshold = sum(1 for v in vals if v < threshold)
        below_threshold_pct = round(below_threshold / len(vals) * 100, 1) if vals else 0
        stdev = math.sqrt(sum((v - avg) ** 2 for v in vals) / len(vals)) if len(vals) > 1 else 0
        
        dim_names = {"H": "Human Consciousness", "U": "Understanding & Empathy",
                     "M": "Moral & Ethical Conduct", "A": "Alive & Environmental",
                     "N": "Natural Transparency"}
        
        # Pressure score: lower avg + higher below_threshold_pct + higher stdev = more pressure
        pressure = round(max(0, 100 - avg) * 0.5 + below_threshold_pct * 0.3 + min(30, stdev) * 0.2, 1)
        
        dim_pressure[d] = {
            "dimension": d,
            "name": dim_names.get(d, d),
            "average": round(avg, 1),
            "below_threshold_count": below_threshold,
            "below_threshold_pct": below_threshold_pct,
            "failing_pct": below_threshold_pct,
            "stdev": round(stdev, 1),
            "pressure_score": pressure,
            "status": "critical" if pressure >= 50 else "warning" if pressure >= 30 else "stable",
            "threshold": round(threshold, 1),
        }
    
    # Industry signals
    industry_signals = []
    for ind, data in industries.items():
        scores = data["scores"]
        if not scores:
            continue
        avg = sum(scores) / len(scores)
        below_threshold_total = data["below_threshold"]
        
        # Worst dimension for this industry
        dim_avgs = {}
        for d, vals in data["dims"].items():
            dim_avgs[d] = sum(vals) / len(vals) if vals else 50
        worst_dim = min(dim_avgs, key=dim_avgs.get) if dim_avgs else "H"
        
        # Industry pressure score
        pressure = round(
            max(0, 100 - avg) * 0.40 +
            min(50, data["hw_flags"] * 5) * 0.20 +
            min(50, data["algo_harm"] * 10) * 0.15 +
            min(50, below_threshold_total * 2) * 0.25
        , 1)
        
        industry_signals.append({
            "industry": ind,
            "company_count": len(scores),
            "average_composite": round(avg, 1),
            "worst_dimension": worst_dim,
            "worst_dimension_avg": round(dim_avgs.get(worst_dim, 50), 1),
            "humanwashing_flags": data["hw_flags"],
            "algo_harm_companies": data["algo_harm"],
            "below_threshold_dimensions": below_threshold_total,
            "pressure_score": pressure,
            "status": "critical" if pressure >= 50 else "warning" if pressure >= 30 else "stable",
        })
    
    industry_signals.sort(key=lambda x: x["pressure_score"], reverse=True)
    
    # Market-wide summary
    all_composites = [c.get("composite", 0) for c in companies]
    market_avg = sum(all_composites) / len(all_composites) if all_composites else 50
    
    signals = {
        "market_average": round(market_avg, 1),
        "total_companies": len(companies),
        "dimension_pressure": dim_pressure,
        "industry_signals": industry_signals[:20],
        "market_status": "critical" if market_avg < 42 else "warning" if market_avg < 55 else "healthy",
        "most_pressured_dimension": max(dim_pressure.values(), key=lambda x: x["pressure_score"])["dimension"] if dim_pressure else "H",
        "most_pressured_industry": industry_signals[0]["industry"] if industry_signals else "Unknown",
    }
    
    return signals


# ═══════════════════════════════════════════════════════════════════════
# HUMAN WATERMARK — Empathy Authenticity
# ═══════════════════════════════════════════════════════════════════════

def compute_watermark(companies):
    """
    Cross-references external signals against internal reality.
    Authenticity = genuine empathy. Performative = fake empathy.
    """
    results = []
    
    for c in companies:
        genome = c.get("genome", {})
        ks = c.get("key_signals", {})
        u_scores = genome.get("U", {}).get("scores", {})
        
        # External signals (what they claim)
        dei_score = u_scores.get("U.3", 50)  # DEI/HRC indices
        glassdoor = ks.get("glassdoor_rating", 3.0) or 3.0
        glassdoor_norm = min(100, max(0, (glassdoor - 1) * 25))
        
        # Internal reality
        worker_empathy = u_scores.get("U.2", 50)  # OSHA, DOL, EEOC
        customer_empathy = u_scores.get("U.1", 50)  # CFPB, BBB
        simulated = u_scores.get("U.4", 50)  # Simulated empathy detection
        
        # Authenticity = internal reality average
        authenticity = round((worker_empathy * 0.35 + customer_empathy * 0.35 + simulated * 0.30), 1)
        
        # Performative = gap between external claims and internal reality
        external = round((dei_score * 0.50 + glassdoor_norm * 0.50), 1)
        performative = round(max(0, external - authenticity + 20), 1)  # Bias toward flagging gaps
        
        is_performative = performative > authenticity and (external - authenticity) > 15
        
        results.append({
            "company": c["company"], "ticker": c.get("ticker", ""),
            "industry": c.get("industry", ""),
            "composite": c.get("composite", 0),
            "authenticity_score": authenticity,
            "performative_score": performative,
            "is_performative": is_performative,
            "external_signals": round(external, 1),
            "internal_reality": round(authenticity, 1),
            "gap": round(external - authenticity, 1),
        })
    
    results.sort(key=lambda x: x["performative_score"], reverse=True)
    return results


# ═══════════════════════════════════════════════════════════════════════
# MAIN — Generate all features
# ═══════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="HI. HUMAN Feature Pipelines")
    parser.add_argument("--data", default="data/scores", help="Path to scored data")
    parser.add_argument("--output", default="data", help="Output base directory")
    args = parser.parse_args()
    
    companies = load_scores(args.data)
    out = Path(args.output)
    
    # Shield
    print("\n═══ HUMAN Shield ═══")
    shield_results, shield_meta = compute_shield(companies)
    shield_dir = out / "ethical_moat"
    shield_dir.mkdir(parents=True, exist_ok=True)
    json.dump(shield_results, open(shield_dir / "all_moats.json", "w"), indent=2)
    json.dump(shield_meta, open(shield_dir / "metadata.json", "w"), indent=2)
    print(f"  {len(shield_results)} companies · avg moat: {shield_meta['average_moat']}")
    print(f"  Distribution: {shield_meta['distribution']}")
    
    # Contagion
    print("\n═══ HUMAN Contagion ═══")
    contagion_results = compute_contagion(companies)
    cont_dir = out / "contagion"
    cont_dir.mkdir(parents=True, exist_ok=True)
    json.dump(contagion_results, open(cont_dir / "all_contagion.json", "w"), indent=2)
    neg = sum(1 for r in contagion_results if r["is_negative_leader"])
    pos = sum(1 for r in contagion_results if r["is_positive_leader"])
    print(f"  {len(contagion_results)} companies · {pos} positive leaders · {neg} negative leaders")
    
    # Lens
    print("\n═══ HUMAN Lens ═══")
    lens_results, lens_meta = compute_lens(companies)
    arb_dir = out / "arbitrage"
    arb_dir.mkdir(parents=True, exist_ok=True)
    json.dump(lens_results, open(arb_dir / "all_arbitrage.json", "w"), indent=2)
    json.dump(lens_meta, open(arb_dir / "metadata.json", "w"), indent=2)
    print(f"  {len(lens_results)} companies · avg gap: {lens_meta['average_gap']}")
    print(f"  Distribution: {lens_meta['arbitrage_distribution']}")
    
    # Wave
    print("\n═══ HUMAN Wave ═══")
    wave_signals = compute_wave(companies)
    cb_dir = out / "collective_bargaining"
    cb_dir.mkdir(parents=True, exist_ok=True)
    json.dump(wave_signals, open(cb_dir / "signals.json", "w"), indent=2)
    print(f"  Market avg: {wave_signals['market_average']}")
    print(f"  Most pressured dimension: {wave_signals['most_pressured_dimension']}")
    print(f"  Most pressured industry: {wave_signals['most_pressured_industry']}")
    
    # Watermark
    print("\n═══ HUMAN Watermark ═══")
    wm_results = compute_watermark(companies)
    wm_dir = out / "empathy_watermark"
    wm_dir.mkdir(parents=True, exist_ok=True)
    json.dump(wm_results, open(wm_dir / "all_watermarks.json", "w"), indent=2)
    perf = sum(1 for r in wm_results if r["is_performative"])
    print(f"  {len(wm_results)} companies · {perf} performative")
    
    print(f"\n✓ All features generated in {out}/")


if __name__ == "__main__":
    main()
