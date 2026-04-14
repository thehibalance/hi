#!/usr/bin/env python3
"""
B Corp — B Lab Certified Benefit Corporations Pipeline
Source: B Lab public directory (bcorporation.net/find-a-b-corp)
URL: https://www.bcorporation.net/en-us/find-a-b-corp/

B Corp Certification is a rigorous third-party standard for social and environmental
performance. Certified companies score 80+ on the B Impact Assessment (median for
uncertified companies: 50.9). Elite certifications: 100+ (top ~20%), 130+ (top ~5%).

3,500+ certified B Corps globally as of 2026. This Stage 1 dataset covers:
  - All Tier A seed companies (Patagonia, Dr. Bronner's, iFixit, etc.)
  - Publicly-traded B Corps in the HI 817 dataset
  - Major privately-held B Corps at scale
  - ~120 total companies

Maps to HUMAN dimensions:
  M.5 (Stakeholder Governance) — B Corp is the defining signal for M.5 (benefit corp legal structure)
  U.3 (Relational Integrity)    — B Impact Workers + Community categories contribute
  A.4 (Product Lifecycle)       — B Impact Environment category contributes

Scoring ladder (B Impact score → M.5 contribution):
  130+ (elite)       → M.5 = 90
  100-129 (strong)   → M.5 = 80
  80-99 (certified)  → M.5 = 70
  Certified, score unknown → M.5 = 65
"""

import json, os
from pathlib import Path

