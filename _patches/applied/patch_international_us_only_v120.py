#!/usr/bin/env python3
"""
v1.2.0 International Coverage Fix — international_tickers.py + universe_tickers.py

Goal: include US-listed ADRs of major international companies in the SEC
iteration list (SHEL, BP, HSBC, UL, AZN, GSK, RIO, BHP, BTI, DEO, etc.) so
they get scored. Exclude foreign-listed tickers with country suffixes (.L,
.T, .DE) since SEC EDGAR can't fetch foreign filers.

Current behavior:
  universe_tickers.get_all_tickers() merges SP500 + RUSSELL_1000 + ALL of
  international_tickers.get_international_tickers(). The international list
  includes both ADRs (no suffix) AND foreign-listed (e.g., AAL.L, 7203.T).
  Result: 295 unscoreable foreign tickers go to fetch_sec(), creating ghost
  records and wasting API calls.

Fix:
  1. Add get_us_listed_tickers() to international_tickers.py — returns ONLY
     entries without country-suffix dots (e.g., "SHEL", "BP", "AZN" but not
     "AAL.L", "7203.T").
  2. Modify universe_tickers.get_all_tickers() to call get_us_listed_tickers()
     instead of get_international_tickers().

The original get_international_tickers() stays for Yahoo/Finnhub use later
(those sources can fetch foreign-listed tickers).

Anchor: exact-string match on both function definitions.

Usage (from repo root):
  python3 patch_international_us_only_v120.py
"""

import sys
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
INTL_TARGET = REPO_ROOT / "pipeline" / "international_tickers.py"
UNIV_TARGET = REPO_ROOT / "pipeline" / "universe_tickers.py"


# ── international_tickers.py: ADD a new function alongside the existing one ──
INTL_OLD = '''def get_international_tickers():
    """Return deduplicated list of all international tickers."""
    all_tickers = set()
    for t in FTSE_100 + DAX_40 + CAC_40 + NIKKEI_225 + GLOBAL_MAJORS:
        t = t.strip()
        if t:
            all_tickers.add(t)
    return sorted(all_tickers)'''

INTL_NEW = '''def get_international_tickers():
    """Return deduplicated list of ALL international tickers, including foreign-listed.
    Use this for Yahoo Finance / Finnhub which support foreign exchanges (.L, .T, .DE)."""
    all_tickers = set()
    for t in FTSE_100 + DAX_40 + CAC_40 + NIKKEI_225 + GLOBAL_MAJORS:
        t = t.strip()
        if t:
            all_tickers.add(t)
    return sorted(all_tickers)


def get_us_listed_tickers():
    """v1.2.0: Return only US-listed ADRs (no country suffix).
    
    Use this for SEC EDGAR collection — SEC cannot fetch foreign filers, so
    sending it tickers like '7203.T' or 'AAL.L' creates ghost records and
    wastes API calls. ADR tickers (SHEL, BP, HSBC, AZN, etc.) trade on
    NYSE/NASDAQ and have full SEC filings via 20-F (or 10-K for some)."""
    all_tickers = set()
    for t in FTSE_100 + DAX_40 + CAC_40 + NIKKEI_225 + GLOBAL_MAJORS:
        t = t.strip()
        if not t:
            continue
        # Skip tickers with foreign-exchange suffixes
        # (.L London, .T Tokyo, .DE Germany, .PA Paris, .HK Hong Kong, .KS Korea,
        #  .SZ Shenzhen, .SS Shanghai, .AX Australia, .TO Toronto, .MI Milan, etc.)
        if "." in t and not t.endswith(".B") and not t.endswith(".A"):
            # Has a dot AND it's not a US class share (BRK.B, BF.B style)
            continue
        all_tickers.add(t.upper())
    return sorted(all_tickers)'''


# ── universe_tickers.py: switch get_all_tickers to use US-only ──
UNIV_OLD = '''def get_all_tickers():
    """Return deduplicated list of all tickers (US + international)."""
    all_tickers = set()
    for t in SP500 + RUSSELL_1000_ADDITIONS:
        t = t.strip().upper()
        if t:
            all_tickers.add(t)
    
    # Add international tickers
    try:
        from international_tickers import get_international_tickers
        intl = get_international_tickers()
        for t in intl:
            all_tickers.add(t)
    except ImportError:
        pass
    
    return sorted(all_tickers)'''

