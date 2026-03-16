#!/usr/bin/env python3
"""
Empathy Authenticity Watermark — Patent Feature #4
Detects whether a company's empathy signals are genuine or performative.

"100/100 on DEI and HRC but Glassdoor is 2.8 stars? That's performative empathy."

Watermark Levels:
  • AUTHENTIC    — Empathy signals align across internal + external sources
  • MIXED       — Some genuine signals, some performative
  • PERFORMATIVE — High public scores but low internal satisfaction
  • INSUFFICIENT — Not enough data to assess

The watermark cross-references:
  - External signals (DEI score, HRC score, CDP disclosure)
  - Internal signals (Glassdoor rating, CEO approval, headcount change)
  - Public signals (media coverage, humanwashing flags)

When external scores are high but internal scores are low, that's
performative empathy — looking good on paper while employees suffer.

Output: data/empathy_watermark/all_watermarks.json

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


def compute_watermarks():
    print(f"\n{'='*60}")
    print(f"  Empathy Authenticity Watermark")
    print(f"  Patent Feature: Real vs Performative Empathy")
    print(f"{'='*60}\n")

    scores = load_json("data/scores/all_scores.json")

    output_dir = Path("data/empathy_watermark")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    level_counts = {"authentic": 0, "mixed": 0, "performative": 0, "insufficient": 0}

    for c in scores:
        name = c.get("company", "")
        ticker = c.get("ticker", "")
        industry = c.get("industry", "")
        ks = c.get("key_signals", {})
        hw_flags = c.get("humanwashing_flags", [])

        D_U = c.get("D_U", 0)

        # ═══ EXTERNAL SIGNALS (public-facing empathy) ═══
        external_signals = []
        dei = ks.get("dei_score")
        hrc = ks.get("hrc_score")
        cdp = ks.get("cdp_climate")

        if dei is not None:
            external_signals.append(dei)
        if hrc is not None:
            external_signals.append(hrc)
        if cdp and cdp not in ["N/A", "—"]:
            cdp_map = {"A": 95, "A-": 85, "B": 75, "B-": 65, "C": 55, "D": 35, "F": 10}
            if cdp in cdp_map:
                external_signals.append(cdp_map[cdp])

        external_avg = round(sum(external_signals) / len(external_signals)) if external_signals else None

        # ═══ INTERNAL SIGNALS (employee experience) ═══
        internal_signals = []
        gd = ks.get("glassdoor_rating")
        ceo = ks.get("ceo_accountability_score")
        hc_change = ks.get("headcount_change_pct")

        if gd is not None:
            internal_signals.append(min(gd * 20, 100))  # 5.0 = 100
        if ceo is not None:
            internal_signals.append(ceo)
        if hc_change is not None:
            # Growing workforce = genuine investment in people
            if hc_change > 5:
                internal_signals.append(80)
            elif hc_change > 0:
                internal_signals.append(60)
            elif hc_change > -5:
                internal_signals.append(45)
            else:
                internal_signals.append(20)

        internal_avg = round(sum(internal_signals) / len(internal_signals)) if internal_signals else None

        # ═══ WATERMARK COMPUTATION ═══
        reasons = []

        if external_avg is None or internal_avg is None:
            watermark = "insufficient"
            watermark_label = "Insufficient Data"
            authenticity_score = None
            reasons.append("Not enough data to cross-reference empathy signals")
        else:
            gap = external_avg - internal_avg  # Positive = external > internal = performative

            if gap > 25:
                watermark = "performative"
                watermark_label = "Performative"
                authenticity_score = max(0, 100 - gap)
                reasons.append(f"External empathy ({external_avg}) far exceeds internal reality ({internal_avg})")
                if dei and dei >= 80 and gd and gd < 3.5:
                    reasons.append(f"DEI score {dei}/100 but Glassdoor only ★{gd}")
                if hrc and hrc >= 80 and ceo and ceo < 40:
                    reasons.append(f"HRC score {hrc}/100 but CEO accountability only {ceo}/100")
            elif gap > 10:
                watermark = "mixed"
                watermark_label = "Mixed"
                authenticity_score = max(0, 100 - gap)
                reasons.append(f"External empathy ({external_avg}) somewhat exceeds internal ({internal_avg})")
            elif gap < -10:
                watermark = "authentic"
                watermark_label = "Authentic"
                authenticity_score = min(100, 100 - gap)  # Internal > external = genuine
                reasons.append(f"Internal reality ({internal_avg}) exceeds public image ({external_avg}) — genuinely human")
            else:
                watermark = "authentic"
                watermark_label = "Authentic"
                authenticity_score = round((external_avg + internal_avg) / 2)
                reasons.append(f"Internal ({internal_avg}) and external ({external_avg}) signals align")

            if hw_flags:
                if watermark == "authentic":
                    watermark = "mixed"
                    watermark_label = "Mixed"
                reasons.append(f"{len(hw_flags)} humanwashing flag(s) detected")
                if authenticity_score:
                    authenticity_score = max(0, authenticity_score - len(hw_flags) * 10)

        level_counts[watermark] += 1

        results.append({
            "company": name,
            "ticker": ticker,
            "industry": industry,
            "hi_grade": c.get("hi_grade", "?"),
            "D_U": D_U,
            "external_avg": external_avg,
            "internal_avg": internal_avg,
            "authenticity_score": authenticity_score,
            "watermark": watermark,
            "watermark_label": watermark_label,
            "signals": {
                "dei_score": dei,
                "hrc_score": hrc,
                "glassdoor": gd,
                "ceo_score": ceo,
                "headcount_change": hc_change,
            },
            "reasons": reasons[:4],
        })

    # Sort by authenticity score (lowest = most performative)
    scored = [r for r in results if r["authenticity_score"] is not None]
    scored.sort(key=lambda x: x["authenticity_score"])
    unscored = [r for r in results if r["authenticity_score"] is None]
    results = scored + unscored

    with open(output_dir / "all_watermarks.json", "w") as f:
        json.dump(results, f, indent=2)

    performative = [r for r in results if r["watermark"] == "performative"]
    authentic = [r for r in results if r["watermark"] == "authentic"]

    with open(output_dir / "performative.json", "w") as f:
        json.dump(performative, f, indent=2)

    metadata = {
        "name": "Empathy Authenticity Watermark",
        "patent": "Patent Pending — Morf Innovations LLC",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "total_analyzed": len(results),
        "distribution": level_counts,
    }
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"  Companies: {len(results)}")
    print(f"  Authentic: {level_counts['authentic']}, Mixed: {level_counts['mixed']}, Performative: {level_counts['performative']}, Insufficient: {level_counts['insufficient']}")
    if performative:
        print(f"\n  MOST PERFORMATIVE (looks good, feels bad):")
        for p in performative[:10]:
            print(f"    {p['authenticity_score']:3d}  {p['company']:30s}  Ext:{p['external_avg']}  Int:{p['internal_avg']}  {p['reasons'][0] if p['reasons'] else ''}")
    if authentic:
        auth_sorted = sorted(authentic, key=lambda x: -(x['authenticity_score'] or 0))
        print(f"\n  MOST AUTHENTIC (genuinely human):")
        for a in auth_sorted[:10]:
            print(f"    {a['authenticity_score']:3d}  {a['company']:30s}  Ext:{a['external_avg']}  Int:{a['internal_avg']}")

    print(f"\n  Output: data/empathy_watermark/")


if __name__ == "__main__":
    compute_watermarks()
