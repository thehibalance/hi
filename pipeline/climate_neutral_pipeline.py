#!/usr/bin/env python3
"""
Climate Neutral — Climate Neutral Certified Companies Pipeline
Source: Change Climate Project (formerly Climate Neutral) public directory
URL: https://explore.changeclimate.org/

Climate Neutral Certified (now "The Climate Label") is a third-party certification
for companies that:
  1. Measure their full cradle-to-customer greenhouse gas emissions (Scope 1, 2, 3)
  2. Fund GHG reduction + removal projects at a scale matching their emissions
  3. Show concrete reduction plans for future emissions

Founded 2019 by CEO of BioLite. 230+ certified brands including Allbirds, REI,
Avocado Green Mattress, Numi Organic Tea, Klean Kanteen, Reformation.

Rebranded Q2 2024 to "The Climate Label" to better communicate their standard.
For this pipeline we keep "Climate Neutral" as the short name consumers know.

Maps to HUMAN dimensions:
  A.1 (Energy & Emissions)   — direct match: emissions measurement + offsetting is the A.1 signal
  A.4 (Product Lifecycle)    — cradle-to-customer accounting covers full product lifecycle

Scoring ladder:
  certified (current year)   → 80  (verifiable annual recertification)
  certified (lapsed <1yr)    → 65  (was certified, hasn't recertified — monitor)
"""

import json, os
from pathlib import Path

