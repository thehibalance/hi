#!/usr/bin/env python3
"""
HI. — CDP Climate Disclosure Pipeline
Pulls climate disclosure data from CDP's public dataset.

Dimensions served:
  A — Alive & Environmental (emissions, targets, climate risk)
  N — Natural Transparency (disclosure quality, reporting completeness)

CDP provides public scores for responding companies.
Data source: https://www.cdp.net/en/responses
Public scores available as CSV downloads.

Usage:
  python cdp_pipeline.py --file data/cdp/CDP_Scores_2024.csv
  python cdp_pipeline.py  # Uses built-in known scores
"""

import json, os, sys, time, csv
from pathlib import Path

OUTPUT_DIR = Path("data/cdp")

# Known CDP scores for companies in our seed database
# Source: CDP public scores (A, A-, B, B-, C, C-, D, D-, F)
# Updated annually. These are from the most recent public disclosure.
CDP_KNOWN_SCORES = {
    # Tech
    "Apple": {"climate": "A-", "water": "B", "forests": None, "year": 2024},
    "Microsoft": {"climate": "A", "water": "A", "forests": None, "year": 2024},
    "Alphabet": {"climate": "B", "water": "B", "forests": None, "year": 2024},
    "Amazon": {"climate": "B-", "water": None, "forests": "B-", "year": 2024},
    "Meta": {"climate": "B", "water": None, "forests": None, "year": 2024},
    "Salesforce": {"climate": "A-", "water": None, "forests": None, "year": 2024},
    "Adobe": {"climate": "B", "water": None, "forests": None, "year": 2024},
    "NVIDIA": {"climate": "C", "water": None, "forests": None, "year": 2024},

    # Retail
    "Walmart": {"climate": "A-", "water": "B", "forests": "B-", "year": 2024},
    "Costco": {"climate": "D", "water": None, "forests": None, "year": 2024},
    "Target": {"climate": "B", "water": "C", "forests": None, "year": 2024},
    "Home Depot": {"climate": "B-", "water": None, "forests": "C", "year": 2024},
    "Nike": {"climate": "A-", "water": "B", "forests": None, "year": 2024},

    # Finance
    "JPMorgan Chase": {"climate": "A-", "water": "B-", "forests": None, "year": 2024},
    "Bank of America": {"climate": "A-", "water": "B", "forests": None, "year": 2024},
    "Goldman Sachs": {"climate": "B", "water": None, "forests": None, "year": 2024},

    # Healthcare
    "Johnson & Johnson": {"climate": "A-", "water": "A-", "forests": None, "year": 2024},
    "Pfizer": {"climate": "B", "water": "B-", "forests": None, "year": 2024},
    "CVS Health": {"climate": "C", "water": None, "forests": None, "year": 2024},

    # Energy
    "ExxonMobil": {"climate": "F", "water": "D", "forests": None, "year": 2024},
    "Chevron": {"climate": "F", "water": "D-", "forests": None, "year": 2024},
    "NextEra Energy": {"climate": "A-", "water": "B", "forests": None, "year": 2024},

    # Food
    "Coca-Cola": {"climate": "A-", "water": "A", "forests": "B", "year": 2024},
    "PepsiCo": {"climate": "A", "water": "A", "forests": "A-", "year": 2024},
    "McDonald's": {"climate": "B", "water": "C", "forests": "B-", "year": 2024},
    "Starbucks": {"climate": "B", "water": "B-", "forests": "C", "year": 2024},

    # Auto
    "Tesla": {"climate": "D-", "water": None, "forests": None, "year": 2024},
    "General Motors": {"climate": "A-", "water": "B", "forests": None, "year": 2024},
    "Ford": {"climate": "A-", "water": "B-", "forests": None, "year": 2024},

    # Defense
    "Boeing": {"climate": "B-", "water": None, "forests": None, "year": 2024},
    "Lockheed Martin": {"climate": "B", "water": None, "forests": None, "year": 2024},

    # Other
    "Disney": {"climate": "B", "water": "C", "forests": None, "year": 2024},
    "Patagonia": {"climate": "A-", "water": "B", "forests": "B", "year": 2024},

    # Non-responders (scored F by CDP for not responding)
    "Temu": {"climate": None, "water": None, "forests": None, "year": 2024, "non_responder": True},
    "Shein": {"climate": None, "water": None, "forests": None, "year": 2024, "non_responder": True},
}

# CDP letter grade to numeric score (0-100)
CDP_SCORE_MAP = {
    "A": 95, "A-": 85,
    "B": 70, "B-": 60,
    "C": 45, "C-": 35,
    "D": 20, "D-": 10,
    "F": 0,
}


