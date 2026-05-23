#!/usr/bin/env python3
"""
HI Grade — Enrich all_scores.json domains from sp500_domains.py

Many scored records have domains=null because the scoring pipeline doesn't
populate them; api_server.py injects domains at runtime from sp500_domains.py
(DOMAIN_MAP). This script makes that injection persistent in the source data
file, so dedupe operations can correctly identify same-domain duplicates.

Without this enrichment, the COIN scored record has domains=null while the
seed Coinbase record has domains=["coinbase.com"] — meaning dedupe v3 never
even compares them (no shared domain = no pairing).

Usage:
  cd ~/Desktop/repo
  python3 enrich_domains.py             # dry-run
  python3 enrich_domains.py --apply
"""

import argparse
import json
import shutil
import sys
import importlib.util
from pathlib import Path
from datetime import datetime


def find_repo_root():
    for c in [Path.home() / "Desktop" / "repo", Path("/mnt/project"), Path.cwd()]:
        if (c / "pipeline" / "data" / "scores" / "all_scores.json").exists():
            return c
    return None


def load_domain_map(root):
    """Load DOMAIN_MAP from sp500_domains.py."""
    sp500_path = root / "pipeline" / "sp500_domains.py"
    if not sp500_path.exists():
        # Try root-level
        sp500_path = root / "sp500_domains.py"
    if not sp500_path.exists():
        print(f"  ✗ Could not find sp500_domains.py")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("sp500_domains", sp500_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    if hasattr(mod, "DOMAIN_MAP"):
        return mod.DOMAIN_MAP
    print(f"  ✗ DOMAIN_MAP not found in {sp500_path}")
    sys.exit(1)


def enrich(scores, domain_map, verbose=True):
    """Add domains from DOMAIN_MAP to scored records that lack them.
    Idempotent — only adds domains not already present.
    """
    records_touched = 0
    domains_added = 0
    additions_detail = []

    for rec in scores:
        t = (rec.get("ticker") or "").upper().strip()
        if not t or t not in domain_map:
            continue

        current = rec.get("domains")
        if current is None:
            current = []
        current_set = set((d or "").lower().strip() for d in current)

        to_add = []
        for d in domain_map[t]:
            d_norm = (d or "").lower().strip()
            if d_norm and d_norm not in current_set:
                to_add.append(d)
                current_set.add(d_norm)

        if to_add:
            if rec.get("domains") is None:
                rec["domains"] = []
            rec["domains"].extend(to_add)
            records_touched += 1
            domains_added += len(to_add)
            additions_detail.append({
                "ticker": t,
                "company": rec.get("company", ""),
                "before": current,
                "added": to_add,
            })

    if verbose:
        print(f"\n  Will enrich {records_touched} records ({domains_added} domain entries)\n")
        # Show first 10 changes as preview
        for d in additions_detail[:10]:
            before = d["before"] if d["before"] else "null"
            print(f"    {d['ticker']:<6} ({d['company'][:40]:40})")
            print(f"      before: {before}")
            print(f"      added : {d['added']}")
        if len(additions_detail) > 10:
            print(f"    ...and {len(additions_detail) - 10} more")

    return scores, additions_detail


def main():
    ap = argparse.ArgumentParser(description="Enrich domain info in all_scores.json")
    ap.add_argument("--apply", action="store_true", help="Write changes")
    ap.add_argument("--root", default=None)
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    print("═══ HI Grade — Domain Enricher ═══\n")

    root = Path(args.root) if args.root else find_repo_root()
    if not root:
        print("  ✗ Could not locate repo. Pass --root.")
        sys.exit(1)

    print(f"  Repo: {root}")

    domain_map = load_domain_map(root)
    print(f"  Loaded DOMAIN_MAP: {len(domain_map)} tickers")

    scores_path = root / "pipeline" / "data" / "scores" / "all_scores.json"
    with open(scores_path) as f:
        scores = json.load(f)
    print(f"  Loaded scores: {len(scores)} records")

    enriched, detail = enrich(scores, domain_map)

    if not detail:
        print("  Nothing to enrich. Exiting.")
        return

    if not args.apply:
        print("\n  --apply not set; not writing.")
        return

    if not args.no_backup:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = scores_path.with_suffix(f".pre_enrich_{ts}.bak")
        shutil.copy2(scores_path, bak)
        print(f"\n  Backup: {bak}")

    tmp = scores_path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(enriched, f, indent=2)
    tmp.replace(scores_path)
    print(f"  ✓ Wrote: {scores_path}\n")


if __name__ == "__main__":
    main()
