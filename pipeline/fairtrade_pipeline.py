#!/usr/bin/env python3
"""
Fair Trade — Fair Trade USA / Fairtrade International Certified Companies Pipeline
Source: Fair Trade USA public partner directory + Fairtrade International directory
URLs:
  https://partner.fairtradecertified.org/directory/results
  https://www.fairtrade.net/en/fairtrade-finder.html
  https://www.fairtradecertified.org/our-community/shop-fair-trade/

Fair Trade Certified is a rigorous sustainable-sourcing standard: ensures safe
working conditions, elimination of forced/child labor, fair compensation,
environmental protections, and product traceability. 1,500+ partner companies.

Fair Trade certification is specifically about SUPPLY CHAIN INTEGRITY —
the strongest signal available for M.3 (Market Ethics: fair practices with
suppliers/customers) and a contributing signal for A.4 (Product Lifecycle).

Maps to HUMAN dimensions:
  M.3 (Market Ethics)        — fair compensation + traceability = the definitional M.3 signal
  A.4 (Product Lifecycle)    — environmental protections + traceability contribute

Scoring ladder (tier → sub-signal contribution):
  Full Fair Trade Certified company (100% of applicable products)    → 85
  Partial Fair Trade (specific product lines certified)              → 70
  Licensed/partner (documented Fair Trade sourcing program)          → 65
"""

import json, os
from pathlib import Path