UNIV_NEW = '''def get_all_tickers():
    """Return deduplicated list of all tickers (US + ADRs of international).
    
    v1.2.0: now uses get_us_listed_tickers() so foreign-exchange tickers
    (.L, .T, .DE, .HK etc.) are excluded. SEC EDGAR cannot fetch them, and
    they previously caused ghost records in the SEC aggregate."""
    all_tickers = set()
    for t in SP500 + RUSSELL_1000_ADDITIONS:
        t = t.strip().upper()
        if t:
            all_tickers.add(t)
    
    # v1.2.0: US-listed ADRs only (SHEL, BP, HSBC, AZN, GSK, RIO, BHP, etc.)
    try:
        from international_tickers import get_us_listed_tickers
        intl = get_us_listed_tickers()
        for t in intl:
            all_tickers.add(t)
    except ImportError:
        # Fallback to old behavior if get_us_listed_tickers not yet deployed
        try:
            from international_tickers import get_international_tickers
            intl = get_international_tickers()
            for t in intl:
                if "." not in t or t.endswith(".B") or t.endswith(".A"):
                    all_tickers.add(t)
        except ImportError:
            pass
    
    return sorted(all_tickers)'''


def patch_file(target, old, new, label):
    src = target.read_text()
    if old not in src:
        sys.exit(f"ABORT [{label}] — anchor not found in {target.name}")
    if new in src:
        print(f"  [{label}] already patched — skipping")
        return False
    new_src = src.replace(old, new, 1)
    if new_src == src:
        sys.exit(f"ABORT [{label}] — replacement had no effect")
    
    tmp = target.with_suffix(target.suffix + ".tmp")
    backup = target.with_suffix(target.suffix + ".intl_bak")
    tmp.write_text(new_src)
    
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(tmp)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        tmp.unlink()
        sys.exit(f"ABORT [{label}] — py_compile failed:\n{result.stderr}")
    
    shutil.copy2(target, backup)
    tmp.replace(target)
    print(f"  ✓ [{label}] {target.name} patched (backup: {backup.name})")
    return True


def main():
    if not INTL_TARGET.exists():
        sys.exit(f"NOT FOUND: {INTL_TARGET}")
    if not UNIV_TARGET.exists():
        sys.exit(f"NOT FOUND: {UNIV_TARGET}")
    
    print("Applying Patcher 27 — international US-only filter:")
    intl_changed = patch_file(INTL_TARGET, INTL_OLD, INTL_NEW, "international_tickers")
    univ_changed = patch_file(UNIV_TARGET, UNIV_OLD, UNIV_NEW, "universe_tickers")
    
    if not (intl_changed or univ_changed):
        print("\n  No changes applied (both files already patched).")
        return
    
    print()
    print("  v1.2.0 international US-only filter applied.")
    print()
    print("  Effect:")
    print("    - universe_tickers.get_all_tickers() now excludes foreign-listed")
    print("      tickers (.L, .T, .DE etc.) from SEC iteration")
    print("    - US-listed ADRs (SHEL, BP, HSBC, AZN, GSK, RIO, BHP, BTI, DEO,")
    print("      LYG, BCS, NWG, VOD, etc.) are still included → they'll get scored")
    print("    - foreign-listed tickers stay available via get_international_tickers()")
    print("      for Yahoo Finance / Finnhub use later")
    print()
    print("  Verify locally:")
    print("    cd pipeline && python3 -c \"")
    print("    from universe_tickers import get_all_tickers")
    print("    from international_tickers import get_us_listed_tickers, get_international_tickers")
    print("    print('US-only intl:', len(get_us_listed_tickers()))")
    print("    print('All intl:', len(get_international_tickers()))")
    print("    print('Universe (now US-only):', len(get_all_tickers()))")
    print("    \"")


if __name__ == "__main__":
    main()
