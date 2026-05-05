#!/usr/bin/env python3
"""
v1.2.0 Subsidiary Domain Expansion — pipeline/sp500_domains.py

Adds 16 subsidiary brand domains identified by audit #7:
  - GOOGL: waze, waymo, nest, fitbit
  - AMZN:  ring, twitch, audible, imdb, zappos
  - MSFT:  xbox, skype, minecraft
  - DIS:   marvel, nationalgeographic
  - AAPL:  beatsbydre
  - META:  oculus

User-impact: a Chrome user browsing twitch.tv (35M DAU) currently gets a
404 from the extension instead of seeing AMZN's score. Same for waze, ring,
xbox, marvel, etc. — all major consumer-facing brands owned by S&P 500
companies.

Pure data change. No logic touched. Idempotent (skips entries already present).

Anchor: exact-string match on each ticker's existing domain list.

Usage (from repo root):
  python3 patch_subsidiary_domains_v120.py
"""

import sys
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
TARGET = REPO_ROOT / "pipeline" / "sp500_domains.py"


# ── Six surgical replacements ──
# Format: (label, old_text, new_text)
EDITS = [
    (
        "AAPL adds beatsbydre.com",
        '"AAPL": ["apple.com", "icloud.com", "store.apple.com"],',
        '"AAPL": ["apple.com", "icloud.com", "store.apple.com", "beatsbydre.com"],',
    ),
    (
        "MSFT adds xbox.com, skype.com, minecraft.net",
        '"MSFT": ["microsoft.com", "office.com", "azure.com", "github.com", "linkedin.com"],',
        '"MSFT": ["microsoft.com", "office.com", "azure.com", "github.com", "linkedin.com", "xbox.com", "skype.com", "minecraft.net"],',
    ),
    (
        "GOOGL adds waze, waymo, nest, fitbit",
        '"GOOGL": ["google.com", "youtube.com", "gmail.com", "android.com"],',
        '"GOOGL": ["google.com", "youtube.com", "gmail.com", "android.com", "waze.com", "waymo.com", "nest.com", "fitbit.com"],',
    ),
    (
        "AMZN adds ring, twitch, audible, imdb, zappos",
        '"AMZN": ["amazon.com", "aws.amazon.com", "primevideo.com", "wholefoods.com"],',
        '"AMZN": ["amazon.com", "aws.amazon.com", "primevideo.com", "wholefoods.com", "ring.com", "twitch.tv", "audible.com", "imdb.com", "zappos.com"],',
    ),
    (
        "META adds oculus.com",
        '"META": ["facebook.com", "instagram.com", "whatsapp.com", "meta.com", "threads.net"],',
        '"META": ["facebook.com", "instagram.com", "whatsapp.com", "meta.com", "threads.net", "oculus.com"],',
    ),
    (
        "DIS adds marvel, nationalgeographic",
        '"DIS": ["disney.com", "disneyplus.com", "espn.com", "hulu.com"],',
        '"DIS": ["disney.com", "disneyplus.com", "espn.com", "hulu.com", "marvel.com", "nationalgeographic.com"],',
    ),
]


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()
    new_src = src
    applied = 0
    skipped = 0

    print("Applying Patcher 28 — subsidiary domain expansion:")
    for label, old, new in EDITS:
        if new in new_src:
            print(f"  ⏭  [{label}] already present, skipping")
            skipped += 1
            continue
        if old not in new_src:
            print(f"  ✗ [{label}] anchor not found — aborting")
            sys.exit(f"ABORT: anchor for '{label}' missing from sp500_domains.py")
        if new_src.count(old) != 1:
            print(f"  ✗ [{label}] anchor appears {new_src.count(old)} times, refusing to patch ambiguously")
            sys.exit(f"ABORT: anchor for '{label}' ambiguous")
        new_src = new_src.replace(old, new, 1)
        applied += 1
        print(f"  ✓ [{label}]")

    if applied == 0 and skipped > 0:
        print(f"\n  All {skipped} edits already applied. No changes.")
        return

    if applied == 0:
        sys.exit("ABORT — no edits applied (and none skipped). Something's wrong.")

    # Atomic write
    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    backup = TARGET.with_suffix(TARGET.suffix + ".sub_bak")
    tmp.write_text(new_src)

    # py_compile
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(tmp)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        tmp.unlink()
        sys.exit(f"ABORT — py_compile failed:\n{result.stderr}")

    shutil.copy2(TARGET, backup)
    tmp.replace(TARGET)

    print()
    print(f"✓ Patched: {TARGET}")
    print(f"  Backup: {backup.name}")
    print(f"  {applied} edits applied, {skipped} skipped (already present)")
    print()
    print("  Coverage gains: 16 subsidiary brands now resolve to parents")
    print("    twitch.tv, ring.com, audible, imdb, zappos → AMZN")
    print("    waze, waymo, nest, fitbit → GOOGL")
    print("    xbox, skype, minecraft → MSFT")
    print("    marvel, nationalgeographic → DIS")
    print("    beatsbydre → AAPL")
    print("    oculus → META")
    print()
    print("  Next:")
    print("    git add pipeline/sp500_domains.py")
    print("    git commit + push → Railway redeploys → 32/32 subsidiary audit pass")


if __name__ == "__main__":
    main()