# Curated list of Fair Trade USA partners and Fairtrade International licensees.
# Tier definitions:
#   "full"      — entire company is Fair Trade Certified (or 100% Fair Trade product line)
#   "partial"   — specific lines certified (e.g. Ben & Jerry's uses Fair Trade ingredients)
#   "licensed"  — formal licensee with documented sourcing program
FAIRTRADE_COMPANIES = [
    # ═══════════════════════════════════════════════════════════════════
    # TIER A SEED COMPANIES (from SEED_AUDIT.md)
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Dr. Bronner's", "ticker": None, "tier": "full", "products": "soaps, oils, coconut"},
    {"company": "Equal Exchange", "ticker": None, "tier": "full", "products": "coffee, tea, chocolate, cocoa, olive oil"},
    {"company": "Patagonia", "ticker": None, "tier": "partial", "products": "apparel (Fair Trade Certified sewn)"},
    {"company": "Ben & Jerry's", "ticker": "UL", "tier": "partial", "products": "ice cream ingredients"},
    {"company": "Newman's Own", "ticker": None, "tier": "partial", "products": "cookies, chocolate, coffee"},
    {"company": "King Arthur Baking", "ticker": None, "tier": "partial", "products": "baking ingredients"},
    {"company": "Clif Bar & Company", "ticker": None, "tier": "partial", "products": "organic bars"},
    {"company": "Pact Apparel", "ticker": None, "tier": "full", "products": "apparel (Fair Trade Certified factory)"},
    {"company": "Tentree", "ticker": None, "tier": "partial", "products": "apparel (Fair Trade factory)"},
    {"company": "Eileen Fisher", "ticker": None, "tier": "partial", "products": "organic cotton apparel"},
    {"company": "REI Co-op", "ticker": None, "tier": "partial", "products": "co-op brand apparel"},

    # ═══════════════════════════════════════════════════════════════════
    # FOOD & BEVERAGE — COFFEE, TEA, CHOCOLATE (the core Fair Trade categories)
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Green Mountain Coffee", "ticker": "KDP", "tier": "partial", "products": "coffee"},
    {"company": "Keurig Dr Pepper", "ticker": "KDP", "tier": "partial", "products": "coffee"},
    {"company": "Allegro Coffee Company", "ticker": "AMZN", "tier": "partial", "products": "coffee (Whole Foods subsidiary)"},
    {"company": "Counter Culture Coffee", "ticker": None, "tier": "partial", "products": "coffee"},
    {"company": "Stumptown Coffee", "ticker": None, "tier": "partial", "products": "coffee"},
    {"company": "Peet's Coffee", "ticker": None, "tier": "partial", "products": "coffee"},
    {"company": "Caribou Coffee", "ticker": None, "tier": "partial", "products": "coffee"},
    {"company": "Starbucks Corporation", "ticker": "SBUX", "tier": "partial", "products": "coffee (C.A.F.E. Practices + Fair Trade)"},
    {"company": "Lavazza", "ticker": None, "tier": "partial", "products": "coffee"},
    {"company": "BLK & Bold", "ticker": None, "tier": "full", "products": "coffee"},
    {"company": "Numi Organic Tea", "ticker": None, "tier": "full", "products": "tea"},
    {"company": "Traditional Medicinals", "ticker": None, "tier": "partial", "products": "herbal tea"},
    {"company": "Honest Tea", "ticker": "KO", "tier": "partial", "products": "tea (Coca-Cola owned, discontinued 2022)"},
    {"company": "Tazo Tea", "ticker": None, "tier": "partial", "products": "tea"},
    {"company": "Rishi Tea", "ticker": None, "tier": "partial", "products": "tea"},
    {"company": "Alter Eco", "ticker": None, "tier": "full", "products": "chocolate, rice, sugar, quinoa"},
    {"company": "Endangered Species Chocolate", "ticker": None, "tier": "partial", "products": "chocolate"},
    {"company": "Theo Chocolate", "ticker": None, "tier": "full", "products": "chocolate"},
    {"company": "Taza Chocolate", "ticker": None, "tier": "full", "products": "chocolate"},
    {"company": "Divine Chocolate", "ticker": None, "tier": "full", "products": "chocolate"},
    {"company": "Sweetriot", "ticker": None, "tier": "full", "products": "chocolate"},
    {"company": "Unreal Chocolate", "ticker": None, "tier": "partial", "products": "chocolate"},
    {"company": "Guayaki Yerba Mate", "ticker": None, "tier": "full", "products": "yerba mate"},
    {"company": "Runa", "ticker": None, "tier": "full", "products": "tea (guayusa)"},

    # ═══════════════════════════════════════════════════════════════════
    # FOOD & BEVERAGE — BANANAS, SUGAR, PRODUCE
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Dole Food Company", "ticker": "DOLE", "tier": "partial", "products": "bananas, pineapples"},
    {"company": "Chiquita Brands", "ticker": None, "tier": "partial", "products": "bananas"},
    {"company": "Wholesome Sweeteners", "ticker": None, "tier": "full", "products": "sugar, sweeteners"},
    {"company": "NatureSweet", "ticker": None, "tier": "full", "products": "tomatoes"},
    {"company": "Driscoll's", "ticker": None, "tier": "partial", "products": "berries"},
    {"company": "Zespri", "ticker": None, "tier": "partial", "products": "kiwifruit"},
    {"company": "Florida Crystals", "ticker": None, "tier": "partial", "products": "sugar"},

    # ═══════════════════════════════════════════════════════════════════
    # APPAREL — FAIR TRADE CERTIFIED FACTORIES
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Madewell", "ticker": None, "tier": "partial", "products": "denim"},
    {"company": "Prana", "ticker": None, "tier": "partial", "products": "apparel"},
    {"company": "Athleta", "ticker": "GPS", "tier": "partial", "products": "apparel"},
    {"company": "Outerknown", "ticker": None, "tier": "full", "products": "apparel"},
    {"company": "Indigenous", "ticker": None, "tier": "full", "products": "apparel"},
    {"company": "Everlane", "ticker": None, "tier": "partial", "products": "apparel (Fair Trade factory)"},
    {"company": "Kowtow", "ticker": None, "tier": "full", "products": "apparel"},
    {"company": "Fair Indigo", "ticker": None, "tier": "full", "products": "apparel"},
    {"company": "People Tree", "ticker": None, "tier": "full", "products": "apparel"},
    {"company": "Liz Alig", "ticker": None, "tier": "full", "products": "apparel"},
    {"company": "Coyuchi", "ticker": None, "tier": "full", "products": "home textiles"},
    {"company": "Boll & Branch", "ticker": None, "tier": "full", "products": "bedding"},
    {"company": "West Elm", "ticker": "WSM", "tier": "partial", "products": "home goods (Williams-Sonoma brand)"},

    # ═══════════════════════════════════════════════════════════════════
    # HEALTH & BEAUTY
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Eco Lips", "ticker": None, "tier": "full", "products": "lip balm"},
    {"company": "Badger Balm", "ticker": None, "tier": "full", "products": "personal care"},
    {"company": "Alaffia", "ticker": None, "tier": "full", "products": "personal care (shea butter)"},
    {"company": "Weleda", "ticker": None, "tier": "partial", "products": "cosmetics, personal care"},
    {"company": "Dr. Hauschka", "ticker": None, "tier": "partial", "products": "cosmetics"},
    {"company": "Aveda", "ticker": "EL", "tier": "partial", "products": "hair care"},

    # ═══════════════════════════════════════════════════════════════════
    # FOOD — ICE CREAM, DAIRY, FROZEN
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Haagen-Dazs", "ticker": "GIS", "tier": "partial", "products": "ice cream (vanilla line)"},
    {"company": "Stonyfield Farm", "ticker": None, "tier": "partial", "products": "yogurt"},
    {"company": "Happy Family Organics", "ticker": None, "tier": "partial", "products": "baby food"},
    {"company": "Plum Organics", "ticker": None, "tier": "partial", "products": "baby food"},

    # ═══════════════════════════════════════════════════════════════════
    # LARGE CPG / RETAIL WITH FAIR TRADE LINES
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Whole Foods Market", "ticker": "AMZN", "tier": "partial", "products": "365 Everyday Value line"},
    {"company": "Sam's Club", "ticker": "WMT", "tier": "partial", "products": "private label coffee"},
    {"company": "Costco Wholesale Corporation", "ticker": "COST", "tier": "partial", "products": "Kirkland Signature coffee"},
    {"company": "Trader Joe's", "ticker": None, "tier": "partial", "products": "coffee, chocolate, bananas"},
    {"company": "Target Corporation", "ticker": "TGT", "tier": "partial", "products": "Archer Farms line"},
    {"company": "Kroger", "ticker": "KR", "tier": "partial", "products": "Simple Truth line"},
    {"company": "Ahold Delhaize", "ticker": None, "tier": "partial", "products": "private label"},
    {"company": "Target", "ticker": "TGT", "tier": "partial", "products": "Threshold home line"},

    # ═══════════════════════════════════════════════════════════════════
    # GLOBAL FAIRTRADE INTERNATIONAL LICENSEES (non-US Fair Trade)
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Cadbury", "ticker": None, "tier": "partial", "products": "chocolate (Mondelez brand)"},
    {"company": "Mondelez International", "ticker": "MDLZ", "tier": "partial", "products": "chocolate via Cadbury"},
    {"company": "Nestle", "ticker": "NSRGY", "tier": "partial", "products": "KitKat (4-finger, UK/IE)"},
    {"company": "Sainsbury's", "ticker": None, "tier": "partial", "products": "private label (UK)"},
    {"company": "Tesco", "ticker": None, "tier": "partial", "products": "private label (UK)"},
    {"company": "Marks & Spencer", "ticker": None, "tier": "partial", "products": "private label (UK)"},
    {"company": "The Body Shop", "ticker": "NTCO", "tier": "partial", "products": "personal care"},
    {"company": "Lush Cosmetics", "ticker": None, "tier": "partial", "products": "personal care"},
    {"company": "Pukka Herbs", "ticker": "UL", "tier": "full", "products": "tea (Unilever owned)"},
]


