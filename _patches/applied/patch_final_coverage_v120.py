#!/usr/bin/env python3
"""
v1.2.0 Final Coverage Polish — pipeline/data_collector.py

After Patchers 26+27+28 + full re-collection, coverage went 308 → 757.
Audit found 6 remaining holes that this patcher closes:

Holes:
  - BRK.B (Berkshire) — not collected. Root cause: SEC's company_tickers.json
    uses HYPHEN for class shares ("BRK-B") while everyone else uses DOT
    ("BRK.B"). Pipeline lookup fails the string match.
  - BF.B (Brown-Forman) — same SEC hyphen vs dot issue.
  - SHEL/BP/GSK/BTI — major UK ADRs in international_tickers.FTSE_100 but
    not in our ADR_NAMES backfill dict. Names stay empty → ghost records.

Fix 1: Normalize ticker for SEC lookup. Try both dot AND hyphen forms.
Fix 2: Extend ADR_NAMES with 16 more global ADRs.

After this patch + one more full run (--incremental 0), coverage should
reach ~775 tickers including all major US-listed global ADRs.

Anchors: exact-string match on (a) the SEC ticker lookup block, (b) the
ADR_NAMES dict definition.

Usage (from repo root):
  python3 patch_final_coverage_v120.py
"""

import sys
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
TARGET = REPO_ROOT / "pipeline" / "data_collector.py"


# ── Fix 1: SEC ticker lookup with dot-to-hyphen normalization ──
LOOKUP_OLD = '''        # First get CIK
        ticker_map = safe_get("https://www.sec.gov/files/company_tickers.json", headers=SEC_HEADERS)
        cik = None
        if ticker_map:
            for entry in ticker_map.values():
                if entry.get("ticker", "").upper() == ticker.upper():
                    cik = str(entry["cik_str"]).zfill(10)
                    result["company"] = entry.get("title", company_name)
                    break'''

LOOKUP_NEW = '''        # First get CIK
        ticker_map = safe_get("https://www.sec.gov/files/company_tickers.json", headers=SEC_HEADERS)
        cik = None
        if ticker_map:
            # v1.2.0 fix: SEC uses HYPHEN for class shares (BRK-B, BF-B) while
            # everyone else uses DOT (BRK.B, BF.B). Try both forms in lookup.
            ticker_upper = ticker.upper()
            ticker_hyphen = ticker_upper.replace(".", "-")
            for entry in ticker_map.values():
                entry_ticker = entry.get("ticker", "").upper()
                if entry_ticker == ticker_upper or entry_ticker == ticker_hyphen:
                    cik = str(entry["cik_str"]).zfill(10)
                    result["company"] = entry.get("title", company_name)
                    break'''


# ── Fix 2: Extend ADR_NAMES dict ──
ADR_OLD = '''    # ADR fallback: major foreign filers not in sp500_companies (different SEC filing format)
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
    }'''

ADR_NEW = '''    # ADR fallback: major foreign filers not in sp500_companies (different SEC filing format)
    # v1.2.0 final polish: extended with UK/Asian/Indian ADRs that audit found missing
    ADR_NAMES = {
        # Asia/Pacific
        "TSM":  "Taiwan Semiconductor Manufacturing Company Limited",
        "BABA": "Alibaba Group Holding Limited",
        "PDD":  "PDD Holdings Inc.",
        "JD":   "JD.com, Inc.",
        "NTES": "NetEase, Inc.",
        "BIDU": "Baidu, Inc.",
        "TCOM": "Trip.com Group Limited",
        "TM":   "Toyota Motor Corporation",
        "SONY": "Sony Group Corporation",
        "SHOP": "Shopify Inc.",
        "SE":   "Sea Limited",
        # Indian ADRs
        "INFY": "Infosys Limited",
        "HDB":  "HDFC Bank Limited",
        "WIT":  "Wipro Limited",
        # European ADRs
        "ASML": "ASML Holding N.V.",
        "SAP":  "SAP SE",
        "STM":  "STMicroelectronics N.V.",
        "NVO":  "Novo Nordisk A/S",
        "NVS":  "Novartis AG",
        "BUD":  "Anheuser-Busch InBev SA/NV",
        # UK ADRs
        "AZN":  "AstraZeneca plc",
        "GSK":  "GSK plc",
        "SHEL": "Shell plc",
        "BP":   "BP p.l.c.",
        "BTI":  "British American Tobacco p.l.c.",
        "DEO":  "Diageo plc",
        "UL":   "Unilever PLC",
        "VOD":  "Vodafone Group Plc",
        "LYG":  "Lloyds Banking Group plc",
        "BCS":  "Barclays PLC",
        "NWG":  "NatWest Group plc",
        "WPP":  "WPP plc",
        "HSBC": "HSBC Holdings plc",
        # Australian/Mining
        "BHP":  "BHP Group Limited",
        "RIO":  "Rio Tinto plc",
        # North American
        "TD":   "Toronto-Dominion Bank",
        "RY":   "Royal Bank of Canada",
    }'''


def patch_block(src, old, new, label):
    if old not in src:
        sys.exit(f"ABORT [{label}] — anchor not found in data_collector.py")
    if new in src:
        print(f"  [{label}] already patched, skipping")
        return src, False
    if src.count(old) != 1:
        sys.exit(f"ABORT [{label}] — anchor appears {src.count(old)} times, ambiguous")
    return src.replace(old, new, 1), True


def main():
    if not TARGET.exists():
        sys.exit(f"NOT FOUND: {TARGET}")

    src = TARGET.read_text()
    new_src = src
    changes = 0

    print("Applying Patcher 29 — final coverage polish:")

    new_src, did_lookup = patch_block(new_src, LOOKUP_OLD, LOOKUP_NEW, "SEC dot-to-hyphen")
    if did_lookup:
        print("  ✓ SEC ticker lookup now tries dot AND hyphen forms (BRK.B → BRK-B)")
        changes += 1

    new_src, did_adr = patch_block(new_src, ADR_OLD, ADR_NEW, "ADR_NAMES expansion")
    if did_adr:
        print("  ✓ ADR_NAMES extended to 37 entries (was 20) — adds SHEL, BP, GSK, BTI, VOD, etc.")
        changes += 1

    if changes == 0:
        print("\n  No changes applied. File already up to date.")
        return

    # Atomic write
    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    backup = TARGET.with_suffix(TARGET.suffix + ".final_polish_bak")
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

    print()
    print(f"✓ Patched: {TARGET}")
    print(f"  Backup: {backup.name}")
    print(f"  Python syntax: clean")
    print()
    print("  Expected effect after next full run (--incremental 0):")
    print("    + BRK.B (Berkshire Hathaway)")
    print("    + BF.B (Brown-Forman)")
    print("    + SHEL, BP, GSK, BTI, VOD, LYG, BCS, NWG, WPP (UK ADRs)")
    print("    + PDD, NTES, BIDU, JD, TCOM (Asian ADRs)")
    print("    + INFY, HDB, WIT (Indian ADRs)")
    print("    Total expected: ~775 tickers (was 757)")
    print()
    print("  Next:")
    print("    git add pipeline/data_collector.py")
    print("    git commit + push")
    print("    Trigger: gh workflow run \"Daily HI. Pipeline\" --ref main")


if __name__ == "__main__":
    main()
