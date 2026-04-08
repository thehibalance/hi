#!/usr/bin/env python3
"""
About page rewrite:
  1. Insert 3 new cards after the opening "HI measures..." card:
     - The Fifth Element
     - What HI Grade does for you
     - When to use it
  2. Remove the "AI Enhancement Layer — COMING SOON" card entirely

Safe to re-run. Backs up file first.

Usage:
    cd ~/Desktop/repo
    python3 update_about.py
"""

import shutil
from pathlib import Path
from datetime import datetime

TARGET_FILE = Path("docs/index.html")

# The anchor immediately BEFORE which we insert new cards.
# This is the closing tag of the opening "HI measures the balance..." card.
INSERT_ANCHOR_END_OF_INTRO_CARD = '<strong style="color:#C49B20">We reward companies that use AI to empower their people.</strong></p></div>'

# The three new cards to insert, matching existing page styling exactly.
NEW_CARDS = '''<strong style="color:#C49B20">We reward companies that use AI to empower their people.</strong></p></div>
<div class="about-card"><h3 style="font-family:'DM Serif Display';font-size:22px;color:var(--navy);margin-bottom:16px">The Fifth Element</h3><p>For centuries, we've made decisions using four elements: <strong>cost, time, convenience, risk.</strong> We left out the most important one.</p><p><img src="/logo-512.png" alt="hi." style="height:16px;vertical-align:middle"> Grade adds <strong>love</strong> back as the fifth element of every decision we make.</p><p style="margin-top:16px;font-style:italic;color:var(--navy);font-weight:600">Human kind? Now you can find out.</p></div>
<div class="about-card"><h3 style="font-family:'DM Serif Display';font-size:22px;color:var(--navy);margin-bottom:16px">What HI Grade does for you</h3><div style="display:flex;flex-direction:column;gap:14px;margin-top:8px"><div><strong>Know where your money goes.</strong><br><span style="color:var(--muted);font-size:14px">Align every purchase with your values. See which companies invest in humans and which extract from them.</span></div><div><strong>Find employers who invest in humans.</strong><br><span style="color:var(--muted);font-size:14px">Check a company's HI Grade before you apply, interview, or accept an offer. Work where people matter.</span></div><div><strong>Spot humanwashing before you're fooled.</strong><br><span style="color:var(--muted);font-size:14px">Detect brands that perform human care without practicing it. The marketing says humans. The data says otherwise.</span></div><div><strong>See the future of the companies you trust.</strong><br><span style="color:var(--muted);font-size:14px">The HUMAN Decay index shows which companies are accelerating toward AI replacement — before the layoffs hit the news.</span></div></div></div>
<div class="about-card"><h3 style="font-family:'DM Serif Display';font-size:22px;color:var(--navy);margin-bottom:16px">When to use it</h3><div style="display:flex;flex-direction:column;gap:14px;margin-top:8px"><div><strong>Before you buy.</strong> <span style="color:var(--muted);font-size:14px">Scan a barcode or search a brand. Know if the humans behind the product are being invested in or replaced.</span></div><div><strong>Before you work.</strong> <span style="color:var(--muted);font-size:14px">Look up the company before the interview. HI Grade tells you what Glassdoor can't.</span></div><div><strong>Before you invest.</strong> <span style="color:var(--muted);font-size:14px">Know what you're funding. HI Grade reveals the human cost of every portfolio.</span></div><div><strong>Before you recommend.</strong> <span style="color:var(--muted);font-size:14px">Don't vouch for a brand you haven't checked. Ask <em>Human kind?</em> before your reputation is on it.</span></div></div><p style="margin-top:20px;padding:14px;background:#F8FAFC;border-radius:8px;font-style:italic;color:var(--navy);font-size:14px"><strong>The fifth check.</strong> Before every decision, ask: <strong>Human kind?</strong></p></div>'''

# The AI Enhancement Layer card — matches the full card from anchor start to anchor end.
# Using unique start+end substrings to avoid accidental deletes elsewhere.
AI_CARD_START = '<div class="about-card"><h3 style="font-family:\'DM Serif Display\';font-size:22px;color:var(--navy);margin-bottom:16px">🤖 AI Enhancement Layer'
AI_CARD_END = 'The AI makes the telescope sharper — it doesn\'t move the stars.</p></div>'


def main():
    if not TARGET_FILE.exists():
        print(f"✗ {TARGET_FILE} not found. Run from the repo root (~/Desktop/repo).")
        return 1
    
    # Backup
    backup = TARGET_FILE.with_suffix(f".html.bak_about_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy(TARGET_FILE, backup)
    print(f"✓ Backed up to {backup.name}")
    
    content = TARGET_FILE.read_text()
    original_length = len(content)
    
    # ─── Edit 1: insert new cards after the intro card ────────────────
    if INSERT_ANCHOR_END_OF_INTRO_CARD not in content:
        print(f"✗ Insert anchor not found. Has the intro card been edited?")
        print(f"   Expected: ...{INSERT_ANCHOR_END_OF_INTRO_CARD[-80:]}")
        return 1
    
    # Check if cards already inserted (re-run safety)
    if '>The Fifth Element</h3>' in content:
        print("⚠ 'The Fifth Element' card already present — skipping insert")
        insert_count = 0
    else:
        content = content.replace(INSERT_ANCHOR_END_OF_INTRO_CARD, NEW_CARDS, 1)
        insert_count = 3
        print(f"✓ Inserted {insert_count} new cards (Fifth Element / Benefits / Use cases)")
    
    # ─── Edit 2: remove the AI Enhancement Layer card ─────────────────
    start_idx = content.find(AI_CARD_START)
    if start_idx == -1:
        print("⚠ AI Enhancement Layer card not found (already removed?)")
    else:
        end_idx = content.find(AI_CARD_END, start_idx)
        if end_idx == -1:
            print(f"✗ Found AI card start but not end marker. Manual fix needed.")
            return 1
        end_idx += len(AI_CARD_END)
        # Also strip a preceding newline if present
        if start_idx > 0 and content[start_idx - 1] == '\n':
            start_idx -= 1
        removed = content[start_idx:end_idx]
        content = content[:start_idx] + content[end_idx:]
        print(f"✓ Removed AI Enhancement Layer card ({len(removed):,} bytes)")
    
    # Sanity check — page still has the founder section and HUMAN Framework
    checks = [
        ("The HUMAN Framework", "H-U-M-A-N dimension breakdown"),
        ("The Founder", "Founder story"),
        ("Human kind?", "Tagline"),
        ("The Fifth Element", "Fifth element card"),
    ]
    print()
    print("Post-edit sanity checks:")
    for text, desc in checks:
        present = text in content
        mark = "✓" if present else "✗"
        print(f"  {mark} {desc}: {'present' if present else 'MISSING'}")
    
    # Write
    TARGET_FILE.write_text(content)
    print()
    print(f"File size: {original_length:,} → {len(content):,} bytes "
          f"({len(content) - original_length:+,})")
    print()
    print("✓ About page updated.")
    print()
    print("Next steps:")
    print(f"  1. Review: diff {backup.name} {TARGET_FILE.name} | head -80")
    print(f"  2. Preview: open docs/index.html in browser, navigate to About")
    print(f"  3. If wrong: cp {backup.name} {TARGET_FILE.name}")
    return 0


if __name__ == "__main__":
    exit(main())
