#!/usr/bin/env python3
"""
1% for the Planet — Certified Members Pipeline
Source: 1% for the Planet public business directory
URL: https://directories.onepercentfortheplanet.org/

1% for the Planet is an international certification founded in 2002 by Yvon
Chouinard (Patagonia) and Craig Mathews (Blue Ribbon Flies). Members pledge
at least 1% of annual revenue to environmental nonprofits — certified and
verified annually. $728M+ donated cumulatively.

Unlike typical "donation" programs, the commitment is:
  - Revenue-based (not profit-based) — so a company pays even at a loss
  - Third-party verified annually with proof of revenue + giving receipts
  - Must go to approved environmental nonprofits in the 1% network

This is a strong signal for environmental commitment PLUS stakeholder
governance — a company that contractually obligates itself to give 1% of
revenue is structurally aligned with non-shareholder stakeholders.

Maps to HUMAN dimensions:
  A.1 (Energy & Emissions) — structural environmental commitment
  M.5 (Stakeholder Governance) — revenue-bound pledge = structural stakeholder alignment

Scoring ladder:
  full_company   → 80  (entire company is member, all revenue subject to 1%)
  brand_level    → 70  (specific brand within parent company)
  product_line   → 60  (single product line — minimum commitment)
"""

import json, os
from pathlib import Path

