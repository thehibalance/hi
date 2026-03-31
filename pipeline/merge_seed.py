#!/usr/bin/env python3
"""
HI. Seed Merger — Merges hand-scored private companies with API-sourced scores.

Runs automatically as part of run_all.py after scoring engine.
- Public companies: scored fresh from 34 APIs (daily)
- Private companies: from seed-data.js (refreshed quarterly)

Usage:
  python3 merge_seed.py
  python3 merge_seed.py --seed ../human-edge/lib/seed-data.js --scores data/scores/all_scores.json
"""

import json, re, os, sys
from pathlib import Path
from datetime import datetime


def parse_seed_js(seed_path):
    """Parse seed-data.js (JavaScript) into Python list."""
    with open(seed_path) as f:
        js = f.read()
    
    start = js.index('[')
    end = js.index('];') + 1
    raw = js[start:end]
    
    # Strip JS comments and trailing commas
    raw = re.sub(r'//.*?\n', '\n', raw)
    raw = re.sub(r'/\*.*?\*/', '', raw, flags=re.DOTALL)
    raw = re.sub(r',\s*([}\]])', r'\1', raw)
    
    return json.loads(raw)


def normalize(name):
    """Normalize company name for matching."""
    n = name.lower().strip()
    # Remove common suffixes
    for s in [' inc.', ' inc', ' corp.', ' corp', ' llc', ' ltd.', ' ltd',
              ' co.', ' co', ' plc', ' sa', ' ag', ' se', ' nv',
              ' group', ' holdings', ' company', ' companies',
              ', inc.', ', inc', ', corp.', ', corp', ', llc']:
        n = n.replace(s, '')
    # Remove parentheticals
    n = re.sub(r'\s*\(.*?\)', '', n)
    # Remove slashes (like "Alphabet / Google")
    n = re.sub(r'\s*/\s*', ' ', n)
    return n.strip()


# Known name mappings: seed name → pipeline name patterns
NAME_MAP = {
    "alphabet / google": ["alphabet"],
    "alphabet": ["alphabet"],
    "ibm": ["international business machines"],
    "tiktok / bytedance": ["bytedance"],
    "meta / facebook": ["meta platforms"],
    "activision blizzard (microsoft)": ["activision"],
    "x / twitter": ["x corp", "twitter"],
    "ring (amazon)": ["ring"],
    "one medical (amazon)": ["one medical"],
    "zara / inditex": ["inditex", "industria de diseno"],
    "37signals / basecamp": ["37signals", "basecamp"],
    "automattic / wordpress": ["automattic"],
    "ikea / ingka group": ["ikea", "ingka"],
    "ben & jerry's": ["ben jerry", "ben & jerry", "unilever"],
    "kellanova / wk kellogg": ["kellanova", "kellogg"],
    "block (square)": ["block"],
    "whole foods market": ["whole foods", "amazon"],
    "ups": ["united parcel"],
    "exxonmobil": ["exxon mobil"],
    "lowe's": ["lowes", "lowe"],
    "mcdonald's": ["mcdonald"],
    "trader joe's": ["trader joe", "aldi"],
    "annie's homegrown": ["annies", "annie", "general mills"],
    "burt's bees": ["burts bees", "burt", "clorox"],
    "newman's own": ["newmans own", "newman"],
    "levi strauss & co.": ["levi strauss", "levi"],
    "samsung electronics": ["samsung"],
    "shell plc": ["shell"],
    "bp": ["bp plc", "british petroleum"],
    "toyota": ["toyota motor"],
    "subaru": ["subaru corp", "fuji heavy"],
    "rivian": ["rivian automotive"],
    "accenture": ["accenture plc"],
    "deloitte": ["deloitte touche"],
    "unilever": ["unilever plc", "unilever nv"],
    "hp inc.": ["hp inc", "hewlett"],
    "dell technologies": ["dell tech"],
    "lyft": ["lyft inc"],
    "doordash": ["doordash inc"],
    "instacart": ["maplebear"],
    "robinhood": ["robinhood markets"],
    "beyond meat": ["beyond meat inc"],
    "impossible foods": ["impossible"],
    "oatly": ["oatly group"],
    "warby parker": ["warby parker inc"],
    "allbirds": ["allbirds inc"],
    "lululemon": ["lululemon athletica"],
    "gap inc.": ["gap inc"],
    "nordstrom": ["nordstrom inc"],
    "coursera": ["coursera inc"],
    "duolingo": ["duolingo inc"],
    "chegg": ["chegg inc"],
    "nintendo": ["nintendo co"],
    "danone": ["danone sa"],
    "h&m": ["hennes", "h & m"],
    "spacex": ["space exploration"],
    "dropbox": ["dropbox inc"],
    "stripe": ["stripe inc"],
    "valve corporation": ["valve corp"],
    "the new york times": ["new york times"],
    "the guardian": ["guardian media", "guardian news"],
    "fidelity investments": ["fidelity", "fmr"],
    "vanguard": ["vanguard group"],
    "seventh generation": ["seventh gen", "unilever"],
    "kaiser permanente": ["kaiser"],
    "mayo clinic": ["mayo"],
    "wegmans": ["wegmans food"],
    "publix": ["publix super"],
    "aldi": ["aldi inc", "aldi us"],
    "biogen": ["biogen inc"],
    "moderna": ["moderna inc"],
    "reuters / thomson reuters": ["thomson reuters"],
    "aspiration": ["aspiration partners"],
    "amalgamated bank": ["amalgamated"],
}


