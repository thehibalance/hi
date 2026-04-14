#!/usr/bin/env python3
"""
USDA Organic — Certified Organic Operations Pipeline
Source: USDA Organic Integrity Database (public, federally administered)
URL: https://organic.ams.usda.gov/integrity/

USDA Organic is the federal certification standard for organic food, fiber,
and livestock operations. Certified operations must meet requirements on:
  - Soil fertility & crop rotation
  - No prohibited synthetic substances (3-year transition required)
  - Livestock raised on organic feed with outdoor access
  - No genetic engineering, sewage sludge, or ionizing radiation
  - Full traceability from farm to finished product

Hundreds of thousands of operations in the database. This Stage 1 dataset
covers ~80 of the best-known certified organic brands + Tier A seeds.

Tiers used:
  "100_percent"  — 100% of products certified organic ("USDA Organic" label)
  "made_with"    — "Made with Organic" (70-94% organic, less strict use of seal)
  "ingredients"  — Specific ingredients organic but not company-wide

Maps to HUMAN dimensions:
  A.3 (Land & Habitat)       — organic farming = documented soil health + habitat preservation
  A.4 (Product Lifecycle)    — organic = no synthetic inputs = better lifecycle footprint
  M.3 (Market Ethics)        — federal third-party verification is a supply-chain integrity signal

Scoring ladder:
  100_percent    → 85
  made_with      → 70
  ingredients    → 60
"""

import json, os
from pathlib import Path

