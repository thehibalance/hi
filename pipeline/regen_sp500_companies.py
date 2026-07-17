#!/usr/bin/env python3
"""
Regenerate pipeline/sp500_companies.py from universe_tickers.

Why this exists:
  sp500_companies.py is the source-of-truth ticker list for SEC EDGAR, FMP,
  and Yahoo pipelines. It is currently stale at 315 entries while
  universe_tickers (SP500 ∪ RUSSELL_1000_ADDITIONS) has ~589 US tickers.
  The gap means ~half the universe never gets SEC/FMP/Yahoo data and
  therefore never enters all_scores.json — which every other enrichment
  pipeline keys off of.

  Fixing sp500_companies once propagates everywhere: SEC/FMP/Yahoo pull the
  full list → all_scores.json grows → Finnhub/AlphaVantage/8-K/NewsAPI etc.
  enrich the new records on the next daily run.

What this script does:
  1. Imports universe_tickers.SP500 and universe_tickers.RUSSELL_1000_ADDITIONS
     (US-only; intentionally skips get_all_tickers() because that includes
     international tickers like .KS/.DE that SEC EDGAR cannot fetch)
  2. Fetches SEC's company_tickers.json (public endpoint, no auth) for
     ticker→company_name lookup
  3. Writes new pipeline/sp500_companies.py with (ticker, name) tuples
  4. Falls back to ticker-as-name for the rare ticker SEC doesn't recognize
     (only used for display/logging in pipelines; CIK lookup uses ticker)

Safety guards:
  - Aborts if SEC fetch fails (no overwrite with empty data)
  - Aborts if fewer than 400 entries would be written (regression guard)
  - py_compile + module-load validation before swap
  - Atomic write: tmp → verify → backup → rename
  - Idempotent: re-running is safe; rebuilds from current sources

Usage (from repo root):
  python3 pipeline/regen_sp500_companies.py
"""

import sys
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TARGET = SCRIPT_DIR / "sp500_companies.py"

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
# SEC requires a User-Agent identifying the requester. Use the project email.
SEC_HEADERS = {"User-Agent": "HI Balance hi@thehibalance.org"}

MIN_EXPECTED_ENTRIES = 400  # regression guard


