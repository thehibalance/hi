#!/usr/bin/env python3
"""
v1.2.0 Coverage Fix — pipeline/data_collector.py

Bugs found in audit #6 + investigation:
  - 353 of 659 SEC aggregate records have empty company name (54%)
  - Scoring engine drops empty-name records silently (line 1685: groups by
    normalize_name(key); empty key → empty norm → no entry)
  - Real impact: ADRs (TSM, BABA, ASML, NVO, TM), Berkshire (BRK.B), Brown-Forman
    (BF.B), and ~340 other tickers never reach scored output despite having
    SEC data on disk
  - True S&P 500 coverage: ~63% (308/503), not the 92% surface count suggests

Root cause: load_company_list() at line ~75 builds the master iteration list.
For tickers from universe_tickers.get_all_tickers() that aren't already in
all_scores.json, it appends them with name="" and a comment "Will be resolved
by SEC/Finnhub." But the SEC resolution at fetch_sec line 167-170 only fires
if SEC's company_tickers.json lookup matches. For ADRs and dot-tickers and
rate-limited fetches, the lookup fails → name stays empty → ghost record.

Fix: at load_company_list, backfill name from sp500_companies.SP500 (which has
authoritative (ticker, name) tuples for the entire S&P 500 + Russell 1000)
PLUS an ADR fallback dict for the major foreign filers.

Anchor: exact-string match on the existing universe-ticker append block.

Usage (from repo root):
  python3 patch_load_company_list_v120.py
"""

import sys
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
TARGET = REPO_ROOT / "pipeline" / "data_collector.py"


# ── Anchor: existing universe-ticker append block (lines ~87-105) ──
OLD_BLOCK = '''    # Add universe tickers not already in scores
    try:
        from universe_tickers import get_all_tickers
        universe = get_all_tickers()
        new_count = 0
        for ticker in universe:
            if ticker.upper() not in seen_tickers:
                companies.append({
                    "name": "",  # Will be resolved by SEC/Finnhub
                    "ticker": ticker,
                    "industry": "",
                    "sic": "",
                    "domains": [],
                })
                seen_tickers.add(ticker.upper())
                new_count += 1
        if new_count:
            print(f"  Universe tickers: {new_count} new tickers added (total: {len(companies)})")
    except ImportError:
        print("  No universe_tickers.py found, using existing scores only.")'''


NEW_BLOCK = '''    # v1.2.0 fix: build a ticker→name lookup from authoritative sources before
    # iterating universe tickers. This ensures we never pass an empty name to
    # fetch_sec(), which previously caused 353 ghost records (empty company
    # field in SEC aggregate) that scoring engine silently dropped.
    name_lookup = {}

    # Primary source: sp500_companies.SP500 — (ticker, name) tuples for full S&P 500
    try:
        from sp500_companies import SP500 as _SP500
        for _t, _n in _SP500:
            if _t and _n:
                name_lookup[_t.upper()] = _n
    except ImportError:
        pass

    # ADR fallback: major foreign filers not in sp500_companies (different SEC filing format)
    ADR_NAMES = {
        "TSM":  "Taiwan Semiconductor Manufacturing Company Limited",
        "BABA": "Alibaba Group Holding Limited",
        "ASML": "ASML Holding N.V.",
        "NVO":  "Novo Nordisk A/S",
        "TM":   "Toyota Motor Corporation",
        "BHP":  "BHP Group Limited",
        "RIO":  "Rio Tinto plc",
        "NVS":  "Novartis AG",
        "AZN":  "AstraZeneca plc",
        "SAP":  "SAP SE",
        "SHOP": "Shopify Inc.",
        "SE":   "Sea Limited",
        "SONY": "Sony Group Corporation",
        "TD":   "Toronto-Dominion Bank",
        "RY":   "Royal Bank of Canada",
        "HSBC": "HSBC Holdings plc",
        "DEO":  "Diageo plc",
        "UL":   "Unilever PLC",
        "BUD":  "Anheuser-Busch InBev SA/NV",
        "STM":  "STMicroelectronics N.V.",
    }
    for _t, _n in ADR_NAMES.items():
        if _t not in name_lookup:
            name_lookup[_t] = _n

    # Add universe tickers not already in scores
    try:
        from universe_tickers import get_all_tickers
        universe = get_all_tickers()
        new_count = 0
        unresolved_count = 0
        for ticker in universe:
            if ticker.upper() not in seen_tickers:
                # v1.2.0: lookup authoritative name; empty only if truly unknown
                resolved_name = name_lookup.get(ticker.upper(), "")
                if not resolved_name:
                    unresolved_count += 1
                companies.append({
                    "name": resolved_name,  # populated from sp500_companies + ADR fallback
                    "ticker": ticker,
                    "industry": "",
                    "sic": "",
                    "domains": [],
                })
                seen_tickers.add(ticker.upper())
                new_count += 1
        if new_count:
            print(f"  Universe tickers: {new_count} new tickers added (total: {len(companies)})")
        if unresolved_count:
            print(f"    ⚠ {unresolved_count} of those have no name in sp500_companies or ADR_NAMES — SEC will try to resolve at fetch time")
    except ImportError:
        print("  No universe_tickers.py found, using existing scores only.")

    # Also backfill any name='' entries that came from existing scores
    backfilled = 0
    for c in companies:
        if not c.get("name") and c.get("ticker"):
            resolved = name_lookup.get(c["ticker"].upper(), "")
            if resolved:
                c["name"] = resolved
                backfilled += 1
    if backfilled:
        print(f"  Name backfill: {backfilled} companies got names from sp500_companies/ADR list")'''


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()

    if OLD_BLOCK not in src:
        sys.exit(
            "ABORT — anchor block not found verbatim.\n"
            "load_company_list() may have been edited.\n"
            "Look for the universe-ticker append block around line 87-105."
        )

    if NEW_BLOCK in src:
        sys.exit("ABORT — file already contains v1.2.0 coverage fix. No-op.")

    new_src = src.replace(OLD_BLOCK, NEW_BLOCK, 1)
    if new_src == src:
        sys.exit("ABORT — replacement had no effect.")

    # Atomic write
    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    backup = TARGET.with_suffix(TARGET.suffix + ".coverage_bak")
    tmp.write_text(new_src)

    # py_compile validation
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(tmp)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        tmp.unlink()
        sys.exit(f"ABORT — py_compile failed:\n{result.stderr}")

    shutil.copy2(TARGET, backup)
    tmp.replace(TARGET)

    print(f"✓ Patched: {TARGET}")
    print(f"  Backup: {backup.name}")
    print()
    print("  Coverage fix applied:")
    print("    - load_company_list now backfills names from sp500_companies.SP500")
    print("    - ADR_NAMES dict adds 20 major foreign filers (TSM, BABA, ASML, etc.)")
    print("    - Existing companies with name='' get backfilled too")
    print()
    print("  Next:")
    print("    1. Verify the change locally first:")
    print("       cd pipeline && python3 -c \"from data_collector import load_company_list; print(len(load_company_list()))\"")
    print("    2. Commit + push to main")
    print("    3. Tonight's cron picks up new logic, regenerates aggregate with names populated")
    print("    4. Tomorrow morning: re-audit. Expected: scored universe jumps from 308 to ~480")


if __name__ == "__main__":
    main()