USDA_ORGANIC_COMPANIES = [
    # ═══════════════════════════════════════════════════════════════════
    # TIER A SEED COMPANIES
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Dr. Bronner's", "ticker": None, "tier": "100_percent", "category": "personal care"},
    {"company": "Equal Exchange", "ticker": None, "tier": "100_percent", "category": "coffee/tea/chocolate"},
    {"company": "King Arthur Baking", "ticker": None, "tier": "ingredients", "category": "baking"},
    {"company": "Bob's Red Mill", "ticker": None, "tier": "ingredients", "category": "grains"},
    {"company": "Clif Bar & Company", "ticker": None, "tier": "ingredients", "category": "bars"},
    {"company": "Newman's Own", "ticker": None, "tier": "ingredients", "category": "food"},
    {"company": "Patagonia", "ticker": None, "tier": "ingredients", "category": "food/Patagonia Provisions"},

    # ═══════════════════════════════════════════════════════════════════
    # MAJOR ORGANIC BRANDS — FOOD & BEVERAGE
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Stonyfield Farm", "ticker": None, "tier": "100_percent", "category": "yogurt/dairy"},
    {"company": "Organic Valley", "ticker": None, "tier": "100_percent", "category": "dairy/eggs"},
    {"company": "Applegate Farms", "ticker": "HRL", "tier": "100_percent", "category": "meats (Hormel owned)"},
    {"company": "Happy Family Organics", "ticker": "DANOY", "tier": "100_percent", "category": "baby food"},
    {"company": "Plum Organics", "ticker": None, "tier": "100_percent", "category": "baby food"},
    {"company": "Earth's Best", "ticker": None, "tier": "100_percent", "category": "baby food"},
    {"company": "Annie's Homegrown", "ticker": "GIS", "tier": "100_percent", "category": "pasta/snacks (General Mills)"},
    {"company": "Cascadian Farm", "ticker": "GIS", "tier": "100_percent", "category": "cereal (General Mills)"},
    {"company": "Amy's Kitchen", "ticker": None, "tier": "100_percent", "category": "frozen/prepared"},
    {"company": "Nature's Path", "ticker": None, "tier": "100_percent", "category": "cereal"},
    {"company": "Lundberg Family Farms", "ticker": None, "tier": "100_percent", "category": "rice"},
    {"company": "Eden Foods", "ticker": None, "tier": "100_percent", "category": "pantry"},
    {"company": "Woodstock Farms", "ticker": None, "tier": "100_percent", "category": "pantry"},
    {"company": "Kashi", "ticker": "K", "tier": "made_with", "category": "cereal/snacks (Kellogg's)"},
    {"company": "Horizon Organic", "ticker": "DANOY", "tier": "100_percent", "category": "dairy (Danone)"},
    {"company": "Silk", "ticker": "DANOY", "tier": "made_with", "category": "plant milk (Danone)"},
    {"company": "So Delicious Dairy Free", "ticker": "DANOY", "tier": "100_percent", "category": "plant-based"},
    {"company": "Earthbound Farm", "ticker": "GIS", "tier": "100_percent", "category": "produce (General Mills)"},
    {"company": "Ripple Foods", "ticker": None, "tier": "made_with", "category": "plant milk"},
    {"company": "Alter Eco", "ticker": None, "tier": "100_percent", "category": "chocolate/rice"},
    {"company": "Theo Chocolate", "ticker": None, "tier": "100_percent", "category": "chocolate"},
    {"company": "Endangered Species Chocolate", "ticker": None, "tier": "100_percent", "category": "chocolate"},
    {"company": "Numi Organic Tea", "ticker": None, "tier": "100_percent", "category": "tea"},
    {"company": "Traditional Medicinals", "ticker": None, "tier": "100_percent", "category": "tea"},
    {"company": "Yogi Tea", "ticker": None, "tier": "100_percent", "category": "tea"},
    {"company": "Celestial Seasonings", "ticker": "HAIN", "tier": "ingredients", "category": "tea (Hain Celestial)"},
    {"company": "Peet's Coffee", "ticker": None, "tier": "ingredients", "category": "coffee"},
    {"company": "Counter Culture Coffee", "ticker": None, "tier": "ingredients", "category": "coffee"},
    {"company": "Sambazon", "ticker": None, "tier": "100_percent", "category": "acai"},
    {"company": "GT's Living Foods", "ticker": None, "tier": "100_percent", "category": "kombucha"},
    {"company": "Suja Juice", "ticker": None, "tier": "100_percent", "category": "juice"},
    {"company": "Late July Snacks", "ticker": None, "tier": "100_percent", "category": "snacks"},
    {"company": "Hain Celestial Group", "ticker": "HAIN", "tier": "ingredients", "category": "multiple brands"},
    {"company": "Vital Farms", "ticker": "VITL", "tier": "ingredients", "category": "pasture-raised eggs"},

    # ═══════════════════════════════════════════════════════════════════
    # PERSONAL CARE / PRODUCTS
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Tom's of Maine", "ticker": "CL", "tier": "ingredients", "category": "personal care (Colgate)"},
    {"company": "Burt's Bees", "ticker": "CLX", "tier": "ingredients", "category": "personal care (Clorox)"},
    {"company": "Weleda", "ticker": None, "tier": "100_percent", "category": "personal care"},
    {"company": "Dr. Hauschka", "ticker": None, "tier": "ingredients", "category": "cosmetics"},
    {"company": "Alaffia", "ticker": None, "tier": "100_percent", "category": "personal care"},
    {"company": "Badger Balm", "ticker": None, "tier": "100_percent", "category": "personal care"},
    {"company": "EO Products", "ticker": None, "tier": "100_percent", "category": "personal care"},

    # ═══════════════════════════════════════════════════════════════════
    # MEAT / DAIRY / EGG
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Niman Ranch", "ticker": None, "tier": "ingredients", "category": "meat"},
    {"company": "Organic Prairie", "ticker": None, "tier": "100_percent", "category": "meat"},
    {"company": "Pete and Gerry's Organic Eggs", "ticker": None, "tier": "100_percent", "category": "eggs"},
    {"company": "Happy Egg Co", "ticker": None, "tier": "100_percent", "category": "eggs"},
    {"company": "Vital Farms Organic", "ticker": "VITL", "tier": "ingredients", "category": "eggs"},
    {"company": "Wholesome Pantry", "ticker": None, "tier": "100_percent", "category": "pantry"},

    # ═══════════════════════════════════════════════════════════════════
    # SUPERMARKET / RETAIL PRIVATE LABELS (USDA Organic certified lines)
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Whole Foods Market", "ticker": "AMZN", "tier": "ingredients", "category": "365 Organic line"},
    {"company": "Trader Joe's", "ticker": None, "tier": "ingredients", "category": "Trader Joe's Organic line"},
    {"company": "Costco Wholesale Corporation", "ticker": "COST", "tier": "ingredients", "category": "Kirkland Organic"},
    {"company": "Target Corporation", "ticker": "TGT", "tier": "ingredients", "category": "Good & Gather Organic"},
    {"company": "Kroger", "ticker": "KR", "tier": "ingredients", "category": "Simple Truth Organic"},
    {"company": "Walmart Inc.", "ticker": "WMT", "tier": "ingredients", "category": "Great Value Organic"},
    {"company": "Sprouts Farmers Market", "ticker": "SFM", "tier": "ingredients", "category": "Sprouts brand"},
    {"company": "Natural Grocers", "ticker": "NGVC", "tier": "ingredients", "category": "store brand"},

    # ═══════════════════════════════════════════════════════════════════
    # PUBLICLY TRADED ORGANIC-FOCUSED
    # ═══════════════════════════════════════════════════════════════════
    {"company": "United Natural Foods", "ticker": "UNFI", "tier": "ingredients", "category": "distributor"},
    {"company": "Sprouts Farmers Market Inc", "ticker": "SFM", "tier": "ingredients", "category": "retail"},
    {"company": "SunOpta", "ticker": "STKL", "tier": "100_percent", "category": "plant-based ingredients"},
    {"company": "Calavo Growers", "ticker": "CVGW", "tier": "ingredients", "category": "avocados"},
    {"company": "Laird Superfood", "ticker": "LSF", "tier": "ingredients", "category": "superfoods"},

    # ═══════════════════════════════════════════════════════════════════
    # BABY / CHILD / FAMILY
    # ═══════════════════════════════════════════════════════════════════
    {"company": "The Honest Company", "ticker": "HNST", "tier": "ingredients", "category": "baby/household"},
    {"company": "Made Of", "ticker": None, "tier": "100_percent", "category": "baby products"},
    {"company": "Earth Mama Organics", "ticker": None, "tier": "100_percent", "category": "maternity/baby"},

    # ═══════════════════════════════════════════════════════════════════
    # FIBER / TEXTILES (Global Organic Textile Standard — GOTS — often overlaps)
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Pact Apparel", "ticker": None, "tier": "100_percent", "category": "organic cotton apparel"},
    {"company": "Eileen Fisher", "ticker": None, "tier": "ingredients", "category": "organic cotton"},
    {"company": "Coyuchi", "ticker": None, "tier": "100_percent", "category": "organic cotton bedding"},
    {"company": "Boll & Branch", "ticker": None, "tier": "100_percent", "category": "organic cotton bedding"},
    {"company": "Naturepedic", "ticker": None, "tier": "100_percent", "category": "organic mattresses"},
    {"company": "Under the Canopy", "ticker": None, "tier": "100_percent", "category": "organic cotton home"},
    {"company": "Kowtow", "ticker": None, "tier": "100_percent", "category": "organic apparel"},

    # ═══════════════════════════════════════════════════════════════════
    # COFFEE / TEA / CHOCOLATE DEDICATED
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Allegro Coffee Company", "ticker": "AMZN", "tier": "ingredients", "category": "coffee"},
    {"company": "Stumptown Coffee", "ticker": None, "tier": "ingredients", "category": "coffee"},
    {"company": "Rishi Tea", "ticker": None, "tier": "100_percent", "category": "tea"},
    {"company": "Taza Chocolate", "ticker": None, "tier": "ingredients", "category": "chocolate"},
    {"company": "Divine Chocolate", "ticker": None, "tier": "ingredients", "category": "chocolate"},
    {"company": "Guayaki Yerba Mate", "ticker": None, "tier": "100_percent", "category": "yerba mate"},
]