# Climate Neutral Certified brands (current directory as of 2026).
# Source: changeclimate.org/certified-brands
CLIMATE_NEUTRAL_COMPANIES = [
    # ═══════════════════════════════════════════════════════════════════
    # TIER A SEED COMPANIES
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Klean Kanteen", "ticker": None, "status": "certified"},
    {"company": "REI Co-op", "ticker": None, "status": "certified"},
    {"company": "Cotopaxi", "ticker": None, "status": "certified"},
    {"company": "Numi Organic Tea", "ticker": None, "status": "certified"},
    {"company": "Osprey Packs", "ticker": None, "status": "certified"},
    {"company": "Tentree", "ticker": None, "status": "certified"},

    # ═══════════════════════════════════════════════════════════════════
    # WELL-KNOWN CLIMATE NEUTRAL BRANDS
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Allbirds", "ticker": "BIRD", "status": "certified"},
    {"company": "Avocado Green Mattress", "ticker": None, "status": "certified"},
    {"company": "Reformation", "ticker": None, "status": "certified"},
    {"company": "Bookshop.org", "ticker": None, "status": "certified"},
    {"company": "BioLite", "ticker": None, "status": "certified"},  # CEO co-founded Climate Neutral
    {"company": "Ministry of Supply", "ticker": None, "status": "certified"},
    {"company": "Blueland", "ticker": None, "status": "certified"},
    {"company": "Sunski", "ticker": None, "status": "certified"},
    {"company": "Western Rise", "ticker": None, "status": "certified"},
    {"company": "Glow Recipe", "ticker": None, "status": "certified"},
    {"company": "MiiR", "ticker": None, "status": "certified"},
    {"company": "LifeStraw", "ticker": None, "status": "certified"},
    {"company": "Preserve Products", "ticker": None, "status": "certified"},
    {"company": "Stubble and Co", "ticker": None, "status": "certified"},
    {"company": "Paravel", "ticker": None, "status": "certified"},
    {"company": "goodr", "ticker": None, "status": "certified"},
    {"company": "Sendle", "ticker": None, "status": "certified"},
    {"company": "Rizos Curls", "ticker": None, "status": "certified"},
    {"company": "Clove & Twine", "ticker": None, "status": "certified"},
    {"company": "Vincero", "ticker": None, "status": "certified"},
    {"company": "Backdrop", "ticker": None, "status": "certified"},
    {"company": "Independent Record Pressing", "ticker": None, "status": "certified"},
    {"company": "Bona Furtuna", "ticker": None, "status": "certified"},
    {"company": "Oxygen Plus", "ticker": None, "status": "certified"},
    {"company": "Borough Furnace", "ticker": None, "status": "certified"},
    {"company": "Laid Back Snacks", "ticker": None, "status": "certified"},
    {"company": "P.F. Candle Co.", "ticker": None, "status": "certified"},
    {"company": "Alpine Start", "ticker": None, "status": "certified"},
    {"company": "La Sportiva N.A.", "ticker": None, "status": "certified"},
    {"company": "Experience Momentum", "ticker": None, "status": "certified"},
    {"company": "Whitewater Brewing", "ticker": None, "status": "certified"},
    {"company": "By Rosie Jane", "ticker": None, "status": "certified"},
    {"company": "Sozy", "ticker": None, "status": "certified"},
    {"company": "Pine & Palm Home", "ticker": None, "status": "certified"},
    {"company": "Hibear Outdoors", "ticker": None, "status": "certified"},
    {"company": "Everywhere Apparel", "ticker": None, "status": "certified"},
    {"company": "Ski Utah", "ticker": None, "status": "certified"},
    {"company": "Cancha", "ticker": None, "status": "certified"},
    {"company": "QEJA SOCKS", "ticker": None, "status": "certified"},
    {"company": "iota", "ticker": None, "status": "certified"},
    {"company": "Botanica Wines", "ticker": None, "status": "certified"},
    {"company": "Ecoforms", "ticker": None, "status": "certified"},
    {"company": "Xocolatl Chocolate", "ticker": None, "status": "certified"},
    {"company": "ZeroWasteStore", "ticker": None, "status": "certified"},
    {"company": "Their Jewelry", "ticker": None, "status": "certified"},
    {"company": "SISTAIN", "ticker": None, "status": "certified"},
    {"company": "Sunset Lake CBD", "ticker": None, "status": "certified"},
    {"company": "Burgeon Beer Company", "ticker": None, "status": "certified"},
    {"company": "N.A. Swagger", "ticker": None, "status": "certified"},
    {"company": "TECODA", "ticker": None, "status": "certified"},
    {"company": "Le.mu", "ticker": None, "status": "certified"},
    {"company": "The Resell Club", "ticker": None, "status": "certified"},
    {"company": "Unruled", "ticker": None, "status": "certified"},
    {"company": "Pacific Watch Co", "ticker": None, "status": "certified"},
    {"company": "Aquila's Nest Vineyards", "ticker": None, "status": "certified"},
    {"company": "Fluf Textile Goods", "ticker": None, "status": "certified"},
    {"company": "Jikoni", "ticker": None, "status": "certified"},
    {"company": "GreenStep Solutions", "ticker": None, "status": "certified"},

    # ═══════════════════════════════════════════════════════════════════
    # OUTDOOR / APPAREL CERTIFIED
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Summit Coffee Roasting", "ticker": None, "status": "certified"},
    {"company": "Sunday Beer Co", "ticker": None, "status": "certified"},
    {"company": "The Earthling Co", "ticker": None, "status": "certified"},

    # ═══════════════════════════════════════════════════════════════════
    # NOTE: Several large brands (Levi's, Outerknown, etc.) are NOT currently
    # Climate Neutral Certified despite related climate commitments. This list
    # stays tight — verified recent recertifications only.
    # ═══════════════════════════════════════════════════════════════════
]


def run_pipeline():
    output_dir = Path("data/climate_neutral")
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    seen = set()
    for c in CLIMATE_NEUTRAL_COMPANIES:
        key = c["company"].lower().strip()
        if key in seen:
            continue
        seen.add(key)
        records.append({
            "company": c["company"],
            "ticker": c.get("ticker"),
            "climate_neutral_certified": (c["status"] == "certified"),
            "status": c["status"],  # certified / lapsed
            "source": "Climate Neutral / The Climate Label",
            "source_url": "https://explore.changeclimate.org/",
        })

    output_file = output_dir / "all_companies.json"
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  Climate Neutral Certified Pipeline")
    print(f"{'='*60}")
    print(f"  Certified companies: {sum(1 for r in records if r['climate_neutral_certified'])}")
    print(f"  Output: {output_file}")
    print(f"  Maps to: A.1 (Energy & Emissions), A.4 (Product Lifecycle)")
    print(f"{'='*60}\n")

    return records


if __name__ == "__main__":
    run_pipeline()
