#!/usr/bin/env python3
"""
Grade Arbitrage Detection — Patent Feature #9
Detects discrepancies between HI Grade and traditional ESG ratings.

"This company scores A on ESG but C on HI — here's why."

Arbitrage Types:
  • ESG WASHING  — High ESG, Low HI (looks good on paper, fails human metrics)
  • HIDDEN GEM   — Low/No ESG, High HI (under-recognized humanity)
  • ALIGNED      — ESG and HI agree (no arbitrage opportunity)
  • DOUBLE RISK  — Low ESG, Low HI (failing everywhere)

Data Sources:
  • Finnhub ESG scores (environment, social, governance)
  • CDP Climate grades (A through F)
  • HI Grade composite + dimensions

Output: data/arbitrage/all_arbitrage.json

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


def load_dict(path, key="ticker"):
    data = load_json(path)
    idx = {}
    for r in data:
        k = r.get(key, "")
        if k:
            idx[k.upper() if isinstance(k, str) else k] = r
    return idx


def normalize_esg(raw_score, scale_max=100):
    """Normalize various ESG score scales to 0-100."""
    if raw_score is None:
        return None
    if isinstance(raw_score, str):
        # Letter grade conversion (CDP-style)
        grade_map = {"A": 95, "A-": 85, "B": 75, "B-": 65, "C": 55,
                     "C-": 45, "D": 35, "D-": 25, "F": 10}
        return grade_map.get(raw_score.strip())
    # Numeric — normalize to 0-100 scale
    if scale_max != 100 and scale_max > 0:
        return round((raw_score / scale_max) * 100, 1)
    return round(raw_score, 1)


def compute_arbitrage():
    print(f"\n{'='*60}")
    print(f"  Grade Arbitrage Detection")
    print(f"  Patent Feature: HI vs ESG Gap Analysis")
    print(f"{'='*60}\n")

    # Load data
    scores = load_json("data/scores/all_scores.json")
    finnhub = load_dict("data/finnhub/all_companies.json")
    cdp_data = load_dict("data/cdp/all_companies.json")

    # Also index CDP by company name
    cdp_names = {}
    for r in load_json("data/cdp/all_companies.json"):
        n = r.get("company", "").lower().strip()
        if n:
            cdp_names[n] = r

    output_dir = Path("data/arbitrage")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    type_counts = {"esg_washing": 0, "hidden_gem": 0, "aligned": 0,
                   "double_risk": 0, "no_esg_data": 0}

    for company in scores:
        ticker = company.get("ticker", "")
        name = company.get("company", "")
        hi_composite = company.get("composite", 0)
        hi_grade = company.get("hi_grade", "?")
        industry = company.get("industry", "")

        # ═══ GATHER ESG SIGNALS ═══
        fh = finnhub.get(ticker.upper(), {}) if ticker else {}
        cd = cdp_data.get(ticker.upper(), {}) if ticker else {}
        if not cd:
            cd = cdp_names.get(name.lower().strip(), {})

        # Finnhub ESG (scored 0-100 or similar)
        fh_esg = fh.get("esg_scores", {}) or fh.get("esg", {})
        esg_total = fh_esg.get("totalEsg") or fh_esg.get("total") or fh_esg.get("esg_score")
        esg_env = fh_esg.get("environmentScore") or fh_esg.get("environment")
        esg_social = fh_esg.get("socialScore") or fh_esg.get("social")
        esg_gov = fh_esg.get("governanceScore") or fh_esg.get("governance")

        # CDP Climate Grade
        cdp_climate = None
        if cd:
            cdp_climate = cd.get("a_signals", {}).get("cdp_climate_score")
            if not cdp_climate:
                cdp_climate = cd.get("n_signals", {}).get("cdp_climate_score")

        # ═══ BUILD COMPOSITE ESG SCORE ═══
        esg_components = []

        # Finnhub ESG total (normalize if needed)
        if esg_total is not None:
            normalized = normalize_esg(esg_total)
            if normalized is not None:
                esg_components.append(("Finnhub ESG", normalized))

        # CDP Climate (letter → numeric)
        if cdp_climate:
            normalized = normalize_esg(cdp_climate)
            if normalized is not None:
                esg_components.append(("CDP Climate", normalized))

        # Finnhub sub-scores as fallback
        if not esg_total and (esg_env or esg_social or esg_gov):
            sub_scores = [s for s in [esg_env, esg_social, esg_gov] if s is not None]
            if sub_scores:
                avg = sum(normalize_esg(s) or 0 for s in sub_scores) / len(sub_scores)
                esg_components.append(("Finnhub Sub-avg", round(avg, 1)))

        if not esg_components:
            type_counts["no_esg_data"] += 1
            continue

        # Weighted composite ESG score
        esg_composite = round(sum(v for _, v in esg_components) / len(esg_components), 1)

        # ═══ ARBITRAGE DETECTION ═══
        gap = hi_composite - esg_composite  # Positive = HI higher, Negative = ESG higher
        abs_gap = abs(gap)

        # Classify
        if abs_gap < 10:
            arb_type = "aligned"
            arb_label = "Aligned"
            arb_desc = "HI Grade and ESG ratings broadly agree."
        elif gap < -10:
            # ESG is higher than HI — potential ESG washing
            arb_type = "esg_washing"
            arb_label = "ESG Washing"
            arb_desc = f"ESG rates this company {abs_gap:.0f} points higher than HI. Traditional metrics may miss human impact."
        elif gap > 10 and hi_composite >= 60:
            # HI is higher than ESG — hidden gem
            arb_type = "hidden_gem"
            arb_label = "Hidden Gem"
            arb_desc = f"HI rates this company {abs_gap:.0f} points higher than ESG. Human practices exceed what traditional ESG captures."
        elif gap > 10 and hi_composite < 60:
            arb_type = "aligned"
            arb_label = "Low ESG, Moderate HI"
            arb_desc = "Both ratings are in the lower range."
        elif esg_composite < 50 and hi_composite < 50:
            arb_type = "double_risk"
            arb_label = "Double Risk"
            arb_desc = "Both HI and ESG ratings are concerning."
        else:
            arb_type = "aligned"
            arb_label = "Aligned"
            arb_desc = "HI Grade and ESG ratings broadly agree."

        type_counts[arb_type] += 1

        # Build reasons for gap
        gap_reasons = []
        hi_dims = {
            "H": company.get("D_H", 0), "U": company.get("D_U", 0),
            "M": company.get("D_M", 0), "A": company.get("D_A", 0),
            "N": company.get("D_N", 0)
        }

        # Find weakest HI dimensions (things ESG might miss)
        for d, v in sorted(hi_dims.items(), key=lambda x: x[1]):
            if v < 50:
                dim_names = {"H": "Human Consciousness", "U": "Understanding & Empathy",
                             "M": "Moral & Ethical Conduct", "A": "Alive & Environmental",
                             "N": "Natural Transparency"}
                esg_note = "ESG typically doesn't measure this" if d in ['H', 'U'] else "flagged by both frameworks"
                gap_reasons.append(f"{dim_names.get(d, d)} scored {v} — {esg_note}")

        # Humanwashing flags add to arbitrage signal
        hw_flags = company.get("humanwashing_flags", [])
        if hw_flags and arb_type == "esg_washing":
            gap_reasons.append(f"{len(hw_flags)} humanwashing flag(s) detected")

        # CEO accountability
        ks = company.get("key_signals", {})
        ceo_score = ks.get("ceo_accountability_score")
        if ceo_score is not None and ceo_score < 40:
            gap_reasons.append(f"CEO accountability score: {ceo_score}/100")

        entry = {
            "company": name,
            "ticker": ticker,
            "industry": industry,
            "hi_composite": hi_composite,
            "hi_grade": hi_grade,
            "esg_composite": esg_composite,
            "esg_components": {src: val for src, val in esg_components},
            "gap": round(gap, 1),
            "abs_gap": round(abs_gap, 1),
            "arbitrage_type": arb_type,
            "arbitrage_label": arb_label,
            "arbitrage_description": arb_desc,
            "gap_reasons": gap_reasons[:5],
            "dimensions": hi_dims,
        }
        results.append(entry)

    # Sort by absolute gap (biggest arbitrage first)
    results.sort(key=lambda x: x["abs_gap"], reverse=True)

    # ═══ SAVE ═══
    with open(output_dir / "all_arbitrage.json", "w") as f:
        json.dump(results, f, indent=2)

    # Top ESG washers and hidden gems
    washers = [r for r in results if r["arbitrage_type"] == "esg_washing"]
    gems = [r for r in results if r["arbitrage_type"] == "hidden_gem"]
    risks = [r for r in results if r["arbitrage_type"] == "double_risk"]

    with open(output_dir / "esg_washers.json", "w") as f:
        json.dump(washers, f, indent=2)
    with open(output_dir / "hidden_gems.json", "w") as f:
        json.dump(gems, f, indent=2)

    # Metadata
    metadata = {
        "name": "Grade Arbitrage Detection",
        "patent": "Patent Pending — Morf Innovations LLC",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_analyzed": len(results),
        "no_esg_data": type_counts["no_esg_data"],
        "arbitrage_distribution": type_counts,
        "top_esg_washers": len(washers),
        "hidden_gems": len(gems),
        "double_risk": len(risks),
        "avg_gap": round(sum(r["abs_gap"] for r in results) / len(results), 1) if results else 0,
    }
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # ═══ PRINT SUMMARY ═══
    print(f"  Companies analyzed: {len(results)}")
    print(f"  No ESG data: {type_counts['no_esg_data']}")
    print(f"\n  Arbitrage Distribution:")
    labels = {"esg_washing": "🔴 ESG Washing", "hidden_gem": "💎 Hidden Gem",
              "aligned": "✅ Aligned", "double_risk": "⚠ Double Risk"}
    for t, label in labels.items():
        print(f"    {label}: {type_counts[t]}")

    if washers:
        print(f"\n  TOP ESG WASHERS (ESG says good, HI says bad):")
        for w in washers[:10]:
            print(f"    {w['company']:30s}  ESG: {w['esg_composite']:5.1f}  HI: {w['hi_composite']:3d}  Gap: {w['gap']:+.0f}  {w['hi_grade']}")
            if w['gap_reasons']:
                print(f"      → {w['gap_reasons'][0]}")

    if gems:
        print(f"\n  HIDDEN GEMS (HI says good, ESG underrates):")
        for g in gems[:10]:
            print(f"    {g['company']:30s}  ESG: {g['esg_composite']:5.1f}  HI: {g['hi_composite']:3d}  Gap: {g['gap']:+.0f}  {g['hi_grade']}")

    if risks:
        print(f"\n  DOUBLE RISK (both say bad):")
        for r in risks[:5]:
            print(f"    {r['company']:30s}  ESG: {r['esg_composite']:5.1f}  HI: {r['hi_composite']:3d}")

    print(f"\n  Average absolute gap: {metadata['avg_gap']}")

    print(f"\n  {'='*60}")
    print(f"  Grade Arbitrage Detection™ — Patent Pending")
    print(f"  {'='*60}")
    print(f"\n  Outputs:")
    print(f"    data/arbitrage/all_arbitrage.json  — {len(results)} companies")
    print(f"    data/arbitrage/esg_washers.json    — {len(washers)} ESG washers")
    print(f"    data/arbitrage/hidden_gems.json    — {len(gems)} hidden gems")
    print(f"    data/arbitrage/metadata.json       — Analysis metadata")

    return results


if __name__ == "__main__":
    compute_arbitrage()
