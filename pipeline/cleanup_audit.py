#!/usr/bin/env python3
"""
HI. Data Cleanup — Fix domain collisions, dupes, and bad mappings.
Run from repo root: python3 pipeline/cleanup_audit.py
"""
import json
import re
import os

SCORES_FILE = "pipeline/data/scores/all_scores.json"
SP500_FILE = "pipeline/sp500_domains.py"

def main():
    print("HI. Data Cleanup")
    print("=" * 60)
    
    if not os.path.exists(SCORES_FILE):
        print(f"ERROR: {SCORES_FILE} not found. Run from repo root.")
        return
    
    data = json.load(open(SCORES_FILE))
    fixes = 0
    
    # ═══ FIX 1: Remove wrong domain mappings ═══
    BAD_DOMAINS = {
        "PPRUY": ["amazon.com"],           # Kering SA is NOT amazon
        "HAL": ["burtsbees.com"],           # Halliburton is NOT Burt's Bees
        "STEM": ["system76.com"],           # Stem Inc is NOT System76
    }
    
    for c in data:
        ticker = c.get("ticker", "")
        if ticker in BAD_DOMAINS:
            bad = BAD_DOMAINS[ticker]
            before = c.get("domains", [])
            c["domains"] = [d for d in before if d.lower() not in [b.lower() for b in bad]]
            if len(before) != len(c["domains"]):
                print(f"  ✓ Removed {bad} from {c['company']} ({ticker})")
                fixes += 1
    
    # Also check by company name for untickerered bad mappings
    for c in data:
        name = c.get("company", "").lower()
        domains = c.get("domains", [])
        cleaned = []
        for d in domains:
            base = d.lower().split(".")[0]
            # If domain doesn't relate to company at all AND company has a ticker
            # Flag known bad ones
            if "kering" in name and "amazon" in d.lower():
                print(f"  ✓ Removed {d} from {c['company']} (name-based)")
                fixes += 1
                continue
            if "halliburton" in name and "burtsbees" in d.lower():
                print(f"  ✓ Removed {d} from {c['company']} (name-based)")
                fixes += 1
                continue
            if "stem inc" in name and "system76" in d.lower():
                print(f"  ✓ Removed {d} from {c['company']} (name-based)")
                fixes += 1
                continue
            cleaned.append(d)
        c["domains"] = cleaned
    
    # ═══ FIX 2: Deduplicate Tyson Foods ═══
    def norm(name):
        n = name.lower().strip()
        n = re.sub(r'[,.\-\'"()\[\]]', ' ', n)
        n = re.sub(r'\s+', ' ', n).strip()
        for s in [' incorporated', ' corporation', ' international', ' technologies',
                  ' company', ' inc', ' corp', ' llc', ' ltd', ' co', ' plc', ' sa', ' ag']:
            if n.endswith(s): n = n[:-len(s)].strip()
        return n
    
    seen = {}
    deduped = []
    dupes_removed = 0
    for c in data:
        n = norm(c.get("company", ""))
        t = c.get("ticker", "")
        
        key = t if t else n
        if key in seen:
            existing = seen[key]
            # Keep the one with more data sources
            if len(c.get("data_sources", [])) > len(existing.get("data_sources", [])):
                deduped.remove(existing)
                seen[key] = c
                deduped.append(c)
                print(f"  ✓ Dedup: kept '{c['company']}' over '{existing['company']}' (more sources)")
            else:
                print(f"  ✓ Dedup: kept '{existing['company']}' over '{c['company']}' (more sources)")
            dupes_removed += 1
            fixes += 1
        else:
            seen[key] = c
            deduped.append(c)
    
    data = deduped
    
    # ═══ FIX 3: Verify no impossible scores ═══
    for c in data:
        for dim in ["D_H", "D_U", "D_M", "D_A", "D_N", "composite"]:
            v = c.get(dim, 0)
            if v < 0:
                c[dim] = 0
                print(f"  ✓ Clamped {c['company']} {dim} from {v} to 0")
                fixes += 1
            elif v > 100:
                c[dim] = 100
                print(f"  ✓ Clamped {c['company']} {dim} from {v} to 100")
                fixes += 1
    
    # ═══ FIX 4: Flag "default" industry companies ═══
    default_industry = [c for c in data if c.get("industry") == "default"]
    print(f"\n  ℹ {len(default_industry)} companies still on 'default' industry (needs SIC mapping)")
    
    # ═══ FIX 5: Verify domain-company alignment for top companies ═══
    print("\n--- Domain Collision Check (post-fix) ---")
    domain_map = {}
    collisions_remaining = 0
    for c in data:
        for d in c.get("domains", []):
            d = d.lower().strip()
            if d in domain_map:
                print(f"  ⚠ STILL COLLISION: {d} → '{c['company']}' AND '{domain_map[d]}'")
                collisions_remaining += 1
            else:
                domain_map[d] = c["company"]
    
    if collisions_remaining == 0:
        print("  ✓ No domain collisions remaining")
    
    # ═══ SAVE ═══
    data.sort(key=lambda x: x.get("composite", 0), reverse=True)
    json.dump(data, open(SCORES_FILE, "w"), indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"CLEANUP COMPLETE: {fixes} fixes applied")
    print(f"Companies: {len(data)}")
    print(f"Domains: {len(domain_map)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