def fetch_sec_name_lookup():
    """Fetch SEC's authoritative ticker→company_name mapping.

    Returns dict like {"AAPL": "Apple Inc.", "MSFT": "Microsoft Corp", ...}
    """
    req = urllib.request.Request(SEC_TICKERS_URL, headers=SEC_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    # SEC format: {"0": {"cik_str": ..., "ticker": "AAPL", "title": "Apple Inc."}, ...}
    lookup = {}
    for entry in data.values():
        ticker = (entry.get("ticker") or "").upper()
        title = (entry.get("title") or "").strip()
        if ticker and title:
            lookup[ticker] = title
    return lookup


def normalize_ticker_for_sec(t):
    """SEC uses dashes for class shares (BRK-B), some sources use dots (BRK.B)."""
    return t.replace(".", "-").upper()


def main():
    # Import universe_tickers.SP500 + RUSSELL_1000_ADDITIONS (US-only union)
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        from universe_tickers import SP500, RUSSELL_1000_ADDITIONS
    except ImportError as e:
        sys.exit(f"ABORT — couldn't import universe_tickers SP500/RUSSELL_1000_ADDITIONS: {e}")

    # Dedupe + sort. Skip get_all_tickers() because it includes international
    # tickers (.KS, .DE) which SEC EDGAR cannot fetch.
    universe = sorted(set(SP500) | set(RUSSELL_1000_ADDITIONS))

    print(f"  universe_tickers.SP500:                 {len(SP500)} tickers")
    print(f"  universe_tickers.RUSSELL_1000_ADDITIONS: {len(RUSSELL_1000_ADDITIONS)} tickers")
    print(f"  Union (US-only):                         {len(universe)} tickers")
    if len(universe) < MIN_EXPECTED_ENTRIES:
        sys.exit(
            f"ABORT — combined universe has only {len(universe)} entries "
            f"(< {MIN_EXPECTED_ENTRIES}). universe_tickers.py may itself be stale."
        )

    # Fetch SEC name lookup
    print(f"  Fetching SEC ticker→name from {SEC_TICKERS_URL} ...")
    try:
        sec_names = fetch_sec_name_lookup()
        print(f"  SEC returned {len(sec_names)} ticker→name pairs")
    except Exception as e:
        sys.exit(f"ABORT — SEC fetch failed: {type(e).__name__}: {e}")

    if len(sec_names) < 5000:
        sys.exit(
            f"ABORT — SEC returned only {len(sec_names)} pairs (suspicious; expect 10k+). "
            "Refusing to overwrite sp500_companies.py with possibly-incomplete data."
        )

    # Build (ticker, name) tuples
    rows = []
    no_name = []
    for t in universe:
        upper = t.upper()
        name = sec_names.get(upper) or sec_names.get(normalize_ticker_for_sec(t))
        if name:
            rows.append((t, name))
        else:
            rows.append((t, t))  # fallback: use ticker as display name
            no_name.append(t)

    print(f"  Mapped {len(rows) - len(no_name)}/{len(rows)} tickers to SEC names")
    if no_name:
        sample = ", ".join(no_name[:8])
        more = f" (+{len(no_name)-8} more)" if len(no_name) > 8 else ""
        print(f"  ⚠ {len(no_name)} tickers had no SEC name, using ticker as name: {sample}{more}")

    if len(rows) < MIN_EXPECTED_ENTRIES:
        sys.exit(
            f"ABORT — only {len(rows)} rows would be written "
            f"(< {MIN_EXPECTED_ENTRIES} guard). Refusing to regress sp500_companies.py."
        )

    # Format new file content
    lines = [
        "#!/usr/bin/env python3",
        '"""',
        "S&P 500 + Russell 1000 additions, as (ticker, name) tuples.",
        "",
        "Source-of-truth for SEC EDGAR, FMP, and Yahoo pipelines. Other pipelines",
        "(Finnhub, AlphaVantage, SEC 8-K, NewsAPI, OpenCorporates, etc.) read from",
        "data/scores/all_scores.json which is bootstrapped by SEC/FMP/Yahoo, so",
        "expanding this list cascades through the whole pipeline.",
        "",
        "Auto-generated from universe_tickers (SP500 ∪ RUSSELL_1000_ADDITIONS) +",
        "SEC company_tickers.json. International tickers from get_all_tickers() are",
        "intentionally excluded — SEC EDGAR cannot fetch foreign filers.",
        "",
        "Regenerate with: python3 pipeline/regen_sp500_companies.py",
        "",
        "Note: variable is still named SP500 for backward compat with importers",
        "(sec_edgar_pipeline.py, fmp_pipeline.py, yahoo_pipeline.py).",
        '"""',
        "",
        "SP500 = [",
    ]
    for t, n in rows:
        n_escaped = n.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    ("{t}", "{n_escaped}"),')
    lines.append("]")
    lines.append("")
    new_src = "\n".join(lines)

    # Atomic write
    tmp = TARGET.with_suffix(TARGET.suffix + ".tmp")
    backup = TARGET.with_suffix(TARGET.suffix + ".bak")
    tmp.write_text(new_src)

    # py_compile validation (sufficient — .tmp extensions break importlib.spec_from_file_location)
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(tmp)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        tmp.unlink()
        sys.exit(f"ABORT — py_compile failed on new file:\n{result.stderr}")

    # Backup + swap
    if TARGET.exists():
        shutil.copy2(TARGET, backup)
    tmp.replace(TARGET)

    # Post-swap sanity check: import and count (now safe — file is named .py)
    post_check = subprocess.run(
        [sys.executable, "-c",
         f"import sys; sys.path.insert(0, '{SCRIPT_DIR}'); "
         f"from sp500_companies import SP500; "
         f"assert len(SP500) >= {MIN_EXPECTED_ENTRIES}, f'too few: {{len(SP500)}}'; "
         f"print(f'  Post-swap import OK: {{len(SP500)}} entries loaded')"],
        capture_output=True, text=True
    )
    if post_check.returncode != 0:
        # Roll back from backup
        if backup.exists():
            shutil.copy2(backup, TARGET)
        sys.exit(f"ABORT — post-swap import failed (rolled back from backup):\n{post_check.stderr}")
    print(post_check.stdout.rstrip())

    old_count = "315 (legacy)"
    print(f"\n✓ Wrote {TARGET}")
    print(f"  Entries: {old_count} → {len(rows)}")
    if backup.exists():
        print(f"  Backup:  {backup}")
    print(f"\n  Next steps:")
    print(f"    git diff pipeline/sp500_companies.py | head -40   # eyeball")
    print(f"    git add pipeline/sp500_companies.py")
    print(f"    git commit -m 'sp500_companies: rebuild from universe_tickers (315→{len(rows)} entries)'")
    print(f"    git push")
    print(f"    # Then trigger pipeline re-run (run_all.py or wait for daily cron)")
    print(f"    # Expect 2 runs to fully propagate (SEC/FMP/Yahoo first, then enrichment pipelines)")


if __name__ == "__main__":
    main()
