#!/usr/bin/env python3
"""
Consumer Consciousness Score — Patent Feature #7
Personal ethical footprint based on the companies a consumer interacts with.

"Your portfolio of companies has an average HI Grade of C. Here's how to improve it."

This generates the framework — the actual consumer score requires the extension
to track which companies a user visits. This engine computes industry and 
category benchmarks so the extension can show relative positioning.

Output: data/consumer_consciousness/benchmarks.json

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


def compute_benchmarks():
    print(f"\n{'='*60}")
    print(f"  Consumer Consciousness Score")
    print(f"  Patent Feature: Personal Ethical Footprint")
    print(f"{'='*60}\n")

    scores = load_json("data/scores/all_scores.json")

    output_dir = Path("data/consumer_consciousness")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Industry benchmarks
    industries = {}
    for c in scores:
        ind = c.get("industry", "other") or "other"
        if ind not in industries:
            industries[ind] = {"composites": [], "grades": {}, "companies": []}
        industries[ind]["composites"].append(c.get("composite", 0))
        g = c.get("hi_grade", "?")
        industries[ind]["grades"][g] = industries[ind]["grades"].get(g, 0) + 1
        industries[ind]["companies"].append({
            "company": c.get("company", ""),
            "ticker": c.get("ticker", ""),
            "composite": c.get("composite", 0),
            "hi_grade": c.get("hi_grade", "?"),
        })

    benchmarks = {}
    for ind, data in industries.items():
        comps = data["composites"]
        sorted_comps = sorted(comps)
        benchmarks[ind] = {
            "avg": round(sum(comps) / len(comps)) if comps else 0,
            "median": sorted_comps[len(sorted_comps)//2] if sorted_comps else 0,
            "best": max(comps) if comps else 0,
            "worst": min(comps) if comps else 0,
            "count": len(comps),
            "grades": data["grades"],
            "top_3": sorted(data["companies"], key=lambda x: -x["composite"])[:3],
            "bottom_3": sorted(data["companies"], key=lambda x: x["composite"])[:3],
        }

    # Overall benchmarks
    all_comps = [c.get("composite", 0) for c in scores]
    overall = {
        "avg": round(sum(all_comps) / len(all_comps)) if all_comps else 0,
        "median": sorted(all_comps)[len(all_comps)//2] if all_comps else 0,
        "total_companies": len(scores),
        "total_industries": len(industries),
    }

    # Consciousness tiers for consumers
    tiers = {
        "Highly Conscious": {"min": 70, "desc": "Your portfolio average is above 70 — you actively support human-centered companies."},
        "Conscious": {"min": 55, "desc": "Your portfolio average is 55-69 — good awareness, room to improve."},
        "Awakening": {"min": 42, "desc": "Your portfolio average is 42-54 — starting to pay attention."},
        "Unaware": {"min": 0, "desc": "Your portfolio average is below 42 — most companies you use are out of balance."},
    }

    # Alternative recommendations per industry
    alternatives = {}
    for ind, data in industries.items():
        top = sorted(data["companies"], key=lambda x: -x["composite"])
        if top:
            alternatives[ind] = {
                "best_option": top[0],
                "top_3": top[:3],
                "industry_avg": benchmarks[ind]["avg"],
            }

    output = {
        "name": "Consumer Consciousness Score",
        "patent": "Patent Pending — Morf Innovations LLC",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "overall": overall,
        "tiers": tiers,
        "industry_benchmarks": benchmarks,
        "alternatives": alternatives,
    }

    with open(output_dir / "benchmarks.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Companies: {len(scores)}")
    print(f"  Industries: {len(industries)}")
    print(f"  Overall average: {overall['avg']}")
    print(f"\n  Industry Benchmarks:")
    for ind, b in sorted(benchmarks.items(), key=lambda x: -x[1]["avg"])[:10]:
        print(f"    {ind:15s}  Avg: {b['avg']:3d}  Best: {b['best']:3d}  Count: {b['count']}")
    print(f"\n  Consumer Tiers:")
    for tier, info in tiers.items():
        print(f"    {tier:20s}  Min: {info['min']}")
    print(f"\n  Output: data/consumer_consciousness/benchmarks.json")


if __name__ == "__main__":
    compute_benchmarks()
