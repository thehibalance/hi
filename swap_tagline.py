#!/usr/bin/env python3
"""
Tagline swap: "Think human intelligence." → "Human kind?"

Targets ONLY the tagline instances in docs/index.html. Preserves references
to "Human Intelligence" as a concept (what HI stands for, the founder story,
the "State of Human Intelligence" product name).

Safe to re-run. Backs up the file before editing.

Usage:
    cd ~/Desktop/repo
    python3 swap_tagline.py
"""

import shutil
from pathlib import Path
from datetime import datetime

TARGET_FILE = Path("docs/index.html")

# List of (exact_old_text, exact_new_text, description) tuples
# Each substring must be unique in the file or the script will report it
SWAPS = [
    # Title tag
    (
        "<title>hi — Think human intelligence.</title>",
        "<title>hi — Human kind?</title>",
        "page title",
    ),
    # Meta description
    (
        '<meta name="description" content="Think human intelligence. Every company gets a HI Grade™.">',
        '<meta name="description" content="Human kind? HI Grade scores every company on how they treat people. Check before you buy, work, or invest.">',
        "meta description",
    ),
    # Open Graph title
    (
        '<meta property="og:title" content="hi — Think human intelligence.">',
        '<meta property="og:title" content="hi — Human kind?">',
        "og:title",
    ),
    # Open Graph description
    (
        '<meta property="og:description" content="Think human intelligence.">',
        '<meta property="og:description" content="The question for every brand, every buy, every decision.">',
        "og:description",
    ),
    # Nav tagline
    (
        '<span class="nav-tagline">THINK HUMAN INTELLIGENCE.</span>',
        '<span class="nav-tagline">HUMAN KIND?</span>',
        "nav tagline",
    ),
    # Hero tagline
    (
        '<p>Think human intelligence.</p>',
        '<p>Human kind?</p>',
        "hero tagline",
    ),
    # About page subtitle
    (
        '<p class="about-sub">Think human intelligence.</p>',
        '<p class="about-sub">Human kind?</p>',
        "about page subtitle",
    ),
    # Footer tagline
    (
        '<div class="footer-tagline">Think human intelligence.</div>',
        '<div class="footer-tagline">Human kind?</div>',
        "footer tagline",
    ),
    # Share text (social)
    (
        "Think human intelligence. thehibalance.org #HIGrade #ThinkHumanIntelligence",
        "Human kind? thehibalance.org #HIGrade #HumanKind",
        "social share text",
    ),
]


def main():
    if not TARGET_FILE.exists():
        print(f"✗ {TARGET_FILE} not found. Run from the repo root (~/Desktop/repo).")
        return 1
    
    # Backup
    backup = TARGET_FILE.with_suffix(f".html.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy(TARGET_FILE, backup)
    print(f"✓ Backed up to {backup.name}")
    
    content = TARGET_FILE.read_text()
    original_length = len(content)
    
    successes = 0
    failures = 0
    
    for old, new, desc in SWAPS:
        if old in content:
            count = content.count(old)
            content = content.replace(old, new)
            successes += 1
            status = f"✓ {desc}"
            if count > 1:
                status += f" ({count} occurrences)"
            print(status)
        else:
            failures += 1
            print(f"✗ {desc}: not found — already changed, or text drifted")
    
    # Preserved references (sanity check — these SHOULD still be present)
    preserved_checks = [
        ("Human Intelligence and Artificial Intelligence", "about card concept explanation"),
        ("is it Human Intelligence, or Artificial", "founder story"),
        ("State of Human Intelligence", "product name for custom reports"),
    ]
    
    print()
    print("Preserved concept references (these should still exist):")
    for text, desc in preserved_checks:
        if text in content:
            print(f"  ✓ {desc}")
        else:
            print(f"  ⚠ {desc}: NOT FOUND — verify this is intentional")
    
    # Write the file
    TARGET_FILE.write_text(content)
    print()
    print(f"Swap summary: {successes} succeeded, {failures} failed")
    print(f"File size: {original_length:,} → {len(content):,} bytes")
    
    if failures:
        print()
        print("⚠ Some swaps failed. Review the file and/or the SWAPS list in this script.")
        return 1
    
    print()
    print("✓ Tagline swap complete.")
    print()
    print("Next steps:")
    print(f"  1. Review the changes: diff {backup.name} {TARGET_FILE.name}")
    print(f"  2. If anything looks wrong: cp {backup.name} {TARGET_FILE.name}")
    print(f"  3. Test locally by opening docs/index.html in your browser")
    return 0


if __name__ == "__main__":
    exit(main())