def run_pipeline():
    output_dir = Path("data/usda_organic")
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    seen = set()
    for c in USDA_ORGANIC_COMPANIES:
        key = c["company"].lower().strip()
        if key in seen:
            continue
        seen.add(key)
        records.append({
            "company": c["company"],
            "ticker": c.get("ticker"),
            "usda_organic_certified": True,
            "usda_organic_tier": c["tier"],
            "category": c.get("category", ""),
            "source": "USDA Organic Integrity Database",
            "source_url": "https://organic.ams.usda.gov/integrity/",
        })

    output_file = output_dir / "all_companies.json"
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)

    tier_counts = {}
    for r in records:
        tier_counts[r["usda_organic_tier"]] = tier_counts.get(r["usda_organic_tier"], 0) + 1

    print(f"\n{'='*60}")
    print(f"  USDA Organic Certified Pipeline")
    print(f"{'='*60}")
    print(f"  Certified companies: {len(records)}")
    for tier, count in sorted(tier_counts.items()):
        print(f"    {tier}: {count}")
    print(f"  Output: {output_file}")
    print(f"  Maps to: A.3 (Land & Habitat), A.4 (Product Lifecycle), M.3 (Market Ethics)")
    print(f"{'='*60}\n")

    return records


if __name__ == "__main__":
    run_pipeline()
