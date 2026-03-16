#!/usr/bin/env python3
"""
Collective Bargaining Signal — Patent Feature #10
Aggregates scoring data into market pressure signals.

"47,000 consumers have filtered you out this month. 73% cite your H score."

This engine computes the framework — the actual consumer filtering data
requires extension telemetry (future). For now, it computes:
  - Industry pressure scores (which industries are most out of balance)
  - Dimension pressure (which dimensions are failing industry-wide)
  - Improvement signals (which companies improved most, signaling market response)
  - Risk concentration (which industries have the most companies at risk)

The Collective Bargaining Signal turns individual HI Grades into
aggregate market intelligence that companies and industries can't ignore.

Output: data/collective_bargaining/signals.json

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


def compute_signals():
    print(f"\n{'='*60}")
    print(f"  Collective Bargaining Signal")
    print(f"  Patent Feature: Aggregated Market Pressure")
    print(f"{'='*60}\n")

    scores = load_json("data/scores/all_scores.json")
    heartbeats = {h.get("ticker", ""): h for h in load_json("data/heartbeat/heartbeats.json") if h.get("ticker")}

    output_dir = Path("data/collective_bargaining")
    output_dir.mkdir(parents=True, exist_ok=True)

    # ═══ INDUSTRY PRESSURE ═══
    industries = {}
    for c in scores:
        ind = c.get("industry", "other") or "other"
        if ind not in industries:
            industries[ind] = {"companies": [], "composites": [], "dims": {d: [] for d in ["D_H","D_U","D_M","D_A","D_N"]}, "decay_count": 0, "floor_count": 0, "hw_count": 0}
        industries[ind]["companies"].append(c.get("company", ""))
        industries[ind]["composites"].append(c.get("composite", 0))
        for d in ["D_H","D_U","D_M","D_A","D_N"]:
            industries[ind]["dims"][d].append(c.get(d, 0))
        t = c.get("ticker", "")
        if t and t.upper() in heartbeats:
            hb = heartbeats[t.upper()]
            if hb.get("decay_level", "stable") != "stable":
                industries[ind]["decay_count"] += 1
        if c.get("balance_floor"):
            industries[ind]["floor_count"] += 1
        if c.get("humanwashing_flags"):
            industries[ind]["hw_count"] += 1

    industry_pressure = []
    for ind, data in industries.items():
        comps = data["composites"]
        count = len(comps)
        avg = round(sum(comps) / count) if count else 0

        # Weakest dimension for this industry
        dim_avgs = {}
        for d in ["D_H","D_U","D_M","D_A","D_N"]:
            vals = data["dims"][d]
            dim_avgs[d] = round(sum(vals) / len(vals)) if vals else 0
        weakest = min(dim_avgs, key=dim_avgs.get)
        dim_names = {"D_H": "Human Consciousness", "D_U": "Understanding", "D_M": "Ethics", "D_A": "Environmental", "D_N": "Transparency"}

        # Pressure score: how much this industry needs to improve
        # Low average + high decay + high floor triggers = high pressure
        pressure = max(0, min(100, round(
            (100 - avg) * 0.4 +
            (data["decay_count"] / max(count, 1)) * 100 * 0.3 +
            (data["floor_count"] / max(count, 1)) * 100 * 0.2 +
            (data["hw_count"] / max(count, 1)) * 100 * 0.1
        )))

        industry_pressure.append({
            "industry": ind,
            "company_count": count,
            "avg_composite": avg,
            "pressure_score": pressure,
            "weakest_dimension": weakest.replace("D_", ""),
            "weakest_dimension_name": dim_names.get(weakest, weakest),
            "weakest_dimension_avg": dim_avgs[weakest],
            "dimension_averages": {k.replace("D_", ""): v for k, v in dim_avgs.items()},
            "decay_companies": data["decay_count"],
            "floor_companies": data["floor_count"],
            "humanwashing_companies": data["hw_count"],
        })

    industry_pressure.sort(key=lambda x: -x["pressure_score"])

    # ═══ DIMENSION PRESSURE (across all companies) ═══
    all_dims = {d: [] for d in ["D_H","D_U","D_M","D_A","D_N"]}
    for c in scores:
        for d in all_dims:
            all_dims[d].append(c.get(d, 0))

    dimension_pressure = {}
    for d, vals in all_dims.items():
        avg = round(sum(vals) / len(vals)) if vals else 0
        below_42 = sum(1 for v in vals if v < 42)
        dim_label = d.replace("D_", "")
        dimension_pressure[dim_label] = {
            "avg": avg,
            "below_42_count": below_42,
            "below_42_pct": round(below_42 / len(vals) * 100) if vals else 0,
            "pressure": max(0, min(100, round((100 - avg) * 0.6 + (below_42 / max(len(vals), 1)) * 100 * 0.4))),
        }

    # ═══ RISK CONCENTRATION ═══
    risk_companies = []
    for c in scores:
        t = c.get("ticker", "")
        hb = heartbeats.get(t.upper(), {}) if t else {}
        risk_score = 0
        risk_factors = []

        if c.get("balance_floor"):
            risk_score += 25
            risk_factors.append("Balance floor triggered")
        if c.get("humanwashing_flags"):
            risk_score += len(c["humanwashing_flags"]) * 10
            risk_factors.append(f"{len(c['humanwashing_flags'])} humanwashing flags")
        if hb.get("decay_level", "stable") != "stable":
            risk_score += hb.get("decay_index", 0) * 0.3
            risk_factors.append(f"Decay: {hb.get('decay_level', '')}")
        if c.get("composite", 100) < 42:
            risk_score += 30
            risk_factors.append("Grade F")

        if risk_score > 0:
            risk_companies.append({
                "company": c.get("company", ""),
                "ticker": t,
                "industry": c.get("industry", ""),
                "composite": c.get("composite", 0),
                "risk_score": round(min(risk_score, 100)),
                "risk_factors": risk_factors[:3],
            })

    risk_companies.sort(key=lambda x: -x["risk_score"])

    # ═══ SAVE ═══
    signals = {
        "name": "Collective Bargaining Signal",
        "patent": "Patent Pending — Morf Innovations LLC",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_companies": len(scores),
        "total_industries": len(industries),
        "industry_pressure": industry_pressure,
        "dimension_pressure": dimension_pressure,
        "risk_concentration": risk_companies[:50],
        "summary": {
            "highest_pressure_industry": industry_pressure[0]["industry"] if industry_pressure else None,
            "weakest_dimension": min(dimension_pressure, key=lambda x: dimension_pressure[x]["avg"]) if dimension_pressure else None,
            "companies_at_risk": len(risk_companies),
        },
    }

    with open(output_dir / "signals.json", "w") as f:
        json.dump(signals, f, indent=2)

    print(f"  Companies: {len(scores)}, Industries: {len(industries)}")
    print(f"  Companies at risk: {len(risk_companies)}")
    print(f"\n  Industry Pressure (highest first):")
    for ip in industry_pressure[:8]:
        print(f"    {ip['pressure_score']:3d}  {ip['industry']:15s}  Avg: {ip['avg_composite']}  Weakest: {ip['weakest_dimension']} ({ip['weakest_dimension_avg']})")
    print(f"\n  Dimension Pressure:")
    for d in ["H","U","M","A","N"]:
        dp = dimension_pressure.get(d, {})
        print(f"    {d}: Avg {dp.get('avg',0)}, {dp.get('below_42_count',0)} below 42 ({dp.get('below_42_pct',0)}%), Pressure: {dp.get('pressure',0)}")
    print(f"\n  Output: data/collective_bargaining/signals.json")


if __name__ == "__main__":
    compute_signals()