# Curated list of Certified B Corps with public B Impact scores where available.
# Score source: bcorporation.net public company profiles.
# Where score is None, the company is confirmed certified but the public score
# wasn't readily verifiable; pipeline scores these as "certified tier" (65).
BCORP_COMPANIES = [
    # ═══════════════════════════════════════════════════════════════════
    # TIER A SEED COMPANIES (from SEED_AUDIT.md) — highest-priority unlock
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Patagonia", "ticker": None, "bcorp_score": 151.4, "certified_year": 2012},
    {"company": "Dr. Bronner's", "ticker": None, "bcorp_score": 206.7, "certified_year": 2015},
    {"company": "iFixit", "ticker": None, "bcorp_score": None, "certified_year": 2014},  # confirmed via B Lab profile
    {"company": "Equal Exchange", "ticker": None, "bcorp_score": None, "certified_year": 2014},
    {"company": "Fairphone", "ticker": None, "bcorp_score": None, "certified_year": 2015},
    {"company": "King Arthur Baking", "ticker": None, "bcorp_score": 128.6, "certified_year": 2007},
    {"company": "Bob's Red Mill", "ticker": None, "bcorp_score": None, "certified_year": 2020},
    {"company": "Eileen Fisher", "ticker": None, "bcorp_score": 114.3, "certified_year": 2015},
    {"company": "Klean Kanteen", "ticker": None, "bcorp_score": 110.9, "certified_year": 2012},
    {"company": "Cotopaxi", "ticker": None, "bcorp_score": 125.6, "certified_year": 2014},
    {"company": "Newman's Own", "ticker": None, "bcorp_score": None, "certified_year": 2018},
    {"company": "New Belgium Brewing", "ticker": None, "bcorp_score": None, "certified_year": 2013},
    {"company": "Who Gives A Crap", "ticker": None, "bcorp_score": None, "certified_year": 2015},
    {"company": "Dansko", "ticker": None, "bcorp_score": 119.8, "certified_year": 2012},
    {"company": "REI Co-op", "ticker": None, "bcorp_score": None, "certified_year": 2024},
    {"company": "Clif Bar & Company", "ticker": None, "bcorp_score": None, "certified_year": 2014},
    {"company": "Tentree", "ticker": None, "bcorp_score": None, "certified_year": 2015},
    {"company": "Amalgamated Bank", "ticker": "AMAL", "bcorp_score": None, "certified_year": 2021},
    {"company": "Osprey Packs", "ticker": None, "bcorp_score": None, "certified_year": 2023},

    # ═══════════════════════════════════════════════════════════════════
    # PUBLICLY-TRADED B CORPS (likely in HI 817 dataset)
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Warby Parker", "ticker": "WRBY", "bcorp_score": None, "certified_year": 2011},
    {"company": "Allbirds", "ticker": "BIRD", "bcorp_score": None, "certified_year": 2016},
    {"company": "Veeva Systems", "ticker": "VEEV", "bcorp_score": None, "certified_year": 2021},
    {"company": "Lemonade", "ticker": "LMND", "bcorp_score": None, "certified_year": 2016},
    {"company": "Vital Farms", "ticker": "VITL", "bcorp_score": 120.5, "certified_year": 2015},
    {"company": "United Natural Foods", "ticker": "UNFI", "bcorp_score": None, "certified_year": 2023},
    {"company": "Silver Spring Networks", "ticker": "SSNI", "bcorp_score": None, "certified_year": 2016},
    {"company": "Etsy", "ticker": "ETSY", "bcorp_score": 105.0, "certified_year": 2012},  # recertified 2017 before going public
    {"company": "Natura &Co", "ticker": "NTCO", "bcorp_score": None, "certified_year": 2014},
    {"company": "The Body Shop", "ticker": "NTCO", "bcorp_score": None, "certified_year": 2019},
    {"company": "Triodos Bank", "ticker": None, "bcorp_score": None, "certified_year": 2015},
    {"company": "Laureate Education", "ticker": "LAUR", "bcorp_score": None, "certified_year": 2015},
    {"company": "Athleta", "ticker": "GPS", "bcorp_score": None, "certified_year": 2018},  # Athleta is a Gap brand
    {"company": "Ben & Jerry's", "ticker": "UL", "bcorp_score": None, "certified_year": 2012},  # Unilever subsidiary

    # ═══════════════════════════════════════════════════════════════════
    # MAJOR PRIVATELY-HELD B CORPS (large, well-known)
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Kickstarter", "ticker": None, "bcorp_score": None, "certified_year": 2015},
    {"company": "Seventh Generation", "ticker": "UL", "bcorp_score": None, "certified_year": 2007},  # Unilever owned
    {"company": "Method Products", "ticker": None, "bcorp_score": None, "certified_year": 2007},
    {"company": "Cabot Creamery", "ticker": None, "bcorp_score": None, "certified_year": 2012},
    {"company": "Pukka Herbs", "ticker": "UL", "bcorp_score": None, "certified_year": 2017},
    {"company": "Numi Organic Tea", "ticker": None, "bcorp_score": None, "certified_year": 2014},
    {"company": "Plum Organics", "ticker": None, "bcorp_score": None, "certified_year": 2013},
    {"company": "Honest Tea", "ticker": None, "bcorp_score": None, "certified_year": 2011},
    {"company": "Ello Products", "ticker": None, "bcorp_score": None, "certified_year": 2014},
    {"company": "Burton Snowboards", "ticker": None, "bcorp_score": 92.8, "certified_year": 2019},
    {"company": "Prana", "ticker": None, "bcorp_score": None, "certified_year": 2014},  # Columbia Sportswear brand
    {"company": "Indigenous", "ticker": None, "bcorp_score": None, "certified_year": 2013},
    {"company": "Toad&Co", "ticker": None, "bcorp_score": None, "certified_year": 2014},
    {"company": "United By Blue", "ticker": None, "bcorp_score": None, "certified_year": 2016},
    {"company": "Outerknown", "ticker": None, "bcorp_score": None, "certified_year": 2017},
    {"company": "Pact Apparel", "ticker": None, "bcorp_score": None, "certified_year": 2015},
    {"company": "Faction Skis", "ticker": None, "bcorp_score": 93.5, "certified_year": 2022},
    {"company": "Stonyfield Farm", "ticker": None, "bcorp_score": None, "certified_year": 2018},
    {"company": "Organic Valley", "ticker": None, "bcorp_score": None, "certified_year": 2018},
    {"company": "Sir Kensington's", "ticker": None, "bcorp_score": None, "certified_year": 2016},
    {"company": "Revolution Foods", "ticker": None, "bcorp_score": None, "certified_year": 2013},
    {"company": "Nature's Path", "ticker": None, "bcorp_score": None, "certified_year": 2016},
    {"company": "Happy Family Organics", "ticker": None, "bcorp_score": None, "certified_year": 2013},
    {"company": "Annie's Homegrown", "ticker": "GIS", "bcorp_score": None, "certified_year": 2012},  # General Mills subsidiary

    # ═══════════════════════════════════════════════════════════════════
    # FINANCE / B2B / SERVICES B CORPS
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Aspiration", "ticker": None, "bcorp_score": None, "certified_year": 2017},
    {"company": "Kiva", "ticker": None, "bcorp_score": None, "certified_year": 2013},
    {"company": "Beneficial State Bank", "ticker": None, "bcorp_score": None, "certified_year": 2010},
    {"company": "New Resource Bank", "ticker": None, "bcorp_score": None, "certified_year": 2010},
    {"company": "Sunrise Banks", "ticker": None, "bcorp_score": None, "certified_year": 2009},
    {"company": "Spring Bank", "ticker": None, "bcorp_score": None, "certified_year": 2014},
    {"company": "City First Bank", "ticker": None, "bcorp_score": None, "certified_year": 2013},
    {"company": "Cooperative Bank", "ticker": None, "bcorp_score": None, "certified_year": 2013},
    {"company": "Trillium Asset Management", "ticker": None, "bcorp_score": None, "certified_year": 2011},
    {"company": "Calvert Impact Capital", "ticker": None, "bcorp_score": None, "certified_year": 2014},
    {"company": "Community Capital Management", "ticker": None, "bcorp_score": None, "certified_year": 2016},

    # ═══════════════════════════════════════════════════════════════════
    # TECH / MEDIA / SAAS B CORPS
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Ecosia", "ticker": None, "bcorp_score": None, "certified_year": 2014},
    {"company": "DuckDuckGo", "ticker": None, "bcorp_score": None, "certified_year": 2023},
    {"company": "Atlassian", "ticker": "TEAM", "bcorp_score": None, "certified_year": None},  # not B Corp but Pledge 1%
    {"company": "Mozilla Corporation", "ticker": None, "bcorp_score": None, "certified_year": None},
    {"company": "Open Media Foundation", "ticker": None, "bcorp_score": None, "certified_year": 2013},
    {"company": "The Guardian Foundation", "ticker": None, "bcorp_score": None, "certified_year": 2019},
    {"company": "Ceres", "ticker": None, "bcorp_score": None, "certified_year": 2014},
    {"company": "GitLab", "ticker": "GTLB", "bcorp_score": None, "certified_year": None},  # not B Corp but transparent
    {"company": "Buffer", "ticker": None, "bcorp_score": None, "certified_year": None},
    {"company": "Too Good To Go", "ticker": None, "bcorp_score": None, "certified_year": 2021},

    # ═══════════════════════════════════════════════════════════════════
    # LARGE COMMERCE / RETAIL B CORPS
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Hanesbrands", "ticker": "HBI", "bcorp_score": None, "certified_year": None},  # cert lapsed
    {"company": "Danone North America", "ticker": "DANOY", "bcorp_score": None, "certified_year": 2018},
    {"company": "Athletic Brewing Company", "ticker": None, "bcorp_score": None, "certified_year": 2022},
    {"company": "Tom's of Maine", "ticker": "CL", "bcorp_score": None, "certified_year": 2019},  # Colgate-owned
    {"company": "Burt's Bees", "ticker": "CL", "bcorp_score": None, "certified_year": 2007},  # Clorox-owned
    {"company": "California Wine Co", "ticker": None, "bcorp_score": None, "certified_year": 2014},
    {"company": "Endangered Species Chocolate", "ticker": None, "bcorp_score": None, "certified_year": 2009},
    {"company": "Alter Eco", "ticker": None, "bcorp_score": None, "certified_year": 2009},
    {"company": "Theo Chocolate", "ticker": None, "bcorp_score": None, "certified_year": 2013},
    {"company": "Taza Chocolate", "ticker": None, "bcorp_score": None, "certified_year": 2011},
    {"company": "Guayaki Yerba Mate", "ticker": None, "bcorp_score": None, "certified_year": 2012},
    {"company": "Runa", "ticker": None, "bcorp_score": None, "certified_year": 2012},

    # ═══════════════════════════════════════════════════════════════════
    # OUTDOOR / APPAREL B CORPS
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Allbirds", "ticker": "BIRD", "bcorp_score": None, "certified_year": 2016},
    {"company": "Rothy's", "ticker": None, "bcorp_score": None, "certified_year": 2021},
    {"company": "MPOWERD", "ticker": None, "bcorp_score": None, "certified_year": 2013},
    {"company": "Deuter USA", "ticker": None, "bcorp_score": None, "certified_year": 2020},
    {"company": "Smartwool", "ticker": "VFC", "bcorp_score": None, "certified_year": None},  # VF Corp brand
    {"company": "Icebreaker", "ticker": "VFC", "bcorp_score": None, "certified_year": 2019},  # VF Corp brand
    {"company": "Girlfriend Collective", "ticker": None, "bcorp_score": None, "certified_year": 2022},
    {"company": "Vestiaire Collective", "ticker": None, "bcorp_score": None, "certified_year": 2021},
    {"company": "TenTree", "ticker": None, "bcorp_score": None, "certified_year": 2015},  # dup ok

    # ═══════════════════════════════════════════════════════════════════
    # HOUSEHOLD / PERSONAL CARE B CORPS
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Grove Collaborative", "ticker": "GROV", "bcorp_score": None, "certified_year": 2014},
    {"company": "Mrs. Meyer's", "ticker": "SCL", "bcorp_score": None, "certified_year": None},
    {"company": "The Honest Company", "ticker": "HNST", "bcorp_score": None, "certified_year": None},  # cert status varied
    {"company": "Hello Products", "ticker": None, "bcorp_score": None, "certified_year": 2016},
    {"company": "Weleda", "ticker": None, "bcorp_score": None, "certified_year": 2013},
    {"company": "Lush Cosmetics", "ticker": None, "bcorp_score": None, "certified_year": None},
    {"company": "The Soap Box Project", "ticker": None, "bcorp_score": None, "certified_year": 2014},
    {"company": "Aveda", "ticker": "EL", "bcorp_score": None, "certified_year": None},  # Estee Lauder

    # ═══════════════════════════════════════════════════════════════════
    # FOOD / BEVERAGE B CORPS
    # ═══════════════════════════════════════════════════════════════════
    {"company": "Grain4Grain", "ticker": None, "bcorp_score": None, "certified_year": 2018},
    {"company": "Applegate Farms", "ticker": "HRL", "bcorp_score": None, "certified_year": None},  # Hormel
    {"company": "Happy Baby Organics", "ticker": "DANOY", "bcorp_score": None, "certified_year": 2013},
    {"company": "Earthbound Farm", "ticker": "GIS", "bcorp_score": None, "certified_year": 2016},
    {"company": "Late July Snacks", "ticker": None, "bcorp_score": None, "certified_year": 2014},
    {"company": "Kin Euphorics", "ticker": None, "bcorp_score": None, "certified_year": 2021},
    {"company": "Ripple Foods", "ticker": None, "bcorp_score": None, "certified_year": 2019},
    {"company": "Happy Egg Co", "ticker": None, "bcorp_score": None, "certified_year": 2018},
    {"company": "JOOB Active", "ticker": None, "bcorp_score": None, "certified_year": 2019},
]