def cdp_to_score(letter):
    """Convert CDP letter grade to 0-100 score."""
    if not letter:
        return None
    return CDP_SCORE_MAP.get(letter)


def compute_cdp_signals(company_name, cdp_data):
    """Convert CDP scores into HUMAN signals."""
    signals = {
        "company": company_name,
        "source": "CDP",
        "retrieved": time.strftime("%Y-%m-%d"),
        "a_signals": {},
        "n_signals": {},
    }

    if not cdp_data:
        signals["error"] = "No CDP data available"
        return signals

    # Climate score
    climate_letter = cdp_data.get("climate")
    climate_score = cdp_to_score(climate_letter)
    if climate_score is not None:
        signals["a_signals"]["cdp_climate_letter"] = climate_letter
        signals["a_signals"]["cdp_climate_score"] = climate_score
    
    # Water score
    water_letter = cdp_data.get("water")
    water_score = cdp_to_score(water_letter)
    if water_score is not None:
        signals["a_signals"]["cdp_water_letter"] = water_letter
        signals["a_signals"]["cdp_water_score"] = water_score

    # Forests score
    forests_letter = cdp_data.get("forests")
    forests_score = cdp_to_score(forests_letter)
    if forests_score is not None:
        signals["a_signals"]["cdp_forests_letter"] = forests_letter
        signals["a_signals"]["cdp_forests_score"] = forests_score

    # Composite CDP score (average of available scores)
    available_scores = [s for s in [climate_score, water_score, forests_score] if s is not None]
    if available_scores:
        signals["a_signals"]["cdp_composite"] = round(sum(available_scores) / len(available_scores), 1)
        signals["a_signals"]["cdp_dimensions_reported"] = len(available_scores)

    # Non-responder flag
    if cdp_data.get("non_responder"):
        signals["n_signals"]["cdp_non_responder"] = True
        signals["n_signals"]["transparency_flag"] = "FAIL — company does not respond to CDP disclosure requests"
    elif climate_letter:
        signals["n_signals"]["cdp_non_responder"] = False
        # Disclosure quality based on grade
        if climate_score and climate_score >= 85:
            signals["n_signals"]["disclosure_quality"] = "EXCELLENT — comprehensive climate disclosure"
        elif climate_score and climate_score >= 60:
            signals["n_signals"]["disclosure_quality"] = "GOOD — meaningful climate disclosure"
        elif climate_score and climate_score >= 35:
            signals["n_signals"]["disclosure_quality"] = "PARTIAL — limited climate disclosure"
        else:
            signals["n_signals"]["disclosure_quality"] = "POOR — minimal climate disclosure"

    signals["year"] = cdp_data.get("year", 2024)

    return signals


def load_from_csv(csv_path):
    """Load CDP scores from a downloaded CSV file."""
    scores = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Organization", row.get("organization", ""))
            climate = row.get("Climate Change Score", row.get("climate_score", ""))
            water = row.get("Water Security Score", row.get("water_score", ""))
            forests = row.get("Forests Score", row.get("forests_score", ""))
            
            if name:
                scores[name] = {
                    "climate": climate if climate and climate != "Not scored" else None,
                    "water": water if water and water != "Not scored" else None,
                    "forests": forests if forests and forests != "Not scored" else None,
                    "year": 2024,
                }
    return scores


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HI. CDP Pipeline")
    parser.add_argument("--file", help="Path to CDP CSV download")
    parser.add_argument("--output", default="data/cdp")
    parser.add_argument("--company", help="Look up a single company")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load scores
    if args.file and os.path.exists(args.file):
        print(f"Loading CDP scores from {args.file}")
        scores = load_from_csv(args.file)
    else:
        print("Using built-in CDP scores (update with --file for latest data)")
        scores = CDP_KNOWN_SCORES

    if args.company:
        cdp_data = scores.get(args.company)
        signals = compute_cdp_signals(args.company, cdp_data)
        print(json.dumps(signals, indent=2))
        return

    print(f"Processing {len(scores)} companies")
    all_signals = []

    for company, cdp_data in scores.items():
        signals = compute_cdp_signals(company, cdp_data)
        all_signals.append(signals)

        climate = cdp_data.get("climate", "—")
        water = cdp_data.get("water", "—")
        nr = " (NON-RESPONDER)" if cdp_data.get("non_responder") else ""
        print(f"  {company:30s}  Climate: {climate:3s}  Water: {water:3s}{nr}")

    combined = output_dir / "all_companies.json"
    with open(combined, "w") as f:
        json.dump(all_signals, f, indent=2)

    print(f"\nDone. Output: {combined}")


if __name__ == "__main__":
    main()