def find_match(seed_name, pipeline_names):
    """Try to match a seed company to an existing pipeline company."""
    norm_seed = normalize(seed_name)
    
    # Direct normalized match
    for pname, pdata in pipeline_names.items():
        if norm_seed == normalize(pname):
            return pname
    
    # Check NAME_MAP
    for map_key, map_vals in NAME_MAP.items():
        if norm_seed == normalize(map_key) or any(v in norm_seed for v in map_vals):
            for pname in pipeline_names:
                pnorm = normalize(pname)
                if any(v in pnorm for v in map_vals):
                    return pname
    
    # Substring match (seed name contained in pipeline name or vice versa)
    for pname in pipeline_names:
        pnorm = normalize(pname)
        if len(norm_seed) >= 4 and (norm_seed in pnorm or pnorm in norm_seed):
            return pname
    
    # First word match (for simple names like "Shell", "Toyota", "Nintendo")
    first_word = norm_seed.split()[0] if norm_seed.split() else ""
    if len(first_word) >= 4:
        for pname in pipeline_names:
            if first_word == normalize(pname).split()[0]:
                return pname
    
    return None


def seed_to_pipeline(seed_entry):
    """Convert a seed-data.js entry to pipeline-compatible score format."""
    h = seed_entry.get("h", 50)
    u = seed_entry.get("u", 50)
    m = seed_entry.get("m", 50)
    a = seed_entry.get("a", 50)
    n = seed_entry.get("n", 50)
    
    composite = round((h + u + m + a + n) / 5)
    
    # Determine industry from tags
    tags = seed_entry.get("tags", [])
    industry_map = {
        "tech": "tech", "technology": "tech", "software": "tech", "ai": "tech",
        "retail": "retail", "e-commerce": "retail", "grocery": "retail",
        "food": "food", "beverage": "food", "restaurant": "food",
        "healthcare": "healthcare", "pharma": "healthcare", "biotech": "healthcare",
        "finance": "finance", "banking": "finance", "fintech": "finance",
        "energy": "energy", "oil": "energy", "solar": "energy", "renewable": "energy",
        "automotive": "auto", "ev": "auto", "car": "auto",
        "media": "media", "news": "media", "publishing": "media",
        "manufacturing": "manufacturing", "industrial": "manufacturing",
        "apparel": "retail", "fashion": "retail", "clothing": "retail",
        "outdoor": "retail", "footwear": "retail",
        "consulting": "finance", "defense": "defense",
        "telecom": "telecom", "telecommunications": "telecom",
        "gaming": "media", "entertainment": "media",
    }
    industry = "default"
    for tag in tags:
        if tag.lower() in industry_map:
            industry = industry_map[tag.lower()]
            break
    
    # Balance floor check
    dims = [h, u, m, a, n]
    balance_floor = any(d < 42 for d in dims)
    triggering = None
    if balance_floor:
        dim_labels = ["H", "U", "M", "A", "N"]
        triggering = dim_labels[dims.index(min(dims))]
    
    # HI Balanced check (simplified — full 10 gates checked later by API)
    hi_balanced = composite >= 64.6 and not balance_floor
    
    # Humanwashing flags
    hw_flags = []
    
    return {
        "company": seed_entry["name"],
        "ticker": seed_entry.get("ticker", ""),
        "industry": industry,
        "sic": "",
        "sic_description": "",
        "D_H": h, "D_U": u, "D_M": m, "D_A": a, "D_N": n,
        "composite": composite,
        "hi_grade": "scored",
        "satire": "",
        "floor_triggered": balance_floor,
        "balance_floor": balance_floor,
        "triggering_dimension": triggering,
        "confidence": "Baseline", "spec_version": "1.1.0",
        "data_sources": ["Public Reporting"],
        "signal_coverage": "0/24 sub-signals — estimated from public data",
        "humanwashing_flags": hw_flags,
        "algo_harm": {"has_harm": False, "algo_harm_score": 0, "flags": []},
        "genome": {
            "H": {"scores": {"H.1": h, "H.2": h, "H.3": h, "H.4": h, "H.5": h}, "sources": ["Public Reporting"]},
            "U": {"scores": {"U.1": u, "U.2": u, "U.3": u, "U.4": u, "U.5": u}, "sources": ["Public Reporting"]},
            "M": {"scores": {"M.1": m, "M.2": m, "M.3": m, "M.4": m, "M.5": m}, "sources": ["Public Reporting"]},
            "A": {"scores": {"A.1": a, "A.2": a, "A.3": a, "A.4": a, "A.5": a}, "sources": ["Public Reporting"]},
            "N": {"scores": {"N.1": n, "N.2": n, "N.3": n, "N.4": n, "N.5": n}, "sources": ["Public Reporting"]},
        },
        "key_signals": {},
        "domains": seed_entry.get("domains", []),
        "tags": tags,
        "notes": seed_entry.get("notes", ""),
        "_source": "seed",
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="HI. Seed Merger")
    parser.add_argument("--seed", default="../human-edge/lib/seed-data.js", help="Path to seed-data.js")
    parser.add_argument("--scores", default="data/scores/all_scores.json", help="Path to pipeline scores")
    parser.add_argument("--output", default="data/scores/all_scores.json", help="Output path (overwrites)")
    args = parser.parse_args()
    
    print("═══ HI. Seed Merger ═══")
    
    # Load pipeline scores
    scores_path = Path(args.scores)
    if not scores_path.exists():
        print(f"  No scores at {scores_path}. Run scoring engine first.")
        return
    
    pipeline = json.load(open(scores_path))
    pipeline_valid = [s for s in pipeline if not s.get("error") and s.get("composite", 0) > 0]
    pipeline_names = {s["company"]: s for s in pipeline_valid}
    print(f"  Pipeline: {len(pipeline_valid)} companies")
    
    # Load seed
    seed_path = Path(args.seed)
    if not seed_path.exists():
        print(f"  No seed at {seed_path}. Skipping merge.")
        return
    
    seed = parse_seed_js(str(seed_path))
    print(f"  Seed: {len(seed)} companies")
    
    # Match and merge
    matched = 0
    added = 0
    enriched = 0
    
    for s in seed:
        name = s.get("name", "")
        match = find_match(name, pipeline_names)
        
        if match:
            # Already in pipeline — enrich with seed domains if missing
            existing = pipeline_names[match]
            if not existing.get("domains") and s.get("domains"):
                existing["domains"] = s["domains"]
                enriched += 1
            if not existing.get("tags") and s.get("tags"):
                existing["tags"] = s.get("tags", [])
            matched += 1
        else:
            # Not in pipeline — convert and add
            converted = seed_to_pipeline(s)
            pipeline.append(converted)
            added += 1
    
    # Save merged output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(pipeline, open(output_path, "w"), indent=2)
    
    total = len([s for s in pipeline if not s.get("error") and s.get("composite", 0) > 0])
    print(f"\n  Results:")
    print(f"    Matched (already in pipeline): {matched}")
    print(f"    Added (private/missing):       {added}")
    print(f"    Enriched with domains:         {enriched}")
    print(f"    Total companies now:           {total}")
    print(f"\n  ✓ Saved to {output_path}")


if __name__ == "__main__":
    main()