def run_pipeline():
    output_dir = Path("data/bcorp")
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    seen_companies = set()  # dedup
    for c in BCORP_COMPANIES:
        # Only count as certified if certified_year is set
        if c.get("certified_year") is None:
            continue

        key = c["company"].lower().strip()
        if key in seen_companies:
            continue
        seen_companies.add(key)

        bcorp_score = c.get("bcorp_score")
        tier = _bcorp_tier(bcorp_score)

        records.append({
            "company": c["company"],
            "ticker": c.get("ticker"),
            "bcorp_certified": True,
            "bcorp_score": bcorp_score,  # None if not publicly known
            "bcorp_tier": tier,  # elite / strong / certified / certified_unscored
            "certified_year": c.get("certified_year"),
            "source": "B Lab Certified B Corporation",
            "source_url": f"https://www.bcorporation.net/en-us/find-a-b-corp/company/{_slug(c['company'])}",
        })

    output_file = output_dir / "all_companies.json"
    with open(output_file, "w") as f:
        json.dump(records, f, indent=2)

    tier_counts = {}
    for r in records:
        tier_counts[r["bcorp_tier"]] = tier_counts.get(r["bcorp_tier"], 0) + 1

    print(f"\n{'='*60}")
    print(f"  B Corp Certified B Corporations Pipeline")
    print(f"{'='*60}")
    print(f"  Certified companies: {len(records)}")
    for tier, count in sorted(tier_counts.items()):
        print(f"    {tier}: {count}")
    print(f"  Output: {output_file}")
    print(f"  Maps to: M.5 (Stakeholder Governance), U.3 (Relational Integrity), A.4 (Product Lifecycle)")
    print(f"{'='*60}\n")

    return records


def _bcorp_tier(score):
    """Map B Impact score to qualitative tier matching sub-signal ladder."""
    if score is None:
        return "certified_unscored"
    if score >= 130:
        return "elite"
    if score >= 100:
        return "strong"
    if score >= 80:
        return "certified"
    return "certified"  # shouldn't be below 80 if certified, but be lenient


def _slug(company_name):
    """Crude slug for building B Lab profile URLs for audit trail."""
    return (company_name.lower()
            .replace("&", "and")
            .replace("'", "")
            .replace(".", "")
            .replace(",", "")
            .replace(" ", "-"))


if __name__ == "__main__":
    run_pipeline()