# Curated list of 1% for the Planet members as of 2026.
# Source: onepercentfortheplanet.org/directories + official member announcements
ONE_PERCENT_COMPANIES = [
    # ═══════════════════════════════════════════════════════════════════
    # TIER A SEED COMPANIES
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Patagonia", "ticker": None, "tier": "full_company"},  # founder, since 1985
    {"company": "Klean Kanteen", "ticker": None, "tier": "full_company"},
    {"company": "Cotopaxi", "ticker": None, "tier": "full_company"},
    {"company": "Newman's Own", "ticker": None, "tier": "full_company"},
    {"company": "New Belgium Brewing", "ticker": None, "tier": "full_company"},
    {"company": "REI Co-op", "ticker": None, "tier": "full_company"},

    # ═══════════════════════════════════════════════════════════════════
    # FOUNDERS + NOTABLE FULL-COMPANY MEMBERS
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Blue Ribbon Flies", "ticker": None, "tier": "full_company"},  # co-founder
    {"company": "Maine Beer Company", "ticker": None, "tier": "full_company"},
    {"company": "Avocado Green Brands", "ticker": None, "tier": "full_company"},
    {"company": "Caudalie", "ticker": None, "tier": "full_company"},
    {"company": "OXO", "ticker": None, "tier": "brand_level"},  # Helen of Troy owned
    {"company": "KeepCup", "ticker": None, "tier": "full_company"},
    {"company": "Spindrift Beverage", "ticker": None, "tier": "full_company"},
    {"company": "Stasher", "ticker": None, "tier": "full_company"},
    {"company": "Alima Pure", "ticker": None, "tier": "full_company"},
    {"company": "Three Twins Ice Cream", "ticker": None, "tier": "full_company"},
    {"company": "Boxed Water", "ticker": None, "tier": "full_company"},
    {"company": "Flickr", "ticker": None, "tier": "full_company"},
    {"company": "The Sunglass Fix", "ticker": None, "tier": "full_company"},

    # ═══════════════════════════════════════════════════════════════════
    # FOOD & BEVERAGE MEMBERS
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Honest Tea", "ticker": "KO", "tier": "product_line"},  # glass product line
    {"company": "Guayaki Yerba Mate", "ticker": None, "tier": "full_company"},
    {"company": "Numi Organic Tea", "ticker": None, "tier": "full_company"},
    {"company": "Runa", "ticker": None, "tier": "full_company"},
    {"company": "Alter Eco", "ticker": None, "tier": "full_company"},
    {"company": "Theo Chocolate", "ticker": None, "tier": "full_company"},
    {"company": "Endangered Species Chocolate", "ticker": None, "tier": "full_company"},
    {"company": "Siete Foods", "ticker": None, "tier": "full_company"},
    {"company": "Patagonia Provisions", "ticker": None, "tier": "full_company"},  # Patagonia's food subsidiary
    {"company": "MALK Organics", "ticker": None, "tier": "full_company"},
    {"company": "Late July Snacks", "ticker": None, "tier": "full_company"},

    # ═══════════════════════════════════════════════════════════════════
    # APPAREL & OUTDOOR GEAR
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Tentree", "ticker": None, "tier": "full_company"},
    {"company": "prAna", "ticker": None, "tier": "full_company"},
    {"company": "United By Blue", "ticker": None, "tier": "full_company"},
    {"company": "Osprey Packs", "ticker": None, "tier": "full_company"},
    {"company": "MiiR", "ticker": None, "tier": "full_company"},
    {"company": "Looptworks", "ticker": None, "tier": "full_company"},
    {"company": "Tasc Performance", "ticker": None, "tier": "full_company"},
    {"company": "Faction Skis", "ticker": None, "tier": "full_company"},
    {"company": "The North Face", "ticker": "VFC", "tier": "product_line"},  # specific lines
    {"company": "Columbia Sportswear", "ticker": "COLM", "tier": "product_line"},

    # ═══════════════════════════════════════════════════════════════════
    # BEAUTY & PERSONAL CARE
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Lush Cosmetics", "ticker": None, "tier": "full_company"},
    {"company": "Weleda", "ticker": None, "tier": "product_line"},
    {"company": "Schmidt's Naturals", "ticker": "UL", "tier": "brand_level"},  # Unilever-owned
    {"company": "Badger Balm", "ticker": None, "tier": "full_company"},
    {"company": "Ethique", "ticker": None, "tier": "full_company"},

    # ═══════════════════════════════════════════════════════════════════
    # BRAND-LEVEL (owned by larger parents)
    # ═══════════════════════════════════════════════════════════════════
    {"company": "TAZO Tea", "ticker": None, "tier": "brand_level"},  # Ekaterra/Unilever
    {"company": "Finlandia Vodka US", "ticker": None, "tier": "brand_level"},
    {"company": "Burton Snowboards", "ticker": None, "tier": "full_company"},

    # ═══════════════════════════════════════════════════════════════════
    # SERVICES / OTHER
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Sendle", "ticker": None, "tier": "full_company"},
    {"company": "Backdrop", "ticker": None, "tier": "full_company"},
    {"company": "Bookshop.org", "ticker": None, "tier": "full_company"},
    {"company": "Ecosia", "ticker": None, "tier": "full_company"},
    {"company": "Allbirds", "ticker": "BIRD", "tier": "full_company"},
]


def run_pipeline():
    output_dir = Path("data/one_percent")
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    seen = set()
    for c in ONE_PERCENT_COMPANIES:
        key = c["company"].lower().strip()
        if key in seen:
            continue
        seen.add(key)
        records.append({
            "company": c["company"],
            "ticker": c.get("ticker"),
            "one_percent_member": True,
            "tier": c["tier"],  # full_company / brand_level / product_line
            "source": "1% for the Planet",
            "source_url": "https://directories.onepercentfortheplanet.org/",
        })

    output_file = output_dir / "all_companies.json"
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)

    tier_counts = {}
    for r in records:
        tier_counts[r["tier"]] = tier_counts.get(r["tier"], 0) + 1

    print(f"\n{'='*60}")
    print(f"  1% for the Planet Members Pipeline")
    print(f"{'='*60}")
    print(f"  Total members: {len(records)}")
    for tier, count in sorted(tier_counts.items()):
        print(f"    {tier}: {count}")
    print(f"  Output: {output_file}")
    print(f"  Maps to: A.1 (Energy & Emissions), M.5 (Stakeholder Governance)")
    print(f"{'='*60}\n")

    return records


if __name__ == "__main__":
    run_pipeline()
