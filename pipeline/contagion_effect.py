#!/usr/bin/env python3
"""
Contagion Effect Score — Patent Feature #5
Measures how a company's ethical behavior ripples through its industry.

"When Amazon cuts 27,000 jobs, does the whole retail sector follow?"

Contagion Types:
  • POSITIVE CONTAGION — High-scoring company lifts its industry average
  • NEGATIVE CONTAGION — Low-scoring company drags its industry down
  • NEUTRAL — Company tracks its industry average

The score measures the gap between a company and its industry peers,
weighted by the company's market influence (headcount, revenue).

Output: data/contagion/all_contagion.json

Patent Pending · Morf Innovations LLC
"""

import json
from pathlib import Path
from datetime import datetime


def load_json(path):
    p = Path(path)
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return []


def compute_contagion():
    print(f"\n{'='*60}")
    print(f"  Contagion Effect Score")
    print(f"  Patent Feature: Supply Chain Ethics Ripple")
    print(f"{'='*60}\n")

    scores = load_json("data/scores/all_scores.json")

    output_dir = Path("data/contagion")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group by industry
    industries = {}
    for c in scores:
        ind = c.get("industry", "other") or "other"
        if ind not in industries:
            industries[ind] = []
        industries[ind].append(c)

    # Compute industry averages
    industry_avgs = {}
    for ind, companies in industries.items():
        composites = [c.get("composite", 0) for c in companies]
        dim_avgs = {}
        for d in ["D_H", "D_U", "D_M", "D_A", "D_N"]:
            vals = [c.get(d, 0) for c in companies]
            dim_avgs[d] = round(sum(vals) / len(vals)) if vals else 0
        industry_avgs[ind] = {
            "avg_composite": round(sum(composites) / len(composites)) if composites else 0,
            "company_count": len(companies),
            "dimensions": dim_avgs,
        }

    results = []
    type_counts = {"positive": 0, "negative": 0, "neutral": 0}

    for c in scores:
        name = c.get("company", "")
        ticker = c.get("ticker", "")
        industry = c.get("industry", "other") or "other"
        composite = c.get("composite", 0)
        ks = c.get("key_signals", {})

        ind_avg = industry_avgs.get(industry, {})
        ind_composite = ind_avg.get("avg_composite", 50)
        ind_count = ind_avg.get("company_count", 1)

        # Gap from industry average
        gap = composite - ind_composite

        # Influence weight — larger companies have more contagion
        headcount = ks.get("headcount", 0) or 0
        if headcount > 100000:
            influence = "high"
            influence_mult = 1.5
        elif headcount > 10000:
            influence = "medium"
            influence_mult = 1.0
        else:
            influence = "low"
            influence_mult = 0.7

        # Contagion score = gap * influence
        contagion_raw = gap * influence_mult
        contagion_score = max(-100, min(100, round(contagion_raw)))

        # Classify
        reasons = []
        if contagion_score > 10:
            contagion_type = "positive"
            contagion_label = "Positive Contagion"
            reasons.append(f"Scores {abs(gap)} points above {industry} average ({ind_composite})")
            if influence == "high":
                reasons.append(f"High influence ({headcount:,} employees) amplifies positive effect")
        elif contagion_score < -10:
            contagion_type = "negative"
            contagion_label = "Negative Contagion"
            reasons.append(f"Scores {abs(gap)} points below {industry} average ({ind_composite})")
            if influence == "high":
                reasons.append(f"High influence ({headcount:,} employees) amplifies negative effect")
        else:
            contagion_type = "neutral"
            contagion_label = "Neutral"
            reasons.append(f"Tracks {industry} average ({ind_composite})")

        type_counts[contagion_type] += 1

        # Dimension contagion — which dimensions are most divergent
        dim_gaps = {}
        ind_dims = ind_avg.get("dimensions", {})
        for d in ["D_H", "D_U", "D_M", "D_A", "D_N"]:
            company_d = c.get(d, 0)
            ind_d = ind_dims.get(d, 50)
            dim_gaps[d] = round(company_d - ind_d)

        # Strongest divergent dimension
        strongest = max(dim_gaps, key=lambda x: abs(dim_gaps[x]))
        dim_names = {"D_H": "Human Consciousness", "D_U": "Understanding", "D_M": "Ethics", "D_A": "Environmental", "D_N": "Transparency"}
        if abs(dim_gaps[strongest]) > 10:
            reasons.append(f"Strongest divergence: {dim_names.get(strongest, strongest)} ({dim_gaps[strongest]:+d} vs industry)")

        results.append({
            "company": name,
            "ticker": ticker,
            "industry": industry,
            "hi_grade": c.get("hi_grade", "?"),
            "composite": composite,
            "industry_avg": ind_composite,
            "industry_count": ind_count,
            "gap": round(gap),
            "influence": influence,
            "contagion_score": contagion_score,
            "contagion_type": contagion_type,
            "contagion_label": contagion_label,
            "dimension_gaps": dim_gaps,
            "reasons": reasons[:4],
        })

    results.sort(key=lambda x: x["contagion_score"])

    with open(output_dir / "all_contagion.json", "w") as f:
        json.dump(results, f, indent=2)
    with open(output_dir / "industry_averages.json", "w") as f:
        json.dump(industry_avgs, f, indent=2)

    metadata = {
        "name": "Contagion Effect Score",
        "patent": "Patent Pending — Morf Innovations LLC",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_analyzed": len(results),
        "industries": len(industry_avgs),
        "distribution": type_counts,
    }
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"  Companies: {len(results)}, Industries: {len(industry_avgs)}")
    print(f"  Positive: {type_counts['positive']}, Negative: {type_counts['negative']}, Neutral: {type_counts['neutral']}")
    print(f"\n  MOST NEGATIVE CONTAGION:")
    for r in results[:5]:
        print(f"    {r['contagion_score']:+4d}  {r['company']:30s}  {r['industry']:12s}  {r['reasons'][0] if r['reasons'] else ''}")
    print(f"\n  MOST POSITIVE CONTAGION:")
    for r in results[-5:]:
        print(f"    {r['contagion_score']:+4d}  {r['company']:30s}  {r['industry']:12s}  {r['reasons'][0] if r['reasons'] else ''}")

    print(f"\n  Output: data/contagion/")


if __name__ == "__main__":
    compute_contagion()
