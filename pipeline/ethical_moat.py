#!/usr/bin/env python3
"""
Ethical Moat Indicator — Patent Feature #6
Measures how resistant a company is to AI displacement.

"If AI came for this company tomorrow, how much irreplaceable human value would be lost?"

Moat Strength Levels:
  • FORTRESS (80-100) — Deep human value that AI cannot replicate
  • STRONG   (60-79)  — Significant human elements, hard to automate
  • MODERATE (40-59)  — Mixed — some human value, some automation risk
  • THIN     (20-39)  — Heavily automatable, limited human differentiation
  • NONE     (0-19)   — Already substantially automated or easily replaceable

Moat Components (what makes a company hard to replace with AI):
  1. Craft Depth      — Revenue per employee vs industry (low = more humans doing real work)
  2. Human Capital    — Headcount stability + growth (investing in people)
  3. Empathy Moat     — Glassdoor rating + DEI/HRC (genuine human care)
  4. Ethics Shield    — CEO accountability + low violations (principled leadership)
  5. Transparency     — CDP disclosure + low humanwashing (nothing to hide)
  6. AI Resistance    — Low AI hiring ratio (not racing to replace humans)

Output: data/ethical_moat/all_moats.json

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


def compute_moats():
    print(f"\n{'='*60}")
    print(f"  Ethical Moat Indicator")
    print(f"  Patent Feature: AI Displacement Resistance")
    print(f"{'='*60}\n")

    scores = load_json("data/scores/all_scores.json")

    output_dir = Path("data/ethical_moat")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    level_counts = {"fortress": 0, "strong": 0, "moderate": 0, "thin": 0, "none": 0}

    for company in scores:
        name = company.get("company", "")
        ticker = company.get("ticker", "")
        industry = company.get("industry", "")
        composite = company.get("composite", 0)
        hi_grade = company.get("hi_grade", "?")
        ks = company.get("key_signals", {})
        hw_flags = company.get("humanwashing_flags", [])

        D_H = company.get("D_H", 50)
        D_U = company.get("D_U", 50)
        D_M = company.get("D_M", 50)
        D_A = company.get("D_A", 50)
        D_N = company.get("D_N", 50)

        moat_components = {}
        moat_reasons = []

        # ═══ 1. CRAFT DEPTH (0-100) ═══
        # Low revenue/employee = more humans doing real work = deeper moat
        rpe = ks.get("revenue_per_employee")
        if rpe is not None:
            if rpe < 150000:
                craft = 90
                moat_reasons.append("Low automation: $" + f"{rpe:,.0f}" + "/employee")
            elif rpe < 300000:
                craft = 75
            elif rpe < 500000:
                craft = 60
            elif rpe < 1000000:
                craft = 40
                moat_reasons.append("Moderate automation: $" + f"{rpe:,.0f}" + "/employee")
            elif rpe < 2000000:
                craft = 25
            else:
                craft = 10
                moat_reasons.append("Heavy automation: $" + f"{rpe:,.0f}" + "/employee")
        else:
            craft = 50  # default
        moat_components["craft_depth"] = craft

        # ═══ 2. HUMAN CAPITAL (0-100) ═══
        # Growing workforce = investing in people
        hc_change = ks.get("headcount_change_pct")
        headcount = ks.get("headcount")
        if hc_change is not None:
            if hc_change > 10:
                hcap = 90
                moat_reasons.append(f"Workforce growing {hc_change}%")
            elif hc_change > 0:
                hcap = 70
            elif hc_change > -5:
                hcap = 50
            elif hc_change > -15:
                hcap = 30
                moat_reasons.append(f"Workforce declining {hc_change}%")
            else:
                hcap = 10
                moat_reasons.append(f"Workforce shrinking {hc_change}%")
        elif headcount and headcount > 50000:
            hcap = 65  # large workforce = some moat
        else:
            hcap = 50
        moat_components["human_capital"] = hcap

        # ═══ 3. EMPATHY MOAT (0-100) ═══
        # High employee satisfaction + inclusion = human culture AI can't replicate
        gd = ks.get("glassdoor_rating")
        dei = ks.get("dei_score")
        hrc = ks.get("hrc_score")

        empathy_signals = []
        if gd is not None:
            empathy_signals.append(min(gd * 20, 100))  # 5.0 = 100
            if gd >= 4.0:
                moat_reasons.append(f"Strong employee culture (★{gd})")
            elif gd < 3.0:
                moat_reasons.append(f"Weak employee culture (★{gd})")
        if dei is not None:
            empathy_signals.append(dei)
        if hrc is not None:
            empathy_signals.append(hrc)

        empathy = round(sum(empathy_signals) / len(empathy_signals)) if empathy_signals else 50
        moat_components["empathy_moat"] = empathy

        # ═══ 4. ETHICS SHIELD (0-100) ═══
        # CEO accountability + clean record = principled leadership that protects humans
        ceo = ks.get("ceo_accountability_score")
        epa = ks.get("epa_violations")

        ethics_signals = []
        if ceo is not None:
            ethics_signals.append(ceo)
            if ceo >= 70:
                moat_reasons.append(f"Strong leadership accountability ({ceo}/100)")
            elif ceo < 30:
                moat_reasons.append(f"Weak leadership accountability ({ceo}/100)")
        if epa is not None:
            ethics_signals.append(max(100 - epa * 10, 0))
        # Use M dimension as baseline
        ethics_signals.append(D_M)

        ethics = round(sum(ethics_signals) / len(ethics_signals)) if ethics_signals else 50
        moat_components["ethics_shield"] = ethics

        # ═══ 5. TRANSPARENCY WALL (0-100) ═══
        # Open disclosure = nothing to hide = moat through trust
        cdp = ks.get("cdp_climate")
        transparency_signals = [D_N]

        if cdp and cdp not in ["N/A", "—"]:
            cdp_map = {"A": 95, "A-": 85, "B": 75, "B-": 65, "C": 55, "D": 35, "F": 10}
            if cdp in cdp_map:
                transparency_signals.append(cdp_map[cdp])

        if not hw_flags:
            transparency_signals.append(80)  # clean = bonus
        else:
            transparency_signals.append(20)  # humanwashing = anti-moat
            moat_reasons.append(f"{len(hw_flags)} humanwashing flag(s) weaken moat")

        transparency = round(sum(transparency_signals) / len(transparency_signals))
        moat_components["transparency_wall"] = transparency

        # ═══ 6. AI RESISTANCE (0-100) ═══
        # Low AI hiring ratio = not racing to replace humans
        ai_ratio = ks.get("ai_hiring_ratio")
        if ai_ratio is not None:
            if ai_ratio < 0.05:
                ai_resist = 90
                moat_reasons.append(f"Very low AI hiring ({ai_ratio*100:.0f}%)")
            elif ai_ratio < 0.15:
                ai_resist = 70
            elif ai_ratio < 0.25:
                ai_resist = 50
            elif ai_ratio < 0.35:
                ai_resist = 30
                moat_reasons.append(f"High AI hiring ({ai_ratio*100:.0f}%)")
            else:
                ai_resist = 10
                moat_reasons.append(f"AI-dominant hiring ({ai_ratio*100:.0f}%)")
        else:
            ai_resist = 50
        moat_components["ai_resistance"] = ai_resist

        # ═══ COMPUTE MOAT SCORE ═══
        # Weighted composite — craft and AI resistance matter most
        moat_score = round(
            0.25 * craft +
            0.15 * hcap +
            0.20 * empathy +
            0.15 * ethics +
            0.10 * transparency +
            0.15 * ai_resist
        )

        moat_score = max(0, min(100, moat_score))

        # Classify
        if moat_score >= 80:
            moat_level = "fortress"
            moat_label = "Fortress"
        elif moat_score >= 60:
            moat_level = "strong"
            moat_label = "Strong"
        elif moat_score >= 40:
            moat_level = "moderate"
            moat_label = "Moderate"
        elif moat_score >= 20:
            moat_level = "thin"
            moat_label = "Thin"
        else:
            moat_level = "none"
            moat_label = "None"

        level_counts[moat_level] += 1

        results.append({
            "company": name,
            "ticker": ticker,
            "industry": industry,
            "hi_grade": hi_grade,
            "composite": composite,
            "moat_score": moat_score,
            "moat_level": moat_level,
            "moat_label": moat_label,
            "components": moat_components,
            "reasons": moat_reasons[:5],
        })

    # Sort by moat score
    results.sort(key=lambda x: x["moat_score"], reverse=True)

    # ═══ SAVE ═══
    with open(output_dir / "all_moats.json", "w") as f:
        json.dump(results, f, indent=2)

    fortresses = [r for r in results if r["moat_level"] == "fortress"]
    thin = [r for r in results if r["moat_level"] in ("thin", "none")]

    with open(output_dir / "fortresses.json", "w") as f:
        json.dump(fortresses, f, indent=2)
    with open(output_dir / "vulnerable.json", "w") as f:
        json.dump(thin, f, indent=2)

    metadata = {
        "name": "Ethical Moat Indicator",
        "patent": "Patent Pending — Morf Innovations LLC",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_analyzed": len(results),
        "distribution": level_counts,
        "avg_moat": round(sum(r["moat_score"] for r in results) / len(results)) if results else 0,
    }
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # ═══ PRINT SUMMARY ═══
    print(f"  Companies analyzed: {len(results)}")
    print(f"  Average moat score: {metadata['avg_moat']}")
    print(f"\n  Distribution:")
    icons = {"fortress": "🏰", "strong": "🛡", "moderate": "⚔", "thin": "📄", "none": "💨"}
    for level in ["fortress", "strong", "moderate", "thin", "none"]:
        print(f"    {icons[level]} {level.capitalize():10s}: {level_counts[level]}")

    if fortresses:
        print(f"\n  FORTRESSES (hardest to replace with AI):")
        for f in fortresses[:10]:
            print(f"    {f['moat_score']:3d}  {f['company']:30s}  {f['hi_grade']:5s}  {f['reasons'][0] if f['reasons'] else ''}")

    if thin:
        print(f"\n  MOST VULNERABLE (easiest to displace):")
        for t in thin[:10]:
            print(f"    {t['moat_score']:3d}  {t['company']:30s}  {t['hi_grade']:5s}  {t['reasons'][0] if t['reasons'] else ''}")

    print(f"\n  {'='*60}")
    print(f"  Ethical Moat Indicator™ — Patent Pending")
    print(f"  {'='*60}")
    print(f"\n  Outputs:")
    print(f"    data/ethical_moat/all_moats.json   — {len(results)} companies")
    print(f"    data/ethical_moat/fortresses.json   — {len(fortresses)} fortress companies")
    print(f"    data/ethical_moat/vulnerable.json   — {len(thin)} vulnerable companies")
    print(f"    data/ethical_moat/metadata.json     — Analysis metadata")

    return results


if __name__ == "__main__":
    compute_moats()
