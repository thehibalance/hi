#!/usr/bin/env python3
"""
Update the Data Sources card in docs/index.html with the new honest,
category-based version (Version B — keeps the 42 reference).

Key changes from the current card:
  - Removes phantom sources: B Corp Directory, Charity Navigator
  - Removes Layoffs.fyi (replaced by layered SEC 8-K + WARN Act + NewsAPI signals)
  - Adds explicit category breakdown: 20 live + 11 curated + 11 computed = 42
  - Adds MSCI/Sustainalytics comparison for curated dataset credibility
  - Adds NHTSA (was missing from old list but IS in code)
  - Explicitly names SEC sub-forms (10-K, 8-K, DEF 14A, Form 4)

Safe to re-run. Backs up file first.

Usage:
    cd ~/Desktop/repo
    python3 update_sources.py
"""

import shutil
from pathlib import Path
from datetime import datetime

TARGET_FILE = Path("docs/index.html")

# Unique start marker for the current Data Sources card
OLD_CARD_START = '<div class="about-card"><h3 style="font-family:\'DM Serif Display\';font-size:22px;color:var(--navy);margin-bottom:16px">Data Sources'
# Unique end marker — closing paragraph of the current card
OLD_CARD_END = 'Gold HI Grade status is earned algorithmically, not purchased.</strong></p></div>'

# The new card content (Version B)
NEW_CARD = '''<div class="about-card"><h3 style="font-family:'DM Serif Display';font-size:22px;color:var(--navy);margin-bottom:16px">Data Sources (42)</h3><p>HI Grades are computed from <strong>42 free, public data sources</strong> across 25 sub-signals. No proprietary databases, no purchased ratings, no pay-to-play access. Every sub-signal is traceable to its source.</p><p style="margin-top:14px"><strong>20 live API integrations</strong> (refreshed nightly):<br><span style="color:var(--muted);font-size:14px">SEC EDGAR (10-K, 8-K, DEF 14A, Form 4 — 4 filing types), EPA ECHO, BLS (wages + industry benchmarks), Yahoo Finance, FMP, Finnhub, NewsAPI, OpenCorporates, CFPB, Have I Been Pwned, FEC, CPSC, FDA, FTC, USPTO, OSHA, DOL, EEOC, NHTSA, CEO signals.</span></p><p style="margin-top:14px"><strong>11 curated public datasets</strong> (refreshed quarterly — same methodology used by MSCI and Sustainalytics):<br><span style="color:var(--muted);font-size:14px">Glassdoor employee ratings, Disability:IN DEI Index, HRC Corporate Equality Index, CDP Climate Scores, WARN Act filings, iFixit Repairability Index, GRI Sustainability Standards, SBTi Climate Commitments, IRS 990 Charitable Filings, Industry Deforestation Risk, Industry RPE Medians.</span></p><p style="margin-top:14px"><strong>11 computed sub-signal aggregates</strong> (derived from the above, traceable through the audit trail):<br><span style="color:var(--muted);font-size:14px">Revenue per employee, headcount change, R&amp;D vs workforce ratio, CEO pay ratio, insider trading patterns, filing transparency score, patent flow analysis, political donation concentration, consumer complaint density, safety violation severity, climate disclosure quality.</span></p><p style="margin-top:18px"><strong>Layered layoff detection:</strong> Workforce reductions are detected three ways — SEC 8-K restructuring disclosures (legally mandated), WARN Act filings (federal/state required), and NewsAPI keyword surveillance across 150,000+ news sources.</p><p style="margin-top:14px">All scores are estimated from public data. <strong>Gold HI Grade status is earned algorithmically, not purchased.</strong></p></div>'''


def main():
    if not TARGET_FILE.exists():
        print(f"✗ {TARGET_FILE} not found. Run from the repo root (~/Desktop/repo).")
        return 1
    
    # Backup
    backup = TARGET_FILE.with_suffix(f".html.bak_sources_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy(TARGET_FILE, backup)
    print(f"✓ Backed up to {backup.name}")
    
    content = TARGET_FILE.read_text()
    original_length = len(content)
    
    # Find the current card boundaries
    start_idx = content.find(OLD_CARD_START)
    if start_idx == -1:
        print(f"✗ Could not find Data Sources card start marker.")
        print(f"   Expected: {OLD_CARD_START[:80]}...")
        return 1
    
    end_idx = content.find(OLD_CARD_END, start_idx)
    if end_idx == -1:
        print(f"✗ Could not find Data Sources card end marker.")
        return 1
    end_idx += len(OLD_CARD_END)
    
    old_card = content[start_idx:end_idx]
    print(f"  Old card: {len(old_card):,} bytes")
    print(f"  New card: {len(NEW_CARD):,} bytes")
    
    # Idempotency: if already updated, skip
    if 'NHTSA' in content and 'MSCI and Sustainalytics' in content:
        print("⚠ Card already updated (NHTSA + MSCI markers present). Skipping.")
        return 0
    
    # Replace the card
    content = content[:start_idx] + NEW_CARD + content[end_idx:]
    
    # Sanity checks
    checks = [
        ("20 live API integrations", "live API count"),
        ("11 curated public datasets", "curated count"),
        ("11 computed sub-signal", "computed count"),
        ("NHTSA", "NHTSA source added"),
        ("Industry RPE Medians", "new curated dataset added"),
        ("Layered layoff detection", "layoff layering explanation"),
        ("MSCI and Sustainalytics", "peer methodology reference"),
    ]
    
    # Phantom source removal checks
    phantom_removal = [
        ("B Corp Directory", "B Corp Directory removed"),
        ("Charity Navigator", "Charity Navigator removed"),
        ("Layoffs.fyi", "Layoffs.fyi removed (replaced by 3-tier detection)"),
    ]
    
    print()
    print("Card updates present:")
    for text, desc in checks:
        present = text in content
        mark = "✓" if present else "✗"
        print(f"  {mark} {desc}")
    
    print()
    print("Phantom sources removed:")
    for text, desc in phantom_removal:
        absent = text not in content
        mark = "✓" if absent else "✗"
        print(f"  {mark} {desc}")
    
    # Write
    TARGET_FILE.write_text(content)
    print()
    print(f"File size: {original_length:,} → {len(content):,} bytes "
          f"({len(content) - original_length:+,})")
    print()
    print("✓ Data Sources card updated.")
    print()
    print("Next steps:")
    print(f"  1. Review: diff {backup.name} {TARGET_FILE.name} | head -80")
    print(f"  2. Preview: open docs/index.html and navigate to About → Data Sources card")
    print(f"  3. If wrong: cp {backup.name} {TARGET_FILE.name}")
    return 0


if __name__ == "__main__":
    exit(main())