def run_pipeline():
    output_dir = Path("data/fairtrade")
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    seen = set()
    for c in FAIRTRADE_COMPANIES:
        key = c["company"].lower().strip()
        if key in seen:
            continue
        seen.add(key)
        records.append({
            "company": c["company"],
            "ticker": c.get("ticker"),
            "fairtrade_certified": True,
            "fairtrade_tier": c["tier"],  # full / partial / licensed
            "products": c.get("products", ""),
            "source": "Fair Trade USA / Fairtrade International",
            "source_url": "https://www.fairtradecertified.org/our-community/shop-fair-trade/",
        })

    output_file = output_dir / "all_companies.json"
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)

    tier_counts = {}
    for r in records:
        tier_counts[r["fairtrade_tier"]] = tier_counts.get(r["fairtrade_tier"], 0) + 1

    print(f"\n{'='*60}")
    print(f"  Fair Trade Certified Companies Pipeline")
    print(f"{'='*60}")
    print(f"  Certified companies: {len(records)}")
    for tier, count in sorted(tier_counts.items()):
        print(f"    {tier}: {count}")
    print(f"  Output: {output_file}")
    print(f"  Maps to: M.3 (Market Ethics), A.4 (Product Lifecycle)")
    print(f"{'='*60}\n")

    return records


if __name__ == "__main__":
    run_pipeline()
